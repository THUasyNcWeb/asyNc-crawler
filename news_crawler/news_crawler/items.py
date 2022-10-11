"""
This module define the NewsCrawlerItem
"""

import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import Join, Identity


def take_first_anything(values):
    """
    Get the first element if not NULL
    """
    for value in values:
        if value is not None:
            return value
    return None


class NewsCrawlerItemLoader(ItemLoader):
    """
    Define the ItemLoader with default output processor
    """
    default_output_processor = take_first_anything


class NewsCrawlerItem(scrapy.Item):
    """
    Define every field of NewsCrawlerItem
    """
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
