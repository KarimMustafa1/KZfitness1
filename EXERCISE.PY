from database import db
from models import Exercise

COMMON_EXERCISES = [
    "Bench Press",
    "Squat",
    "Deadlift",
    "Lat Pulldown",
    "Shoulder Press",
    "T-bar Row",
    "Preacher Curl",
    "Tricep Pushdown",
]


def seed_common_exercises():
    exercise_count = db.session.execute(db.select(db.func.count(Exercise.id))).scalar()
    if exercise_count > 0:
        return

    for name in COMMON_EXERCISES:
        db.session.add(Exercise(name=name))
    db.session.commit()