from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import InputRequired

class LocationForm(FlaskForm):
    town = StringField("Stadt", validators=[InputRequired("Bitte gib an, in welcher Stadt du Pizza essen willst.")])
    plz = IntegerField("PLZ", validators=[InputRequired("Bitte gib an, in welcher PLZ du Pizza essen willst.")])
