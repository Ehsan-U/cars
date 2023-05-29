import datetime
import json
import scrapy 
from scrapy.crawler import CrawlerProcess
from cars.items import CarItem
from scrapy.loader import ItemLoader
import dateparser


class BringaTrailer(scrapy.Spider):
    name = 'bringatrailer_spider'
    allowed_domains = ['bringatrailer.com']


    def start_requests(self):
        url = "https://bringatrailer.com/auctions/"
        yield scrapy.Request(url=url, callback=self.parse_listing)


    def parse_listing(self, response):
        raw_data = response.xpath("//script[@id='bat-theme-auctions-current-initial-data']/text()").get().split('Data = ')[-1].replace('\n','').split('];')[0] + "]"
        if raw_data:
            data = json.loads(raw_data)
            for car in data:
                url = car.get("url")
                yield scrapy.Request(url=url, callback=self.parse_car)


    def parse_car(self, response):
        loader = ItemLoader(item=CarItem())

        item = dict(
            source="bringatrailer.com",
            year=self.get_year(response),
            model=self.get_model(response),
            description=self.get_description(response),
            price=self.get_price(response),
            auction_end_date=self.get_end_date(response, self.convert_date_string),
            bid_count=self.get_bid_count(response),
            comment_count=self.get_comment_count(response),
            engine=self.get_value(response, 'Engine'),
            drivetrain=self.get_value(response, 'Drivetrain'),
            mileage=self.get_value(response, 'Mileage'),
            vin=self.get_value(response, 'VIN'),
            body_style=self.get_value(response, 'Body Style'),
            transmission=self.get_value(response, 'Transmission'),
            title_status=self.get_title(response),
            exterior=self.get_value(response, 'Exterior Color'),
            location=self.get_location(response),
            interior=self.get_value(response, 'Interior Color'),
            seller=self.get_seller(response),
            seller_type=self.get_seller_type(response),
            # options=self.get_options(response),
            bids=self.get_bids(response),
            reserve=self.check_reserve(response),
            scraped_date=datetime.datetime.now().date().strftime("%m/%d/%Y"),
        )

        for k,v in item.items():
            loader.add_value(k, v)
        yield loader.load_item()


    @staticmethod
    def get_year(response):
        year = response.xpath("//h1[@class='post-title listing-post-title']/text()").re_first('\d{4}')
        return year

    @staticmethod
    def get_description(response):
        description = response.xpath("//div[contains(@class, 'post')]/div/p/text()").getall()
        return "\n".join(description)

    @staticmethod
    def get_price(response):
        price = response.xpath("//span[@class='info-value noborder-tiny']/strong/text()").get()
        return price

    @staticmethod
    def get_end_date(response, converter):
        end_date = response.xpath("//span[@data-ends]/text()").get()
        return converter(end_date)

    @staticmethod
    def get_bid_count(response):
        bid_count = response.xpath("//td[@class='listing-stats-value number-bids-value']/text()").get()
        return bid_count

    @staticmethod
    def get_comment_count(response):
        comment_count = response.xpath("//span[@class='comments_header_html']/span[@class='info-value']/text()").get()
        return comment_count

    @staticmethod
    def get_model(response):
        model =response.xpath(f"//strong[contains(text(), 'Model')]/following-sibling::text()").get()
        return model

    @staticmethod
    def get_title(response):
        title = response.xpath("//h1[@class='post-title listing-post-title']/text()").get()
        return title

    @staticmethod
    def get_location(response):
        location = response.xpath("//strong[contains(text(), 'Location')]/following-sibling::a/text()").get()
        return location

    @staticmethod
    def get_seller(response):
        seller = response.xpath("//strong[contains(text(), 'Seller')]/following-sibling::a/text()").get()
        return seller

    @staticmethod
    def get_seller_type(response):
        seller_type = response.xpath("//strong[contains(text(), 'Party')]/following-sibling::text()").get()
        return seller_type

    @staticmethod
    def get_options(response):
        options = response.xpath("//strong[contains(text(), 'Listing')]/following-sibling::ul/li/text()").getall()
        return ", ".join(options)

    @staticmethod
    def get_bids(response):
        bids = []
        rawdata = response.xpath("//script[@id='bat-theme-viewmodels-js-extra']/text()").get()
        if rawdata:
            data = json.loads(rawdata.split("VMS =")[-1].strip().replace('\n','').rstrip(';'))
            for bid in data.get("comments", []):
                bid_amount = bid.get("bidAmount", 0)
                if bid_amount:
                    bids.append({
                        "bidder": bid.get("authorName"),
                        "amount": f"{bid_amount}$",
                        "timestamp": bid.get("timestamp")
                    })
        return bids

    @staticmethod
    def get_value(response, key):
        mapping = {
            'Engine': 3,
            'Transmission': 4,
            'Mileage': 2,
            'VIN': 1,
        }
        if key != 'VIN':
            value = response.xpath(f"//div[@class='item']/ul/li[{mapping.get(key)}]/text()").get()
        else:
            value = response.xpath(f"//div[@class='item']/ul/li[{mapping.get(key)}]/a/text()").get()
        return value

    @staticmethod
    def check_reserve(response):
        no_reserve = response.xpath("//div[@class='item-tag item-tag-noreserve']")
        if no_reserve:
            return False
        return True

    @staticmethod
    def convert_date_string(date_str):
        formatted_date_str = dateparser.parse(date_str).strftime(f'%m/%d/%Y')
        return formatted_date_str

            
#
# crawler = CrawlerProcess()
# crawler.crawl(BringaTrailer)
# crawler.start()
