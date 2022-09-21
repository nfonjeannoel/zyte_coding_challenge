import copy
import json

import scrapy


class WebbotSpider(scrapy.Spider):
    name = 'webbot'
    # allowed_domains = ['x']
    start_urls = ['https://web-5umjfyjn4a-ew.a.run.app/']

    def parse(self, response):
        products = response.css("a[href*='click'] ::attr(href)").extract_first("")
        yield scrapy.Request(response.urljoin(products), callback=self.parse_products)

    def parse_products(self, response):
        products = response.css(".gtco-copy > a::attr(href)").extract()
        for product in products:
            yield scrapy.Request(url=response.urljoin(product), callback=self.parse_product)

        next_page = response.xpath("//a[text()[contains(., 'Next Page')]]").css("::attr(href)").extract_first()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse_products)

    def parse_product(self, response):
        item_id = response.css("#uuid::text").extract_first("").strip()
        name = response.css(".heading-colored::text").extract_first("").strip()
        image_id = response.css(".img-shadow img::attr(src)").re_first(r"gen/(.*)\.")
        if not image_id:
            image_id = None
        rating = response.xpath("//p[text()[contains(., 'Rating')]] /span//text()").extract_first("").strip()

        item = {
            "item_id": item_id,
            "name": name,
            "image_id": image_id,
            "rating": rating,
        }

        if rating == 'NO RATING':
            rating_url = response.xpath("//p[text()[contains(., 'Rating')]] /span").css(
                "::attr(data-price-url)").extract_first("")
            meta = {"item": item}
            yield scrapy.Request(response.urljoin(rating_url), callback=self.parse_rating, meta=meta)

        else:
            yield item

    def parse_rating(self, response):
        item = copy.deepcopy(response.meta["item"])
        rating = json.loads(response.body.decode("utf-8"))
        item["rating"] = rating.get("value", "").strip()
        yield item
