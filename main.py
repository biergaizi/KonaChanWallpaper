#!/usr/bin/env python3

import os
import re
import json
from subprocess import call
import argparse

import pycurl
import curl


# TODO:
# * tag filters
# * better error handling


def fequal(a, b):
    return abs(a - b) < 0.001


def ratio(a, b):
    return a / b


def pick_up_a_url(r18=False):
    URL_SAFE = "http://konachan.net/post/random"
    URL_R18 = "http://konachan.com/post/random"

    c = curl.Curl()
    c.set_option(pycurl.FOLLOWLOCATION, False)

    if r18:
        c.get(URL_R18)
    else:
        c.get(URL_SAFE)
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", dest="width", type=int, default=0)
    parser.add_argument("--height", dest="height", type=int, default=0)
    parser.add_argument("--r18", dest="r18", type=bool, default=False)
    args = parser.parse_args()

    random_url = pick_up_a_url(args.r18)
    full_info = fetch_image_info(random_url)

    image_info = full_info["posts"][0]
    if (args.height and args.width and
       not fequal(ratio(image_info["height"], image_info["width"]), ratio(args.height, args.width))):
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
