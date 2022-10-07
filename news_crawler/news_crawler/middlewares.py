# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from asyncio import sleep
from scrapy import signals
import scrapy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wdw
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


class QqHomePageDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        if request.meta.get("crawler") != "QqHomePage":
            return response

        if request.url in spider.start_urls:
            driver = spider.driver
            driver.get(request.url)
            wdw(driver, 5).until(EC.visibility_of_element_located(
                (By.ID, 'load-more')))
            last_num = 1
            ac = ActionChains(driver)
            while(True):
                load_more = driver.find_elements(By.XPATH, '//div[@id="load-more"]/a')
                if len(load_more) == 1:
                    break
                img_num = len(driver.find_elements(By.XPATH, '//*[@class="item cf itme-ls"]'))
                # driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                while last_num <= img_num:
                    ac.move_to_element(driver.find_element('xpath', '//*[@class="item cf itme-ls"][{}]'.format(last_num))).perform()
                    wdw(driver, 5).until(EC.visibility_of_all_elements_located(
                        (By.XPATH, '//*[@class="item cf itme-ls"][{}]/a/img'.format(last_num))))
                    last_num += 1
                # break
            # file = open('test.html', 'w', encoding='utf-8')
            # file.write(str(driver.page_source))
            # file.close()
            response = scrapy.http.HtmlResponse(url=request.url, body=driver.page_source, request=request, encoding='utf-8')

        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
