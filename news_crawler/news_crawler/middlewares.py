"""
Define the DownloaderMiddleware
"""

from scrapy import signals
import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wdw
from selenium.webdriver.support import expected_conditions as EC
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

        driver.get(request.url)

        wdw(driver, 5).until(EC.visibility_of_element_located(
            (By.ID, 'load-more')))
        while(True):
            have_load_more = driver.find_elements(By.XPATH,
                                             '//div[@id="load-more"]')
            load_more = driver.find_elements(By.XPATH,
                                             '//div[@id="load-more"]/a')
            if len(have_load_more) == 0 or len(load_more) == 1:
                break
            # img_num = len(driver.find_elements(By.XPATH, 
            #                                    '//*[@class="item cf itme-ls"]'))
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            # wdw(driver, 5).until(EC.visibility_of_all_elements_located(
            #     (By.XPATH, f'//*[@class="item cf itme-ls"][{img_num}]/a/img')))

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
