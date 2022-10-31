"""
Receive information from redis and communicate with the crawler.
"""

import time
import json
import logging
import redis


class TencentIncrementTimer():
    """
    Tencent news crawler incremental crawl timer.
    """

    def __init__(self) -> None:
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
        self.start_urls = urls['tencent_news']

    def execute(self):
        """
        Trigger timer.
        """
        self.add_job()
        while True:
            if len(self.my_redis.lrange('TencentNewsIncre:start_urls', 0, 1)) \
                    == 0:
                self.add_job()
            time.sleep(1)

    def add_job(self):
        """
        Add job into redis.
        """
        logging.info('Insert start_urls into TencentNewsIncre:start_urls')
        for start_url in self.start_urls:
            start = {}
            start['url'] = start_url
            start['meta'] = {'crawler': 'TencentNewsIncre'}
            self.my_redis.lpush('TencentNewsIncre:start_urls',
                                json.dumps(start))


class XinhuaIncrementTimer():
    """
    Xinhua news crawler incremental crawl timer.
    """

    def __init__(self) -> None:
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
        self.start_urls = urls['xinhua_news']

    def execute(self):
        """
        Trigger timer.
        """
        self.add_job()
        while True:
            if len(self.my_redis.lrange('XinhuaNewsIncre:start_urls', 0, 1)) \
                    == 0:
                self.add_job()
            time.sleep(1)

    def add_job(self):
        """
        Add job into redis.
        """
        logging.info('Insert start_urls into XinhuaNewsIncre:start_urls')
        for start_url in self.start_urls:
            start = {}
            start['url'] = start_url
            start['meta'] = {'crawler': 'XinhuaNewsIncre'}
            self.my_redis.lpush('XinhuaNewsIncre:start_urls',
                                json.dumps(start))