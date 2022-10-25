'''
Scrapy pipelines
'''

import json
import logging
from scrapy.exporters import JsonItemExporter
import psycopg2
from elasticsearch_dsl import Document, Date, Keyword, Text, connections
import elasticsearch


class ArticleType(Document):
    '''
    Define the article type
    '''
    title = Text(analyzer="ik_max_word")
    tags = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")
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
        self.hostname = config['hostname']
        self.port = config['port']
        self.username = config['username']
        self.password = config['password']
        self.database = config['database']
        self.connection = psycopg2.connect(
            host=self.hostname, port=self.port, user=self.username,
            password=self.password, dbname=self.database)
        self.cur = self.connection.cursor()

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
        del spider
        try:
            self.cur.execute('INSERT INTO news(news_url, media, category,\
                              tags, title, description, content, \
                              first_img_url, pub_time) \
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) \
                              ON CONFLICT (news_url) DO NOTHING;',
                             (item['news_url'], item['media'],
                              item['category'], item['tags'],
                              item['title'], item['description'],
                              item['content'], item['first_img_url'],
                              item['pub_time']))
            self.connection.commit()
        except (psycopg2.errors.InFailedSqlTransaction, KeyError):
            self.cur.close()
            self.connection.close()
            self.connection = psycopg2.connect(
                host=self.hostname, port=self.port,
                user=self.username, password=self.password,
                dbname=self.database)
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
