import math


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_CALORIE_ADJUSTMENTS = {
    "lose_fat": (-500, -300),
    "maintain": (0, 0),
    "gain_muscle": (200, 300),
}

MIN_CALORIES = 1200

PROTEIN_PER_KG = {
    "lose_fat": 2.0,
    "maintain": 1.6,
    "gain_muscle": 2.0,
}
FAT_PERCENT = 0.25
KCAL_PER_G_PROTEIN = 4
KCAL_PER_G_CARBS = 4
KCAL_PER_G_FAT = 9

BODY_FAT_CATEGORIES = {
    "male": [(6, "Essential fat"), (14, "Athletic"), (18, "Fitness"), (25, "Average")],
    "female": [(14, "Essential fat"), (21, "Athletic"), (25, "Fitness"), (32, "Average")],
}


def calculate_bmr(weight_kg, height_cm, age, sex):
    shared_part = 10 * weight_kg + 6.25 * height_cm - 5 * age

    if sex == "male":
        return shared_part + 5
    elif sex == "female":
        return shared_part - 161
    else:
        raise ValueError(f"sex must be 'male' or 'female', not {sex!r}")


def calculate_tdee(bmr, activity_level):
    if activity_level not in ACTIVITY_MULTIPLIERS:
        raise ValueError(f"Unknown activity level: {activity_level!r}")

    return bmr * ACTIVITY_MULTIPLIERS[activity_level]


def calculate_goal_calories(tdee, goal):
    if goal not in GOAL_CALORIE_ADJUSTMENTS:
        raise ValueError(f"Unknown goal: {goal!r}")

    lower, upper = GOAL_CALORIE_ADJUSTMENTS[goal]
    middle = (lower + upper) / 2

    return {
        "low": max(round(tdee + lower), MIN_CALORIES),
        "high": max(round(tdee + upper), MIN_CALORIES),
        "target": max(round(tdee + middle), MIN_CALORIES),
    }


def describe_goal_adjustment(goal):
    lower, upper = GOAL_CALORIE_ADJUSTMENTS[goal]

    if lower == 0 and upper == 0:
        return "At maintenance"

    small, big = sorted([abs(lower), abs(upper)])
    amount = f"{small}" if small == big else f"{small}–{big}"
    direction = "below" if upper < 0 else "above"
    return f"{amount} kcal {direction} maintenance"


def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    return round(weight_kg / height_m ** 2, 1)


def bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Healthy weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def calculate_body_fat_navy(sex, height_cm, neck_cm, waist_cm, hip_cm=None):
    if sex == "male":
        girth = waist_cm - neck_cm
        if girth <= 0:
            raise ValueError("Waist must be larger than neck for this formula.")
        density = 1.0324 - 0.19077 * math.log10(girth) + 0.15456 * math.log10(height_cm)

    elif sex == "female":
        if hip_cm is None:
            raise ValueError("The hip measurement is needed for women.")
        girth = waist_cm + hip_cm - neck_cm
        if girth <= 0:
            raise ValueError("Waist + hip must be larger than neck for this formula.")
        density = 1.29579 - 0.35004 * math.log10(girth) + 0.22100 * math.log10(height_cm)

    else:
        raise ValueError(f"sex must be 'male' or 'female', not {sex!r}")

    body_fat = 495 / density - 450

    if not (2 <= body_fat <= 60):
        raise ValueError("These measurements give an unrealistic result. Please re-check them.")

    return round(body_fat, 1)


def body_fat_category(body_fat, sex):
    for upper_limit, label in BODY_FAT_CATEGORIES[sex]:
        if body_fat < upper_limit:
            return label
    return "Above average"


def energy_breakdown(weight_kg, height_cm, age, sex, activity_level):
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculate_tdee(bmr, activity_level)

    goals = {goal: calculate_goal_calories(tdee, goal) for goal in GOAL_CALORIE_ADJUSTMENTS}

    return {
        "bmr": round(bmr),
        "multiplier": ACTIVITY_MULTIPLIERS[activity_level],
        "tdee": round(tdee),
        "goals": goals,
    }


def calculate_macros(calorie_target, weight_kg, goal):
    protein_g = round(weight_kg * PROTEIN_PER_KG.get(goal, 1.6))
    fat_g = round(calorie_target * FAT_PERCENT / KCAL_PER_G_FAT)

    used_kcal = protein_g * KCAL_PER_G_PROTEIN + fat_g * KCAL_PER_G_FAT
    carbs_g = round(max(calorie_target - used_kcal, 0) / KCAL_PER_G_CARBS)

    return {"protein": protein_g, "carbs": carbs_g, "fat": fat_g}


def build_summary(profile):
    bmi = calculate_bmi(profile.weight_kg, profile.height_cm)
    bmr = calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.sex)
    tdee = calculate_tdee(bmr, profile.activity_level)
    calories = calculate_goal_calories(tdee, profile.goal)
    macros = calculate_macros(calories["target"], profile.weight_kg, profile.goal)

    return {
        "bmi": bmi,
        "bmi_category": bmi_category(bmi),
        "bmr": round(bmr),
        "tdee": round(tdee),
        "calorie_target": calories["target"],
        "calorie_low": calories["low"],
        "calorie_high": calories["high"],
        "macros": macros,
    }


NUTRIENTS = ("calories", "protein", "carbs", "fat")


def scale_nutrients(per_100g, grams):
    if grams < 0:
        raise ValueError("Grams cannot be negative.")

    factor = grams / 100

    return {nutrient: per_100g[nutrient] * factor for nutrient in NUTRIENTS}


def add_up_totals(items):
    totals = {nutrient: 0 for nutrient in NUTRIENTS}
    for item in items:
        for nutrient in NUTRIENTS:
            totals[nutrient] += item[nutrient]
    return totals


def daily_progress(totals, targets):
    progress = {}
    for nutrient in NUTRIENTS:
        consumed = totals[nutrient]
        target = targets[nutrient]
        remaining = target - consumed
        percent = min(consumed / target * 100, 100) if target > 0 else 0
        progress[nutrient] = {
            "consumed": consumed,
            "target": target,
            "remaining": remaining,
            "percent": percent,
            "over": remaining < 0,
        }
    return progress


def estimate_one_rep_max(weight_kg, reps):
    if reps < 1:
        raise ValueError("Reps must be at least 1.")
    if weight_kg < 0:
        raise ValueError("Weight cannot be negative.")

    if reps == 1:
        return weight_kg

    return weight_kg * (1 + reps / 30)


MIN_CHART_POINTS = 2


def weight_summary(weigh_ins):
    if not weigh_ins:
        return None

    start_date, start_kg = weigh_ins[0]
    current_date, current_kg = weigh_ins[-1]
    return {
        "start": start_kg,
        "start_date": start_date,
        "current": current_kg,
        "current_date": current_date,
        "change": current_kg - start_kg,
    }


def total_by_day(amounts):
    totals = {}
    for day, amount in amounts:
        totals[day] = totals.get(day, 0) + amount
    return sorted(totals.items())


def strength_by_day(lifts):
    best_per_day = {}
    for day, weight, reps in lifts:
        e1rm = estimate_one_rep_max(weight, reps)
        if day not in best_per_day:
            best_per_day[day] = (weight, e1rm)
        else:
            heaviest, best_e1rm = best_per_day[day]
            best_per_day[day] = (max(heaviest, weight), max(best_e1rm, e1rm))

    return [(day, heaviest, best_e1rm) for day, (heaviest, best_e1rm) in sorted(best_per_day.items())]


def best_lift(lifts):
    if not lifts:
        return None

    def heaviness(lift):
        day, weight, reps = lift
        return (weight, reps)

    return max(lifts, key=heaviness)