'''
Crawler of Tencent
'''

import re
import scrapy
from scrapy.http import Request
from scrapy_redis.spiders import RedisSpider

from news_crawler.items import NewsCrawlerItem, NewsCrawlerItemLoader


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
    for catalog in re.findall(r'"catalog\d+": "(.*?)"', window_data):
        item_loader.add_value('category', catalog)
    for tag in re.findall(r'"tags": "(.*?)"', window_data)[0].split(','):
        item_loader.add_value('tags', tag)
    item_loader.add_xpath('title', '/html/head/title/text()')
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


class TencentNewsHomePageSpider(RedisSpider):
    '''
    Crawl the TencentNewsHomePage
    '''
    name = 'TencentNewsHomePage'
    allowed_domains = ['news.qq.com', 'new.qq.com']
    # start_urls = ['https://news.qq.com/',
    #               'https://new.qq.com/d/bj/',
    #               'https://new.qq.com/ch/ent/',
    #               'https://new.qq.com/ch/tech/',
    #               'https://new.qq.com/ch/finance/',
    #               'https://new.qq.com/ch/auto/']
    redis_key = "TencentNewsHomePage:start_urls"

    def __init__(self, *args, **kwargs):
        '''
        Init the spider
        '''
        super(TencentNewsHomePageSpider, self).__init__(*args, **kwargs)

    def parse(self, response, **_kwargs):
        '''
        Get all legal urls
        '''
        urls_candidate = response.xpath('//a/@href').extract()
        for url_candidate in urls_candidate:
            # https://new.qq.com/omn/20221016/20221016A068MZ00.html
            if re.match(r'https://new.qq.com/.*?\d{8}A0[0-9A-Z]{4}00\.html', \
                url_candidate) != None:
                yield Request(url=url_candidate, callback=self.parse_tencent_news)

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
        self.begin_date = int(kwargs.get('begin_date', '20221008'))
        self.end_date = int(kwargs.get('end_date', '20221008'))
        self.legal = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                      'A', 'B', 'C', 'D', 'E', 'F', 'G',
                      'H', 'I', 'J', 'K', 'L', 'M', 'N',
                      'O', 'P', 'Q', 'R', 'S', 'T',
                      'U', 'V', 'W', 'X', 'Y', 'Z']
        self.legal_first = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    def start_requests(self):
        '''
        Get all possible urls
        '''
        for date in range(self.begin_date, self.end_date + 1):
            for first in self.legal_first:
                for second in self.legal:
                    for third in self.legal:
                        for forth in self.legal:
                            url = 'https://new.qq.com/rain/a/' + \
                                  str(date) + 'A0' + first + second + \
                                  third + forth + '00'
                            yield Request(url, dont_filter=True)
                            url = 'https://new.qq.com/rain/a/' + \
                                  str(date) + 'V0' + first + second + \
                                  third + forth + '00'
                            yield Request(url, dont_filter=True)

    def parse(self, response, **_kwargs):
        '''
        Parse legal url
        '''
        if response.status == 200 and \
           response.url != 'https://www.qq.com/?pgv_ref=404':
            item_loader = parse_detail_to_item_loader(response)
            yield item_loader.load_item()
