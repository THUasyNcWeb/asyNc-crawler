import redis
import schedule
import time
import json
import logging

rd = redis.Redis(host='localhost', port=6379, decode_responses=True, password=123456)

def tencent_news_home_page_job():
    logging.info('Insert start_urls into TencentNewsHomePage:start_urls')
    start_urls = ['https://news.qq.com/',
                  'https://new.qq.com/d/bj/',
                  'https://new.qq.com/ch/ent/',
                  'https://new.qq.com/ch/tech/']
    for start_url in start_urls:
        start = {}
        start['url'] = start_url
        start['meta'] = {'crawler': 'TencentNewsHomePage'}
        rd.lpush('TencentNewsHomePage:start_urls', json.dumps(start))

def tencent_news_home_page_execute():
    tencent_news_home_page_job()
    schedule.every(10).minutes.do(tencent_news_home_page_job)
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == '__main__':
    schedule.every(20).seconds.do(tencent_news_home_page_job)
    while True:
        schedule.run_pending()
        time.sleep(10)