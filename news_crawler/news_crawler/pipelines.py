'''
Scrapy pipelines
'''

import json
import logging

from elasticsearch_dsl import Document, Date, Keyword
from elasticsearch_dsl import Text, connections, Completion
import elasticsearch

from tinyrpc import RPCClient
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport

from scrapy.exporters import JsonItemExporter
import psycopg2
import news_crawler.utils.utils as Utils


class ArticleType(Document):
    '''
    Define the article type
    '''
    title = Text(analyzer="ik_max_word", search_analyzer="ik_smart")
    content = Text(analyzer="ik_max_word", search_analyzer="ik_smart")
    tags = Text(analyzer="ik_max_word", search_analyzer="ik_smart")
    category = Text(analyzer="ik_max_word", search_analyzer="ik_smart")
    first_img_url = Keyword()
    news_url = Keyword()
    front_image_path = Keyword()
    media = Keyword()
    create_date = Date()
    suggest = Completion(analyzer="ik_max_word")

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


def gen_suggest(index, info_tuple):
    """_summary_

    Args:
        index (_type_): index path
        info_tuple (_type_): base and keywords

    Returns:
        _type_: generating suggestions
    """
    used_words = set()
    suggests = []

    for text, weight in info_tuple:
        if text:
            # 调用ES的analyzer接口进行分词
            esearch = connections.create_connection(ArticleType)
            params = {
                'filter': ['lowercase']
                }
            body = {
                "analyzer": "ik_max_word",
                "text": "{0}".format(text)
                }
            words = esearch.indices.analyze(index=index, body=body,
                                            params=params)

            analyzed_words = set()
            for word in words:
                if len(word["token"]) > 1:
                    analyzed_words.add(word["token"])
            new_words = analyzed_words - used_words
        else:
            new_words = set()

        if new_words:
            suggest = {"input": list(new_words), "weight": weight}
            suggests.append(suggest)

    return suggests


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
    article.suggest = item_json['title']+item_json['content']
    article.category = item_json['category']
    article.save()


class RpcClient:
    """
    Type designed to connect with search backend
    """
    def __init__(self) -> None:
        try:
            with open('../config/lucene.json', 'r', encoding='utf-8') as file:
                config = json.load(file)
                ip_loc = 'http://' + str(config['url'])
                self.rpc_client = RPCClient(
                    JSONRPCProtocol(),
                    HttpPostClientTransport(ip_loc)
                )

        except Exception as error:
            print(error)
            ip_loc = 'http://asyNc-search-asyNc.app.secoder.net:80'
            self.rpc_client = RPCClient(
                JSONRPCProtocol(),
                HttpPostClientTransport(ip_loc)
                )

        self.rpc_server = self.rpc_client.get_proxy()

    def add_news(self, data):
        """_summary_

        Args:
            data_json (_type_): data of json

        Returns:
            _type_: Success or not
        """
        try:
            data_dict = {}
            for key in data.keys():
                data_dict[key] = data[key]
            self.rpc_server.write_news(data_dict)
            return True
        except Exception as error:
            logging.error(error)
            return False


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

        with open('../config/es.json', 'r', encoding='utf-8') as file:
            es_config = json.load(file)
            try:
                connections.create_connection(hosts=[es_config['url']])
                ArticleType.init()
            except (elasticsearch.exceptions.ConnectionError, ConnectionError):
                print("Elasticseach not run")
        # try:
        #     self.rpc_client = RpcClient()
        # except Exception as error:
        #     print(error)
        #     print("Rpc Not Run")

    def process_item(self, item, spider):
        '''
        Insert the item into the database
        '''
        dul_tag = self.de_dul.is_exist(item['title'])

        try:
            if not dul_tag:
                self.connection.commit()
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
                try:
                    write_to_es(item)
                    # self.rpc_client.add_news(item)
                except Exception as error:
                    print(error)

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
