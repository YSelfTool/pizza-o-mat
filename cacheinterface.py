import pizzainterface as backend
from pizzainterface import Ingredient, Food, Restaurant
import json
import os
import base64
from datetime import datetime

from config import CACHE_DIR, CACHE_TIME

def get_filename(name):
    return os.path.join(CACHE_DIR, encode_name(name))

def encode_name(name):
    return base64.b64encode(name.encode("utf-8")).decode("utf-8")
def decode_name(name):
    return base64.b64decode(name).decode("utf-8").encode("utf-8")

def save_cache(name, value):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(get_filename(name), "w") as file:
        json.dump({"v": value}, file)
def load_cache(name):
    with open(get_filename(name), "r") as file:
        return json.load(file)["v"]

def check_cache(name):
    filename = get_filename(name)
    if not os.path.isfile(filename):
        return False
    return datetime.now().timestamp() - os.path.getmtime(filename) > CACHE_TIME


def validate_location(town, plz):
    name = f"loc-{town}-{plz}"
    if check_cache(name):
        return load_cache(name)
    result = backend.validate_location(town, plz)
    save_cache(name, result)
    return result

def extract_restaurants(town, plz):
    name = f"res-{town}-{plz}"
    if check_cache(name):
        return [Restaurant.from_json(data) for data in load_cache(name)]
    result = backend.extract_restaurants(town, plz)
    save_cache(name, [restaurant.to_json() for restaurant in result])
    return result

def generate_pizza_data(restaurant):
    name = f"piz-{restaurant.id}"
    if check_cache(name):
        return load_cache(name)
    result = backend.generate_pizza_data(restaurant)
    save_cache(name, result)
    return result

