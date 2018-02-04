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
from contextlib import closing
from typing import Callable, Iterable, Awaitable, Coroutine
import ebookservice_lover.utils as utils

COMMON_IMAGE_EXTENSIONS = ["jpg", "png"]


async def download_consecutive_numbered_images(
        event_loop: asyncio.AbstractEventLoop,
        format_url: str,
        out_dir: str,
        start_number: int = 1,
        stop_number: int = -1,
        file_name_replacement_field: str = "{:03}",
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
    if _total_replacement_field_number(format_url) != 1:
        raise ValueError("The format URL should only has one replacement field.")

    if not os.path.isdir(out_dir):
        raise ValueError("The output directory doesn't exist.")

    if stop_number < 0:
        stop_number = _fetch_stop_number(format_url, start_number)

    file_extension = _fetch_possible_extension(format_url.format(start_number))

    if progress_coroutine is None:
        progress_coroutine = asyncio.wait

    async with aiohttp.ClientSession(loop=event_loop) as session:
        semaphore = asyncio.Semaphore(16)
        futures = []
        for i in range(start_number, stop_number):
            download_url = format_url.format(i)
            file_name = "{}.{}".format(file_name_replacement_field.format(i), file_extension)
            file_path = os.path.join(out_dir, file_name)
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


def _fetch_stop_number(format_url: str, start_number: int, steps: int = 100) -> int:
    """Fetch the stop number of consecutive numbered content

    :param format_url: The format URL of consecutive numbered content
    :param start_number:
    :param steps:
    :return: The stop number of content
    """
    if start_number < 0:
        raise ValueError("Start number should be an unsigned integer")
    stop_number = start_number + steps
    h = requests.head(format_url.format(stop_number))
    if h.status_code == requests.codes.ok:
        if steps < 0:
            steps = (steps * -1) // 2
        if steps == 0:
            steps += 1
    else:
        if steps == 1:
            return stop_number
        elif steps > 0:
            steps = (steps * -1) // 2
        else:
            steps = steps // 2
    return _fetch_stop_number(format_url, stop_number, steps=steps)


def _fetch_possible_extension(content_url: str) -> str:
    """

    :param content_url:
    :return:
    """
    h = requests.head(content_url)
    h.raise_for_status()
    content_type = h.headers["content-type"].split()[0].rstrip(";")
    for mime_type in mimetypes.guess_all_extensions(content_type):
        extension = mime_type.replace(".", "")
        if extension in COMMON_IMAGE_EXTENSIONS:
            return extension
    raise ValueError("Didn't fetch a valid image extension")


def _total_replacement_field_number(format_str: str) -> int:
    """Get the total number of replacement field in the format string

    :param format_str: The string which contains replacement field.
    :return: Total number of replacement field.
    """
    field_count = 0
    for _, field_name, _, _ in _string.formatter_parser(format_str):
        if field_name is not None:
            field_count += 1
    return field_count


def compress_images_to_zip_format(source_dir: str, zip_name: str, zip_ext: str = "zip") -> bool:
    """Compress all image contents in the root folder of source

    :param source_dir: The directory of image contents.
    :param zip_name: File name of the Zip file.
    :param zip_ext: (optional) Extension of Zip file, for comic book it can be set as "cbz".
    :return: bool
    """
    if not os.path.isdir(source_dir):
        raise FileNotFoundError("The source directory {} does not exist.".format(source_dir))

    with zipfile.ZipFile("{}.{}".format(zip_name, zip_ext), mode="w") as zip_file:
        for root, _, files in os.walk(source_dir):
            for file in files:
                _, file_ext = os.path.split(file)
                if file_ext.lower() in COMMON_IMAGE_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, file)
    return True
