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
        self.host = config['host']
        self.port = config['port']
        self.password = config['password']
        self.my_redis = redis.Redis(host=self.host,
                                    port=self.port,
                                    decode_responses=True,
                                    password=self.password)

    def execute(self):
        """
        Trigger timer.
        """
        self.add_job()
        schedule.every(10).minutes.do(self.add_job)
        while True:
            schedule.run_pending()
            time.sleep(10)

    def add_job(self):
        """
        Add job into redis.
        """
        logging.info('Insert start_urls into TencentNewsHomePage:start_urls')
        start_urls = ['https://news.qq.com/',
                      'https://new.qq.com/d/bj/',
                      'https://new.qq.com/ch/ent/',
                      'https://new.qq.com/ch/tech/']
        for start_url in start_urls:
            start = {}
            start['url'] = start_url
            start['meta'] = {'crawler': 'TencentNewsHomePage'}
            self.my_redis.lpush('TencentNewsHomePage:start_urls',
                                json.dumps(start))


if __name__ == '__main__':
    tencent_timer = TencentIncrementTimer()
    tencent_timer.execute()
