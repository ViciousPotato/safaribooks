import os
import re
import ast
import shutil
from functools import partial
import codecs

import scrapy
from scrapy.http import HtmlResponse
from scrapy.shell import inspect_response
from jinja2 import Template
from BeautifulSoup import BeautifulSoup
import scrapy.spiders

null = None
false = False

PAGE_TEMPLATE="""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
{{body}}
</body>
</html>"""

class SafariBooksSpider(scrapy.spiders.Spider):
  toc_url = 'https://www.safaribooksonline.com/nest/epub/toc/?book_id='
  name = "SafariBooks"
  #allowed_domains = []
  start_urls = ["https://www.safaribooksonline.com/"]
  host = "https://www.safaribooksonline.com/"

  def __init__(self, user='', password='', bookid=''):
    self.user = user
    self.password = password
    self.bookid = bookid
    self.book_name = ''
    self.info = {}
    self.initialize_output()

  def initialize_output(self):
    shutil.rmtree('output/', ignore_errors=True)
    shutil.copytree('data/', 'output/')

  def parse(self, response):
    return scrapy.FormRequest.from_response(
      response,
      formdata={"email": self.user, "password1": self.password},
      callback=self.after_login)

  def after_login(self, response):
    if not 'Recommended For You' in response.body:
      self.logger.error("Failed login")
      return
    yield scrapy.Request(self.toc_url+self.bookid, callback=self.parse_toc)

  def parse_cover_img(self, name, response):
    #inspect_response(response, self)
    with open("./output/OEBPS/cover-image.jpg", "w") as f:
      f.write(response.body)

  def parse_content_img(self, img, response):
    img_path = os.path.join("./output/OEBPS", img)
 
    img_dir = os.path.dirname(img_path)
    if not os.path.exists(img_dir):
      os.makedirs(img_dir)

    with open(img_path, "wb") as f:
      f.write(response.body)

  def parse_page_json(self, title, bookid, response):
    page_json = eval(response.body)
    yield scrapy.Request(page_json["content"], callback=partial(self.parse_page, title, bookid, page_json["full_path"]))

  def parse_page(self, title, bookid, path, response):
    template = Template(PAGE_TEMPLATE)
    with codecs.open("./output/OEBPS/" + path, "wb", "utf-8") as f:
      pretty = BeautifulSoup(response.body).prettify()
      f.write(template.render(body=pretty.decode('utf8')))

    for img in response.xpath("//img/@src").extract():
      if img:
        yield scrapy.Request(self.host + '/library/view/' + title + '/' + bookid + '/' + img,
                             callback=partial(self.parse_content_img, img))

  def parse_toc(self, response):
    toc = eval(response.body)
    self.book_name = toc['title_safe']
    cover_path, = re.match(r'<img src="(.*?)" alt.+', toc["thumbnail_tag"]).groups()
    yield scrapy.Request(self.host + cover_path,
                         callback=partial(self.parse_cover_img, "cover-image"))
    for item in toc["items"]:
      yield scrapy.Request(self.host + item["url"], callback=partial(self.parse_page_json, toc["title_safe"], toc["book_id"]))

    template = Template(file("./output/OEBPS/content.opf").read())
    with codecs.open("./output/OEBPS/content.opf", "wb", "utf-8") as f:
      f.write(template.render(info=toc))

    template = Template(file("./output/OEBPS/toc.ncx").read())
    with codecs.open("./output/OEBPS/toc.ncx", "wb", "utf-8") as f:
      f.write(template.render(info=toc))

  def closed(self, reason):
    shutil.make_archive(self.book_name, 'zip', './output/')
    shutil.move(self.book_name + '.zip', self.book_name + '.epub')