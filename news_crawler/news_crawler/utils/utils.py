"""
Receive information from redis and communicate with the crawler.
"""

import time
import json
import logging
import redis


class DeDuplicate():
    """
    The news weight checker.
    """

    def __init__(self) -> None:
        with open('../config/redis.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        host = config['host']
        port = config['port']
        password = config['password']
        self.my_redis = redis.Redis(host=host,
                                    port=port,
                                    decode_responses=True,
                                    password=password)
        self.key = 'news_name'

    def is_exist(self, name):
        """
        Check whether the name exist in the redis.
        """
        name_tmp = name[0:10]
        return self.my_redis.sismember(self.key, name_tmp)
    
    def insert(self, name):
        """
        Insert the name of news into redis.
        """
        name_tmp = name[0:10]
        self.my_redis.sadd(self.key, name_tmp)


class IncrementTimer():
    """
    Incremental crawl timer.
    """

    def __init__(self, news_category, key) -> None:
        """
        Init the timer to connect with redis.
        """
        with open('../config/redis.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        host = config['host']
        port = config['port']
        password = config['password']
        self.my_redis = redis.Redis(host=host,
                                    port=port,
                                    decode_responses=True,
                                    password=password)
        with open('./web_news_config.json', 'r', encoding='utf-8') as file:
            urls = json.load(file)
        self.start_urls = urls[news_category]
        self.key = key

    def execute(self):
        """
        Trigger timer.
        """
        self.add_job()
        while True:
            if len(self.my_redis.lrange(self.key, 0, 1)) \
                    == 0:
                self.add_job()
            time.sleep(1)

    def add_job(self):
        """
        Add job into redis.
        """
        logging.info('Insert start_urls into %s', self.key)
        for start_url in self.start_urls:
            start = {}
            start['url'] = start_url
            self.my_redis.lpush(self.key, json.dumps(start))
