from tkinter import INSERT
from scrapy.exporters import JsonItemExporter
import psycopg2
import json


class JsonExporterPipleline(object):
    def __init__(self):
        self.file = open('test.json', 'wb')
        self.exporter = JsonItemExporter(
            self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class PostgreSQLPipline(object):
    def open_spider(self, spider):
        with open('../../config.json', 'r') as f:
            config = json.load(f)
        self.hostname = config['hostname']
        self.port = config['port']
        self.username = config['username']
        self.password = config['password']
        self.database = config['database']
        self.connection = psycopg2.connect(
            host=self.hostname, port=self.port, user=self.username, password=self.password, dbname=self.database)
        self.cur = self.connection.cursor()

    def process_item(self, item, spider):
        try:
            self.cur.execute('INSERT INTO news(news_url, media, category, tags, title, description, content, first_img_url, pub_time) \
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (news_url) DO NOTHING;',
                              (item['news_url'], item['media'], item['category'], item['tags'], item['title'], item['description'],
                              item['content'], item['first_img_url'], item['pub_time']))
            self.connection.commit()
            return item
        except:
            self.cur.close()
            self.connection.close()
            self.connection = psycopg2.connect(
                host=self.hostname, port=self.port, user=self.username, password=self.password, dbname=self.database)
            self.cur = self.connection.cursor()

            file = open('insert_error.json', 'ab')
            JsonItemExporter(file, encoding="utf-8", ensure_ascii=False).export_item(item)
            file.close()
        
        return item

    def close_spider(self, spider):
        if self.connection:
            self.cur.close()
            self.connection.close()
