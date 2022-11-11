'''
Crawler of Wangyi
'''

import logging
import re
import threading
from scrapy.http import Request
from scrapy_redis.spiders import RedisSpider

from news_crawler.items import NewsCrawlerItem, NewsCrawlerItemLoader
import news_crawler.utils.utils as Utils


def parse_wangyi_to_item_loader(response):
    '''
    parse single news item
    '''
    item_loader = NewsCrawlerItemLoader(
        item=NewsCrawlerItem(), response=response)

    item_loader.add_value('news_url', response.url)
    item_loader.add_xpath('title', '/html/head/meta[@property="og:title"]/@content')
    item_loader.add_value('category', '')
    item_loader.add_xpath('media', '//*[@id="container"]/div[1]/div[2]/a[1]/text()')
    keywords = response.xpath('/html/head/meta[@name="keywords"]/@content').extract_first()
    keywords.split(',')
    for keyword in keywords:
        item_loader.add_value('tags', keyword)
    item_loader.add_xpath('description', '/html/head/meta[@name="description"]/@content')
    paras = response.xpath('//*[@id="content"]/div[@class="post_body"]/p/text()').extract()
    if len(paras) == 0:
        paras.append('')
    for para in paras:
        item_loader.add_value('content', para)
    item_loader.add_xpath('first_img_url', '/html/head/meta[@property="og:image"]/@content')
    item_loader.add_value('first_img_url', '')
    item_loader.add_xpath('pub_time', '/html/head/meta[@property="article:published_time"]/@content')

    return item_loader


class WangyiNewsIncreSpider(RedisSpider):
    '''
    Crawl the WangyiNewsIncre
    '''
    name = 'WangyiNewsIncre'
    redis_key = "WangyiNewsIncre:start_urls"

    def __init__(self, *args, **kwargs):
        '''
        Init the spider
        '''
        self.data_table = kwargs.get('data_table', 'news')
        self.attribution = kwargs.get('attribution', 'minor')
        if self.attribution == 'main':
            incre_timer = \
                Utils.IncrementTimer('wangyi_news',
                                     'WangyiNewsIncre:start_urls')
            start_urls_execute = threading.Thread(
                target=incre_timer.execute, daemon=True)
            start_urls_execute.start()
        super().__init__(*args, **kwargs)

    def parse(self, response, **_kwargs):
        '''
        Get all legal urls
        '''
        logging.info('Find news_url from %s', response.url)
        urls_candidate = re.findall(r'"docurl":"(.*?)"', response.text)
        for url_candidate in urls_candidate:
            if re.match(r'https://www.163.com.*.html',
                        url_candidate) is not None:
                logging.info('Crawl the %s', url_candidate)
                yield Request(url=url_candidate,
                              callback=self.parse_wangyi_news)

    def parse_wangyi_news(self, response):
        '''
        parse single news item
        '''
        item_loader = parse_wangyi_to_item_loader(response)

        yield item_loader.load_item()
