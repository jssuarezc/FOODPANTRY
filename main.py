import datetime
import os
import random
import string
from dotenv import load_dotenv
from flask import Flask, request
from flask_jwt_extended import (JWTManager, create_access_token, get_jwt,
                                get_jwt_identity, jwt_required)
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True

db = SQLAlchemy(app)
api = Api(
    app,
    errors={
        "NoAuthorizationError": {"message": "Missing or invalid token", "status": 401}
    },
)

app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=24)
jwt = JWTManager(app)

BLOCKLIST = set()


@jwt.unauthorized_loader
def unauthorized_response(_):
    return {"message": "Missing or invalid token"}, 401


@jwt.token_in_blocklist_loader
def check_if_token_revoked(_, jwt_payload):
    return jwt_payload["jti"] in BLOCKLIST


@jwt.revoked_token_loader
def revoked_token_response(_, __):
    return {"message": "Token has been revoked"}, 401

def generate_join_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    items = db.relationship(
        "PantryItem", back_populates="item_added", foreign_keys="PantryItem.added_by",cascade="all, delete-orphan"
    )
    households = db.relationship("HouseholdMember", back_populates="user", cascade="all, delete-orphan")

    def serialize(self):
        return {
            "username": self.username,
            "email": self.email,
        }

    def pwd_set(self, password):
        self.password = generate_password_hash(password)

    def pwd_check(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def json_schema():
        schema = {"type": "object", "required": ["username", "email", "password"]}
        props = schema["properties"] = {}
        props["username"] = {"description": "Name of the user", "type": "string"}
        props["email"] = {"description": "Email of a user", "type": "string"}
        props["password"] = {"description": "User's password", "type": "string"}
        return schema

class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    join_code = db.Column(db.String(8), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    members = db.relationship("HouseholdMember", back_populates="household", cascade="all, delete-orphan")

class HouseholdMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"),nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(10),nullable=False, default="member")
    household = db.relationship("Household", back_populates="members")
    user = db.relationship("User", back_populates="households")

class PantryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    exp_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(64), nullable=False)
    brand = db.Column(db.String(80), nullable = True)
    added_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    item_added = db.relationship("User", back_populates="items", foreign_keys=[added_by])
    household = db.relationship("Household")

    def serialize(self):
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "exp_date": str(self.exp_date),
            "location": self.location,
            "brand": self.brand
        }

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["name", "quantity", "unit", "exp_date", "location"],
        }
        props = schema["properties"] = {}
        props["name"] = {"description": "Item name", "type": "string"}
        props["quantity"] = {"description": "Quantity to use", "type": "number"}
        props["unit"] = {"description": "Unit: ml, onz, pieces", "type": "string"}
        props["exp_date"] = {"description": "Expiration date", "type": "string"}
        props["location"] = {"description": "fridge, freezer", "type": "string"}
        return schema


class UserCollection(Resource):

    @jwt_required()
    def get(self):
        users = User.query.all()
        return [u.serialize() for u in users], 200

    def post(self):
        if not request.json:
            return "Request type must be JSON", 415
        try:
            username = request.json["username"]
            email = request.json["email"]
            password = request.json["password"]

            new_user = User(
                username=username,
                email=email,
            )

            new_user.pwd_set(password)
            db.session.add(new_user)
            db.session.commit()
        except KeyError:
            return "Missing Fields", 400
        except IntegrityError:
            return "User already exists", 409
        return "User added", 201


class UserItem(Resource):

    @jwt_required()
    def get(self, user):
        user_obj = User.query.filter_by(username=user).first()
        if user_obj is None:
            return "User not found", 404

        return user_obj.serialize(), 200

    @jwt_required()
    def put(self, user):
        user_obj = User.query.filter_by(username=user).first()
        if user_obj is None:
            return "User not found", 404
        if not request.json:
            return "User is not a JSON object", 415
        user_obj.username = request.json["username"]
        user_obj.email = request.json["email"]
        user_obj.pwd_set(request.json["password"])
        try:
            db.session.commit()
        except IntegrityError:
            return "Username or email already in use", 409
        return "", 204

    @jwt_required()
    def delete(self, user):
        user_obj = User.query.filter_by(username=user).first()
        if user_obj is None:
            return "User not found", 404
        db.session.delete(user_obj)
        db.session.commit()
        return "", 204


class PantryItemCollection(Resource):

    @jwt_required()
    def get(self):
        pantry = PantryItem.query.all()
        return [p.serialize() for p in pantry], 200

    @jwt_required()
    def post(self):
        if not request.json:
            return "request type shoyld be JSON", 415
        try:
            name = request.json["name"]
            quantity = request.json["quantity"]
            unit = request.json["unit"]
            exp_date = datetime.date.fromisoformat(request.json["exp_date"])
            owner_id = request.json["owner_id"]
            location = request.json["location"]
            brand = request.json.get("brand")
            new_pantry = PantryItem(
                name=name,
                quantity=quantity,
                unit=unit,
                exp_date=exp_date,
                owner_id=owner_id,
                location = location,
                brand = brand
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

    @jwt_required()
    def get(self, item):
        item_obj = PantryItem.query.filter_by(name=item).first()
        if item_obj is None:
            return "Item not found", 404
        return item_obj.serialize(), 200

    @jwt_required()
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
        item_obj.location = request.json["location"]
        item_obj.brand = request.json.get("brand")

        try:
            db.session.commit()
        except IntegrityError:
            return "Item already registered", 409
        return "", 204

    @jwt_required()
    def delete(self, item):
        item_obj = PantryItem.query.filter_by(name=item).first()
        if item_obj is None:
            return "Item not found", 404
        db.session.delete(item_obj)
        db.session.commit()
        return "", 204


class ExpiredCollection(Resource):

    @jwt_required()
    def get(self):
        today = datetime.date.today()

        results = PantryItem.query.filter(PantryItem.exp_date < today)
        return [p.serialize() for p in results], 200


class DateItem(Resource):

    @jwt_required()
    def get(self, date):
        item_date = datetime.date.fromisoformat(date)

        results = PantryItem.query.filter(PantryItem.exp_date == item_date)
        return [p.serialize() for p in results], 200


class RefillCollection(Resource):

    @jwt_required()
    def get(self):
        results = PantryItem.query.filter(PantryItem.quantity <= 0)
        return [p.serialize() for p in results], 200


class UserLogin(Resource):

    def post(self):

        if not request.json:
            return "Request must be JSON", 415

        username = request.json.get("username")
        password = request.json.get("password")

        user_obj = User.query.filter_by(username=username).first()

        if not user_obj or not user_obj.pwd_check(password):
            return "Invalid username or password", 401

        token = create_access_token(identity=username)
        return {"token": token}, 200


class UserLogout(Resource):

    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out"}, 200


@app.route("/hello/<name>")
def index(name):
    return f"Hello {name}", 200


api.add_resource(UserCollection, "/api/users/")
api.add_resource(UserItem, "/api/users/<user>/")
api.add_resource(PantryItemCollection, "/api/items/")
api.add_resource(PantryItemItem, "/api/items/<item>/")
api.add_resource(ExpiredCollection, "/api/items/expires/")
api.add_resource(RefillCollection, "/api/items/refills/")
api.add_resource(DateItem, "/api/items/expiring/<date>/")
api.add_resource(UserLogin, "/api/users/login/")
api.add_resource(UserLogout, "/api/users/logout/")
