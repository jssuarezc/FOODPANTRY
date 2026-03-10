from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pantry.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), nullable = False, unique = True)
    email = db.Column(db.String(64), nullable = False, unique = True)
    password = db.Column(db.String(256),nullable = False)
    items = db.relationship("PantryItem", back_populates = "owner")
    
class PantryItem(db.Model):
    id = db.Column(db.Integer, primary_key =  True)
    name = db.Column(db.String(64), nullable = False)
    quantity = db.Column(db.Float, nullable = False)
    unit = db.Column(db.String(20), nullable = False)
    exp_date = db.Column(db.Date,nullable = False )
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable= False)
    owner = db.relationship("User", back_populates="items")

@app.route("/hello/<name>")
def index(name):
    return "Hello {}".format(name), 200
