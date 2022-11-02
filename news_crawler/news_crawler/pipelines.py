'''
Scrapy pipelines
'''

import json
import logging
from scrapy.exporters import JsonItemExporter
import psycopg2
import news_crawler.utils.utils as Utils


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
        self.de_dul = Utils.DeDuplicate()

    def process_item(self, item, spider):
        '''
        Insert the item into the database
        '''
        dul_tag = self.de_dul.is_exist(item['title'])

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
                self.de_dul.insert(item['title'])
        except (psycopg2.errors.InFailedSqlTransaction,
                psycopg2.OperationalError,
                KeyError):
            self.cur.close()
            self.connection.close()
            try:
                self.connection = psycopg2.connect(
                    host=self.postgres[0], port=self.postgres[1],
                    user=self.postgres[2], password=self.postgres[3],
                    dbname=self.postgres[4])
                self.cur = self.connection.cursor()
            except psycopg2.OperationalError:
                pass
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
        return item

    def close_spider(self, _spider):
        '''
        Close the connection with the database
        '''
        if self.connection:
            self.cur.close()
            self.connection.close()
