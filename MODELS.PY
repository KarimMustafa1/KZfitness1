from datetime import date, datetime
from database import db
from calculations import scale_nutrients, estimate_one_rep_max

SEX_CHOICES = {"male": "Male", "female": "Female"}

ACTIVITY_CHOICES = {
    "sedentary": "Sedentary (little or no exercise)",
    "light": "Lightly active (1–3 days/week)",
    "moderate": "Moderately active (3–5 days/week)",
    "active": "Very active (6–7 days/week)",
    "very_active": "Extremely active (hard daily training or physical job)",
}

GOAL_CHOICES = {
    "lose_fat": "Lose fat",
    "maintain": "Maintain weight",
    "gain_muscle": "Gain muscle",
}


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    activity_level = db.Column(db.String(20), nullable=False)
    goal = db.Column(db.String(20), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def goal_label(self):
        return GOAL_CHOICES.get(self.goal, self.goal)

    @property
    def activity_label(self):
        return ACTIVITY_CHOICES.get(self.activity_level, self.activity_level)

    def __repr__(self):
        return f"<Profile {self.name}, {self.age}y, {self.weight_kg}kg>"


class Food(db.Model):
    __tablename__ = "foods"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    calories_per_100g = db.Column(db.Float, nullable=False)
    protein_per_100g = db.Column(db.Float, nullable=False)
    carbs_per_100g = db.Column(db.Float, nullable=False)
    fat_per_100g = db.Column(db.Float, nullable=False)
    is_custom = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def per_100g(self):
        return {
            "calories": self.calories_per_100g,
            "protein": self.protein_per_100g,
            "carbs": self.carbs_per_100g,
            "fat": self.fat_per_100g,
        }

    def __repr__(self):
        return f"<Food {self.name}: {self.calories_per_100g} kcal/100 g>"


class FoodLog(db.Model):
    __tablename__ = "food_log"

    id = db.Column(db.Integer, primary_key=True)

    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=False)

    grams = db.Column(db.Float, nullable=False)
    logged_on = db.Column(db.Date, nullable=False, default=date.today, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    food = db.relationship("Food")

    @property
    def nutrients(self):
        return scale_nutrients(self.food.per_100g, self.grams)

    def __repr__(self):
        return f"<FoodLog {self.grams} g of food #{self.food_id} on {self.logged_on}>"


class Exercise(db.Model):
    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False, unique=True)
    is_custom = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Exercise {self.name}>"


class Workout(db.Model):
    __tablename__ = "workouts"

    id = db.Column(db.Integer, primary_key=True)

    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.id"), nullable=False, index=True)

    weight_kg = db.Column(db.Float, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    performed_on = db.Column(db.Date, nullable=False, default=date.today, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    exercise = db.relationship("Exercise")

    @property
    def estimated_1rm(self):
        return estimate_one_rep_max(self.weight_kg, self.reps)

    def __repr__(self):
        return f"<Workout {self.weight_kg} kg × {self.reps} × {self.sets} on {self.performed_on}>"


class WeightLog(db.Model):
    __tablename__ = "weight_log"

    id = db.Column(db.Integer, primary_key=True)
    weight_kg = db.Column(db.Float, nullable=False)
    logged_on = db.Column(db.Date, nullable=False, unique=True, default=date.today)

    def __repr__(self):
        return f"<WeightLog {self.weight_kg} kg on {self.logged_on}>"