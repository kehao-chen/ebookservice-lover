import argparse
import asyncio
import csv
import os
import shutil
import re
from ebookservice_lover import image


def main(format_url: str, out_dir="out"):
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    loop = asyncio.get_event_loop()
    download_coroutine = image.download_consecutive_numbered_images(
        event_loop=loop,
        format_url=format_url,
        out_dir=out_dir,
        progress_coroutine=image.basic_progress_coroutine)
    loop.run_until_complete(download_coroutine)
    image.compress_images_to_zip_format(out_dir, out_dir, zip_ext="cbz")
    shutil.rmtree(out_dir)


if __name__ == '__main__':
    with open("image_samples.csv", encoding="utf8") as csv_file:
        for row in csv.reader(csv_file):
            if len(row) == 2:
                file_name = row[0]
                file_url = row[1]
                if "img?p=" in file_url:
                    format_url = re.sub(r"[?|&]p=[\d]+&", "?p={}&", file_url)
                    main(format_url, out_dir=file_name)
