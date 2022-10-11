'''
Scrapy pipelines
'''

from scrapy.exporters import JsonItemExporter
import psycopg2
import json
from elasticsearch_dsl import Document, Date, Keyword, Text, connections


class PostgreSQLPipeline:
    '''
    The pipeline that exports item into database
    '''
    def open_spider(self, spider):
        '''
        Connect to the database
        '''
        with open('../config/config.json', 'r') as f:
            config = json.load(f)
        self.hostname = config['hostname']
        self.port = config['port']
        self.username = config['username']
        self.password = config['password']
        self.database = config['database']
        self.connection = psycopg2.connect(
            host=self.hostname, port=self.port, user=self.username,
            password=self.password, dbname=self.database)
        self.cur = self.connection.cursor()

    def process_item(self, item, spider):
        '''
        Insert the item into the database
        '''
        try:
            self.cur.execute('INSERT INTO news(news_url, media, category, tags, \
                              title, description, content, first_img_url, pub_time) \
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) \
                              ON CONFLICT (news_url) DO NOTHING;',
                              (item['news_url'], item['media'], item['category'],
                               item['tags'], item['title'], item['description'],
                               item['content'], item['first_img_url'], item['pub_time']))
            self.connection.commit()
            return item
        except:
            self.cur.close()
            self.connection.close()
            self.connection = psycopg2.connect(
                host=self.hostname, port=self.port,
                user=self.username, password=self.password, dbname=self.database)
            self.cur = self.connection.cursor()

            file = open('insert_error.json', 'ab')
            JsonItemExporter(file, encoding="utf-8", ensure_ascii=False).export_item(item)
            file.close()
        return item

    def close_spider(self, spider):
        '''
        Close the connection with the database
        '''
        if self.connection:
            self.cur.close()
            self.connection.close()


connections.create_connection(hosts=["localhost"])


class ArticleType(Document):
    '''
    Define the article type
    '''
    title = Text(analyzer = "ik_max_word")
    tags = Text(analyzer = "ik_max_word")
    content = Text(analyzer = "ik_max_word")
    first_img_url = Keyword()
    news_url = Keyword()
    front_image_path = Keyword()
    media = Keyword()
    create_date = Date()

    class Index:
        name = "tencent_news"


class ElasticsearchPipeline:
    '''
    The pipeline that export item into ES
    '''
    def process_item(self,item_json):
        '''
        Export item into ES
        '''
        article = ArticleType(meta={'id':item_json['news_url']})
        article.title = item_json['title']
        article.create_date = item_json['pub_time']
        article.news_url = item_json['news_url']
        article.first_img_url = item_json['first_img_url']
        article.content = item_json['content']
        article.tags = item_json['tags']
        article.save()
        