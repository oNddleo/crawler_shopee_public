from view.utils import timer

import os
import json
import logging
import asyncio
import datetime

import aiohttp
import pandas as pd

from pydantic import BaseModel
from view.utils import buildQueryString

logger = logging.getLogger(__name__)


class ItemParams(BaseModel):
    itemid: str
    shopid: int
    name: str
    currency: str
    stock: int
    status: int
    ctime: int
    t_ctime: str
    sold: int
    historical_sold: int
    liked_count: int
    brand: str
    cmt_count: int
    item_status: str
    price: int
    price_min: int
    price_max: int
    price_before_discount: int
    show_discount: int
    raw_discount: int
    tier_variations_option: str
    rating_star_avg: int
    rating_star_1: int
    rating_star_2: int
    rating_star_3: int
    rating_star_4: int
    rating_star_5: int
    item_type: int
    is_adult: bool
    has_lowest_price_guarantee: bool
    is_official_shop: bool
    is_cc_installment_payment_eligible: bool
    is_non_cc_installment_payment_eligible: bool
    is_preferred_plus_seller: bool
    is_mart: bool
    is_on_flash_sale: bool
    is_service_by_shopee: bool
    shopee_verified: bool
    show_official_shop_label: bool
    show_shopee_verified_label: bool
    show_official_shop_label_in_title: bool
    show_free_shipping: bool
    insert_date: str

    class Config:
        allow_extra = False


class ProductDetailCrawler:
    def __init__(self):
        self.basepath = os.path.abspath(os.path.dirname(__file__))

        self.search_item_api = "https://shopee.vn/api/v4/shop/search_items"
        self.items_list = []

        today = datetime.datetime.now()
        self.today_date = today.strftime("%Y-%m-%d %H:%M:%S")

    @timer
    def __call__(self, shop_detail):
        async def parser_shop_html(html):
            info = json.loads(html)

            if info["total_count"] != 0:

                for item in info["items"]:
                    item = item["item_basic"]

                    dateArray = datetime.datetime.utcfromtimestamp(
                        item["ctime"])
                    transfor_time = dateArray.strftime("%Y-%m-%d %H:%M:%S")

                    item_info = ItemParams(
                        **item,
                        t_ctime=transfor_time,
                        insert_date=self.today_date,
                        rating_star_avg=item["item_rating"]["rating_star"],
                        rating_star_1=item["item_rating"]["rating_count"][1],
                        rating_star_2=item["item_rating"]["rating_count"][2],
                        rating_star_3=item["item_rating"]["rating_count"][3],
                        rating_star_4=item["item_rating"]["rating_count"][4],
                        rating_star_5=item["item_rating"]["rating_count"][5],
                        tier_variations_option=",".join(
                            item["tier_variations"][0]["options"]
                        )
                        if item.get("tier_variations")
                        else "",
                    )
                    self.items_list.append(item_info.dict())

        async def get_item_detail(client, query_url):
            try:
                async with client.get(query_url) as response:
                    html = await response.text()
                    rsp_status = response.status
                    assert rsp_status == 200, (
                        f"rsp status {rsp_status}, {query_url}"
                    )
                    await parser_shop_html(html)
            except Exception as error:
                logger.warning("Exception: %s", error)

        async def main(crawler_item_urls):
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 "
                    "Safari/537.36"
                ),
                "Referer": "https://shopee.vn/",
                "X-Requested-With": "XMLHttpRequest",
            }
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False, limit=10),
                headers=headers,
            ) as client:
                tasks = [
                    get_item_detail(client, query_url)
                    for query_url in crawler_item_urls
                ]
                await asyncio.gather(*tasks)

        df_header = pd.DataFrame(
            columns=[field.name for field in ItemParams.__fields__.values()]
        )
        df_header.to_csv(self.basepath + "/csv/pdp_detail.csv", index=False)

        for row in shop_detail.itertuples():
            crawler_item_urls = []

            shop_id = row.shopid
            shop_product_count = row.item_count
            num = 0
            while num < shop_product_count:
                query = buildQueryString({
                    'offset': str(num),
                    'limit': 100,
                    'filter_sold_out': 3,
                    'use_case': 1,
                    'order': 'sales',
                    'sort_by': 'sales',
                    'shopid': shop_id
                })
                crawler_item_urls.append(
                    f"{self.search_item_api}?{query}"
                )
                num += 100
            asyncio.run(main(crawler_item_urls))

            logger.info(f"└── add Product Page Detail: {shop_product_count}")
        df = pd.DataFrame(self.items_list)
        df.to_csv(
            self.basepath + "/csv/pdp_detail.csv",
            index=False,
            mode="a",
            header=False,
        )
        return df


if __name__ == "__main__":
    '''
    # api example
    # https://shopee.vn/api/v4/shop/search_items?filter_sold_out=1&limit=100&offset=1&order=desc&shopid=5547415&sort_by=pop&use_case=1

    params use_case:
    1: Top Product
    2: ?
    3: ?
    4: Sold out items

    params filter_sold_out:
    1: = sold_out
    2: != sold_out
    3: both
    '''

    basepath = os.path.abspath(os.path.dirname(__file__))
    shop_detail = pd.read_csv(basepath + "/csv/shop_detail.csv")
    crawler_product_detail = ProductDetailCrawler()
    result_product_detail = crawler_product_detail(shop_detail)
