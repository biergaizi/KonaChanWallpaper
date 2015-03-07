#!/usr/bin/env python3

import os
import re
import json
from subprocess import call

import pycurl
import curl

HEIGHT = 1920
WIDTH = 1080


# TODO:
# * tag filters
# * better error handling
# * safe mode (easy)
# * commmand-line arguments


def fequal(a, b):
    return abs(a - b) < 0.001


def ratio(a, b):
    return a / b


def pick_up_a_url():
    c = curl.Curl()
    c.set_option(pycurl.FOLLOWLOCATION, False)
    c.get("http://konachan.net/post/random")
    return c.get_info(pycurl.REDIRECT_URL)


def fetch_image_info(image_page_url):
    c = curl.Curl()
    html = c.get(image_page_url).decode("UTF-8")
    json_info = re.findall('(?<=Post.register_resp\\().*(?=\\);)', html)[0]
    return json.loads(json_info)


def download_image(image_url, filename):
    print("\nnow downloading %s..." % filename)
    c = curl.Curl()
    data = c.get(image_url)
    c.set_option(pycurl.PROGRESSFUNCTION, lambda dt, d, ut, u: print("%f%%" % d / dt))
    with open(filename, "wb") as file:
        file.write(data)


def set_wallpaper(path):
    path = "file://%s" % path
    call(("gsettings", "set", "org.gnome.desktop.background", "picture-uri", path))


def main():
    random_url = pick_up_a_url()
    full_info = fetch_image_info(random_url)

    image_info = full_info["posts"][0]
    if not fequal(ratio(image_info["height"], image_info["width"]), ratio(HEIGHT, WIDTH)):
        print("The ratio is not prefect, maybe you'd like to try again?")

    print("tags:")
    tag_info = full_info["tags"]
    for key in tag_info.keys():
        print(key)

    filename = str(image_info["id"])

    download_image(image_info["file_url"], filename)
    set_wallpaper(os.path.realpath(filename))


if __name__ == "__main__":
    main()
