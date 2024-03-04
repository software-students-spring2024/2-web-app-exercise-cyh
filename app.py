from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import base64

load_dotenv()

app = Flask(__name__)

app.config['ALLOWED_IMAGE_EXTENSIONS'] = ['PNG', 'JPG', 'JPEG', 'GIF']


mongo_uri = os.getenv("MONGO_URI")
mongo_dbname = os.getenv("MONGO_DBNAME")
client = MongoClient(mongo_uri)
db = client[mongo_dbname]


@app.template_filter('b64encode')
def b64encode_filter(data):
    return base64.b64encode(data).decode() if data else ''

def allowed_image(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config['ALLOWED_IMAGE_EXTENSIONS']:
        return True
    else:
        return False

from PIL import Image
import io

def save_image_to_mongodb(photo):
    
    img_io = io.BytesIO()
    img = Image.open(photo)
    img.save(img_io, format='PNG')  
    img_io.seek(0)
    return img_io.getvalue()  

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

        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '' and allowed_image(photo.filename):
                # Instead of saving the file to the filesystem, save it in MongoDB as binary data
                recipe['photo'] = save_image_to_mongodb(photo)

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

        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '' and allowed_image(photo.filename):
                updated_recipe['photo'] = save_image_to_mongodb(photo)

        db.recipes.update_one({"_id": ObjectId(recipe_id)}, {"$set": updated_recipe})
        return redirect(url_for("recipe_detail", recipe_id=recipe_id))
    return render_template("edit_recipe.html", recipe=recipe)

@app.route("/delete/<recipe_id>", methods=["POST"])
def delete_recipe(recipe_id):
    db.recipes.delete_one({"_id": ObjectId(recipe_id)})
    return redirect(url_for("home"))

@app.route('/delete_confirmation/<recipe_id>')
def delete_confirmation(recipe_id):
    recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if recipe:
        return render_template('delete_confirmation.html', recipe=recipe)
    else:
        return 'Recipe not found', 404



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
