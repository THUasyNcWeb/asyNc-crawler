import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst, Identity


class NewsCrawlerItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class NewsCrawlerItem(scrapy.Item):
    news_url = scrapy.Field()
    category = scrapy.Field()
    source = scrapy.Field()
    key_words = scrapy.Field(
        output_processor=Identity()
    )
    title = scrapy.Field()
    summary = scrapy.Field()
    content = scrapy.Field()
    first_img_url = scrapy.Field()
    date = scrapy.Field()
