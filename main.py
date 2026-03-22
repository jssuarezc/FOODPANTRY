from flasgger import Swagger
import datetime
import os
import random
import string
from dotenv import load_dotenv
from sqlalchemy import or_
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
app.config["SWAGGER"] = {
    "title": "Fridgeventory",
    "openapi": "3.0.3",
    "uiversion": 3,
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT token. Format: Bearer <token>"
        }
    },
    "security": [
        {"Bearer": []}
    ]
}
swagger = Swagger(app, template_file="foodpantry.yaml")

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

class Category(db.Model):
    __table_args__= (db.UniqueConstraint("name", "household_id"),)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    household = db.relationship("Household")    

pantry_item_category = db.Table(
    "pantry_item_category",
    db.Column("item_id", db.Integer, db.ForeignKey("pantry_item.id"), primary_key=True),
    db.Column("category_id", db.Integer, db.ForeignKey("category.id"), primary_key=True)
)

class PantryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    min_quantity = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(20), nullable=False)
    exp_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(64), nullable=False)
    brand = db.Column(db.String(80), nullable = True)
    added_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    item_added = db.relationship("User", back_populates="items", foreign_keys=[added_by])
    household = db.relationship("Household")
    categories = db.relationship("Category", secondary=pantry_item_category)

    def serialize(self):
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "min_quantity": self.min_quantity,
            "exp_date": str(self.exp_date),
            "location": self.location,
            "brand": self.brand,
            "categories": [c.name for c in self.categories]
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
        props["min_quantity"] = {"description": "Minimum quantity before refill needed", "type": "number"}
        props["unit"] = {"description": "Unit: ml, onz, pieces", "type": "string"}
        props["exp_date"] = {"description": "Expiration date", "type": "string"}
        props["location"] = {"description": "fridge, freezer", "type": "string"}
        return schema

def get_membership(username, household_id):
    user_obj = User.query.filter_by(username=username).first()
    if user_obj is None:
        return None, None
    member_assign = HouseholdMember.query.filter_by(
        household_id=household_id,
        user_id=user_obj.id
    ).first()
    return user_obj, member_assign

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

class HouseholdCollection(Resource):

    @jwt_required()
    def get(self):
        username = get_jwt_identity()
        user_obj = User.query.filter_by(username=username).first()
        if user_obj is None:
            return "User not found", 404        

        members_in = HouseholdMember.query.filter_by(user_id=user_obj.id).all()

        return [{"id": m.household.id, "name": m.household.name, "role": m.role} for m in members_in], 200


    @jwt_required()
    def post(self):
        if not request.json:
            return "request type should be JSON", 415
        if "name" not in request.json:
            return "Name field missing", 400
        try:
            current_user = get_jwt_identity()
            user_find = User.query.filter_by(username=current_user).first()

            join_code = generate_join_code()

            new_household = Household(
                name=request.json["name"],
                join_code=join_code,
                created_by=user_find.id
            )

            db.session.add(new_household)
            db.session.flush()

            new_member = HouseholdMember(
                household_id=new_household.id,
                user_id=user_find.id,
                role="owner"
            )
            db.session.add(new_member)
            db.session.commit()
        except KeyError:
            return "Missing fields", 400
        except IntegrityError:
            return "Household already assigned", 409
        return {
            "message": "Household created",
            "name": new_household.name,
            "join_code": join_code,
            "id": new_household.id
        }, 201

class HouseholdItem(Resource):

    @jwt_required()
    def get(self, household):

        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access denied", 403
        
        house = Household.query.get(household)
        if house is None:
            return "House not found", 404
        
        return {"id": house.id, "name": house.name,"join_code": house.join_code}, 200

    @jwt_required()
    def put(self, household):

        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access denied", 403
        
        if membership.role != "owner":
            return "Only owner can rename household", 403
        
        if not request.json or "name" not in request.json:
            return "Name field missing", 400
        
        house = Household.query.get(household)
        if house is None:
            return "Household not found", 404
        
        house.name = request.json["name"]
        try:
            db.session.commit()
        except IntegrityError:
            return "Cannot update household", 409
        return "", 204
    
    @jwt_required()
    def delete(self, household):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403
        if membership.role != "owner":
            return "Only owner can delete household", 403
        house = Household.query.get(household)
        if house is None:
            return "Household not found", 404
        db.session.delete(house)
        db.session.commit()
        return "", 204

class MemberCollection(Resource):

    @jwt_required()
    def get(self, household):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403
        
        find_members = HouseholdMember.query.filter_by(household_id = household).all()

        return [{"username": m.user.username, "role": m.role} for m in find_members], 200

class JoinHousehold(Resource):

    @jwt_required()
    def post(self):
        if not request.json:
            return "request type should be JSON", 415
        if "join_code" not in request.json:
            return "Code not found", 400
        try:
            join_code = request.json["join_code"]
            current_user=get_jwt_identity()
            user_find = User.query.filter_by(username=current_user).first()
            find_house = Household.query.filter_by(join_code=join_code).first()
            if find_house is None:
                return "Household not found", 404

            existing_member = HouseholdMember.query.filter_by(
                household_id=find_house.id,
                user_id=user_find.id
            ).first()
            if existing_member:
                return "Already a member in this house", 409

            new_h_member = HouseholdMember(
                household_id = find_house.id,
                user_id=user_find.id,
                role = "member"
            )
            db.session.add(new_h_member)
            db.session.commit()
        except KeyError:
            return "Bad request", 400

        return "Used added to household", 201

class PantryItemCollection(Resource):

    @jwt_required()
    def get(self, household):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403
        pantry = PantryItem.query.filter_by(household_id=household).all()
        return [p.serialize() for p in pantry], 200

    @jwt_required()
    def post(self, household):
        if not request.json:
            return "request type shoyld be JSON", 415
        _, membership = get_membership(get_jwt_identity(),household)
        if membership is None:
            return "Access Denied", 403
        try:
            current_user = get_jwt_identity()
            user_find = User.query.filter_by(username=current_user).first()
            name = request.json["name"]
            quantity = request.json["quantity"]
            min_quantity = request.json.get("min_quantity")
            unit = request.json["unit"]
            exp_date = datetime.date.fromisoformat(request.json["exp_date"])
            location = request.json["location"]
            brand = request.json.get("brand")
            new_pantry = PantryItem(
                name=name,
                quantity=quantity,
                min_quantity=min_quantity,
                unit=unit,
                exp_date=exp_date,
                added_by=user_find.id,
                household_id=household,
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
    def get(self, household, item):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access denied", 403
        
        item_obj = PantryItem.query.filter_by(name=item, household_id=household).first()
        if item_obj is None:
            return "Item not found", 404
        return item_obj.serialize(), 200

    @jwt_required()
    def put(self, household, item):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access denied", 403
        
        item_obj = PantryItem.query.filter_by(name=item, household_id=household).first()
        if item_obj is None:
            return "Item not found", 404
        if not request.json:
            return "Item is not a JSON object", 415
        item_obj.name = request.json["name"]
        item_obj.quantity = request.json["quantity"]
        item_obj.min_quantity = request.json.get("min_quantity")
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
    def delete(self, household, item):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access denied", 403
        
        item_obj = PantryItem.query.filter_by(name=item, household_id=household).first()
        if item_obj is None:
            return "Item not found", 404
        db.session.delete(item_obj)
        db.session.commit()
        return "", 204

class PantryItemSearch(Resource):

    @jwt_required()
    def get(self, household):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403

        search = request.args.get("q")
        if search is None:
            return "No term provided for search", 400

        results = PantryItem.query.filter(
            PantryItem.household_id == household,
            PantryItem.name.ilike(f"%{search}%")
        )
        return [p.serialize() for p in results], 200
    
class PantryItemCategoryCollection(Resource):

    @jwt_required()
    def post(self, household, item):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403
        
        item_obj = PantryItem.query.filter_by(name=item, household_id=household).first()
        if item_obj is None:
            return "Item not found", 404
        
        if not request.json or "category_id" not in request.json:
            return "category_id required", 400
        
        category = Category.query.filter_by(
            id=request.json["category_id"],
            household_id=household
        ).first()
        if category is None:
            return "Category not found", 404
        
        if category in item_obj.categories:
            return "Category already assigned for this item", 409
        
        item_obj.categories.append(category)
        db.session.commit()
        return {"message": "Category assigned"}, 201

    @jwt_required()
    def delete(self, household, item):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403

        item_obj = PantryItem.query.filter_by(name=item, household_id=household).first()
        if item_obj is None:
            return "Item not found", 404
        
        if not request.json or "category_id" not in request.json:
            return "category_id required", 400
        
        category = Category.query.filter_by(
            id=request.json["category_id"],
            household_id=household
        ).first()
        if category is None:
            return "Category not found", 404
        
        if category not in item_obj.categories:
            return "Category not assigned for this item", 409
        
        item_obj.categories.remove(category)
        db.session.commit()
        return "", 204

class ExpiredCollection(Resource):

    @jwt_required()
    def get(self, household):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403
        today = datetime.date.today()

        results = PantryItem.query.filter(
            PantryItem.household_id == household,
            PantryItem.exp_date < today
            )
        return [p.serialize() for p in results], 200


class DateItem(Resource):

    @jwt_required()
    def get(self, household, date):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403
        item_date = datetime.date.fromisoformat(date)

        results = PantryItem.query.filter(
            PantryItem.household_id == household,
            PantryItem.exp_date == item_date
            )
        return [p.serialize() for p in results], 200


class RefillCollection(Resource):

    @jwt_required()
    def get(self, household):
        _, membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403
        results = PantryItem.query.filter(
            PantryItem.household_id == household,
            or_(PantryItem.quantity <= PantryItem.min_quantity, PantryItem.quantity <= 0)
            ).all()
        return [p.serialize() for p in results], 200
    
class CategoryCollection(Resource):

    @jwt_required()
    def get(self, household):
        _,membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403
        
        categories = Category.query.filter_by(household_id=household).all()

        return [{"id": c.id, "name": c.name} for c in categories], 200

    @jwt_required()
    def post(self, household):
        _,membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403
        
        if not request.json or "name" not in request.json:
            return "Name Required", 400
        
        try:
            new_category = Category(
                name=request.json["name"],
                household_id=household
            )
            db.session.add(new_category)
            db.session.commit()
        except IntegrityError:
            return "Category currently exists in the house", 409
        
        return {"id": new_category.id, "name": new_category.name}, 201

class CategoryItem(Resource):

    @jwt_required()
    def get(self, household, category):
        _,membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403
        
        category = Category.query.filter_by(id=category, household_id=household).first()
        if category is None:
            return "Category not found", 404
        
        return {"id": category.id, "name": category.name}, 200

    @jwt_required()
    def delete(self, household, category):
        _,membership = get_membership(get_jwt_identity(), household)
        if membership is None:
            return "Access Denied", 403
        
        category = Category.query.filter_by(id=category, household_id=household).first()
        if category is None:
            return "Category not found", 404
        
        db.session.delete(category)
        db.session.commit()
        return "", 204

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

api.add_resource(UserCollection, "/api/users/")
api.add_resource(UserItem, "/api/users/<user>/")
api.add_resource(HouseholdCollection, "/api/households/")
api.add_resource(HouseholdItem, "/api/households/<household>/")
api.add_resource(MemberCollection, "/api/households/<household>/members/")
api.add_resource(JoinHousehold, "/api/join/")
api.add_resource(PantryItemCollection, "/api/households/<household>/items/")
api.add_resource(PantryItemItem, "/api/households/<household>/items/<item>/")
api.add_resource(PantryItemSearch, "/api/households/<household>/items/search/")
api.add_resource(ExpiredCollection, "/api/households/<household>/items/expires/")
api.add_resource(RefillCollection, "/api/households/<household>/items/refills/")
api.add_resource(DateItem, "/api/households/<household>/items/expiring/<date>/")
api.add_resource(CategoryCollection, "/api/households/<household>/categories/")
api.add_resource(CategoryItem, "/api/households/<household>/categories/<category>/")
api.add_resource(PantryItemCategoryCollection, "/api/households/<household>/items/<item>/categories/")
api.add_resource(UserLogin, "/api/users/login/")
api.add_resource(UserLogout, "/api/users/logout/")
