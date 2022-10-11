"""
Define the DownloaderMiddleware
"""

from scrapy import signals
import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wdw
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


class TencentNewsHomePageDownloaderMiddleware:
    """
    Download all message in TencentNewsHomePage
    """
    @classmethod
    def from_crawler(cls, crawler):
        """
        This method is used by Scrapy to create your spiders.
        """
        spider = cls()
        crawler.signals.connect(spider.spider_opened,
                                signal=signals.spider_opened)
        return spider

    def process_response(self, request, response, spider):
        '''
        Use selenium to get all message from TencentNewsHomePage
        '''
        if request.meta.get("crawler") != "TencentNewsHomePage":
            return response

        option = ChromeOptions()
        option.add_argument('--ignore-certificate-errors')
        option.add_argument('--no-sandbox')
        option.add_argument('--disable-gpu')
        option.add_argument('--headless')
        option.add_argument('--ignore-ssl-errors')
        option.add_experimental_option(
            'excludeSwitches', ['enable-automation', 'enable-logging'])
        driver = webdriver.Chrome(service=ChromeService(
            ChromeDriverManager().install()), options=option)

        if request.url in spider.start_urls:
            driver.get(request.url)
            wdw(driver, 5).until(EC.visibility_of_element_located(
                (By.ID, 'load-more')))
            last_num = 1
            action_chains = ActionChains(driver)
            while True:
                load_more = driver.find_elements(
                    By.XPATH, '//div[@id="load-more"]/a')
                if len(load_more) == 1:
                    break
                img_num = len(driver.find_elements(
                    By.XPATH, '//*[@class="item cf itme-ls"]'))
                while last_num <= img_num:
                    action_chains.move_to_element(driver.find_element(
                        'xpath',
                        f'//*[@class="item cf itme-ls"][{last_num}]')
                    ).perform()
                    wdw(driver, 5).until(EC.visibility_of_all_elements_located(
                        (By.XPATH,
                         f'//*[@class="item cf itme-ls"][{last_num}]/a/img')))
                    last_num += 1
            response = scrapy.http.HtmlResponse(
                url=request.url, body=driver.page_source,
                request=request, encoding='utf-8')

        driver.quit()

        return response

    def spider_opened(self, spider):
        '''
        Open the spider
        '''
        spider.logger.info(f'Spider opened: {spider.name}')
