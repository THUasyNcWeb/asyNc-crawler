'''
Crawler of ChinaDaily
'''

import logging
import re
import threading
from scrapy.http import Request
from scrapy_redis.spiders import RedisSpider

from news_crawler.items import NewsCrawlerItem, NewsCrawlerItemLoader
import news_crawler.utils.utils as Utils


def parse_china_daily_to_item_loader(response):
    '''
    parse single news item
    '''
    item_loader = NewsCrawlerItemLoader(
        item=NewsCrawlerItem(), response=response)

    item_loader.add_value('news_url', response.url)
    item_loader.add_xpath(
        'title', '/html/head/meta[@property="og:title"]/@content')
    
    category = response.xpath(
        '//*[@id="bread-nav"]/a[3]/text()').extract_first()
    if category == '/ Health':
        category = 'health'
    elif category == '/ Society':
        category = 'social'
    elif category == '/ Military' or category == '/ Innovation':
        category = 'mil'
    category_second = response.xpath(
        '//*[@id="bread-nav"]/a[2]/text()').extract_first()    
    if category_second == '/ World':
        category = 'politics'
    elif category_second == '/ Culture' or category_second == '/ Lifestyle':
        category = 'women'
    elif category_second == '/ Sports':
        category = 'sports'
    item_loader.add_value('category', category)
    item_loader.add_value('category', '')

    item_loader.add_xpath(
        'media', '/html/head/meta[@name="source"]/@content')

    key_words = response.xpath('/html/head/meta[@name="keywords"]/@content').extract_first()
    if key_words != None:
        key_words = key_words.spilt(',')
        for key_word in key_words:
            item_loader.add_value('tags', key_word)
    else:
        item_loader.add_value('tags', '')
    item_loader.add_xpath(
        'description', '/html/head/meta[@name="description"]/@content')
    
    paras = response.xpath('//*[@id="Content"]/p/text()').extract()
    if len(paras) == 0:
        paras.append('')
    else:
        for para in paras:
            item_loader.add_value('content', para)
    
    item_loader.add_xpath(
        'first_img_url', '/html/head/meta[@property="og:image"]/@content')
    item_loader.add_value('first_img_url', '')

    update_info = response.xpath('//*[@id="lft-art"]/div[1]/span[1]/text()').extract_first()
    pub_time = re.findall(r'.*Updated: (.*)\n.*', update_info)[0]
    item_loader.add_value('pub_time', pub_time)

    return item_loader


class ChinaDailyNewsIncreSpider(RedisSpider):
    '''
    Crawl the ChinaDailyNewsIncre
    '''
    name = 'ChinaDailyNewsIncre'
    redis_key = "ChinaDailyNewsIncre:start_urls"

    def __init__(self, *args, **kwargs):
        '''
        Init the spider
        '''
        self.data_table = kwargs.get('data_table', 'news')
        self.attribution = kwargs.get('attribution', 'minor')
        if self.attribution == 'main':
            incre_timer = \
                Utils.IncrementTimer('china_daily_news',
                                     'ChinaDailyNewsIncre:start_urls')
            start_urls_execute = threading.Thread(
                target=incre_timer.execute, daemon=True)
            start_urls_execute.start()
        super().__init__(*args, **kwargs)

    def parse(self, response, **_kwargs):
        '''
        Get all legal urls
        '''
        logging.info('Find news_url from %s', response.url)
        urls_candidate = re.findall(r'href="(.*?)"', response.text)
        # //www.chinadaily.com.cn/a/202211/11/WS636de4a4a3104917543292d5.html
        for url_candidate in urls_candidate:
            if re.match(r'//www.chinadaily.com.cn/a/\d{6}/\d{2}/.*.html',
                        url_candidate) is not None:
                logging.info('Crawl the %s', url_candidate)
                yield Request(url=url_candidate,
                              callback=self.parse_china_daily_news)

    def parse_china_daily_news(self, response):
        '''
        parse single news item
        '''
        item_loader = parse_china_daily_to_item_loader(response)

        yield item_loader.load_item()
