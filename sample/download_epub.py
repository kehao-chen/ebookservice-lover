import argparse
import asyncio
import csv
import os
import shutil
import re
from ebookservice_lover import epub


def main(content_url: str):
    title = epub.fetch_title(content_url)
    if not os.path.isdir(title):
        os.mkdir(title)
    loop = asyncio.get_event_loop()
    download_coroutine = epub.download_epub_content(
        event_loop=loop,
        content_url=content_url,
        out_dir=title,
        progress_coroutine=epub.basic_progress_coroutine)
    loop.run_until_complete(download_coroutine)
    epub.package_epub_files(title)
    shutil.rmtree(title)


if __name__ == '__main__':
    with open("epub_samples.csv", encoding="utf8") as csv_file:
        for row in csv.reader(csv_file):
            if len(row) == 1:
                content_url = row[0]
                if "OEBPS/content.opf" in content_url:
                    main(content_url)
