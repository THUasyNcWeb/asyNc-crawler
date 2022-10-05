import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import Join, MapCompose, TakeFirst, Identity


class NewsCrawlerItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class NewsCrawlerItem(scrapy.Item):
    news_url = scrapy.Field()
    category = scrapy.Field(
        output_processor=Identity()
    )
    media = scrapy.Field()
    tags = scrapy.Field(
        output_processor=Identity()
    )
    title = scrapy.Field()
    description = scrapy.Field()
    content = scrapy.Field(
        output_processor=Join(separator='\n')
    )
    first_img_url = scrapy.Field()
    pub_time = scrapy.Field()
