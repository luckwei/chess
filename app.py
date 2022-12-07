import os

from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = "secretsecretsecret"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"sqlite:///{os.path.join(basedir, 'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Todo(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), index=True, unique=False)


class TodoForm(FlaskForm):
    todo = StringField("Todo", validators=[DataRequired()])
    submit = SubmitField("Submit")

def db_init():
    with app.app_context():
        db.drop_all()  # reset
        db.create_all()
        things_to_do = ["Learn Flask", "Edit package of chess", "Integrate chess into website"]

        for thing in things_to_do:
            db.session.add(Todo(text=thing))
            try:
                db.session.commit()
            except:
                db.session.rollback()

db_init()

@app.route("/", methods=["GET", "POST"])
def chess():
    return render_template("chess.html")

# @app.route("/", methods=["GET", "POST"])
def index():
    todo_form = TodoForm()
    if todo_form.validate_on_submit():
        db.session.add(Todo(text=todo_form.todo.data))
        try:
            db.session.commit()
        except:
            db.session.rollback()

        todo_form = TodoForm(formdata=None)

    return render_template("index.html", todos=Todo.query.all(), todo_form=todo_form)
