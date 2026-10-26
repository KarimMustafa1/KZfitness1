from database import db
from models import Food

STARTER_FOODS = [
    {"name": "Chicken breast (cooked)",     "calories_per_100g": 165, "protein_per_100g": 31.0, "carbs_per_100g": 0.0,  "fat_per_100g": 3.6},
    {"name": "Eggs (whole)",                "calories_per_100g": 143, "protein_per_100g": 12.6, "carbs_per_100g": 0.7,  "fat_per_100g": 9.5},
    {"name": "Rice, white (cooked)",        "calories_per_100g": 130, "protein_per_100g": 2.7,  "carbs_per_100g": 28.2, "fat_per_100g": 0.3},
    {"name": "Oats (dry)",                  "calories_per_100g": 389, "protein_per_100g": 16.9, "carbs_per_100g": 66.3, "fat_per_100g": 6.9},
    {"name": "Greek yogurt (plain, 0% fat)", "calories_per_100g": 59,  "protein_per_100g": 10.2, "carbs_per_100g": 3.6,  "fat_per_100g": 0.4},
    {"name": "Banana",                      "calories_per_100g": 89,  "protein_per_100g": 1.1,  "carbs_per_100g": 22.8, "fat_per_100g": 0.3},
    {"name": "Apple",                       "calories_per_100g": 52,  "protein_per_100g": 0.3,  "carbs_per_100g": 13.8, "fat_per_100g": 0.2},
    {"name": "Potatoes (boiled)",           "calories_per_100g": 87,  "protein_per_100g": 1.9,  "carbs_per_100g": 20.1, "fat_per_100g": 0.1},
    {"name": "Beef mince, 90% lean (cooked)", "calories_per_100g": 217, "protein_per_100g": 26.1, "carbs_per_100g": 0.0, "fat_per_100g": 11.7},
    {"name": "Tuna (canned in water)",      "calories_per_100g": 116, "protein_per_100g": 25.5, "carbs_per_100g": 0.0,  "fat_per_100g": 0.8},
    {"name": "Bread (wholemeal)",           "calories_per_100g": 247, "protein_per_100g": 13.0, "carbs_per_100g": 41.3, "fat_per_100g": 3.4},
    {"name": "Milk (whole)",                "calories_per_100g": 61,  "protein_per_100g": 3.2,  "carbs_per_100g": 4.8,  "fat_per_100g": 3.3},
    {"name": "Salmon (cooked)",             "calories_per_100g": 206, "protein_per_100g": 22.1, "carbs_per_100g": 0.0,  "fat_per_100g": 12.4},
]


def seed_starter_foods():
    food_count = db.session.execute(db.select(db.func.count(Food.id))).scalar()
    if food_count > 0:
        return

    for item in STARTER_FOODS:
        db.session.add(Food(**item))
    db.session.commit()
    
    #MORE FOODS WILL BE ADDED, THESE ARE JUST THE ONES I EAT MOST