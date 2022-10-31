"""
Receive information from redis and communicate with the crawler.
"""

import time
import json
import logging
import redis
import schedule


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
        with open('./url.json', 'r', encoding='utf-8') as file:
            urls = json.load(file)
        self.start_urls = urls['tencent_news']

    def execute(self):
        """
        Trigger timer.
        """
        self.add_job()
        schedule.every(1).seconds.do(self.add_job)
        while True:
            schedule.run_pending()
            time.sleep(0.5)

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


if __name__ == '__main__':
    tencent_timer = TencentIncrementTimer()
    tencent_timer.execute()
