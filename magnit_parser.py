from pathlib import Path

import requests
import bs4
import time
import pymongo
from datetime import datetime, date, time
from urllib.parse import urljoin

#url = "https://magnit.ru/promo/"
#response = requests.get(url)
#file = Path(__file__).parent.joinpath('magnit.html')
#file.write_text(response.text, encoding='UTF-8')
#soup = bs4.BeautifulSoup(response.text, "lxml")

MONTHS = {
    "янв": 1,
    "фев": 2,
    "мар": 3,
    "апр": 4,
    "май": 5,
    "мая": 5,
    "июн": 6,
    "июл": 7,
    "авг": 8,
    "сен": 9,
    "окт": 10,
    "ноя": 11,
    "дек": 12,
}

class MagnitParser:

    def __init__(self, start_url, mongo_url):
        self.start_url = start_url
        client = pymongo.MongoClient(mongo_url)
        self.db = client["gb_parse_12_04_21"]

    def get_response(self, url, *args, **kwargs):
        for _ in range(15):
            response = requests.get(url, *args, **kwargs)
            if response.status_code == 200:
                return response
            time.sleep(1)
        raise ValueError("URL DIE")

    def get_soup(self, url, *args, **kwargs) -> bs4.BeautifulSoup:
        soup = bs4.BeautifulSoup(self.get_response(url, *args, **kwargs).text, "lxml")
        return soup

    @property
    def template(self):
        data_template = {
            "url": lambda a: urljoin(self.start_url, a.attrs.get("href", "/")),
            "promo_name": lambda a: a.find("div", attrs={"class": "card-sale__header"}).text,
            "product_name": lambda a: a.find("div", attrs={"class": "card-sale__title"}).text,
            "old_price": lambda a: float(
                ".".join(
                    itm for itm in a.find("div", attrs={"class": "label__price_old"}).text.split()
                )
            ),
            "new_price": lambda a: float(
                ".".join(
                    itm for itm in a.find("div", attrs={"class": "label__price_new"}).text.split()
                )
            ),
            "image_url": lambda a: urljoin(
                self.start_url, a.find("picture").find("img").attrs.get("data-src", "/")),
            "date_from": lambda a: self.__get_date(
                a.find("div", attrs={"class": "card-sale__date"}).text
            )[0],
            "date_to": lambda a: self.__get_date(
                a.find("div", attrs={"class": "card-sale__date"}).text
            )[1],
        }
        return data_template

    def __get_date(self, date_string) -> list:
        date_list = date_string.replace("с ", "", 1).replace("\n", "").split("до ")
        result = []
        for date in date_list:
            temp_date = date.split()
            result.append(
                datetime.datetime(
                    year=datetime.datetime.now().year,
                    day=int(temp_date[0]),
                    month=MONTHS[temp_date[1][:3]],
                )
            )
        print(1)
        return result

    def run(self):
        for product in self._parse(self.get_soup(self.start_url)):
            self.save(product)

    def _parse(self, soup):
        products_a = soup.find_all('a', attrs={"class": "card-sale"})
        for prod_tag in products_a:
            product_data = {}
            for key, func in self.template.items():
                try:
                    product_data[key] = func(prod_tag)
                except AttributeError:
                    pass
                except ValueError:
                    ""
            yield product_data

    def save(self, data):
        collection = self.db["magnit"]
        collection.insert_one(data)


if __name__ == '__main__':
    url = "https://magnit.ru/promo/"
    mongo_url = "mongodb://localhost:27017"
    parser = MagnitParser(url, mongo_url)
    parser.run()