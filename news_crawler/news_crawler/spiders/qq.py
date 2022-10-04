import scrapy
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from scrapy.http import Request

from news_crawler.items import NewsCrawlerItem, NewsCrawlerItemLoader


class QqSpider(scrapy.Spider):
    name = 'qq'
    allowed_domains = ['news.qq.com']
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

    def close(self, spider):
        self.driver.quit()

    def parse(self, response):
        news_nodes = response.xpath('//*[@class="item cf itme-ls"]')
        for news_node in news_nodes:
            item_loader = NewsCrawlerItemLoader(
                item=NewsCrawlerItem(), selector=news_node)
            # image_url = news_node.xpath('./a/img/@src').get()
            news_url = news_node.xpath('./div/h3/a/@href').get()
            # source = news_node.xpath('./div/div[2]/div[1]/a/text()').get()
            item_loader.add_xpath('first_img_url', './a/img/@src')
            item_loader.add_value('news_url', news_url)
            item_loader.add_xpath('source', './div/div[2]/div[1]/a/text()')
            yield Request(url=news_url, meta={"item_loader": item_loader},
                          callback=self.parse_news)
            break

    def parse_news(self, response):
        pass
