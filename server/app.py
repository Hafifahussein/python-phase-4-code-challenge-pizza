#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask_restful import Api, Resource
import os
from flask import Flask, request, make_response, jsonify


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    return make_response(
        [restaurant.to_dict() for restaurant in restaurants],
        200,
    )


@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant:
        return make_response(restaurant.to_dict(include_pizzas=True), 200)
    return make_response({"error": "Restaurant not found"}, 404)


@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant:
        # Since we have cascade delete set up, the associated RestaurantPizzas will be deleted automatically
        db.session.delete(restaurant)
        db.session.commit()
        return make_response("", 204)
    return make_response({"error": "Restaurant not found"}, 404)


@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    return make_response(
        [{
            "id": pizza.id,
            "name": pizza.name,
            "ingredients": pizza.ingredients
        } for pizza in pizzas],
        200,
    )


@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()
    
    # Check if all required fields are present
    if not all(key in data for key in ["price", "pizza_id", "restaurant_id"]):
        return make_response(jsonify({"errors": ["validation errors"]}), 400)
    
    try:
        # Create the RestaurantPizza - this will trigger validation
        restaurant_pizza = RestaurantPizza(
            price=data["price"],
            pizza_id=data["pizza_id"],
            restaurant_id=data["restaurant_id"],
        )
        
        db.session.add(restaurant_pizza)
        db.session.commit()
        
        # Get the associated pizza and restaurant
        pizza = Pizza.query.get(restaurant_pizza.pizza_id)
        restaurant = Restaurant.query.get(restaurant_pizza.restaurant_id)
        
        # Build the response in the exact format expected
        response_data = {
            "id": restaurant_pizza.id,
            "price": restaurant_pizza.price,
            "pizza_id": restaurant_pizza.pizza_id,
            "restaurant_id": restaurant_pizza.restaurant_id,
            "pizza": {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients
            },
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
            }
        }
        
        return make_response(jsonify(response_data), 201)
    
    except ValueError as e:
        db.session.rollback()
        # Return the generic error message that the test expects
        return make_response(jsonify({"errors": ["validation errors"]}), 400)
    
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({"errors": ["validation errors"]}), 400)


if __name__ == "__main__":
    app.run(port=5555, debug=True)