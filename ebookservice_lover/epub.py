# -*- coding: utf-8 -*-
"""Download image files and compress them to the Zip format.
"""
import _string
import aiohttp
import asyncio
import zipfile
import os
import mimetypes
import requests
import xml.etree.ElementTree as ET
from contextlib import closing
from typing import Callable, Iterable, Awaitable, Coroutine
from urllib.parse import urljoin

import ebookservice_lover.utils as utils

TAG_ITEM = "{http://www.idpf.org/2007/opf}item"
TAG_TITLE = "{http://purl.org/dc/elements/1.1/}title"

FOLDER_OEBPS = "OEBPS"
FOLDER_META = "META-INF"
FOLDER_OUTPUT = "out"

FILE_OPF = "content.opf"
FILE_CONTAINER = "container.xml"


def fetch_title(content_url: str):
    tree = ET.fromstring(requests.get(content_url).text)
    for elm in tree.iter(tag=TAG_TITLE):
        return elm.text


def package_epub_files(title):
    epub_file = zipfile.ZipFile("{}.epub".format(title), mode='w')
    epub_file.writestr("mimetype", "application/epub+zip")

    os.chdir(title)
    for root, folders, files in os.walk('.'):
        for file in files:
            file_path = os.path.join(root, file)
            epub_file.write(file_path)
    epub_file.close()
    os.chdir('..')


async def download_epub_content(
        event_loop: asyncio.AbstractEventLoop,
        content_url: str,
        out_dir: str,
        progress_coroutine: callable = None):
    """
    :param event_loop:
    :param format_url:
    :param out_dir:
    :param start_number:
    :param stop_number:
    :param file_name_replacement_field:
    :param progress_coroutine:
    :return:
    """
    if not os.path.isdir(out_dir):
        raise ValueError("The output directory doesn't exist.")

    if progress_coroutine is None:
        progress_coroutine = asyncio.wait

    oebps_dir = os.path.join(out_dir, FOLDER_OEBPS)
    if not os.path.isdir(oebps_dir):
        os.makedirs(oebps_dir)
    meta_dir = os.path.join(out_dir, FOLDER_META)
    if not os.path.isdir(meta_dir):
        os.makedirs(meta_dir)

    oebps_url = content_url.replace(FILE_OPF, '')
    container_url = content_url.replace(
        "{}/{}".format(FOLDER_OEBPS, FILE_OPF),
        "{}/{}".format(FOLDER_META, FILE_CONTAINER))
    container_file_path = os.path.join(meta_dir, FILE_CONTAINER)
    utils.simple_download_file(container_url, container_file_path)
    content_file_path = os.path.join(oebps_dir, FILE_OPF)
    utils.simple_download_file(content_url, content_file_path)
    tree = ET.fromstring(requests.get(content_url).text)

    async with aiohttp.ClientSession(loop=event_loop) as session:
        semaphore = asyncio.Semaphore(16)
        futures = []

        for elm in tree.iter(tag=TAG_ITEM):
            paths = elm.attrib["href"].split('/')
            if len(paths) > 1:
                tmp_path = paths[:-1]
                tmp_path = os.path.join(oebps_dir, *tmp_path)
                if not os.path.isdir(tmp_path):
                    os.makedirs(tmp_path)
            download_url = urljoin(oebps_url, elm.attrib['href'])
            file_path = os.path.join(oebps_dir, *paths)
            download_task = asyncio.ensure_future(utils.download_file(download_url, semaphore, session, file_path))
            futures.append(download_task)
        await progress_coroutine(futures)


async def basic_progress_coroutine(tasks: Iterable) -> None:
    """ A basic example of coroutine to update progress

    :param tasks: Asynchronous tasks which are callable.
    :return:
    """
    total_number = len(tasks)
    success_number = 0
    failed_number = 0
    for future in asyncio.as_completed(tasks):
        result = await future
        if result:
            success_number += 1
        else:
            failed_number += 1
        print("{}/{} (Failed: {})".format(success_number + failed_number, total_number, failed_number))


