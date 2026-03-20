from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError
import datetime



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
    
    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["username", "email", "password"]
        }
        props = schema["properties"] = {}
        props["username"] = {
            "description": "Name of the user",
            "type": "string"
        }
        props["email"] = {
            "description": "Email of a user",
            "type": "string"
        }
        props["password"] = {
            "description": "User's password",
            "type": "string"
        }
        return schema
    
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

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["name", "quantity", "unit", "exp_date"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Item name",
            "type": "string"
        }
        props["quantity"] = {
            "description": "Quantity to use",
            "type": "number"
        }
        props["unit"] = {
            "description": "Unit: ml, onz, pieces",
            "type": "string"
        }
        props["exp_date"] = {
            "description": "Expiration date",
            "type": "string"
        }
        return schema

class UserCollection(Resource):
    def get(self):
        users = User.query.all()
        return [u.serialize() for u in users], 200
    
    def post(self):
        if not request.json:
            return "Request type must be JSON", 415
        try:
            username=request.json["username"]
            email=request.json["email"]
            password=request.json["password"]

            new_user = User(
                username=username,
                email=email,
                password=password
            )
            db.session.add(new_user)
            db.session.commit()
        except KeyError:
            return "Request not found", 400
        except (ValueError, TypeError):
            return "user and email formats are incorrect", 400
        except IntegrityError:
            return "User already exists", 409
        return "User added", 201

class UserItem(Resource):
    def get(self, user):
        user_obj = User.query.filter_by(username=user).first()
        if user_obj is None:
            return "User not found", 404
        
        return user_obj.serialize(), 200
    
    def put(self, user):
        user_obj = User.query.filter_by(username=user).first()
        if user_obj is None:
            return "User not found", 404
        if not request.json:
            return "User is not a JSON object", 415
        user_obj.username = request.json["username"]
        user_obj.email = request.json["email"]
        user_obj.password = request.json["password"]
        try:
            db.session.commit()
        except IntegrityError:
            return "Username or email already in use", 409
        return "", 204

    def delete(self,user):
        user_obj = User.query.filter_by(username=user).first()
        if user_obj is None:
            return "User not found", 404
        db.session.delete(user_obj)
        db.session.commit()
        return "", 204

class PantryItemCollection(Resource):

    def get(self):
        pantry = PantryItem.query.all()
        return [p.serialize() for p in pantry], 200

    def post(self):
        if not request.json:
            return "request type shoyld be JSON", 415
        try:
            name=request.json["name"]
            quantity=request.json["quantity"]
            unit=request.json["unit"]
            exp_date=datetime.date.fromisoformat(request.json["exp_date"])
            owner_id=request.json["owner_id"]
            new_pantry = PantryItem(
                name=name,
                quantity=quantity,
                unit=unit,
                exp_date=exp_date,
                owner_id=owner_id
            )
            db.session.add(new_pantry)
            db.session.commit()
        except KeyError:
            return "Request not found", 400
        except (ValueError, TypeError):
            return "pantry item formats are incorrect", 400
        except IntegrityError:
            return "Pantry Item already exists", 409
        return "Product added to pantry", 201

class PantryItemItem(Resource):
    def get(self, item):
        item_obj = PantryItem.query.filter_by(name=item).first()
        if item_obj is None:
            return "Item not found", 404
        return item_obj.serialize(), 200
    
    def put(self, item):
        item_obj = PantryItem.query.filter_by(name=item).first()
        if item_obj is None:
            return "Item not found", 404
        if not request.json:
            return "Item is not a JSON object", 415
        item_obj.name = request.json["name"]
        item_obj.quantity = request.json["quantity"]
        item_obj.unit = request.json["unit"]
        item_obj.exp_date = datetime.date.fromisoformat(request.json["exp_date"])

        try:
            db.session.commit()
        except IntegrityError:
            return "Item already registered", 409
        return "", 204

    def delete(self,item):
        item_obj = PantryItem.query.filter_by(name=item).first()
        if item_obj is None:
            return "Item not found", 404
        db.session.delete(item_obj)
        db.session.commit()
        return "", 204

class ExpiredCollection(Resource):

    def get(self):
        today = datetime.date.today()

        results = PantryItem.query.filter(PantryItem.exp_date < today)
        return [p.serialize() for p in results], 200

class DateItem(Resource):

    def get(self, date):
        item_date = datetime.date.fromisoformat(date)

        results = PantryItem.query.filter(PantryItem.exp_date == item_date)
        return [p.serialize() for p in results], 200

class RefillCollection(Resource):

    def get(self):
        results = PantryItem.query.filter(PantryItem.quantity <= 0)
        return [p.serialize() for p in results], 200

class UserLogin(Resource):

    def post(self):
        pass #TO DO: Implement this later!!!
    
class UserLogout(Resource):

    def post(self):
        pass #TO DO: Implement this later!!!

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
