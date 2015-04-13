#!/usr/bin/env python3

# Copyright (c) 2015 Tom Li
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import os
import sys

import re
import json
from subprocess import call
from time import sleep
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


def detect_desktop_environment():
    desktop_env = "unknown"
    if os.environ.get("KDE_FULL_SESSION") == "true":
        desktop_env = "kde"
    elif os.environ.get("GNOME_DESKTOP_SESSION_ID"):
        desktop_env = "gnome"
    elif os.environ.get("MATE_DESKTOP_SESSION_ID"):
        desktop_env = "mate"
    elif sys.platform == "win32":
        desktop_env = "windows"
    return desktop_env


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

    def progress(dt, d, ut, u):
        global progress_prev
        if dt == 0:
            return
        progress = int(d / dt * 100)
        if progress != progress_prev and progress % 10 == 0:
            print("downloaded", "%d%%" % progress)
        progress_prev = progress

    print("\nnow downloading %s..." % filename)
    c = curl.Curl()

    global progress_prev
    progress_prev = 0
    c.set_option(pycurl.NOPROGRESS, 0)
    c.set_option(pycurl.PROGRESSFUNCTION, progress)

    data = c.get(image_url)
    with open(filename, "wb") as file:
        file.write(data)


def set_wallpaper(path):
    path = os.path.realpath(path)
    desktop = detect_desktop_environment()
    if desktop == "gnome":
        path = "file://%s" % path
        call(("gsettings", "set", "org.gnome.desktop.background", "picture-uri", path))
    elif desktop == "mate":
        call(("gsettings", "set", "org.mate.background", "picture-filename", path))
    elif desktop == "kde":
        raise NotImplementedError("How to change wallpaper for KDE?")
    elif desktop == "windows":
        path = '"%s"' % path
        call(("reg", "add", "HKCU\Control Panel\Desktop", "/v", "Wallpaper", "/f", "/t", "REG_SZ", "/d", path))
    else:
        raise NotImplementedError("I don't know how to do it")


def main():
    parser = argparse.ArgumentParser(description="Fetch a random wallpaper from Konachan")
    parser.add_argument("--width", dest="width", type=int, default=0,
                        help="download only if the ratio of the image not matches with your suggestion")
    parser.add_argument("--height", dest="height", type=int, default=0,
                        help="download only if the ratio of the image not matches with your suggestion")
    parser.add_argument("--r18", dest="r18", action="store_true", default=False,
                        help="allow to fetch explicit (R-18) images")
    args = parser.parse_args()

    while 1:
        random_url = pick_up_a_url(args.r18)
        full_info = fetch_image_info(random_url)

        image_info = full_info["posts"][0]
        if (args.height and args.width and
           not fequal(ratio(image_info["height"], image_info["width"]), ratio(args.height, args.width))):
            print("ratio is not perfect, try again...")
            sleep(5)
        else:
            break

    print("tags:")
    tag_info = full_info["tags"]
    for key in tag_info.keys():
        print(key)

    filename = str(image_info["id"])

    download_image(image_info["file_url"], filename)
    set_wallpaper(filename)


if __name__ == "__main__":
    main()
