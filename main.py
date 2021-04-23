import os
import dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from gb_parse.spiders.autoyoula import AutoyoulaSpider
from gb_parse.spiders.instagram import InstagramSpider

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule("gb_parse.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)

    insta_tag = ['ivan.kurdin', 'echoesarinan']
    #insta_tag = ['python', 'programming']

    dotenv.load_dotenv(".env")
    insta_params = {
        'username': 'kurdinivan@gmail.com',
        'enc_password': os.getenv('ENC_PASSWORD'),
        'search_users': insta_tag,
    }

    #crawler_proc.crawl(AutoyoulaSpider)
    crawler_proc.crawl(InstagramSpider, **insta_params)
    crawler_proc.start()