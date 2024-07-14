import datetime
from urllib.parse import parse_qs, urlparse, urlencode, quote
import dateparser
import scrapy
from scrapy.http import Response
from scrapy_playwright.page import PageMethod
from playwright.async_api import Page
from twisted.python.failure import Failure
import uuid


class Carsandbids(scrapy.Spider):
    name = 'carsandbids'
    custom_settings = {
        "DOWNLOAD_DELAY": 0,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        }
    }
    playwright_args = {
        "playwright": True,
        "playwright_include_page": True,
    }
    wait_timeout = 60*1000


    def __init__(self, car_year: str, car_make: str, car_model: str, car_trim: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_args = [car_year.strip(), car_make.strip(), car_model.strip(), car_trim.strip()]


    def construct_url(self) -> str:
        query = ' '.join(arg for arg in self.user_args if arg != '')
        url = f"https://carsandbids.com/search?q={quote(query)}"
        return url


    def start_requests(self):
        url = self.construct_url()
        yield scrapy.Request(
            url,
            callback=self.parse,
            meta={
                **self.playwright_args,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", selector="//ul[contains(@class,'auctions-list past-auctions')]", timeout=self.wait_timeout),
                    PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight / 2);"),
                    PageMethod("wait_for_timeout", timeout=5*1000),
                    PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight);"),
                    PageMethod("wait_for_timeout", timeout=5*1000),
                ]
            },
            errback=self.close_on_err
        )


    async def parse(self, response: Response, **kwargs):
        """ goto to each car page """
        page: Page = response.meta.get("playwright_page")
        if page and not page.is_closed():
            await page.close()
        cars_count = len(response.xpath("//ul[contains(@class, 'auctions-list')]/li//a[@class='hero']/@href").getall())
        self.logger.info(f"Cars: {cars_count}")
        for link in response.xpath("//ul[contains(@class, 'auctions-list')]/li//a[@class='hero']/@href").getall():
            yield scrapy.Request(
                url=response.urljoin(link),
                callback=self.parse_car,
                meta={
                    **self.playwright_args,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", selector="//div[contains(@class, 'quick-facts')]", timeout=self.wait_timeout)
                    ]
                },
                errback=self.close_on_err
            )

        next_page = response.xpath("//li[@class='arrow next']/button[not(@disabled)]")
        if next_page:
            query = parse_qs(urlparse(self.url).query)
            query['page'] = int(query['page'][0]) + 1 if 'page' in query else 2
            self.url = urlparse(self.url)._replace(query=urlencode(query)).geturl()
            yield scrapy.Request(
                url=self.url,
                callback=self.parse,
                meta={
                    **self.playwright_args,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", selector="//ul[contains(@class,'auctions-list past-auctions')]", timeout=self.wait_timeout),
                        PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight / 2);"),
                        PageMethod("wait_for_timeout", timeout=5*1000),
                        PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight);"),
                        PageMethod("wait_for_timeout", timeout=5*1000),
                    ]
                },
                errback=self.close_on_err
            )


    async def parse_car(self, response: Response):
        """ individual car page """
        page: Page = response.meta.get("playwright_page")
        if page and not page.is_closed():
            await page.close()
        source = 'carsandbids.com'
        year =  response.xpath("//title/text()").re_first('\d{4}')
        description = "".join(response.xpath("//div[contains(@class, 'auction-title')]/following-sibling::div/h2/text()").getall())
        price = "".join(response.xpath("//div[contains(@class, 'current-bid')]//span[@class='bid-value']//text()").getall())
        comment_count = response.xpath("//li[@class='num-comments']/span[@class='value']/text()").get()
        engine = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Engine')]/following-sibling::dd//text()").get()
        drivetrain = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Drivetrain')]/following-sibling::dd//text()").get()
        mileage = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Mileage')]/following-sibling::dd//text()").get()
        vin = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'VIN')]/following-sibling::dd//text()").get()
        transmission = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Transmission')]/following-sibling::dd//text()").get()
        exterior = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Exterior Color')]/following-sibling::dd//text()").get()
        interior = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Interior Color')]/following-sibling::dd//text()").get()
        body_style = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Body Style')]/following-sibling::dd//text()").get()
        model = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Model')]/following-sibling::dd//text()").get()
        make = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Make')]/following-sibling::dd//text()").get()
        location = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Location')]/following-sibling::dd//text()").get()
        seller = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Seller')]/following-sibling::dd//text()").get()
        seller_type = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Seller Type')]/following-sibling::dd//text()").get()

        no_reserve = response.xpath("//div[@class='row auction-heading']//span[@class='no-reserve']")
        reserve = False if no_reserve else True
        auction_end_date = self.convert_date_string("".join(response.xpath("//span[@class='time-ended']/text()").getall()))
        bid_count = response.xpath("//li[@class='num-bids']/span[@class='value']/text()").get()
        comments = []
        try:
            for comment in response.xpath("//li[@class='comment']"):
                text = " ".join(comment.xpath(".//div[@class='message']//text()").getall())
                comments.append(text)
        except Exception:
            pass
        title_status = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), 'Title Status')]/following-sibling::dd//text()").get()
        bids = []
        try:
            for bid in response.xpath("//li[@class='bid']"):
                bids.append({
                    "bidder": bid.xpath(".//div[@class='username']//div[@class='text']//a[@class='user']/@title").get(),
                    "amount": "".join(bid.xpath(".//dd/text()").getall()),
                    "timestamp": int(dateparser.parse(
                        bid.xpath(".//div[@class='text']//span[@class='time']/@data-full").get()).timestamp())
                })
        except Exception:
            pass

        return dict(
            source=source,
            year=year,
            description=description,
            price=price,
            comment_count=comment_count,
            engine=engine,
            drivetrain=drivetrain,
            mileage=mileage,
            vin=vin,
            transmission=transmission,
            exterior=exterior,
            interior=interior,
            body_style=body_style,
            model=model,
            make=make,
            location=location,
            seller=seller,
            seller_type=seller_type,
            reserve=reserve,
            auction_end_date=auction_end_date,
            bid_count=bid_count,
            comment_text=comments,
            title_status=title_status,
            bids=bids,
            source_page=response.url
        )


    async def close_on_err(self, failure: Failure):
        page: Page = failure.request.meta.get("playwright_page")
        self.logger.error(failure.value)
        if page and not page.is_closed():
            await page.close()


    @staticmethod
    def convert_date_string(date_str):
        try:
            formatted_date_str = dateparser.parse(date_str).strftime(f'%m/%d/%Y')
            return formatted_date_str
        except Exception:
            today = datetime.datetime.today().strftime(f'%m/%d/%Y')
            return today
