import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "fitness.db")


def init_db(app):
    database_path = os.environ.get("FITNESS_DB_PATH", DATABASE_PATH)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    import models
    from food_data import seed_starter_foods
    from exercise_data import seed_common_exercises

    with app.app_context():
        db.create_all()

        seed_starter_foods()
        seed_common_exercises()
        
        ##USED SQL ALCHEMY AS TRANSLATOR TO THE PYTHON CODE
