import scrapy
import json
import datetime as dt
from ..items import InstaPost, InstaTag
from urllib.parse import urlencode
from urllib.parse import urlparse, parse_qs

class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    _login_url = 'https://www.instagram.com/accounts/login/ajax/'
    _tag_path = '/explore/tags/'
    _start_page = 'https://www.instagram.com/'
    _fr_query_url = 'https://www.instagram.com/graphql/query/'
    _api_url = '/graphql/query/'

    def __init__(self, username, enc_password, sourse_user, target_user, *args, **kwargs):
        super(InstagramSpider, self).__init__(*args, **kwargs)
        self.username = username
        self.enc_password = enc_password
        self.sourse_user = sourse_user
        self.target_user = target_user

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
                for tag in self.sourse_user:
                    yield response.follow(f"{self._start_page}{tag}/", callback=self.tag_page_parse)

    def tag_page_parse(self, response):
        js_data = self.js_data_extract(response)
        insta_tag = InstTag(js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"])
        username = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["username"]
        yield response.follow(
            f"{self._api_url}?{urlencode(insta_tag.paginate_params())}",
            callback=self.follows_page_parse,
        )

    def follows_page_parse(self, response):
        follow_json = json.loads(response.body.decode("utf-8"))["data"]["user"]["edge_followed_by"]["edges"]
        follow_next_json = json.loads(response.body.decode("utf-8"))["data"]["user"]["edge_followed_by"]["page_info"]
        if follow_next_json["has_next_page"]:
            sourse_url = urlparse(response.url)
            sourse_query = parse_qs(sourse_url.query)
            insta_tag = InstTag(sourse_query['variables'])
            insta_tag.add_after(follow_next_json["end_cursor"])
            yield response.follow(
                f"{self._api_url}?{urlencode(insta_tag.paginate_params())}",
                callback=self.follows_page_parse,
            )
        for status in follow_json:
            node = status["node"]
            if not node['is_private']:
                insta_tag = InstTag(node)
                #yield response.follow(
                #    f"{self._api_url}?{urlencode(insta_tag.paginate_params())}",
                #    callback=self.follows_page_parse,
                #)
                print(1)
            else:
                print("user:", node['username'], "is_private")
            print(3)

    def is_paginate(self, response):
        print(4)

    def js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData = ")]/text()').extract_first()
        return json.loads(script.replace("window._sharedData = ", "")[:-1])


class InstTag:
    query_hash = "5aefa9893005572d237da5068082d8d5"

    def __init__(self, hashtag: dict):
        self.variable = {
            "tag_name": hashtag["username"],
            "id": hashtag["id"],
            "first": 100,
        }
        self.hashtag = hashtag

    def add_after(self, after):
        self.variable = {
            "after": after,
        }

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