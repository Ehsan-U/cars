import json
import datetime
import scrapy
from scrapy.crawler import CrawlerProcess
from cars.items import CarItem
from scrapy.loader import ItemLoader


class AutoTrader(scrapy.Spider):
    name = 'autotrader_spider'
    allowed_domains = ['autotrader.com']
    base_url = "https://www.autotrader.com/rest/searchresults/base?allListingType=all-cars&isNewSearch=false&sortBy=relevance&numRecords=25&firstRecord={}"
    page_no = 0
    custom_settings = dict(
        DOWNLOAD_HANDLERS={
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        }
    )


    def start_requests(self):
        url = self.base_url.format(self.page_no)
        yield scrapy.Request(url, callback=self.parse, meta={"playwright": True})


    def parse(self, response, **kwargs):
        data = self.get_data(response)
        if data and not data.get("stackTrace"):
            for car in data.get("listings"):
                url = f"https://www.autotrader.com/cars-for-sale/vehicledetails.xhtml?listingId={car.get('id')}"
                yield scrapy.Request(url, callback=self.parse_car, meta={"playwright": True})
            self.page_no +=1
            next_url = self.base_url.format(self.page_no * 25)
            yield scrapy.Request(url=next_url, callback=self.parse, meta={"playwright": True})


    def parse_car(self, response):
        raw_data = response.xpath("//div[@id='mountNode']/following-sibling::script[1]/text()").get()
        response = self.get_data(raw_data, load=True)
        if response:
            loader = ItemLoader(item=CarItem())
            item  = dict(
                source="autotrader.com",
                year=self.get_year(response),
                description=self.get_desc(response),
                price=self.get_price(response),
                comment_count=self.get_comment_count(response),
                engine=self.get_engine(response),
                drivetrain=self.get_drivetrain(response),
                mileage=self.get_mileage(response),
                vin=self.get_vin(response),
                transmission=self.get_transmission(response),
                exterior=self.get_exterior(response),
                interior=self.get_interior(response),
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
        year = list(response.get("initialState").get("inventory").values())[0].get("year")
        return year

    @staticmethod
    def get_desc(response):
        desc = list(response.get("initialState").get("inventory").values())[0].get("additionalInfo").get("vehicleDescription")
        return desc

    @staticmethod
    def get_price(response):
        price = list(response.get("initialState").get("inventory").values())[0].get("pricingDetail").get("salePrice")
        return f"{price}$" if price else price

    @staticmethod
    def get_comment_count(response):
        comments = list(response.get("initialState").get("inventory").values())[0].get("kbbConsumerReviewCount")
        return comments

    @staticmethod
    def get_engine(response):
        engine = list(response.get("initialState").get("inventory").values())[0].get("specifications").get("engineDescription").get("value")
        return engine

    @staticmethod
    def get_drivetrain(response):
        drivetrain = list(response.get("initialState").get("inventory").values())[0].get("specifications").get("driveType").get("value")
        return drivetrain

    @staticmethod
    def get_mileage(response):
        mileage = list(response.get("initialState").get("inventory").values())[0].get("specifications").get("mileage").get("value")
        return mileage

    @staticmethod
    def get_vin(response):
        vin = list(response.get("initialState").get("inventory").values())[0].get("vin")
        return vin

    @staticmethod
    def get_transmission(response):
        transmission = list(response.get("initialState").get("inventory").values())[0].get("specifications").get("transmission").get("value")
        return transmission

    @staticmethod
    def get_exterior(response):
        exterior = list(response.get("initialState").get("inventory").values())[0].get("exteriorColorSimple")
        return exterior

    @staticmethod
    def get_interior(response):
        exterior = list(response.get("initialState").get("inventory").values())[0].get("interiorColorSimple")
        return exterior

    @staticmethod
    def get_bodystyle(response):
        bodystyle = ", ".join(list(response.get("initialState").get("inventory").values())[0].get("bodyStyleCodes"))
        return bodystyle

    @staticmethod
    def get_model(response):
        model = list(response.get("initialState").get("inventory").values())[0].get("model")
        return model

    @staticmethod
    def get_location(response):
        location = " ".join(list(response.get("initialState").get("owners").values())[0].get("location").get("address").values())
        return location

    @staticmethod
    def get_seller(response):
        seller = list(response.get("initialState").get("owners").values())[0].get("name")
        return seller

    @staticmethod
    def get_seller_type(response):
        seller_type = list(response.get("initialState").get("owners").values())[0].get("dealer", 'dealer')
        return seller_type

    @staticmethod
    def get_data(response, load=None):
        try:
            if not load:
                return json.loads(response.xpath("//pre/text()").get())
            else:
                return json.loads(response.split("DATA__=")[-1])
        except json.decoder.JSONDecodeError:
            return None

#
# crawler = CrawlerProcess(settings=dict(
#    USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
# ))
# crawler.crawl(AutoTrader)
# crawler.start()
