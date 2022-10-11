import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import Join, MapCompose, TakeFirst, Identity
from datetime import datetime
from elasticsearch_dsl import Document, Date, Integer, Keyword, Text, connections

connections.create_connection(hosts=["localhost"])

class TakeFirstAnything:
    def __call__(self, values):
        for value in values:
            if value is not None:
                return value


class NewsCrawlerItemLoader(ItemLoader):
    default_output_processor = TakeFirstAnything()


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

class ArticleType(Document):
    title = Text(analyzer = "ik_max_word")
    tags = Text(analyzer = "ik_max_word")
    content = Text(analyzer = "ik_max_word")
    
    
    first_img_url = Keyword()
    news_url = Keyword()
    front_image_path = Keyword()
    media = Keyword()
    
    create_date = Date()
    
    class Index:
        name = "tencent_news"