import json
import os
from datetime import date, datetime

import folium
from flask import Flask
from flask import render_template
from flask import request
from geopy import distance

app = Flask(__name__)

@app.route('/')
def root():
    return render_template("root.html", date=get_latest_date())

office_coordinates=[56.951790, 24.124830]
BASE_URL = "https://www.ss.lv"

def parse_price(text):
    text_price = text.split()[0]
    price = int("".join(text_price.split(",")))
    if text.find(" \u20ac/\u0434\u0435\u043d\u044c") > 0:
        price *= 30
    return price

@app.route('/map')
def map():
    result_map = folium.Map(location=office_coordinates, zoom_start=14, control_scale=True)
    folium.Marker(
        location=office_coordinates, tooltip="JOOM", icon=folium.Icon(color="red"),
    ).add_to(result_map)

    today = date.today()
    with open(f"dumps/{get_latest_date()}.json", "r") as openfile:
        flats = json.load(openfile)

    skip_daily = request.args.get("skip_daily")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    min_square = request.args.get("min_square")
    max_distance = request.args.get("max_distance")
    with_fireplace = request.args.get("with_fireplace")

    for f in flats:
        if skip_daily == "true":
            if f["price"].find(" \u20ac/\u0434\u0435\u043d\u044c") > 0:
                continue
        price = parse_price(f["price"])
        try:
            if min_price and (int(min_price) > price):
                continue
            if max_price and (int(max_price) < price):
                continue
            meters = float(f["meters"])
        except:
            continue
        if min_square and (meters < int(min_square)):
            continue
        if max_distance and (float(max_distance) < distance.distance(office_coordinates, f["coordinates"])):
            continue
        if with_fireplace:
            if not ("fireplace" in f["description"] or "камин" in f["description"] or "kamīns" in f["description"]):
                continue
        address = escape(f["address"])
        description = escape(f["description"])
        folium.Marker(
            location=f["coordinates"],
            popup=folium.Popup(
                f"<a href=\"{BASE_URL}{f['link']}\">{address}</a><br>{description}",
                min_width=500, max_width=500),
            tooltip=f"{meters} m2, {price} €/month",
        ).add_to(result_map)

    return result_map.get_root().render()

def get_latest_date():
    filenames = os.listdir("dumps/")
    dates = []
    for f in filenames:
        dates.append(datetime.strptime(f[:-5], "%d_%m_%Y"))
    dates.sort()
    return dates[-1].strftime("%d_%m_%Y")

def escape(s):
    return "\\\\".join(s.split("\\"))
