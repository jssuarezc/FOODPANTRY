from flask import request
from flask_restful  import Resource
from models import db, Category, Household
from schemas import CategorySchema
from marshmallow import ValidationError

category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)

class CategoryCollection(Resource):
    def get(self, household_id):
        Household.query.get_or_404(household_id)
        categories = Category.query.filter_by(household_id=household_id).all()
        return categories_schema.dump(categories), 200
    
    def post(self, household_id):
        Household.query.get_or_404(household_id)
        try:
            category = category_schema.load(request.json)
            category.household_id = household_id

            db.session.add(category)
            db.session.commit()
            return category_schema.dump(category), 201
        except ValidationError as error:
            return error.messages, 400
        
class CategoryItem(Resource):
    def delete(self, household_id, category_id):
        category = Category.query.filter_by(id=category_id, household_id=household_id).first_or_404()
        db.session.delete(category)
        db.session.commit()
        return None, 204
