from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI")
mongo_dbname = os.getenv("MONGO_DBNAME")
client = MongoClient(mongo_uri)
db = client[mongo_dbname]

@app.route("/")
def home():
    recipes = db.recipes.find()
    return render_template("index.html", recipes=recipes)

@app.route("/recipe/<recipe_id>")
def recipe_detail(recipe_id):
    recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    return render_template("recipe_detail.html", recipe=recipe)

@app.route("/add", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        recipe = {
            "name": request.form.get("name"),
            "ingredients": request.form.get("ingredients"),
            "steps": request.form.get("steps")
        }
        db.recipes.insert_one(recipe)
        return redirect(url_for("home"))
    return render_template("add_recipe.html")

@app.route("/edit/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if request.method == "POST":
        updated_recipe = {
            "name": request.form.get("name"),
            "ingredients": request.form.get("ingredients"),
            "steps": request.form.get("steps")
        }
        db.recipes.update_one({"_id": ObjectId(recipe_id)}, {"$set": updated_recipe})
        return redirect(url_for("recipe_detail", recipe_id=recipe_id))
    return render_template("edit_recipe.html", recipe=recipe)

@app.route("/delete/<recipe_id>", methods=["POST"])
def delete_recipe(recipe_id):
    db.recipes.delete_one({"_id": ObjectId(recipe_id)})
    return redirect(url_for("home"))

@app.route("/search", methods=["GET", "POST"])
def search_recipes():
    query = request.args.get("query", "")
    recipes = db.recipes.find({"name": {"$regex": query, "$options": "i"}})
    return render_template("search_results.html", recipes=recipes, query=query)

@app.route("/profile")
def profile():
    # Placeholder for actual user profile data
    return render_template("profile.html")

if __name__ == "__main__":
    app.run(debug=True, port=os.getenv("FLASK_PORT", 5000))
