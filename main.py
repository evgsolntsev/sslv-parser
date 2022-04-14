#!/usr/bin/env python3

import json
import time
from datetime import date

import argparse
import requests

parser = argparse.ArgumentParser(description="Parse ss.lv flats for rent.")
parser.add_argument("--gently", type=bool, default=True, help="wait a bit after each request")
parser.add_argument("--verbose", type=bool, default=True, help="verbose output")
parser.add_argument("--only-first", type=bool, default=False, help="analize only first page")

args = parser.parse_args()

def log(text):
    if args.verbose:
        print(text)

def wait(f):
    def wrap(*a, **kw):
        result = f(*a, **kw)
        if args.gently:
            time.sleep(0.2)
        return result
    return wrap

BASE_URL = "https://www.ss.lv"
SESSION = requests.Session()
url = f"/ru/real-estate/flats/riga/all/hand_over/"

@wait
def get(link):
    log(f"requesting {link}...")
    return SESSION.get(f"{BASE_URL}{link}", allow_redirects=False)

@wait
def post(link, data):
    log(f"posting {link}...")
    return SESSION.post(f"{BASE_URL}{link}", data=data)

class Flat:
    def __init__(self, link, _, address, rooms, meters, floor, home_type, price):
        self.link = link
        self.address = address
        self.rooms = rooms
        self.meters = meters
        self.floor = floor
        self.home_type = home_type
        self.price = price
        self.coordinates = [0, 0]
        self.description = ""

    def __str__(self):
        return f"coordinates: {self.coordinates}, price: {self.price}, meters: {self.meters}, link: {BASE_URL}{self.link}"

    def init(self):
        r = get(self.link)

        text = r.text[r.text.find("ads_opt_link_map"):]
        text = text[text.find("&c=")+3:]
        text = text[:text.find("'")]

        text_coordinates = text.split(",")
        self.coordinates = [float(text_coordinates[0]), float(text_coordinates[1])]

        text = r.text[r.text.find("content_sys_div_msg")+28:]
        text = text[:text.find("<table")]
        text = "\n".join(text.split("<br>"))
        self.description = text

def process_flat(text):
    text = "".join(text.split("<b>"))
    text = "".join(text.split("</b>"))

    link_start_index = text.find("<a href=\"") + 9
    link_end_index = text.find("\" ", link_start_index)
    link = text[link_start_index: link_end_index]
    if "other" in link:
        return None

    text = text[link_end_index:]

    fields = text.split("</td>")[-8:-1]
    fields_processed = []
    for f in fields:
        tmp = f
        while ">" in tmp:
            tmp = tmp[tmp.find(">")+1:]
        fields_processed.append(tmp)

    flat = Flat(link, *fields_processed)
    flat.init()
    return flat

def process_html(text):
    text = text[text.find("head_line"):text.find("tr_bnr")-8]
    text = text[text.find("</td>")+5:]

    flats_list = text.split("</tr>")[1:-1]
    result = []
    for f in flats_list:
        tmp = process_flat(f)
        if tmp is None:
            continue
        result.append(tmp)

    return result

r = get(url)
flats = process_html(r.text)

if not args.only_first:
    i = 2
    while True:
        r = get(f"{url}page{i}.html")
        if r.status_code != 200:
            break
        flats += process_html(r.text)
        i += 1

print(f"found {len(flats)}")


class MyEncoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

today = date.today()
with open(today.strftime("dumps/%d_%m_%Y")+".json", "w") as out_file:
    out_file.write(json.dumps(flats, cls=MyEncoder))
