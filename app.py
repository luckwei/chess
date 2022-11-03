from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretsecretsecret'

@app.route("/", methods=["GET", "POST"])
def home():
    return "Hello World"

if __name__ == "__main__":
    app.run()

