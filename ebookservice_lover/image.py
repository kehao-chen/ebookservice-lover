# -*- coding: utf-8 -*-
"""Download image files and compress them to the Zip format.
"""
import zipfile
import os

COMMON_IMAGE_EXTENSIONS = ["jpeg", "jpg", "png"]


def download_consecutive_numbered_images(format_url: str, out_dir: str, format_image_name: str = "{:03}") -> bool:
    pass


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
