import argparse
import glob
import os
import subprocess

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def download_epub(args):
    if not args.user:
        raise ValueError('argument -u/--user is required for downloading')
    if not args.password:
        raise ValueError('argument -p/--password is required for downloading')
    if not args.book_id:
        raise ValueError('argument -b/--book-id is required for downloading')

    process = CrawlerProcess(get_project_settings())
    process.crawl(
        'SafariBooks',
        user=args.user,
        password=args.password,
        bookid=args.book_id,
        output_directory=args.output_directory,
    )
    process.start()
    return process


def convert_to_mobi(args):
    print(args.output_directory)
    if args.full_path:
        path = args.full_path
    else:
        if not args.book_id:
            raise ValueError(
                'argument -b/--book-id is required when -p/--full-path '
                'is not specified',
            )
        path = glob.glob(
            os.path.join(
                args.output_directory,
                '*-{0}.epub'.format(args.book_id),
            ),
        )[0]

    subprocess.call(['kindlegen', path])


def download(args):
    download_epub(args)

    # This arg is needed for `convert_to_mobi`
    args.full_path = None

    convert_to_mobi(args)


parser = argparse.ArgumentParser(
    description='Crawl Safari Books Online book content',
)
parser.add_argument(
    '-o',
    '--output-directory',
    default=os.path.join(os.getcwd(), 'converted'),
    help='Directory where converted files are located / should be placed',
)
parser.add_argument(
    '-u',
    '--user',
    help='Safari Books Online user / e-mail address',
)
parser.add_argument(
    '-p',
    '--password',
    help='Safari Books Online password',
)
parser.add_argument(
    '-b',
    '--book-id',
    type=int,
    help='Safari Books Online book ID',
)

subparsers = parser.add_subparsers()

download_epub_parser = subparsers.add_parser(
    'download-epub',
    help='Download as epub',
)
download_epub_parser.set_defaults(func=download_epub)

download_parser = subparsers.add_parser(
    'download',
    help='Download as epub, and convert to mobi',
)
download_parser.set_defaults(func=download)

convert_to_mobi_parser = subparsers.add_parser(
    'convert-to-mobi',
    help='Convert existing epub file to mobi.'
)
convert_to_mobi_parser.add_argument(
    '-p',
    '--full-path',
    help='Full path to the epub file to convert, if not in default location.',
)
convert_to_mobi_parser.set_defaults(func=convert_to_mobi)


def main():
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
