# -*- coding: utf-8 -*-
"""This module provides utility functions.
"""
import requests


def download_file(url: str, path: str) -> bool:
    """Download content from URL and save it to target path

    :param url: URL of content.
    :param path: Target path for saving file.
    :return: bool
    """
    r = requests.get(url, stream=True)
    with open(path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return True
