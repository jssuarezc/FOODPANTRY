import random
import string
from flask import request, session
from flask_restful import Resource
from models import db, Household, HouseholdMember
from schemas import HouseholdSchema
from marshmallow import ValidationError

household_schema = HouseholdSchema()
households_schema = HouseholdSchema(many=True)

def generate_join_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class HouseholdCollection(Resource):
    def get(self):
        households = Household.query.all()
        return households_schema.dump(households), 200

    def post(self):
        user_id = Household.query.all()
        if not user_id:
            return {"message": "Unauthorized"}, 401
        try:
            household = household_schema.load(request.json)

            household.created_by = user_id
            household.join_code = generate_join_code()

            db.session.add(household)
            db.session.flush()

            member= HouseholdMember(household_id=household.id,user_id=user_id,role="owner")
            db.session.add(member)
            db.session.commit()

            return household_schema.dump(household), 201
        
        except ValidationError as error:
            return error.messages, 400
        
class JoinHousehold(Resource):
    def post(self):
        user_id = session.get("user_id")
        code = request.json.get("join_code")

        household = Household.query.filter_by(join_code=code).first_or_404()

        exists = HouseholdMember.query.filter_by(household_id=household.id, user_id=user_id).first()

        if exists:
            return {"message": "Already a member of this household"}, 400
        
        new_member= HouseholdMember(household_id=household.id, user_id=user_id)
        db.session.add(new_member)
        db.session.commit()

        return {"message": f"Joined {household.name}"}, 201


