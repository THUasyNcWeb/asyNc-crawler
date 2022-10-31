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
        item_loader.add_value('first_img_url','')
    else:
        image_pre = re.findall(r'(http://www.news.cn/.*?/\d{4}-\d{1,2}/\d{1,2}/).*?', response.url)[0]
        item_loader.add_value('first_img_url',image_pre + image_last)
    
    time_label = response.xpath('//div[@class="info"]').extract_first()
    item_loader.add_value('pub_time', re.findall(r'.*?(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}).*', time_label)[0])

    paras = response.xpath('//div[@id="detail"]/p/text()').extract()
    if len(paras) == 0:
        paras.append('')
    for para in paras:
        item_loader.add_value('content', para)

    item_loader.add_value('category', re.findall(r'http://www.news.cn/(.*?)/.*', response.url)[0])

    return item_loader
