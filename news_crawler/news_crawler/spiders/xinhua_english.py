'''
Crawler of XinhuaEng
'''

import logging
import re
import threading
from scrapy.http import Request
from scrapy_redis.spiders import RedisSpider

from news_crawler.items import NewsCrawlerItem, NewsCrawlerItemLoader
import news_crawler.utils.utils as Utils


def parse_xinhua_eng_to_item_loader(response):
    '''
    parse single news item
    '''
    item_loader = NewsCrawlerItemLoader(
        item=NewsCrawlerItem(), response=response)

    item_loader.add_value('news_url', response.url)
    item_loader.add_xpath(
        'title', '/html//meta[@property="og:title"]/@content')

    item_loader.add_xpath(
        'category', '/html//meta[@property="og:type"]/@content')
    item_loader.add_value('category', '')

    item_loader.add_value('media', 'Xinhua')

    keys = response.xpath(
        '/html//meta[@name="keywords"]/@content'
    ).extract_first()
    if keys is not None:
        keys = keys.split(',')
        for key in keys:
            item_loader.add_value('tags', key[0:30])
    else:
        item_loader.add_value('tags', '')

    item_loader.add_xpath(
        'description', '/html//meta[@property="og:description"]/@content')
    item_loader.add_value('description', '')

    params = response.xpath('//*[@id="detailContent"]/p/text()').extract()
    if len(params) == 0:
        item_loader.add_value('content', '')
    else:
        for param in params:
            item_loader.add_value('content', param)

    img_src = response.xpath(
        '//*[@id="detailContent"]/p/img/@src').extract_first()
    if img_src is not None:
        img_src = response.url[:-6] + img_src
        item_loader.add_value('first_img_url', img_src)
    else:
        item_loader.add_value('first_img_url', '')

    item_loader.add_xpath('pub_time', '//*[@class="time"]/text()')

    return item_loader


class XinhuaEngNewsIncreSpider(RedisSpider):
    '''
    Crawl the XinhuaEngNewsIncre
    '''
    name = 'XinhuaEngNewsIncre'
    redis_key = "XinhuaEngNewsIncre:start_urls"

    def __init__(self, *args, **kwargs):
        '''
        Init the spider
        '''
        self.data_table = kwargs.get('data_table', 'news')
        self.attribution = kwargs.get('attribution', 'minor')
        if self.attribution == 'main':
            incre_timer = \
                Utils.IncrementTimer('xinhua_eng_news',
                                     'XinhuaEngNewsIncre:start_urls')
            start_urls_execute = threading.Thread(
                target=incre_timer.execute, daemon=True)
            start_urls_execute.start()
        super().__init__(*args, **kwargs)

    def parse(self, response, **_kwargs):
        '''
        Get all legal urls
        '''
        logging.info('Find news_url from %s', response.url)
        urls_candidate = re.findall(
            r'href="(../\d{8}/.{32}/c.html)"', response.text)
        for url_candidate in urls_candidate:
            url = 'https://english.news.cn/' + url_candidate[2:]
            logging.info('Crawl the %s', url)
            yield Request(url=url,
                          callback=self.parse_xinhua_eng_news)

    def parse_xinhua_eng_news(self, response):
        '''
        parse single news item
        '''
        item_loader = parse_xinhua_eng_to_item_loader(response)

        yield item_loader.load_item()
