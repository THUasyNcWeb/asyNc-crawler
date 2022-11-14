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
        item_loader.add_value('category', 'health')
    elif category == '/ Society':
        item_loader.add_value('category', 'social')
    elif category in ('/ Military', '/ Innovation'):
        item_loader.add_value('category', 'mil')
    category_second = response.xpath(
        '//*[@id="bread-nav"]/a[2]/text()').extract_first()
    if category_second == '/ World':
        item_loader.add_value('category', 'politics')
    elif category_second in ('/ Culture', '/ Lifestyle'):
        item_loader.add_value('category', 'women')
    elif category_second == '/ Sports':
        item_loader.add_value('category', 'sports')
    item_loader.add_value('category', '')

    item_loader.add_xpath(
        'media', '/html/head/meta[@name="source"]/@content')
    item_loader.add_value('media', 'China Daily')

    key_words = response.xpath(
        '/html/head/meta[@name="keywords"]/@content'
    ).extract_first()
    if key_words is not None:
        key_words = key_words.split(',')
        for key_word in key_words:
            item_loader.add_value('tags', key_word)
    else:
        item_loader.add_value('tags', '')
    item_loader.add_xpath(
        'description', '/html/head/meta[@name="description"]/@content')
    item_loader.add_value(
        'description', '')

    paras = response.xpath('//*[@id="Content"]/p/text()').extract()
    if len(paras) == 0:
        item_loader.add_value('content', '')
    else:
        for para in paras:
            item_loader.add_value('content', para)

    item_loader.add_xpath(
        'first_img_url', '/html/head/meta[@property="og:image"]/@content')
    item_loader.add_value('first_img_url', '')
    # /html/body/div[5]/div[3]/span[1]/text()
    update_info = response.xpath('//*[@class="info_l"]/text()').extract_first()
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
        # //www.chinadaily.com.cn/a/202211/12/WS636f92cba3104917543295bb.html
        # https://www.chinadaily.com.cn/a/202211/12/WS636f92cba3104917543295bb.html
        for url_candidate in urls_candidate:
            if re.match(r'.*www.chinadaily.com.cn/a/\d{6}/\d{2}/.*.html',
                        url_candidate) is not None:
                url = 'https:' + url_candidate
                yield Request(url=url,
                              callback=self.parse_china_daily_news)

    def parse_china_daily_news(self, response):
        '''
        parse single news item
        '''
        if re.match(r'.*www.chinadaily.com.cn/a/\d{6}/\d{2}/.*.html',
                    response.url) is not None:
            logging.info('Crawl the %s', response.url)
            item_loader = parse_china_daily_to_item_loader(response)

            yield item_loader.load_item()
