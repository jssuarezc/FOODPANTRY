from flask import request
from flask_restful import Resource
from models import db, User
from schemas import UserSchema
from werkzeug.security import generate_password_hash
from marshmallow import ValidationError

user_schema = UserSchema()
users_schema = UserSchema(many=True)

class UserCollection(Resource):
    def get(self):

        users = User.query.all()
        return users_schema.dump(users), 200

    def post(self):
        try:
            user_data = user_schema.load(request.json)

            db.session.add(user_data)
            db.session.commit()

            return user_schema.dump(user_data), 201

        except ValidationError as error:
            return error.messages, 400
        
class UserItem(Resource):
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        return user_schema.dump(user), 200
