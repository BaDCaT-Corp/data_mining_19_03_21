from scrapy.loader import ItemLoader
from scrapy import Selector
from itemloaders.processors import TakeFirst, MapCompose

def clear_price(price: str) -> float:
    try:
        result = float(price.replace("\u2009", ""))
    except ValueError:
        result = None
    return result

def get_characteristics(item: str) -> dict:
    selector = Selector(text=item)
    data = {
        "name": selector.xpath("//div[contains(@class, 'AdvertSpecs')]/text()").extract_first(),
        "value": selector.xpath("//div[contains(@class, 'AdvertSpecs_data')]//text()").extract_first(),
    }

class AutoyoulaLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_out = TakeFirst()
    price_in = MapCompose(clear_price)
    price_out = TakeFirst()
    characteristics_in = MapCompose(get_characteristics)