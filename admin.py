from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
import uvicorn
import json
import os
from collections import defaultdict

app = FastAPI()

JSON_FILE = "updated_data.json"

# Setup Jinja2 environment
env = Environment(loader=FileSystemLoader("."))  # Load templates from current directory


# Function to load JSON data
def load_json():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as file:
            return json.load(file)
    return []


# Function to save JSON data
def save_json(data):
    with open(JSON_FILE, "w") as file:
        json.dump(data, file, indent=4)


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    """Render the admin panel displaying ingredients."""
    dish_data = load_json()

    # Create a dictionary of unique ingredients and their associated dishes
    ingredient_dish_map = defaultdict(lambda: {"dishes": [], "shelf_life": "Not Set", "expiry_date": "Not Set"})

    for dish in dish_data:
        for ingredient in dish["ingredients"]:
            ingredient_dish_map[ingredient]["dishes"].append(dish["dish"])
            # Preserve existing shelf life & expiry if present
            if "shelf_life" in dish:
                ingredient_dish_map[ingredient]["shelf_life"] = dish["shelf_life"]
            if "expiry_date" in dish:
                ingredient_dish_map[ingredient]["expiry_date"] = dish["expiry_date"]

    # Render HTML using Jinja2
    template = env.get_template("templates/admin.html")
    return HTMLResponse(template.render(ingredient_dish_map=ingredient_dish_map))


@app.post("/add-ingredient")
async def add_ingredient(
        ingredient: str = Form(...),
        shelf_life: int = Form(...),
        expiry_date: str = Form(None),
):
    """Update shelf life & expiry date inside `updated_data.json`."""
    data = load_json()

    for dish in data:
        if ingredient in dish["ingredients"]:
            dish["shelf_life"] = shelf_life
            dish["expiry_date"] = expiry_date or "Not Set"

    save_json(data)

    return {"message": f"Shelf life for {ingredient} updated!"}


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8001)
