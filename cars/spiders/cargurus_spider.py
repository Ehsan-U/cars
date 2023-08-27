import datetime
import scrapy
from scrapy.crawler import CrawlerProcess
from cars.items import CarItem
from scrapy.loader import ItemLoader


class Cargurus(scrapy.Spider):
    name = 'cargurus_spider'
    allowed_domains = ['cargurus.com']
    base_url = "https://www.cargurus.com/Cars/searchResults.action?offset={}&maxResults=15"
    # page_no * 15 = offset
    page_no = 0


    def start_requests(self):
        url = self.base_url.format(self.page_no)
        yield scrapy.Request(url, callback=self.parse)


    def parse(self, response, **kwargs):
        data = response.json()
        for car in data:
            car_id = car.get("id")
            url = f"https://www.cargurus.com/Cars/detailListingJson.action?inventoryListing={car_id}"
            yield scrapy.Request(url, callback=self.parse_car)
        if data:
            self.page_no += 1
            next_url = self.base_url.format(self.page_no * 15)
            yield scrapy.Request(url=next_url, callback=self.parse)


    def parse_car(self, response):
        response = response.json()
        loader = ItemLoader(item=CarItem())

        item  = dict(
            source="cargurus.com",
            year=self.get_value(response, 'year'),
            description=self.get_value(response, 'description'),
            price=self.get_value(response, 'priceString'),
            comment_count=self.get_value(response, 'reviewCount'),
            engine=self.get_value(response, 'localizedEngineDisplayName'),
            drivetrain=self.get_value(response, 'localizedDriveTrain'),
            mileage=self.get_value(response, 'mileageString'),
            vin=self.get_value(response, 'vin'),
            transmission=self.get_value(response, "localizedTransmission"),
            exterior=self.get_value(response, "localizedExteriorColor"),
            interior=self.get_value(response, "localizedInteriorColor"),
            body_style=self.get_value(response, ("autoEntityInfo", "bodyStyle")),
            model=self.get_value(response, "modelName"),
            make = self.get_value(response, "makeName"),
            location=self.get_value(response, ("seller", "address", "addressLines")),
            seller=self.get_value(response, ("seller", "name")),
            seller_type=self.get_value(response, ("seller", "sellerType")),
            reserve=True,
            scraped_date=datetime.datetime.now().date().strftime("%m/%d/%Y"),
        )
        for k, v in item.items():
            loader.add_value(k, v)

        yield loader.load_item()


    @staticmethod
    def get_value(response, key):
        if isinstance(key, tuple):
            if len(key) == 2:
                value = response.get("listing").get(key[0], {}).get(key[1])
            elif len(key) == 3:
                value = response.get("listing").get(key[0], {}).get(key[1],{}).get(key[2])
                if isinstance(value, list):
                    value = " ".join(value)
        else:
            value = response.get("listing").get(key)
        return value


# crawler = CrawlerProcess()
# crawler.crawl(Cargurus)
# crawler.start()

