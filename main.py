from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pantry.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), nullable = False, unique = True)
    email = db.Column(db.String(64), nullable = False, unique = True)
    password = db.Column(db.String(256),nullable = False)
    items = db.relationship("PantryItem", back_populates = "owner")

    def serialize(self):
        return {
            "username": self.username,
            "email": self.email,
        }
    
class PantryItem(db.Model):
    id = db.Column(db.Integer, primary_key =  True)
    name = db.Column(db.String(64), nullable = False)
    quantity = db.Column(db.Float, nullable = False)
    unit = db.Column(db.String(20), nullable = False)
    exp_date = db.Column(db.Date,nullable = False )
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable= False)
    owner = db.relationship("User", back_populates="items")

    def serialize(self):
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "exp_date": str(self.exp_date),
        }

class UserCollection(Resource):

    def get(self):
        users = User.query.all()
        return [u.serialize() for u in users], 200
    
    def post(self):
        pass

class UserItem(Resource):

    def get(self, user):
        pass
    def put(self, user):
        pass
    def delete(self,user):
        pass

class PantryItemCollection(Resource):

    def get(self):
        pantry = PantryItem.query.all()
        return [p.serialize() for p in pantry], 200

    def post(self):
        pass

class PantryItemItem(Resource):

    def get(self, item):
        pass
    def put(self, item):
        pass
    def delete(self, item):
        pass

class ExpiredCollection(Resource):

    def get(self, date):
        pass

class DateItem(Resource):

    def get(self, date):
        pass

class RefillCollection(Resource):

    def get(self, date):
        pass

class UserLogin(Resource):

    def post(self):
        pass
    
class UserLogout(Resource):

    def post(self):
        pass

@app.route("/hello/<name>")
def index(name):
    return "Hello {}".format(name), 200

api.add_resource(UserCollection, "/api/users/")
api.add_resource(UserItem, "/api/users/<user>/")
api.add_resource(PantryItemCollection, "/api/items/")
api.add_resource(PantryItemItem, "/api/items/<item>/")
api.add_resource(ExpiredCollection, "/api/items/expires/")
api.add_resource(RefillCollection, "/api/items/refills/")
api.add_resource(DateItem, "/api/items/expiring/<date>/")
api.add_resource(UserLogin, "/api/users/login/")
api.add_resource(UserLogout, "/api/users/logout/")
