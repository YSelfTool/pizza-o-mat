#!/usr/bin/env python3

from flask import Flask, g, current_app, request, session, flash, redirect, url_for, abort, render_template, Response, Markup

import pizzainterface

import config
from forms import LocationForm

app = Flask(__name__)
app.config.from_object(config)

@app.route("/", methods=["GET", "POST"])
def index():
    form = LocationForm()
    if form.validate_on_submit():
        town = form.town.data
        plz = str(form.plz.data)
        if not pizzainterface.validate_location(town, plz):
            flash("Der eingegebene Ort ist ungültig.", "alert-error")
        else:
            return redirect(url_for("restaurants", town=town, plz=plz))
    return render_template("index.html", form=form)

def get_restaurant_by_name(town, plz, name):
    restaurants = pizzainterface.extract_restaurants(town, plz)
    restaurant = None
    for candidate in restaurants:
        if candidate.name == name:
            restaurant = candidate
            break
    if restaurant is None:
        abort(404)
    return restaurant

@app.route("/<town>_<plz>_restaurants.html")
def restaurants(town, plz):
    if not pizzainterface.validate_location(town, plz):
        flash("Der Ort ist ungültig.", "alert-error")
        return redirect(url_for("index"))
    restaurants = pizzainterface.extract_restaurants(town, plz)
    return render_template("restaurants.html", restaurants=restaurants, town=town, plz=plz)

@app.route("/<town>_<plz>_<restaurant>_app.html")
def restaurant(town, plz, restaurant):
    if not pizzainterface.validate_location(town, plz):
        flash("Der Ort ist ungültig.", "alert-error")
        return redirect(url_for("index"))
    restaurant = get_restaurant_by_name(town, plz, restaurant)
    return render_template("app.html", town=town, plz=plz, restaurant=restaurant)

@app.route("/<town>_<plz>_<restaurant>_app.js")
def app_js(town, plz, restaurant):
    if not pizzainterface.validate_location(town, plz):
        abort(404)
    restaurant = get_restaurant_by_name(town, plz, restaurant)
    return render_template("app.js", town=town, plz=plz, restaurant=restaurant)

@app.route("/data/<town>_<plz>_<restaurant>.json")
def data(town, plz, restaurant):
    if not pizzainterface.validate_location(town, plz):
        abort(404)
    restaurant = get_restaurant_by_name(town, plz, restaurant)
    return pizzainterface.generate_pizza_data(restaurant)

@app.route("/imprint")
def imprint():
    return render_template("imprint.html")

if __name__ == "__main__":
    app.run()
        
