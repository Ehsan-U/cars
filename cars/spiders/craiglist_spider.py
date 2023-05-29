import json
import datetime
import scrapy
from scrapy.crawler import CrawlerProcess

from cars import utils
from cars.items import CarItem
from scrapy.loader import ItemLoader
from scrapy_playwright.page import PageMethod


class CraigList(scrapy.Spider):
    name = 'craiglist_spider'
    allowed_domains = ['craiglist.com']
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
        url = "https://dallas.craigslist.org/search/cta#search=1~gallery~0~0"
        yield scrapy.Request(url, callback=self.parse, meta={
            **self.playwright_args,
            "playwright_page_methods":[
                PageMethod("wait_for_selector", "//div[@class='gallery-card']"),
            ]
        })


    async def parse(self, response, **kwargs):
        for car in response.xpath("//div[@class='gallery-card']/a/@href").getall():
            yield scrapy.Request(url=car, callback=self.parse_car, meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "//section[@class='userbody']"),
                ]
            }, dont_filter=True)
        # page = response.meta['playwright_page']
        # try:
        #     await page.wait_for_selector("//div[@class='gallery-card']", timeout=5000)
        # except Exception:
        #     pass
        # next_btn_disabled = await page.locator("(//span[@class='cl-page-number']/following-sibling::button[1])[1]").is_disabled()
        # if not next_btn_disabled:
        #     await page.locator("(//span[@class='cl-page-number']/following-sibling::button[1])[1]").click()
        #     await page.wait_for_selector("//div[@class='gallery-card']")
        #     content = await page.content()
        #     response = scrapy.http.Response(url=response.url, body=content)
        #     response.meta['playwright_page'] = page
        #     async for item in self.parse(response):
        #         yield item



    def parse_car(self, response):
        loader = ItemLoader(item=CarItem())

        item  = dict(
            source="craiglist.com",
            year=self.get_year(response),
            description=self.get_desc(response),
            price=self.get_price(response),
            drivetrain=self.get_value(response, 'drive'),
            mileage=self.get_value(response, 'odometer'),
            transmission=self.get_value(response, 'transmission'),
            exterior=self.get_value(response, 'color'),
            reserve=True,
            scraped_date=datetime.datetime.now().date().strftime("%m/%d/%Y"),
        )
        for k, v in item.items():
            loader.add_value(k, v)

        yield loader.load_item()


    @staticmethod
    def get_year(response):
        year = response.xpath("//span[@id='titletextonly']/text()").re_first('\d{4}')
        return year

    @staticmethod
    def get_desc(response):
        desc = " ".join(response.xpath("//section[@id='postingbody']//text()").getall())
        return desc

    @staticmethod
    def get_price(response):
        price = response.xpath("//span[@class='price']/text()").get()
        return price

    @staticmethod
    def get_value(response, value):
        for span in response.xpath("//p[@class='attrgroup'][last()]/span"):
            name = span.xpath("./text()").get()
            if value.lower() in name.lower():
                return span.xpath("./b/text()").get()



#
# crawler = CrawlerProcess(settings=dict(
#     USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
#     PLAYWRIGHT_MAX_CONTEXTS = 8,
#     PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 4,
#     PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60000,
#     PLAYWRIGHT_ABORT_REQUEST = utils.request_should_abort,
#     PLAYWRIGHT_BROWSER_TYPE = 'firefox',
#     TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
# ))
# crawler.crawl(CraigList)
# crawler.start()
