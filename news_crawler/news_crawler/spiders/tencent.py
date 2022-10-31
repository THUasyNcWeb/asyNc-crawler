'''
Crawler of Tencent
'''

import logging
import re
import threading
import json
import scrapy
import redis
from scrapy.http import Request
from scrapy_redis.spiders import RedisSpider

from news_crawler.items import NewsCrawlerItem, NewsCrawlerItemLoader
import news_crawler.utils.utils as IncreTimer


def parse_detail_to_item_loader(response):
    '''
    parse single news item
    '''
    item_loader = NewsCrawlerItemLoader(
        item=NewsCrawlerItem(), response=response)

    item_loader.add_value('news_url', response.url)
    window_data = response.xpath(
        '/html/head/script[7]/text()').extract_first()
    item_loader.add_value('media', re.findall(
        r'"media": "(.*?)"', window_data)[0])
    for catalog in re.findall(r'"catalog1": "(.*?)"', window_data):
        item_loader.add_value('category', catalog)
    for tag in re.findall(r'"tags": "(.*?)"', window_data)[0].split(','):
        item_loader.add_value('tags', tag)
    for title in re.findall(r'"title": "(.*?)"', window_data):
        item_loader.add_value('title', title)
    item_loader.add_xpath('description', '/html/head/meta[2]/@content')
    item_loader.add_value('description', '')
    item_loader.add_xpath(
        'first_img_url', '//img[@class="content-picture"]/@src')
    item_loader.add_value('first_img_url', '')
    item_loader.add_value('pub_time', re.findall(
        r'"pubtime": "(.*?)"', window_data)[0])
    paras = response.xpath(
        '/html/body/div[3]/div[1]/div[1]/div[2]/p/text()').extract()
    if len(paras) == 0:
        paras.append('')
    for para in paras:
        item_loader.add_value('content', para)

    return item_loader


class TencentNewsIncreSpider(RedisSpider):
    '''
    Crawl the TencentNewsIncre
    '''
    name = 'TencentNewsIncre'
    redis_key = "TencentNewsIncre:start_urls"

    def __init__(self, *args, **kwargs):
        '''
        Init the spider
        '''
        self.data_table = kwargs.get('data_table', 'news')
        self.attribution = kwargs.get('attribution', 'minor')
        if self.attribution == 'main':
            incre_timer = IncreTimer.TencentIncrementTimer()
            start_urls_execute = threading.Thread(
                target=incre_timer.execute, daemon=True)
            start_urls_execute.start()
        super().__init__(*args, **kwargs)

    def parse(self, response, **_kwargs):
        '''
        Get all legal urls
        '''
        logging.info('Find news_url from %s', response.url)
        urls_candidate = re.findall(r'"url":"(.*?)"', response.text)
        for url_candidate in urls_candidate:
            if re.match(r'https://new.qq.com/.*?\d{8}[VA]0[0-9A-Z]{4}00',
                        url_candidate) is not None:
                logging.info('Crawl the %s', url_candidate)
                yield Request(url=url_candidate,
                              callback=self.parse_tencent_news)

    def parse_tencent_news(self, response):
        '''
        parse single news item
        '''
        item_loader = parse_detail_to_item_loader(response)

        yield item_loader.load_item()


class TencentNewsAllQuantitySpider(scrapy.Spider):
    '''
    Crawl the TencentNews with all quantity
    '''
    name = 'TencentNewsAllQuantity'
    allowed_domains = ['new.qq.com']
    start_urls = []

    def __init__(self, *_args, **kwargs):
        '''
        Init the legal characters
        '''
        super().__init__()
        self.data_table = kwargs.get('data_table', 'news')
        self.begin_date = int(kwargs.get('begin_date', '20221008'))
        self.end_date = int(kwargs.get('end_date', '20221008'))
        self.legal = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                      'A', 'B', 'C', 'D', 'E', 'F', 'G',
                      'H', 'I', 'J', 'K', 'L', 'M', 'N',
                      'O', 'P', 'Q', 'R', 'S', 'T',
                      'U', 'V', 'W', 'X', 'Y', 'Z']
        self.legal_first = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
        self.legal_date = ((101, 131), (201, 228), (301, 331),
                           (401, 430), (501, 531), (601, 630),
                           (701, 731), (801, 831), (901, 930),
                           (1001, 1031), (1101, 1130), (1201, 1231))

        with open('../config/redis.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        host = config['host']
        port = config['port']
        password = config['password']
        self.my_redis = redis.Redis(host=host,
                                    port=port,
                                    decode_responses=True,
                                    password=password)

    def start_requests(self):
        '''
        Get all possible urls
        '''
        for date in range(self.begin_date, self.end_date + 1):
            month_day = date % 10000
            month_day_legal = False
            for month in self.legal_date:
                if month[0] <= month_day <= month[1]:
                    month_day_legal = True
                    break
            if not month_day_legal:
                continue

            if self.my_redis.sismember("TencentNewsAllQuantity:dates",
                                       date):
                continue
            self.my_redis.sadd("TencentNewsAllQuantity:dates", date)
            for first in self.legal_first:
                for second in self.legal:
                    for third in self.legal:
                        for forth in self.legal:
                            url = 'https://new.qq.com/rain/a/' + \
                                  str(date) + 'A0' + first + second + \
                                  third + forth + '00'
                            yield Request(url)
                            url = 'https://new.qq.com/rain/a/' + \
                                  str(date) + 'V0' + first + second + \
                                  third + forth + '00'
                            yield Request(url)

    def parse(self, response, **_kwargs):
        '''
        Parse legal url
        '''
        if response.status == 200 and \
           response.url != 'https://www.qq.com/?pgv_ref=404':
            logging.info('Crawl the %s', response.url)
            item_loader = parse_detail_to_item_loader(response)
            yield item_loader.load_item()
