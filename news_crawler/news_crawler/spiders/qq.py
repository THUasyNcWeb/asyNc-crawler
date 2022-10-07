import scrapy
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from scrapy.http import Request
import re

from news_crawler.items import NewsCrawlerItem, NewsCrawlerItemLoader


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
                          callback=self.parse_news)

    def parse_news(self, response):
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
        item_loader.add_value('first_img_url', response.meta.get('image_url'))
        item_loader.add_value('pub_time', re.findall(
            '"pubtime": "(.*?)"', window_data)[0])
        paras = response.xpath(
            '/html/body/div[3]/div[1]/div[1]/div[2]/p/text()').extract()
        if len(paras) == 0:
            paras.append('')
        for para in paras:
            item_loader.add_value('content', para)

        yield item_loader.load_item()
