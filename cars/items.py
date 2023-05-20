# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import datetime

import scrapy
from itemloaders.processors import TakeFirst, MapCompose


def clean(text: str):
    if isinstance(text, str):
        text = text.replace('\n', '')
        text = text.strip()
    return text


class CarItem(scrapy.Item):

    source = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    year = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    title = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    description = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    price = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    auction_end_date = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    bid_count = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    comment_count = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    engine = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    drivetrain = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    mileage = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    vin = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    transmission = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    title_status = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    exterior = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    interior = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    body_style = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    model = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    location = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    seller = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    seller_type = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    options = scrapy.Field(input_processor=MapCompose(clean), output_processor=TakeFirst())
    reserve = scrapy.Field(output_processor=TakeFirst())
    scraped_date = scrapy.Field(output_processor=TakeFirst())




