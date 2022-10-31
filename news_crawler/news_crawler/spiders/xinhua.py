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


def parse_xinhua_to_item_loader(response):
    '''
    parse single news item
    '''
    item_loader = NewsCrawlerItemLoader(
        item=NewsCrawlerItem(), response=response)

    item_loader.add_value('news_url', response.url)
    item_loader.add_xpath('media', '/html/head/meta[3]/@content')
    item_loader.add_xpath('tags', '/html/head/meta[10]/@content')
    item_loader.add_xpath('title', '//span[@class="title"]/text()')
    item_loader.add_xpath('description', '/html/head/meta[11]/@content')
    item_loader.add_value('description', '')

    image_last = response.xpath(r'//img[@id]/@src').extract_first()
    if image_last == None:
        item_loader.add_value('first_img_url', '')
    else:
        image_pre = re.findall(
            r'(http://www.news.cn/.*?/\d{4}-\d{2}/\d{2}/).*?', response.url)[0]
        item_loader.add_value('first_img_url', image_pre + image_last)

    time_label = response.xpath('//div[@class="info"]').extract_first()
    item_loader.add_value('pub_time', re.findall(
        r'.*?(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}).*', time_label)[0])

    paras = response.xpath('//div[@id="detail"]/p/text()').extract()
    if len(paras) == 0:
        paras.append('')
    for para in paras:
        item_loader.add_value('content', para)

    item_loader.add_value('category', re.findall(
        r'http://www.news.cn/(.*?)/.*', response.url)[0])

    return item_loader


class XinhuaNewsAllQuantitySpider(scrapy.Spider):
    '''
    Crawl the XinhuaNews with all quantity
    '''
    name = 'XinhuaNewsAllQuantity'
    start_urls = []

    def __init__(self, *_args, **kwargs):
        '''
        Init the legal characters
        '''
        super().__init__()
        self.data_table = kwargs.get('data_table', 'news')
        self.begin_date = int(kwargs.get('begin_date', '20221008'))
        self.end_date = int(kwargs.get('end_date', '20221008'))
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

        with open('./web_news_config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        self.categories = config['xinhua_categories']

        self.prefixes = ['1128', '1129', '1211']

    def start_requests(self):
        '''
        Get all possible urls
        '''
        # http://www.news.cn/world/2022-10/30/c_1129088514.htm
        for date in range(self.begin_date, self.end_date + 1):
            month_day = date % 10000
            month_day_legal = False
            for month in self.legal_date:
                if month[0] <= month_day <= month[1]:
                    month_day_legal = True
                    break
            if not month_day_legal:
                continue

            if self.my_redis.sismember("XinhuaNewsAllQuantity:dates",
                                       date):
                continue
            self.my_redis.sadd("XinhuaNewsAllQuantity:dates", date)

            date_trans = '/' + str(date)[:4] + '-' + \
                str(date)[4:6] + '/' + str(date)[6:]
            for id in range(0, 1000000):
                id_tran = str(id)
                while len(id_tran) < 6:
                    id_tran = '0' + id_tran
                for category in self.categories:
                    for prefix in self.prefixes:
                        url = 'http://www.news.cn/' + category + \
                            date_trans + '/c_' + prefix + id_tran + '.htm'
                        yield Request(url)

    def parse(self, response, **_kwargs):
        '''
        Parse legal url
        '''
        if response.status == 200 and \
           response.xpath('//div[@class="zjd"]/p/text()').extract_first() == \
                '对不起，您要访问的页面不存在或已被删除!':
            logging.info('Crawl the %s', response.url)
            item_loader = parse_xinhua_to_item_loader(response)
            yield item_loader.load_item()
