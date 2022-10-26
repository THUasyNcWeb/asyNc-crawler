'''
Scrapy pipelines
'''

import json
import logging
import hashlib
import urllib.request
from scrapy.exporters import JsonItemExporter
import psycopg2
from elasticsearch_dsl import Document, Date, Keyword, Text, connections
import elasticsearch


class ArticleType(Document):
    '''
    Define the article type
    '''
    title = Text(analyzer="ik_max_word", search_analyzer="ik_smart")
    content = Text(analyzer="ik_max_word", search_analyzer="ik_smart")
    tags = Text(analyzer="ik_max_word", search_analyzer="ik_smart")
    first_img_url = Keyword()
    news_url = Keyword()
    front_image_path = Keyword()
    media = Keyword()
    create_date = Date()

    def get_url(self):
        """
        return article's url
        """
        return self.news_url

    def get_content(self):
        """
        return content
        """
        return self.content

    class Index:
        """
        Index to connect
        """
        name = "tencent_news"

        def get_index(self):
            """
            return index's name
            """
            return self.name

        def set_index(self, index_name):
            """
            set index
            """
            self.name = index_name


def write_to_es(item_json):
    """
    Export item_json into Elasticsearh
    """
    article = ArticleType(meta={'id': item_json['news_url']})
    article.title = item_json['title']
    article.create_date = item_json['pub_time']
    article.news_url = item_json['news_url']
    article.first_img_url = item_json['first_img_url']
    article.content = item_json['content']
    article.media = item_json['media']
    article.tags = item_json['tags']
    article.save()


class SQLPipeline:
    '''
    The pipeline that exports item into database
    '''

    def __init__(self) -> None:
        '''
        Connect to the database
        '''
        with open('../config/config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        self.postgres = (config['hostname'], config['port'],
                         config['username'], config['password'],
                         config['database'])
        self.connection = psycopg2.connect(
            host=self.postgres[0], port=self.postgres[1],
            user=self.postgres[2], password=self.postgres[3],
            dbname=self.postgres[4])
        self.cur = self.connection.cursor()

        with open('../config/image_path.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        self.image_download_path = config['path']
        self.image_prefix = config['prefix']

        with open('../config/es.json', 'r', encoding='utf-8') as file:
            es_config = json.load(file)
            try:
                connections.create_connection(hosts=[es_config['url']])
                ArticleType.init()
            except (elasticsearch.exceptions.ConnectionError, ConnectionError):
                print("Elasticseach not run")

    def process_item(self, item, spider):
        '''
        Insert the item into the database
        '''
        dul_tag = True
        try:
            query = f'select * from {spider.data_table} where news_url=%s'
            self.cur.execute(query, (item['news_url'],))
            if len(self.cur.fetchall()) == 0:
                dul_tag = False
        except (psycopg2.errors.InFailedSqlTransaction, KeyError):
            self.cur.close()
            self.connection.close()
            self.connection = psycopg2.connect(
                host=self.postgres[0], port=self.postgres[1],
                user=self.postgres[2], password=self.postgres[3],
                dbname=self.postgres[4])
            self.cur = self.connection.cursor()

        try:
            if not dul_tag and item['first_img_url'] != '':
                img_url = item['first_img_url'].strip()
                md5 = hashlib.md5(img_url.encode(encoding='UTF-8')) \
                             .hexdigest()
                item['first_img_url'] = 'https:' + \
                                        item['first_img_url']
                filepath = self.image_download_path + md5 + '.jpg'
                urllib.request.urlretrieve(
                    item['first_img_url'], filename=filepath)
                item['first_img_url'] = self.image_prefix + \
                    md5 + '.jpg'
        except urllib.error.URLError:
            print("Error occurred when downloading file, error message:")
            print('urllib.error.URLError')

        try:
            if not dul_tag:
                query = f'INSERT INTO {spider.data_table}(news_url, media, \
                          category, tags, title, description, content, \
                          first_img_url, pub_time) \
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) \
                          ON CONFLICT (news_url) DO NOTHING;'
                self.cur.execute(query, (item['news_url'], item['media'],
                                         item['category'], item['tags'],
                                         item['title'], item['description'],
                                         item['content'],
                                         item['first_img_url'],
                                         item['pub_time']))
                self.connection.commit()
        except (psycopg2.errors.InFailedSqlTransaction, KeyError):
            self.cur.close()
            self.connection.close()
            self.connection = psycopg2.connect(
                host=self.postgres[0], port=self.postgres[1],
                user=self.postgres[2], password=self.postgres[3],
                dbname=self.postgres[4])
            self.cur = self.connection.cursor()
            logging.warning(
                'Error Insertion:\nnews_url: %s\nmedia: %s\n\
                 category: %s\ntags: %s\ntitle: %s\n\
                 description: %s\ncontent: %s\n\
                 first_img_url: %s\npub_time: %s',
                item['news_url'], item['media'], item['category'],
                item['tags'], item['title'], item['description'],
                item['content'], item['first_img_url'], item['pub_time'])

            with open('insert_error.json', 'ab', encoding='utf-8') as file:
                JsonItemExporter(file, encoding="utf-8",
                                 ensure_ascii=False).export_item(item)
                file.close()
        try:
            if not dul_tag:
                write_to_es(item)
        except (elasticsearch.exceptions.ConnectionError, ConnectionError):
            print("Elasticseach not run")
        return item

    def close_spider(self, _spider):
        '''
        Close the connection with the database
        '''
        if self.connection:
            self.cur.close()
            self.connection.close()
