from config.config import settings
from view.utils import timer
from view.check_ip_pool import CheckIPAddress
from view.get_shop_detail import ShopDetailCrawler
from view.get_product_detail import ProductDetailCrawler


import logging

logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, user_dict):
        self.input_shop_names = user_dict["input_shop_names"]
        self.user_email = user_dict["user_info"]["Email"]
        self.user_name = user_dict["user_info"]["Name"]

    @timer
    def __call__(self):

        # Step 0 > check ip pool as expected (This step is not necessary.)
        logger.info("⌲ Step 0: Test the IP you're using 5 times.")
        self.check_ip_pool()

        # Step 1 > input shop_names > get shop_detail
        logger.info("⌲ Step 1: Total shop detail fetchedd:")
        crawler_shop_detail = ShopDetailCrawler()
        result_shop_detail = crawler_shop_detail(self.input_shop_names)

        # Step 2 > input shop_detail > get product_id
        logger.info("⌲ Step 2: Total pdp detail fetched:")
        crawler_product_detail = ProductDetailCrawler()
        result_product_detail = crawler_product_detail(result_shop_detail)
        result_product_detail["user_name"] = self.user_name
        result_product_detail["user_email"] = self.user_email

        # Step 3 > save shop & pdp data to the Bigquery
        if settings.ENV == "prod":
            logger.info("⌲ Step 3: Data saved to BigQuery.")
            self.save_to_bigquery(result_shop_detail, result_product_detail)

    def check_ip_pool(self):
        check_ip = CheckIPAddress()
        check_ip(test_times=5)

    def save_to_bigquery(self, shop_details, product_details):

        client = settings.setup_bigquery()
        shop_details.to_gbq(
            "shopee.shop_detail",
            client.project,
            if_exists="append"
        )
        product_details.to_gbq(
            "shopee.pdp_detail",
            client.project, if_exists="append"
        )


if __name__ == "__main__":

    # Insert your email and the shop names you want to crawl
    user_list = [
        {
            "user_info": {
                "Email": "a0025071@gmail.com",
                "Name": "Max",
            },
            "input_shop_names": [
                "fulinxuan",
                "pat6116xx",
                "join800127",
                "ginilin0982353562",
                "ru8285fg56",
                "wangshutung",
                "taiwan88888",
                "baoshenfg",
                "cyf66666",
                "buddha8888",
                "dragon9168",
                "sinhochen77",
                "jouhsuansu",
            ],
        }
    ]

    do = Crawler(user_list[0])
    do()
