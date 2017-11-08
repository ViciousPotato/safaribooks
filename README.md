# safaribooks
Convert safaribooksonline ebook to Kindle format

# Usage
WARNING: use at your own risk.

1. Download kindlegen from Amazon and put the binary somewhere in PATH.
    
   If you only need epub books this step can be skipped.

2. Make sure you have Python, Scrapy and BeautifulSoup 4 installed.

`pip install -r requirements.txt`

3. Make a folder for temporary files
`mkdir output`

4. Download a book.
   
`./crawl.sh user password bookid`.
   
`bookid` is the id in url such as `https://www.safaribooksonline.com/library/view/real-world-machine-learning/9781617291920/kindle_split_011.html` (`9781617291920` in this case) when you read books in safaribooksonline.
   
   An epub and mobi file will be generated.
   
Create an issue if you find it does not work!
