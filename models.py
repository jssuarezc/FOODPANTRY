from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

item_categories = db.Table('item_categories',
    db.Column('item_id', db.Integer, db.ForeignKey('pantry_item.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    households = db.relationship("Household", secondary='members', back_populates="user", cascade="all, delete-orphan")

class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    join_code = db.Column(db.String(8), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    items = db.relationship('PantryItem', backref='household', lazy=True, cascade="all, delete-orphan")
    members = db.relationship("HouseholdMember", back_populates="household", cascade="all, delete-orphan")

class PantryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
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
    categories = db.relationship('Category', secondary=item_categories, backref='items')

class Category(db.Model):
#    __table_args__= (db.UniqueConstraint("name", "household_id"),)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
#    household = db.relationship("Household")


class Member(db.Model):
    __tablename__ = 'members'
#    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"),nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(10),nullable=False, default="member")
#    household = db.relationship("Household", back_populates="members")
#    user = db.relationship("User", back_populates="households")
