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

    sourse_user = ['echoesarinan']
    target_user = ['ivan.kurdin']
    #insta_tag = ['python', 'programming']

    dotenv.load_dotenv(".env")
    insta_params = {
        'username': 'kurdinivan@gmail.com',
        'enc_password': os.getenv('ENC_PASSWORD'),
        'sourse_user': sourse_user,
        'target_user': target_user,
    }

    #crawler_proc.crawl(AutoyoulaSpider)
    crawler_proc.crawl(InstagramSpider, **insta_params)
    crawler_proc.start()