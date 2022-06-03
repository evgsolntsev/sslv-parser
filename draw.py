#!/usr/bin/env python3

import json

import argparse
import folium

parser = argparse.ArgumentParser(description="Parse ss.lv flats for rent")
parser.add_argument("--skip-daily", type=bool, default=True, help="Skip flats with daily rent")
parser.add_argument("--min-price", type=float, default=500, help="Minimum price")
parser.add_argument("--max-price", type=float, default=1000, help="Maximum price")
parser.add_argument("--min-square", type=float, default=70, help="Minimum square")
parser.add_argument(
    "--with-fireplace", type=bool, default=False, help="Check that description contains fireplace")

args = parser.parse_args()


BASE_URL = "https://www.ss.lv"

with open('dump.json', 'r') as openfile:
    flats = json.load(openfile)

office_coordinates=[56.951790, 24.124830]

result_map = folium.Map(location=office_coordinates, zoom_start=14, control_scale=True)
folium.Marker(
    location=office_coordinates, tooltip="JOOM", icon=folium.Icon(color="red"),
).add_to(result_map)


def parse_price(text):
    text_price = text.split()[0]
    price = int("".join(text_price.split(",")))
    if text.find(" \u20ac/\u0434\u0435\u043d\u044c") > 0:
        price *= 30
    return price

for f in flats:
    if args.skip_daily:
        if f["price"].find(" \u20ac/\u0434\u0435\u043d\u044c") > 0:
            continue
    price = parse_price(f["price"])
    if price < args.min_price or price > args.max_price:
        continue
    meters = float(f["meters"])
    if meters < args.min_square:
        continue
    if args.with_fireplace:
        if not ("fireplace" in f["description"] or "камин" in f["description"] or "kamīns" in f["description"]):
            continue
    folium.Marker(
        location=f["coordinates"],
        popup=folium.Popup(f"<a href=\"{BASE_URL}{f['link']}\">{f['address']}</a><br>{f['description']}", min_width=500, max_width=500),
        tooltip=f"{meters} m2, {price} €/month",
    ).add_to(result_map)

result_map.save("map.html")
