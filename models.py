from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

pantry_item_category = db.Table(
    "pantry_item_category",
    db.Column("item_id", db.Integer, db.ForeignKey("pantry_item.id"), primary_key=True),
    db.Column("category_id", db.Integer, db.ForeignKey("category.id"), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    items = db.relationship("PantryItem", back_populates="item_added", foreign_keys="PantryItem.added_by", cascade="all,delete-orphan")
    households = db.relationship("HouseholdMember", back_populates="user", cascade="all, delete-orphan")

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
    categories = db.relationship('Category', secondary=pantry_item_category)
