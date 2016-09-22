# safaribooks
Convert safaribooksonline ebook to Kindle format

# Usage
WARNING: use at your own risk.

`scrapy crawl SafariBooks -a user=<user> -a password=<password> -a bookid=<bookid>`
`kindlegen output.epub`

Or simply run `./craw.sh user password bookid` if you have kindlegen at your path.