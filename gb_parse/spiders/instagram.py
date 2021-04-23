import scrapy
import json
import datetime as dt
from ..items import InstaPost, InstaTag
from urllib.parse import urlencode

class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    _login_url = 'https://www.instagram.com/accounts/login/ajax/'
    _tag_path = '/explore/tags/'
    _start_page = 'https://www.instagram.com/'
    _fr_query_url = 'https://www.instagram.com/graphql/query/'
    _api_url = '/graphql/query/'

    def __init__(self, username, enc_password, search_users, *args, **kwargs):
        super(InstagramSpider, self).__init__(*args, **kwargs)
        self.username = username
        self.enc_password = enc_password
        self.search_users = search_users

    def auth(self, response):
        js_data = self.js_data_extract(response)
        return scrapy.FormRequest(
            self._login_url,
            method="POST",
            callback=self.parse,
            formdata={
                'username': self.username,
                'enc_password': self.enc_password,
            },
            headers={'x-csrftoken': js_data['config']['csrf_token']}
        )

    def parse(self, response):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self._login_url,
                method="POST",
                callback=self.parse,
                formdata={  'username': self.username,
                            'enc_password': self.enc_password,},
                headers={'x-csrftoken': js_data['config']['csrf_token']},
            )
        except AttributeError as e:
            print(e)
            if response.json()["authenticated"]:
                for tag in self.search_users:
                    yield response.follow(f"{self._start_page}{tag}/", callback=self.tag_page_parse)

    def tag_page_parse(self, response):
        js_data = self.js_data_extract(response)
        insta_tag = InstTag(js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"])
        yield insta_tag.get_tag_item()
        yield from insta_tag.get_post_item()
        yield response.follow(
            f"{self._api_url}?{urlencode(insta_tag.paginate_params())}",
            callback=self._api_tag_parse,
        )

    def _api_tag_parse(self, response):
        data = response.json()
        insta_tag = InstTag(data["data"]["hashtag"])
        yield from insta_tag.get_post_item()
        yield response.follow(
            f"{self._api_url}?{urlencode(insta_tag.paginate_params())}",
            callback=self._api_tag_parse,
        )


    def js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData = ")]/text()').extract_first()
        return json.loads(script.replace("window._sharedData = ", "")[:-1])


class InstTag:
    query_hash = "5aefa9893005572d237da5068082d8d5"

    def __init__(self, hashtag: dict):
        self.variable = {
            "tag_name": hashtag["username"],
            "first": 100,
            #"after": hashtag["edge_hashtag_to_media"]["page_info"]["end_cursor"],
        }
        self.hashtag = hashtag

    def get_tag_item(self):
        item = InstaTag()
        item["date_parse"] = dt.datetime.utcnow()
        data = {}
        for key, value in self.hashtag.items():
            if not (isinstance(value, dict) or isinstance(value, list)):
                data[key] = value
        item["data"] = data
        return item

    def paginate_params(self):
        url_query = {"query_hash": self.query_hash, "variables": json.dumps(self.variable)}
        return url_query

    def get_post_item(self):
        for edge in self.hashtag["edge_hashtag_to_media"]["edges"]:
            yield InstaPost(date_parse=dt.datetime.utcnow(), data=edge["node"])
