from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin

# Define naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata)

class Restaurant(db.Model, SerializerMixin):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)

    # Relationships
    restaurant_pizzas = db.relationship(
        "RestaurantPizza", 
        backref="restaurant", 
        cascade="all, delete-orphan"
    )
    
    # Association proxy
    pizzas = association_proxy("restaurant_pizzas", "pizza")

    # Serialization rules
    serialize_rules = ("-restaurant_pizzas.restaurant",)

    def to_dict(self, include_pizzas=False):
        data = {
            "id": self.id,
            "name": self.name,
            "address": self.address,
        }
        if include_pizzas:
            data["restaurant_pizzas"] = [rp.to_dict(include_pizza=True) for rp in self.restaurant_pizzas]
        return data

    def __repr__(self):
        return f"<Restaurant {self.name}>"


class Pizza(db.Model, SerializerMixin):
    __tablename__ = "pizzas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    ingredients = db.Column(db.String(200), nullable=False)

    # Relationships
    restaurant_pizzas = db.relationship(
        "RestaurantPizza", 
        backref="pizza", 
        cascade="all, delete-orphan"
    )
    
    # Association proxy
    restaurants = association_proxy("restaurant_pizzas", "restaurant")

    # Serialization rules
    serialize_rules = ("-restaurant_pizzas.pizza",)

    def __repr__(self):
        return f"<Pizza {self.name}, {self.ingredients}>"


class RestaurantPizza(db.Model, SerializerMixin):
    __tablename__ = "restaurant_pizzas"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False)
    pizza_id = db.Column(db.Integer, db.ForeignKey("pizzas.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"))

    # Serialization rules
    serialize_rules = ("-restaurant.restaurant_pizzas", "-pizza.restaurant_pizzas")

    # Validation
    @validates("price")
    def validate_price(self, key, price):
        if not 1 <= price <= 30:
            raise ValueError("Price must be between 1 and 30")
        return price

    def to_dict(self, include_pizza=False, include_restaurant=False):
        data = {
            "id": self.id,
            "price": self.price,
            "pizza_id": self.pizza_id,
            "restaurant_id": self.restaurant_id,
        }
        if include_pizza:
            data["pizza"] = {
                "id": self.pizza.id,
                "name": self.pizza.name,
                "ingredients": self.pizza.ingredients
            }
        if include_restaurant:
            data["restaurant"] = {
                "id": self.restaurant.id,
                "name": self.restaurant.name,
                "address": self.restaurant.address
            }
        return data

    def __repr__(self):
        return f"<RestaurantPizza ${self.price}>"