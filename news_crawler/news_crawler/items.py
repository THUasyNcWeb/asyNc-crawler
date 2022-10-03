import scrapy


class NewsCrawlerItem(scrapy.Item):
    news_url = scrapy.Field()
    category = scrapy.Field()
    source = scrapy.Field()
    key_words = scrapy.Field()
    title = scrapy.Field()
    summary = scrapy.Field()
    content = scrapy.Field()
    first_img_url = scrapy.Field()
    date = scrapy.Field()