import datetime
import scrapy
from scrapy_playwright.page import PageMethod
from scrapy.crawler import CrawlerProcess
from cars.items import CarItem
from scrapy.loader import ItemLoader
import dateparser


class CarsandBids(scrapy.Spider):
    name = 'carsandbids_spider'
    allowed_domains = ['carsandbids.com']
    base_url = "https://carsandbids.com/past-auctions/?page={}"
    page_no = 1
    playwright_args = {
        "playwright": True,
        "playwright_include_page": True,
        "playwright_context_kwargs": {
            "ignore_https_errors": True,
        },
    }
    custom_settings = dict(
        DOWNLOAD_HANDLERS={
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        }
    )


    def start_requests(self):
        url = self.base_url.format(self.page_no)
        yield scrapy.Request(url, callback=self.parse_listing, errback=self.close_context_on_error, meta={
            **self.playwright_args,
            "playwright_page_methods": [
                PageMethod("wait_for_selector", "//ul[@class='auctions-list past-auctions ']"),
            ]
        })

    async def parse_listing(self, response):
        page = response.meta['playwright_page']
        for n, car in enumerate(response.xpath("//li[@class='auction-item ']")):
            url = car.xpath(".//div[@class='auction-title']/a/@href").get()
            yield response.follow(url, callback=self.parse_car, errback=self.close_context_on_error, meta={
                **self.playwright_args,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "//div[@class='quick-facts']"),
                ]
            })
        next_disabled = await page.locator("//li[@class='arrow next']/button").is_disabled()
        await page.close()
        if not next_disabled:
            self.logger.info(" [+] Next Page:")
            self.page_no += 1
            url = self.base_url.format(self.page_no)
            yield scrapy.Request(url, callback=self.parse_listing, errback=self.close_context_on_error, meta={
                **self.playwright_args,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "//ul[@class='auctions-list past-auctions ']"),
                    PageMethod("evaluate", "() => {window.scrollTo(0, document.body.scrollHeight);}"),
                ]
            })

    async def parse_car(self, response):
        page = response.meta['playwright_page']
        while True:
            try:
                await page.locator("//li[@class='load-more']/button").click()
                await page.wait_for_selector("//li[@class='load-more']/button", timeout=3000)
            except Exception:
                break
            else:
                continue
        content = await page.content()
        response = scrapy.Selector(text=content)
        await page.close()

        loader = ItemLoader(item=CarItem())
        item = dict(
            source='carsandbids.com',
            year=self.get_year(response),
            model=self.get_value(response, 'Model'),
            description=self.get_description(response),
            price=self.get_price(response),
            auction_end_date=self.get_end_date(response, self.convert_date_string),
            bid_count=self.get_bid_count(response),
            comment_count=self.get_comment_count(response),
            comment_text=self.get_comment_text(response),
            engine=self.get_value(response, 'Engine'),
            drivetrain=self.get_value(response, 'Drivetrain'),
            mileage=self.get_value(response, 'Mileage'),
            vin=self.get_value(response, 'VIN'),
            body_style=self.get_value(response, 'Body Style'),
            transmission=self.get_value(response, 'Transmission'),
            title_status=self.get_value(response, 'Title Status'),
            exterior=self.get_value(response, 'Exterior Color'),
            location=self.get_value(response, 'Location'),
            interior=self.get_value(response, 'Interior Color'),
            seller=self.get_value(response, 'Seller'),
            seller_type=self.get_value(response, 'Seller Type'),
            bids=self.get_bids(response),
            reserve=self.check_reserve(response),
            scraped_date=datetime.datetime.now().date().strftime("%m/%d/%Y")
        )
        for k, v in item.items():
            loader.add_value(k, v)
        yield loader.load_item()

    @staticmethod
    def get_year(response):
        year = response.xpath("//title/text()").re_first('\d{4}')
        return year

    @staticmethod
    def get_description(response):
        description = response.xpath("//div[@class='auction-title ']/following-sibling::div/h2/text()").getall()
        return "".join(description)

    @staticmethod
    def get_price(response):
        price = response.xpath("//div[contains(@class, 'current-bid')]//span[@class='bid-value']//text()").getall()
        return "".join(price)

    @staticmethod
    def get_end_date(response, converter):
        end_date = response.xpath("//span[@class='time-ended']/text()").getall()
        return converter("".join(end_date))

    @staticmethod
    def get_bid_count(response):
        bid_count = response.xpath("//li[@class='num-bids']/span[@class='value']/text()").get()
        return bid_count

    @staticmethod
    def get_comment_count(response):
        comment_count = response.xpath("//li[@class='num-comments']/span[@class='value']/text()").get()
        return comment_count

    @staticmethod
    def get_comment_text(response):
        comments = []
        for comment in response.xpath("//li[@class='comment']"):
            text = " ".join(comment.xpath(".//div[@class='message']//text()").getall())
            comments.append(text)
        return comments

    @staticmethod
    def check_reserve(response):
        no_reserve = response.xpath("//div[@class='row auction-heading']//span[@class='no-reserve']")
        if no_reserve:
            return False
        return True

    @staticmethod
    def get_bids(response):
        bids = []
        for bid in response.xpath("//li[@class='bid']"):
            bids.append({
                "bidder": bid.xpath(".//div[@class='username']//div[@class='text']/a/text()").get(),
                "amount": "".join(bid.xpath(".//dd/text()").getall()),
                "timestamp": int(dateparser.parse(bid.xpath(".//div[@class='text']//span[@class='time']/@data-full").get()).timestamp())
            })
        return bids

    @staticmethod
    def get_value(response, key):
        value = response.xpath(f"//div[@class='quick-facts']//dl//dt[contains(text(), '{key}')]/following-sibling::dd//text()").get()
        return value

    async def close_context_on_error(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()

    @staticmethod
    def convert_date_string(date_str):
        date = datetime.datetime.strptime(date_str, '%m/%d/%y')
        full_year = date.strftime('%Y')
        formatted_date_str = date.strftime(f'%m/%d/{full_year}')
        return formatted_date_str

#
# crawler = CrawlerProcess()
# crawler.crawl(CarsandBids)
# crawler.start()
