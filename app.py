from datetime import date, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, abort

import ai
from database import db, init_db
from models import (
    Profile, Food, FoodLog, Exercise, Workout, WeightLog,
    SEX_CHOICES, ACTIVITY_CHOICES, GOAL_CHOICES,
)
from calculations import (
    build_summary,
    add_up_totals,
    daily_progress,
    scale_nutrients,
    weight_summary,
    total_by_day,
    strength_by_day,
    best_lift,
    MIN_CHART_POINTS,
    energy_breakdoown
    calculate_bmi,
    bmi_category,
    calculate_body_fat_navy,
    body_fat_category,
    describe_goal_adjustment,
)


app = Flask(__name__)

app.config["SECRET_KEY"] = "dev-key-change-me"

init_db(app)


LIMITS = {
    "age": (13, 100),
    "height_cm": (100, 250),
    "weight_kg": (30, 300),
    "neck_cm": (20, 70),
    "waist_cm": (40, 200),
    "hip_cm": (50, 200),
    "grams": (1, 5000),
    "calories": (0, 900),
    "protein": (0, 100),
    "carbs": (0, 100),
    "fat": (0, 100),
    "weight": (0, 500),
    "reps": (1, 100),
    "sets": (1, 20),
}

GOAL_HINTS = {goal: describe_goal_adjustment(goal) for goal in GOAL_CHOICES}

PLACEHOLDER_PAGES = {}


@app.template_filter("amount")
def format_amount(value, decimals=1):
    text = f"{value:,.{decimals}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def read_number(form, field, label, errors, whole_number=False):
    low, high = LIMITS[field]
    raw = form.get(field, "").strip()
    convert = int if whole_number else float

    if raw == "":
        errors.append(f"{label} is required.")
        return None

    try:
        value = convert(raw)
    except ValueError:
        kind = "a whole number" if whole_number else "a number"
        errors.append(f"{label} must be {kind}.")
        return None

    if not (low <= value <= high):
        errors.append(f"{label} must be between {low} and {high}.")
        return None

    return value


def read_date(form, field, label, errors):
    raw = form.get(field, "").strip()
    try:
        value = date.fromisoformat(raw)
    except ValueError:
        errors.append(f"Please choose a valid {label.lower()}.")
        return None

    if value > date.today():
        errors.append(f"{label} can't be in the future.")
        return None
    if value.year < 2000:
        errors.append(f"{label} must be in the year 2000 or later.")
        return None
    return value


def read_choice(form, field, label, choices, errors):
    value = form.get(field, "")
    if value not in choices:
        errors.append(f"Please choose a valid {label}.")
        return None
    return value


def parse_profile_form(form):
    errors = []
    data = {}

    data["name"] = form.get("name", "").strip()
    if not data["name"]:
        errors.append("Please enter your name.")

    data["age"] = read_number(form, "age", "Age", errors, whole_number=True)
    data["height_cm"] = read_number(form, "height_cm", "Height", errors)
    data["weight_kg"] = read_number(form, "weight_kg", "Weight", errors)
    data["sex"] = read_choice(form, "sex", "sex", SEX_CHOICES, errors)
    data["activity_level"] = read_choice(form, "activity_level", "activity level", ACTIVITY_CHOICES, errors)
    data["goal"] = read_choice(form, "goal", "goal", GOAL_CHOICES, errors)

    return data, errors


def get_profile():
    return db.session.execute(db.select(Profile)).scalars().first()


def search_foods(search_text, limit=20):
    query = db.select(Food).order_by(Food.name).limit(limit)
    if search_text:
        query = query.where(Food.name.ilike(f"%{search_text}%"))
    return db.session.execute(query).scalars().all()


def todays_entries():
    query = (
        db.select(FoodLog)
        .where(FoodLog.logged_on == date.today())
        .order_by(FoodLog.created_at)
    )
    return db.session.execute(query).scalars().all()


def todays_totals(entries):
    return add_up_totals([entry.nutrients for entry in entries])


def daily_targets(summary):
    return {"calories": summary["calorie_target"], **summary["macros"]}


def profile_to_form(profile):
    if profile is None:
        return {}
    return {
        "name": profile.name,
        "age": profile.age,
        "sex": profile.sex,
        "height_cm": "{:g}".format(profile.height_cm),
        "weight_kg": "{:g}".format(profile.weight_kg),
        "activity_level": profile.activity_level,
        "goal": profile.goal,
    }


def render_profile_page(form, status=200):
    return render_template(
        "profile.html",
        form=form,
        sex_choices=SEX_CHOICES,
        activity_choices=ACTIVITY_CHOICES,
        goal_choices=GOAL_CHOICES,
        goal_hints=GOAL_HINTS,
        limits=LIMITS,
    ), status


def run_energy_calculator(form):
    errors = []
    sex = read_choice(form, "sex", "sex", SEX_CHOICES, errors)
    age = read_number(form, "age", "Age", errors, whole_number=True)
    height = read_number(form, "height_cm", "Height", errors)
    weight = read_number(form, "weight_kg", "Weight", errors)
    activity = read_choice(form, "activity_level", "activity level", ACTIVITY_CHOICES, errors)

    if errors:
        return None, errors

    return energy_breakdown(weight, height, age, sex, activity), []


def run_bmi_calculator(form):
    errors = []
    height = read_number(form, "height_cm", "Height", errors)
    weight = read_number(form, "weight_kg", "Weight", errors)

    if errors:
        return None, errors

    bmi = calculate_bmi(weight, height)
    return {"bmi": bmi, "category": bmi_category(bmi)}, []


def run_body_fat_calculator(form):
    errors = []
    sex = read_choice(form, "sex", "sex", SEX_CHOICES, errors)
    height = read_number(form, "height_cm", "Height", errors)
    neck = read_number(form, "neck_cm", "Neck", errors)
    waist = read_number(form, "waist_cm", "Waist", errors)

    hip = None
    if sex == "female":
        hip = read_number(form, "hip_cm", "Hip", errors)

    if errors:
        return None, errors

    try:
        body_fat = calculate_body_fat_navy(sex, height, neck, waist, hip)
    except ValueError as problem:
        return None, [str(problem)]

    return {"body_fat": body_fat, "category": body_fat_category(body_fat, sex)}, []


@app.route("/")
def dashboard():
    profile = get_profile()

    if profile is None:
        return render_template("dashboard.html", profile=None)

    summary = build_summary(profile)
    entries = todays_entries()
    progress = daily_progress(todays_totals(entries), daily_targets(summary))

    weigh_ins = get_weigh_ins()
    weight = weight_summary(weigh_ins)
    recent_weigh_ins = weigh_ins[-14:]
    chart_data = {
        "weight": {
            "labels": [short_date(day) for day, kg in recent_weigh_ins],
            "values": [kg for day, kg in recent_weigh_ins],
            "compact": True,
        }
    }

    recent_workouts = db.session.execute(
        db.select(Workout).order_by(Workout.performed_on.desc(), Workout.created_at.desc()).limit(5)
    ).scalars().all()

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    trained = set(db.session.execute(
        db.select(Workout.performed_on).where(Workout.performed_on >= week_start)
    ).scalars())
    logged = set(db.session.execute(
        db.select(FoodLog.logged_on).where(FoodLog.logged_on >= week_start)
    ).scalars())
    week = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        week.append({
            "letter": day.strftime("%a")[0],
            "name": day.strftime("%A"),
            "trained": day in trained,
            "logged": day in logged,
            "is_today": day == today,
            "is_future": day > today,
        })

    return render_template(
        "dashboard.html",
        profile=profile,
        summary=summary,
        progress=progress,
        entry_count=len(entries),
        weight=weight,
        weigh_in_count=len(weigh_ins),
        chart_data=chart_data,
        recent_workouts=recent_workouts,
        week=week,
        training_days=len(trained),
        food_days=len(logged),
        days_so_far=today.weekday() + 1,
        coach_connected=ai.is_connected(),
    )


@app.route("/profile", methods=["GET", "POST"])
def profile():
    existing = get_profile()

    if request.method == "POST":
        data, errors = parse_profile_form(request.form)

        if errors:
            for message in errors:
                flash(message, "error")
            return render_profile_page(request.form, 400)

        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
        else:
            db.session.add(Profile(**data))

        db.session.commit()
        flash("Profile saved.", "success")

        return redirect(url_for("dashboard"))

    return render_profile_page(profile_to_form(existing))


def render_food_page(custom_form=None, status=200):
    search_text = request.args.get("q", "").strip()

    selected = None
    food_id = request.args.get("food_id", type=int)
    if food_id is not None:
        selected = db.session.get(Food, food_id)

    entries = todays_entries()
    totals = todays_totals(entries)

    profile = get_profile()
    progress = None
    if profile:
        progress = daily_progress(totals, daily_targets(build_summary(profile)))

    return render_template(
        "food.html",
        search_text=search_text,
        results=search_foods(search_text),
        selected=selected,
        selected_preview=scale_nutrients(selected.per_100g, 100) if selected else None,
        entries=entries,
        totals=totals,
        progress=progress,
        custom_form=custom_form or {},
        limits=LIMITS,
    ), status


@app.route("/food")
def food():
    return render_food_page()


@app.route("/food/log", methods=["POST"])
def add_food_to_log():
    errors = []
    food_id = request.form.get("food_id", type=int)
    selected = db.session.get(Food, food_id) if food_id else None
    grams = read_number(request.form, "grams", "Amount", errors)

    if selected is None:
        flash("Please choose a food first.", "error")
        return redirect(url_for("food"))

    if errors:
        for message in errors:
            flash(message, "error")
        return redirect(url_for("food", food_id=selected.id))

    db.session.add(FoodLog(food_id=selected.id, grams=grams))
    db.session.commit()

    calories = scale_nutrients(selected.per_100g, grams)["calories"]
    flash(f"Added {format_amount(grams)} g {selected.name} ({format_amount(calories, 0)} kcal).", "success")
    return redirect(url_for("food"))


@app.route("/food/log/<int:entry_id>/delete", methods=["POST"])
def delete_food_entry(entry_id):
    entry = db.session.get(FoodLog, entry_id)
    if entry is None:
        abort(404)
    food_name = entry.food.name
    db.session.delete(entry)
    db.session.commit()
    flash(f"Removed {food_name}.", "success")
    return redirect(url_for("food"))


@app.route("/food/custom", methods=["POST"])
def add_custom_food():
    form = request.form
    errors = []

    name = form.get("name", "").strip()
    if not name:
        errors.append("Please enter a food name.")
    elif len(name) > 100:
        errors.append("Food name must be 100 characters or fewer.")
    else:
        same_name = db.session.execute(
            db.select(Food).where(db.func.lower(Food.name) == name.lower())
        ).scalar()
        if same_name:
            errors.append(f'"{same_name.name}" is already in the food database.')

    calories = read_number(form, "calories", "Calories", errors)
    protein = read_number(form, "protein", "Protein", errors)
    carbs = read_number(form, "carbs", "Carbohydrates", errors)
    fat = read_number(form, "fat", "Fat", errors)

    if None not in (protein, carbs, fat) and protein + carbs + fat > 100:
        errors.append("Protein + carbs + fat can't add up to more than 100 g per 100 g.")

    if errors:
        for message in errors:
            flash(message, "error")
        return render_food_page(custom_form=form, status=400)

    new_food = Food(
        name=name,
        calories_per_100g=calories,
        protein_per_100g=protein,
        carbs_per_100g=carbs,
        fat_per_100g=fat,
        is_custom=True,
    )
    db.session.add(new_food)
    db.session.commit()

    flash(f"Added {name} to the food database.", "success")
    return redirect(url_for("food", food_id=new_food.id))


def get_workouts(exercise_id=None):
    query = db.select(Workout).order_by(Workout.performed_on.desc(), Workout.created_at.desc())
    if exercise_id is not None:
        query = query.where(Workout.exercise_id == exercise_id)
    return db.session.execute(query).scalars().all()


def find_or_create_exercise(name):
    existing = db.session.execute(
        db.select(Exercise).where(db.func.lower(Exercise.name) == name.lower())
    ).scalar()
    if existing:
        return existing

    new_exercise = Exercise(name=name, is_custom=True)
    db.session.add(new_exercise)
    return new_exercise


def render_workout_page(form=None, status=200):
    exercise_id = request.args.get("exercise", type=int)
    selected_exercise = db.session.get(Exercise, exercise_id) if exercise_id else None
    if selected_exercise is None:
        exercise_id = None

    workouts = get_workouts(exercise_id)

    best = None
    if selected_exercise and workouts:
        best = max(workouts, key=lambda workout: workout.estimated_1rm)

    if form is None:
        form = {"performed_on": date.today().isoformat()}
        if selected_exercise:
            form["exercise"] = selected_exercise.name

    return render_template(
        "workout.html",
        exercises=db.session.execute(db.select(Exercise).order_by(Exercise.name)).scalars().all(),
        workouts=workouts,
        selected_exercise=selected_exercise,
        best=best,
        last=workouts[0] if selected_exercise and workouts else None,
        form=form,
        today=date.today().isoformat(),
        today_date=date.today(),
        limits=LIMITS,
    ), status


@app.route("/workout")
def workout():
    return render_workout_page()


@app.route("/workout/add", methods=["POST"])
def add_workout():
    form = request.form
    errors = []

    name = " ".join(form.get("exercise", "").split())
    if not name:
        errors.append("Please enter an exercise.")
    elif len(name) > 60:
        errors.append("Exercise name must be 60 characters or fewer.")

    weight = read_number(form, "weight", "Weight", errors)
    reps = read_number(form, "reps", "Reps", errors, whole_number=True)
    sets = read_number(form, "sets", "Sets", errors, whole_number=True)
    performed_on = read_date(form, "performed_on", "Date", errors)

    if errors:
        for message in errors:
            flash(message, "error")
        return render_workout_page(form=form, status=400)

    exercise = find_or_create_exercise(name)
    new_workout = Workout(exercise=exercise, weight_kg=weight, reps=reps, sets=sets, performed_on=performed_on)
    db.session.add(new_workout)
    db.session.commit()

    flash(
        f"Saved {exercise.name}: {format_amount(weight)} kg × {reps} reps × {sets} sets "
        f"(estimated 1RM ≈ {format_amount(new_workout.estimated_1rm)} kg).",
        "success",
    )
    return redirect(url_for("workout", exercise=exercise.id))


@app.route("/workout/<int:workout_id>/delete", methods=["POST"])
def delete_workout(workout_id):
    workout_row = db.session.get(Workout, workout_id)
    if workout_row is None:
        abort(404)

    description = f"{workout_row.exercise.name} on {workout_row.performed_on.strftime('%d %b')}"
    db.session.delete(workout_row)
    db.session.commit()
    flash(f"Deleted {description}.", "success")

    return redirect(url_for("workout", exercise=request.form.get("exercise_filter", type=int)))


CALORIE_CHART_DAYS = 30


def short_date(day):
    return "Today" if day == date.today() else day.strftime("%d %b").lstrip("0")


def get_weigh_ins():
    query = db.select(WeightLog.logged_on, WeightLog.weight_kg).order_by(WeightLog.logged_on)
    return db.session.execute(query).all()


def get_daily_calories():
    first_day = date.today() - timedelta(days=CALORIE_CHART_DAYS - 1)
    entries = db.session.execute(
        db.select(FoodLog).where(FoodLog.logged_on >= first_day)
    ).scalars().all()

    return total_by_day([(entry.logged_on, entry.nutrients["calories"]) for entry in entries])


def get_lifts(exercise_id):
    query = db.select(Workout.performed_on, Workout.weight_kg, Workout.reps).where(
        Workout.exercise_id == exercise_id
    )
    return db.session.execute(query).all()


def render_progress_page(form=None, status=200):
    profile = get_profile()

    weigh_ins = get_weigh_ins()
    weight = weight_summary(weigh_ins)
    recent_weigh_ins = db.session.execute(
        db.select(WeightLog).order_by(WeightLog.logged_on.desc()).limit(5)
    ).scalars().all()

    daily_calories = get_daily_calories()
    calorie_target = build_summary(profile)["calorie_target"] if profile else None

    exercises_with_workouts = db.session.execute(
        db.select(Exercise).join(Workout).distinct().order_by(Exercise.name)
    ).scalars().all()

    chosen_id = request.args.get("exercise", type=int)
    exercise = None
    for option in exercises_with_workouts:
        if option.id == chosen_id:
            exercise = option
    if exercise is None and exercises_with_workouts:
        exercise = exercises_with_workouts[0]

    lifts = get_lifts(exercise.id) if exercise else []
    strength = strength_by_day(lifts)
    best = best_lift(lifts)

    chart_data = {
        "weight": {
            "labels": [short_date(day) for day, kg in weigh_ins],
            "values": [kg for day, kg in weigh_ins],
        },
        "calories": {
            "labels": [short_date(day) for day, kcal in daily_calories],
            "values": [round(kcal) for day, kcal in daily_calories],
            "target": calorie_target,
        },
        "strength": {
            "exercise": exercise.name if exercise else None,
            "labels": [short_date(day) for day, heaviest, e1rm in strength],
            "heaviest": [heaviest for day, heaviest, e1rm in strength],
            "estimated_1rm": [round(e1rm, 1) for day, heaviest, e1rm in strength],
        },
    }

    if form is None:
        if weight:
            latest_kg = weight["current"]
        elif profile:
            latest_kg = profile.weight_kg
        else:
            latest_kg = None
        form = {
            "weight_kg": "{:g}".format(latest_kg) if latest_kg else "",
            "logged_on": date.today().isoformat(),
        }

    return render_template(
        "progress.html",
        weight=weight,
        weigh_in_count=len(weigh_ins),
        recent_weigh_ins=recent_weigh_ins,
        calorie_days=len(daily_calories),
        exercises=exercises_with_workouts,
        exercise=exercise,
        best=best,
        chart_data=chart_data,
        min_points=MIN_CHART_POINTS,
        calorie_chart_days=CALORIE_CHART_DAYS,
        form=form,
        today=date.today().isoformat(),
        limits=LIMITS,
    ), status


@app.route("/progress")
def progress():
    return render_progress_page()


@app.route("/progress/weight", methods=["POST"])
def log_weight():
    errors = []
    weight = read_number(request.form, "weight_kg", "Weight", errors)
    day = read_date(request.form, "logged_on", "Date", errors)

    if errors:
        for message in errors:
            flash(message, "error")
        return render_progress_page(form=request.form, status=400)

    latest_day = db.session.execute(db.select(db.func.max(WeightLog.logged_on))).scalar()
    is_newest = latest_day is None or day >= latest_day

    when = "today" if day == date.today() else day.strftime("%d %b")
    existing = db.session.execute(db.select(WeightLog).where(WeightLog.logged_on == day)).scalar()
    if existing:
        existing.weight_kg = weight
        message = f"Updated the weigh-in for {when} to {format_amount(weight)} kg."
    else:
        db.session.add(WeightLog(weight_kg=weight, logged_on=day))
        message = f"Saved {format_amount(weight)} kg for {when}."

    profile = get_profile()
    if profile and is_newest:
        profile.weight_kg = weight
        message += " Your profile weight was updated too."

    db.session.commit()
    flash(message, "success")
    return redirect(url_for("progress"))


@app.route("/progress/weight/<int:entry_id>/delete", methods=["POST"])
def delete_weigh_in(entry_id):
    entry = db.session.get(WeightLog, entry_id)
    if entry is None:
        abort(404)
    description = f"{format_amount(entry.weight_kg)} kg on {short_date(entry.logged_on)}"
    db.session.delete(entry)
    db.session.commit()
    flash(f"Deleted {description}.", "success")
    return redirect(url_for("progress"))


COACH_SUGGESTIONS = [
    "What should I eat for dinner if I have 700 calories left?",
    "I need 50 g of protein but only have 400 calories left.",
    "Give me a high-protein breakfast.",
    "How can I improve my bench press?",
    "How much protein should I eat?",
]


def describe_remaining(progress_row, unit):
    if progress_row["over"]:
        return f"0 {unit} ({format_amount(-progress_row['remaining'], 0)} {unit} over target)"
    return f"{format_amount(progress_row['remaining'], 0)} {unit}"


def build_coach_info(profile):
    info = {"Today's date": date.today().strftime("%A %d %B %Y")}

    entries = todays_entries()
    totals = todays_totals(entries)

    if profile:
        summary = build_summary(profile)
        targets = daily_targets(summary)
        progress = daily_progress(totals, targets)

        info["Age"] = f"{profile.age} years"
        info["Sex"] = profile.sex
        info["Height"] = f"{format_amount(profile.height_cm)} cm"
        info["Weight"] = f"{format_amount(profile.weight_kg)} kg"
        info["Activity level"] = profile.activity_label
        info["Goal"] = profile.goal_label
        info["Daily calorie target"] = f"{format_amount(targets['calories'], 0)} kcal"
        info["Daily macro targets"] = (
            f"protein {format_amount(targets['protein'], 0)} g, "
            f"carbs {format_amount(targets['carbs'], 0)} g, "
            f"fat {format_amount(targets['fat'], 0)} g"
        )
    else:
        info["Profile"] = "not set up yet (no age, weight or targets available)"

    info["Eaten today"] = (
        f"{format_amount(totals['calories'], 0)} kcal, "
        f"protein {format_amount(totals['protein'], 0)} g, "
        f"carbs {format_amount(totals['carbs'], 0)} g, "
        f"fat {format_amount(totals['fat'], 0)} g"
    )
    if profile:
        info["Remaining today"] = (
            f"{describe_remaining(progress['calories'], 'kcal')}, "
            f"protein {describe_remaining(progress['protein'], 'g')}"
        )
    if entries:
        info["Foods logged today"] = "; ".join(
            f"{entry.food.name} {format_amount(entry.grams)} g" for entry in entries[:12]
        )

    recent = db.session.execute(
        db.select(Workout)
        .where(Workout.performed_on >= date.today() - timedelta(days=14))
        .order_by(Workout.performed_on.desc())
        .limit(8)
    ).scalars().all()
    if recent:
        info["Workouts in the last 14 days"] = "; ".join(
            f"{w.exercise.name} {format_amount(w.weight_kg)} kg × {w.reps} reps × {w.sets} sets "
            f"({w.performed_on.strftime('%d %b')})"
            for w in recent
        )

    weight = weight_summary(get_weigh_ins())
    if weight and weight["start_date"] != weight["current_date"]:
        info["Weight trend"] = (
            f"{format_amount(weight['start'])} kg on {weight['start_date'].strftime('%d %b')} → "
            f"{format_amount(weight['current'])} kg on {weight['current_date'].strftime('%d %b')}"
        )

    return info


def build_today_summary(profile):
    if profile is None:
        return None
    return daily_progress(todays_totals(todays_entries()), daily_targets(build_summary(profile)))


@app.route("/coach", methods=["GET", "POST"])
def coach():
    profile = get_profile()
    info = build_coach_info(profile)

    question = ""
    answer = None
    error = None
    status = 200

    prefill = request.args.get("q", "")[:ai.MAX_QUESTION_LENGTH]

    if request.method == "POST":
        question = (request.form.get("suggestion") or request.form.get("question", "")).strip()

        if not question:
            error, status = "Please type a question.", 400
        elif len(question) > ai.MAX_QUESTION_LENGTH:
            error, status = f"Please keep your question under {ai.MAX_QUESTION_LENGTH} characters.", 400
        else:
            answer, error = ai.get_ai_response(question, info)

    return render_template(
        "coach.html",
        connected=ai.is_connected(),
        info=info,
        question=question,
        answer=answer,
        error=error,
        prefill=prefill,
        today=build_today_summary(profile),
        suggestions=COACH_SUGGESTIONS,
        max_length=ai.MAX_QUESTION_LENGTH,
        model=ai.MODEL,
    ), status


@app.route("/calculators")
def calculators():
    profile = get_profile()

    chosen = request.args.get("calculator")
    result = None
    errors = []

    if chosen == "energy":
        result, errors = run_energy_calculator(request.args)
    elif chosen == "bmi":
        result, errors = run_bmi_calculator(request.args)
    elif chosen == "body_fat":
        result, errors = run_body_fat_calculator(request.args)

    return render_template(
        "calculators.html",
        chosen=chosen,
        result=result,
        errors=errors,
        submitted=request.args,
        defaults=profile_to_form(profile),
        profile=profile,
        sex_choices=SEX_CHOICES,
        activity_choices=ACTIVITY_CHOICES,
        goal_choices=GOAL_CHOICES,
        goal_hints=GOAL_HINTS,
        limits=LIMITS,
    )


@app.route("/<page_name>")
def placeholder(page_name):
    page = PLACEHOLDER_PAGES.get(page_name)
    if page is None:
        abort(404)
    return render_template("placeholder.html", page=page)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
    
   
