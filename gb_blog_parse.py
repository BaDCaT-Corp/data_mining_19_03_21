import typing
import requests
import bs4
from urllib.parse import urljoin

from database import db

class GbBlogParse:

    def __init__(self, start_url, database: db.Database):
        self.db = database
        self.start_url = start_url
        self.done_urls = set()
        self.tasks = []


    def get_task(self, url: str, callback: typing.Callable) -> typing.Callable:
        def task():
            soup = self._get_soup(url)
            return callback(url, soup)
        return task

    def _get_response(self, url, *args, **kwargs) -> requests.Response:
        response = requests.get(url, *args, **kwargs)
        return response

    def _get_soup(self, url, *args, **kwargs) -> bs4.BeautifulSoup:
        soup = bs4.BeautifulSoup(self._get_response(url, *args, **kwargs).text, "lxml")
        return soup

    def parse_post(self, url, soup):
        author_tag = soup.find('div', attrs={"itemprop": "author"})
        data = {
            'post_data': {
                'title': soup.find('h1', attrs={"class": "blogpost-title"}).text,
                'url': url,
            },
            "author_data": {
                "url": urljoin(url, author_tag.parent.attrs.get("href")),
                "name": author_tag.text,
            },
            "tags_data": [{"url": urljoin(url, tag_a.attrs.get("href")), "name": tag_a.text}
                          for tag_a in soup.find_all("a",  attrs={'class': "small"})],
            "comments_data": self._get_comments(soup.find("comments").attrs.get("commentable-id")),
        }
        return data

    def _get_comments(self, post_id):
        api_path = f"/api/v2/comments?commentable_type=Post&commentable_id={post_id}&order=desc"
        response = self._get_response(urljoin(self.start_url, api_path))
        data = response.json()
        return data


    def parse_feed(self, url, soup):
        pag_urls = set()
        post_urls = set()
        ul = soup.find('ul', attrs={"class": "gb__pagination"})
        for url_a in ul.find_all("a"):
            if url_a.attrs.get('href'):
                pag_urls.add(urljoin(url, url_a.attrs.get('href')))
        #pag_urls = set(urljoin(url, url_a.attrs.get('href')) for url_a in ul.findall("a") if url_a.attrs.get('href'))
        for pag_url in pag_urls:
            if pag_url not in self.done_urls:
                self.done_urls.add(pag_url)
                task = self.get_task(pag_url, self.parse_feed)
                self.tasks.append(task)


        for url_a in soup.find_all('a', attrs={"class": "post-item__title"}):
            if url_a.attrs.get('href'):
                post_urls.add(urljoin(url, url_a.attrs.get('href')))
        for post_url in post_urls:
            if post_url not in self.done_urls:
                self.done_urls.add(post_url)
                task = self.get_task(post_url, self.parse_post)
                self.tasks.append(task)

    def run(self):
        task = self.get_task(self.start_url, self.parse_feed)
        self.tasks.append(task)
        self.done_urls.add(self.start_url)

        for task in self.tasks:
            task_result = task()
            if task_result:
                self.save(task_result)

    def save(self, data):
        self.db.create_post(data)


if __name__ == '__main__':
    #database = db.Database(r'sqlite///db_blog.db')
    database = db.Database(r'sqlite:///D:\GeekBrains\data_mining\data_mining_19_03_21\db_blog.db')
    parser = GbBlogParse("https://gb.ru/posts", database)
    parser.run()