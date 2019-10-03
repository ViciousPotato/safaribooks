import codecs
import json
import os
import re
import shutil
import tempfile
from functools import partial

import scrapy
# from scrapy.shell import inspect_response
from jinja2 import Template
from bs4 import BeautifulSoup

from .. import utils

DEFAULT_STYLE = """
p.pre {
  font-family: monospace;
  white-space: pre;
}"""

PAGE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
    <head>
        <title></title>
        <style>
        {{style}}
        </style>
    </head>
    {{body}}
</html>"""


# def url_base(u):
#   # Actually I can use urlparse, but don't want to fall into the trap of py2 py3
#   # Does this code actually support py3?
#   try:
#     idx = u.rindex('/')
#   except:
#     idx = len(u)
#   return u[:idx]

def decode(s):
    try:
        return s.decode("utf8")
    except:
        return s

class Chapter:
    id=''
    href=''

class SafariBooksSpider(scrapy.spiders.Spider):
    toc_url = 'https://learning.oreilly.com/api/v1/book/'
    name = 'SafariBooks'
    # allowed_domains = []
    start_urls = ['https://www.oreilly.com/member/']
    host = 'https://www.safaribooksonline.com/'

    def __init__(
        self,
        user,
        password,
        cookie,
        bookid,
        output_directory=None
    ):
        self.user = user
        self.password = password
        self.cookie = cookie
        self.bookid = str(bookid)
        self.output_directory = utils.mkdirp(
            output_directory or tempfile.mkdtemp()
        )
        self.book_name = ''
        self.epub_path = ''
        self.style = ''
        self.info = {}
        self._stage_toc = False
        self.tmpdir = tempfile.mkdtemp()
        self._initialize_tempdir()

    def _initialize_tempdir(self):
        self.logger.info(
            'Using `{0}` as temporary directory'.format(self.tmpdir)
        )

        # `copytree` doesn't like when the target directory already exists.
        os.rmdir(self.tmpdir)

        shutil.copytree(utils.pkg_path('data/'), self.tmpdir)

    def parse(self, response):
        if self.cookie is not None:
            # cookies = dict(x.strip().split('=') for x in self.cookie.split(';'))

            return scrapy.Request(url=self.host + 'home', 
                callback=self.after_login,
                cookies=self.cookie,
                headers={
                    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
                })

        return scrapy.Request(
            url='https://www.oreilly.com/member/auth/login/',
            callback=self.after_login,
            method="POST",            
            headers={
                'Origin':'https://oreilly.com',
                'Referer': 'https://www.oreilly.com/member/',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',         
                'content-type': 'application/json',
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
            },
            body='{"email":"'+ self.user +'","password":"'+self.password+'"}'

        )


    def after_login(self, response):
        # Loose rule to decide if user signed in successfully.
        if response.status == 401:
            self.logger.error('Failed login')
            return
        elif response.status != 200:
            self.logger.error('Something went wrong')
            return
        
        self.cookie = dict(str(x).strip().split(';')[0].split('=') for x in response.headers.getlist('Set-Cookie'))

        yield scrapy.Request(
            url=self.toc_url + self.bookid+'/',
            callback=self.parse_toc,
            cookies=self.cookie
        )

    def parse_cover_img(self, name, response):
        # inspect_response(response, self)
        cover_img_path = os.path.join(self.tmpdir, 'OEBPS', 'cover-image.jpg')
        with open(cover_img_path, 'wb') as fh:
            fh.write(response.body)

    def parse_content_img(self, img, response):
        img_path = os.path.join(os.path.join(self.tmpdir, 'OEBPS'), img)

        img_dir = os.path.dirname(img_path)
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)

        with open(img_path, 'wb') as fh:
            fh.write(response.body)

    def parse_page_json(self, title, bookid, response):
        page_json = json.loads(response.body)

        style_sheets = page_json.get('stylesheets', [])
        style_sheets_paths = []

        for style_sheet in style_sheets:
            style_sheets_paths.append(style_sheet['full_path'])
            yield scrapy.Request(
                style_sheet['url'], # I don't know when style_sheets will have multiple elements
                callback=partial(self.load_page_style, style_sheet['full_path'])
            )

        yield scrapy.Request(
            page_json['content'],
            callback=partial(
                self.parse_page,
                title,
                bookid,
                page_json['full_path'],
                page_json['images'],
                style_sheets_paths
            )
        )

    def load_page_style(self, full_path, response):
        # TODO: obviously the best approach is to create file for styles
        # and share them in the downloaded files. But you need to carefully calculates the relative path.
        # For now just append to self.style
        self.style += response.body


    def parse_page(self, title, bookid, path, images, style, response):
        template = Template(PAGE_TEMPLATE)

        # path might have nested directory
        dirs_to_make = os.path.join(
            self.tmpdir,
            'OEBPS',
            os.path.dirname(path),
        )
        if not os.path.exists(dirs_to_make):
            os.makedirs(dirs_to_make)

        oebps_body_path = os.path.join(self.tmpdir, 'OEBPS', path)
        with codecs.open(oebps_body_path, 'wb', 'utf-8') as fh:
            body = decode(str(BeautifulSoup(response.body, 'lxml').find('body')))
            style = self.style if self.style != '' else DEFAULT_STYLE
            style = decode(style)
            fh.write(template.render(body=body, style=style))

        for img in images:
            if not img:
                continue

            # fix for books which are one level down
            img = img.replace('../', '')

            yield scrapy.Request(
                '/'.join((self.host, 'library/view', title, bookid, img)),
                callback=partial(self.parse_content_img, img),
            )

    def parse_toc(self, response):
        try:
            toc = json.loads(response.body)
        except Exception:
            self.logger.error(
                'Failed evaluating toc body: {0}'.format(response.body),
            )
            return

        self._stage_toc = True

        self.book_name = toc['title']
        self.book_title = re.sub(r'["%*/:<>?\\|~\s]', r'_', toc['title'])  # to be used for filename

        cover_path= toc['cover']

        yield scrapy.Request(
            url=cover_path,
            cookies=self.cookie,
            callback=partial(self.parse_cover_img, 'cover-image'),
        )
        items=[];
        for item in toc['chapters']:
            splited = item.split('/')
            ch = Chapter()
            ch.id =splited[-1]
            ch.href =  ch.id if splited[-2] =='chapter' else splited[-2]+'/'+splited[-1]
            items.append(ch)
            yield scrapy.Request(
                url=item,
                cookies=self.cookie,
                callback=partial(
                    self.parse_page_json,
                    toc['title'],
                    toc['identifier'],
                ),
            )
        content_path = os.path.join(self.tmpdir, 'OEBPS', 'content.opf')
        with open(content_path) as fh:
            template = Template(fh.read())
        with codecs.open(content_path, 'wb', 'utf-8') as fh:
            fh.write(template.render(info=toc,chapters=items))

        toc_path = os.path.join(self.tmpdir, 'OEBPS', 'toc.ncx')
        with open(toc_path) as fh:
            template = Template(fh.read())
        with codecs.open(toc_path, 'wb', 'utf-8') as fh:
            fh.write(template.render(info=toc,chapters=items))

    def closed(self, reason):
        if self._stage_toc is False:
            self.logger.info(
                'Did not even got toc, ignore generated file operation.'
            )
            return

        zip_path = shutil.make_archive(self.book_name, 'zip', self.tmpdir)
        self.logger.info('Made archive {0}'.format(zip_path))

        self.epub_path = os.path.join(
            self.output_directory,
            '{0}-{1}.epub'.format(self.book_title, self.bookid),
        )
        self.logger.info('Moving {0} to {1}'.format(zip_path, self.epub_path))
        shutil.move(zip_path, self.epub_path)

