import os
import re
import json
import shutil
import codecs
from functools import partial

import scrapy
from scrapy.http import HtmlResponse
from scrapy.shell import inspect_response
from jinja2 import Template
from bs4 import BeautifulSoup

PAGE_TEMPLATE="""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title></title>
<style>
p.pre {
    font-family: monospace;
    white-space: pre;
}
</style></head>
{{body}}
</html>"""

def url_base(u):
  # Actually I can use urlparse, but don't want to fall into the trap of py2 py3
  # Does this code actually support py3?
  try:
    idx = u.rindex('/')
  except:
    idx = len(u)
  return u[:idx]

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
    self._stage_toc = False
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
    # Loose role to decide if user signed in successfully.
    if '/login' in response.url:
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
    page_json = json.loads(response.body)
    yield scrapy.Request(page_json["content"],
                         callback=partial(self.parse_page, title, bookid, page_json["full_path"], page_json["images"]))

  def parse_page(self, title, bookid, path, images, response):
    template = Template(PAGE_TEMPLATE)

    # path might have nested directory
    dirs_to_make = os.path.join('./output/OEBPS', os.path.dirname(path))
    if not os.path.exists(dirs_to_make):
      os.makedirs(dirs_to_make)

    with codecs.open("./output/OEBPS/" + path, "wb", "utf-8") as f:
      pretty = BeautifulSoup(response.body).find('body')
      f.write(template.render(body=pretty))

    for img in images:
      if img:
        img = img.replace('../', '') # fix for books which are one level down
        yield scrapy.Request(self.host + '/library/view/' + title + '/' + bookid + '/' + img,
                             callback=partial(self.parse_content_img, img))

  def parse_toc(self, response):
    try:
      toc = json.loads(response.body)
    except:
      self.logger.error("Failed evaluating toc body: %s" % response.body)
      return

    self._stage_toc = True

    self.book_name = toc['title_safe']
    self.book_title = re.sub(r'["%*/:<>?\\|~\s]', r'_', toc['title']) # to be used for filename

    cover_path, = re.match(r'<img src="(.*?)" alt.+', toc["thumbnail_tag"]).groups()
    yield scrapy.Request(self.host + cover_path,
                         callback=partial(self.parse_cover_img, "cover-image"))

    for item in toc["items"]:
      yield scrapy.Request(self.host + item["url"],
                           callback=partial(self.parse_page_json, toc["title_safe"], toc["book_id"]))

    template = Template(file("./output/OEBPS/content.opf").read())
    with codecs.open("./output/OEBPS/content.opf", "wb", "utf-8") as f:
      f.write(template.render(info=toc))

    template = Template(file("./output/OEBPS/toc.ncx").read())
    with codecs.open("./output/OEBPS/toc.ncx", "wb", "utf-8") as f:
      f.write(template.render(info=toc))

  def closed(self, reason):
    if self._stage_toc == False:
      self.logger.info("Did not even got toc, ignore generated file operation.")
      return

    shutil.make_archive(self.book_name, 'zip', './output/')
    shutil.move(self.book_name + '.zip', self.book_title + '-' + self.bookid + '.epub')
