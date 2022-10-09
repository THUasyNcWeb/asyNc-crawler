import scrapy
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from scrapy.http import Request
import re

from news_crawler.items import NewsCrawlerItem, NewsCrawlerItemLoader


def parse_qq_news(response):
    item_loader = NewsCrawlerItemLoader(
        item=NewsCrawlerItem(), response=response)

    item_loader.add_value('news_url', response.url)
    window_data = response.xpath(
        '/html/head/script[7]/text()').extract_first()
    item_loader.add_value('media', re.findall(
        '"media": "(.*?)"', window_data)[0])
    for catalog in re.findall('"catalog\d+": "(.*?)"', window_data):
        item_loader.add_value('category', catalog)
    for tag in re.findall('"tags": "(.*?)"', window_data)[0].split(','):
        item_loader.add_value('tags', tag)
    item_loader.add_xpath('title', '/html/head/title/text()')
    item_loader.add_xpath('description', '/html/head/meta[2]/@content')
    # item_loader.add_value('first_img_url', response.meta.get('image_url'))
    item_loader.add_xpath('first_img_url', '//img[@class="content-picture"]/@src')
    item_loader.add_value('first_img_url', '')
    item_loader.add_value('pub_time', re.findall(
        '"pubtime": "(.*?)"', window_data)[0])
    paras = response.xpath(
        '/html/body/div[3]/div[1]/div[1]/div[2]/p/text()').extract()
    if len(paras) == 0:
        paras.append('')
    for para in paras:
        item_loader.add_value('content', para)

    yield item_loader.load_item()


class QqHomePageSpider(scrapy.Spider):
    name = 'QqHomePage'
    allowed_domains = ['news.qq.com', 'new.qq.com']
    start_urls = ['https://news.qq.com/']

    def __init__(self):
        super().__init__()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'}

        option = ChromeOptions()
        option.add_argument('--ignore-certificate-errors')
        option.add_argument('--no-sandbox')
        option.add_argument('--disable-gpu')
        option.add_argument('--headless')
        option.add_argument('--ignore-ssl-errors')
        option.add_experimental_option(
            'excludeSwitches', ['enable-automation', 'enable-logging'])
        self.driver = webdriver.Chrome(service=ChromeService(
            ChromeDriverManager().install()), options=option)

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, dont_filter=True, meta={'crawler': 'QqHomePage'})

    def close(self, spider):
        self.driver.quit()

    def parse(self, response):
        news_nodes = response.xpath('//*[@class="item cf itme-ls"]')
        for news_node in news_nodes:
            image_url = news_node.xpath('./a/img/@src').get()
            news_url = news_node.xpath('./div/h3/a/@href').get()
            yield Request(url=news_url, meta={"image_url": image_url},
                          callback=parse_qq_news)

# https://new.qq.com/rain/a/20221007A01LVJ00
class QqAllQuantitySpider(scrapy.Spider):
    name = 'QqAllQuantity'
    allowed_domains = ['new.qq.com']

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.begin_date = int(kwargs.get('begin_date', '20221008'))
        self.end_date = int(kwargs.get('end_date', '20221008'))
        self.legal = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G',
                      'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        self.legal_first = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    def start_requests(self):
        # num = 0
        for date in (self.begin_date, self.end_date + 1):
            for i in self.legal:
                for j in self.legal:
                    for k in self.legal:
                        for p in self.legal:
                            # if num > 100000:
                            #     break
                            url = 'https://new.qq.com/rain/a/' + str(date) + 'A0' + i + j + k + p + '00'
                            yield Request(url, dont_filter=True)
        # url = 'https://new.qq.com/rain/a/' + str('20221007') + 'A0' + '1' + 'L' + 'V' + 'J' + '00'
        # yield Request(url, dont_filter=True)

    def parse(self, response):
        if response.status == 200:
            yield Request(url=response.url, callback=parse_qq_news)
            # parse_qq_news(response)
