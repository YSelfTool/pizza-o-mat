#!/usr/bin/env python3

from flask import Flask, g, current_app, request, session, flash, redirect, url_for, abort, render_template, Reponse, Markup

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


if __name__ == "__main__":
    app.run()
        
