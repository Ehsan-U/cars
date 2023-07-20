import json
import datetime
import scrapy
from scrapy.crawler import CrawlerProcess
from cars.items import CarItem
from scrapy.loader import ItemLoader


class Cars(scrapy.Spider):
    name = 'cars_spider'
    allowed_domains = ['cars.com']
    base_url = "https://www.cars.com/shopping/results/?page={}&page_size=20"
    page = 1
    done = set()


    def start_requests(self):
        url = self.base_url.format(self.page)
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response, **kwargs):
        rawData = response.xpath("//div[@class='sds-page-section listings-page']/@data-site-activity").get()

        if rawData:
            data = json.loads(rawData)
            for car in data.get("vehicleArray"):
                url = f"https://www.cars.com/vehicledetail/{car.get('listing_id')}/"
                yield scrapy.Request(url, callback=self.parse_car)

            page_id = response.xpath("//li[@class='sds-pagination__item active']/text()").re_first('\d+')
            if not page_id in self.done:
                self.page +=1
                self.done.add(page_id)
                url = self.base_url.format(self.page)
                yield scrapy.Request(url, callback=self.parse)

    def parse_car(self, response):
        loader = ItemLoader(item=CarItem())

        item  = dict(
            source="cars.com",
            year=self.get_year(response),
            description=self.get_desc(response),
            price=self.get_price(response),
            comment_count=self.get_comment_count(response),
            engine=self.get_value(response, 'engine'),
            drivetrain=self.get_value(response, 'drivetrain'),
            mileage=self.get_value(response, 'mileage'),
            vin=self.get_value(response, 'vin'),
            transmission=self.get_value(response, "transmission"),
            exterior=self.get_value(response, "exterior"),
            interior=self.get_value(response, "interior"),
            body_style=self.get_bodystyle(response),
            model=self.get_model(response),
            location=self.get_location(response),
            seller=self.get_seller(response),
            seller_type=self.get_seller_type(response),
            reserve=True,
            scraped_date=datetime.datetime.now().date().strftime("%m/%d/%Y"),
        )
        for k, v in item.items():
            loader.add_value(k, v)

        yield loader.load_item()


    @staticmethod
    def get_year(response):
        year = response.xpath("//h1[@class='listing-title']/text()").re_first('\d{4}')
        return year

    @staticmethod
    def get_desc(response):
        desc = response.xpath("//div[@class='sellers-notes']/text()").get()
        return desc

    @staticmethod
    def get_price(response):
        price = response.xpath("//div[@class='price-section ']/span[@class='primary-price']/text()").get()
        return price

    @staticmethod
    def get_comment_count(response):
        comments = response.xpath("//div[@class='reviews-collection']/following-sibling::a[@data-linkname='research-consumer-reviews']/text()").re_first('\d+')
        return comments

    @staticmethod
    def get_value(response, value):
        for name,val in zip(response.xpath("//dl[@class='fancy-description-list']/dt/text()").getall(), response.xpath("//dl[@class='fancy-description-list']/dd/text()").getall()):
            if value.lower() in name.lower():
                return val

    @staticmethod
    def get_bodystyle(response):
        rawdata = response.xpath("//div[@class='vehicle-badging']/@data-override-payload").get()
        if rawdata:
            data = json.loads(rawdata)
            bodystyle = data.get("bodystyle")
            return bodystyle

    @staticmethod
    def get_model(response):
        rawdata = response.xpath("//div[@class='vehicle-badging']/@data-override-payload").get()
        if rawdata:
            data = json.loads(rawdata)
            model = data.get("model")
            return model

    @staticmethod
    def get_location(response):
        location = response.xpath("//div[@class='dealer-address']/text()").get()
        return location

    @staticmethod
    def get_seller(response):
        seller = response.xpath("//h3[contains(@class, 'seller-name')]/text()").get()
        return seller

    @staticmethod
    def get_seller_type(response):
        rawdata = response.xpath("//script[@id='initial-activity-data']/text()").get()
        if rawdata:
            data = json.loads(rawdata)
            seller_type = data.get("seller_type")
            return seller_type


# crawler = CrawlerProcess()
# crawler.crawl(Cars)
# crawler.start()
#
