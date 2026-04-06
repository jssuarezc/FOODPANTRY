from flask_marshmallow import Marshmallow
from marshmallow import fields, validate, post_load
from werkzeug.security import generate_password_hash
from models import User, Household, HouseholdMember, Category, PantryItem

ma = Marshmallow()

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True
        load_only = ("password",)

    @post_load
    def hash_password(self, data, **kwargs):
        if data.password:
            data.password = generate_password_hash(data.password)
            return data

class CategorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        load_instance = True
        include_fk = True

class PantryItemSchema(ma.SQLAlchemyAutoSchema):
    id = fields.Integer(dump_only=True)
    added_by = fields.Integer(dump_only=True)
    categories = ma.Pluck(CategorySchema, "name", many=True)
    quantity = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        model = PantryItem
        load_instance = True
        include_fk = True
        dateformat = '%Y-%m-%d'

class HouseholdMemberSchema(ma.SQLAlchemyAutoSchema):
     
    user = ma.Nested(UserSchema, only=("username", "email"))

    class Meta:
        model = HouseholdMember
        load_instance = True
        include_fk = True

class HouseholdSchema(ma.SQLAlchemyAutoSchema):
    items = ma.Nested(PantryItemSchema, many=True)
    members = ma.Nested(HouseholdMemberSchema, many=True)

    class Meta:
        model = Household
        load_instance = True
        include_fk = True
