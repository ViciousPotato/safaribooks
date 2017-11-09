# safaribooks
Convert safaribooksonline ebook to epub and Kindle mobi format

# Usage
WARNING: use at your own risk.

1. If you want Kindle mobi output, download kindlegen from Amazon and put the binary somewhere in PATH.
    
   If you only need epub books this step can be skipped.

2. Make sure you have Python 2 installed (Tested version Python 2.7).

   Run `pip install -r requirements.txt` to install dependency

3. Download a book.
   
  `./crawl.sh user password bookid`.
   
   `bookid` is the id in url such as `9781617291920` in `https://www.safaribooksonline.com/library/view/real-world-machine-learning/9781617291920/kindle_split_011.html`.
   
   An epub and a mobi file will be generated.
   
Create an issue if you find it does not work!
