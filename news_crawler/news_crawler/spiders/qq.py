import scrapy
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService


class QqSpider(scrapy.Spider):
    name = 'qq'
    start_urls = ['http://news.qq.com/']
    allowed_domains = ['news.qq.com']

    def __init__(self):
        super().__init__()
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'}

        option = ChromeOptions()
        option.add_argument('--ignore-certificate-errors')
        option.add_argument('--no-sandbox')
        option.add_argument('--disable-gpu')
        option.add_argument('--headless')
        option.add_argument('--ignore-ssl-errors')
        option.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=option)
        
    
    def parse(self, response):
        yield {'text': response.text}

    def close(self, spider):
        self.driver.quit()