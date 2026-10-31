# KZfitness

KZfitness is a personal computer science project built around my interest in fitness
and strength training. It's a web app that puts macro tracking, workout logging, and an
AI fitness assistant in one place, so you don't have to keep switching between a tracker
and a chatbot just to find out how many calories are in a chicken breast.

**Built with:** Python, Flask, SQLite, HTML/CSS/JavaScript, Chart.js and the Claude API.

## Features

- **Macro tracking:** log daily calories, protein, carbohydrates, and fats.
- **Workout logging:** record exercises and lifts for each gym session.
- **AI fitness assistant:** ask about nutrition, calorie estimates, and workout splits.
- **Personalized guidance:** enter your age, sex, weight, and height to get recommendations that fit you.
- **Fitness calculators:** BMI, daily calorie needs, and a one-rep max calculator.

## The very special features
- **Estimated one-rep max:** you never have to risk testing your max. Log a normal set,
  like 80 kg × 8, and KZfitness works out the heaviest single rep you could probably
  lift (about 101 kg) using the Epley formula. It also tracks your best one for each
  exercise and charts it over time, so you can see yourself getting stronger.
 - **Progress graphs:** everything you log turns into a graph. Weigh-ins show your body
  weight over time, your food log shows how many calories you ate each day against your
  target, and every exercise gets its own strength graph with your heaviest lift and
  your estimated one-rep max.


## Screenshots

*The screenshots use sample data. Every page has a light and a dark theme.*

### Dashboard
<img src="KZfitness_screenshots%202/01_dashboard_dark_desktop.png" width="650" alt="KZfitness dashboard">

### Food
<img src="KZfitness_screenshots%202/02_food_light_desktop.png" width="650" alt="Food log with live preview">

### Workout
<img src="KZfitness_screenshots%202/03_workout_light_desktop.png" width="650" alt="Workout log and estimated one-rep max">

### Progress
<img src="KZfitness_screenshots%202/04_progress_light_desktop.png" width="650" alt="Weight, calorie and strength charts">

### AI Fitness Assistant
<img src="KZfitness_screenshots%202/06_coach_dark_desktop.png" width="650" alt="AI fitness assistant">

*The answer shown is a sample.*

### Calculators
<img src="KZfitness_screenshots%202/05_calculators_dark_desktop.png" width="650" alt="Calorie, BMI and body fat calculators">

### Profile
<img src="KZfitness_screenshots%202/07_profile_dark_desktop.png" width="650" alt="Profile form">

### On a phone
<p>
  <img src="KZfitness_screenshots%202/01_dashboard_light_phone.png" width="200" alt="Dashboard on a phone">
  <img src="KZfitness_screenshots%202/04_progress_dark_phone.png" width="200" alt="Progress on a phone">
  <img src="KZfitness_screenshots%202/06_coach_light_phone.png" width="200" alt="AI assistant on a phone">
</p>

## What I Learned

- **How the parts of a web app connect.** When you press a button, the browser sends a
  request to Flask, Python reads or saves data in the SQLite database, and the result
  gets put into an HTML page. Once I understood that loop, the whole app made sense.

- **Small mistakes can stop everything.** One missing comma in `app.py` meant the app
  wouldn't start at all. Deleting the end of a comment in `progress.js` made every chart
  disappear. I learned to read error messages properly instead of guessing.

- **File names matter.** I renamed my Python files to capital letters (`APP.PY`) and the
  app broke, because Python is case-sensitive and the code imports `app`, not `APP`.

- **How to keep an API key secret.** The key for the AI coach is read from an environment
  variable, so it's never written in the code or uploaded to GitHub.

- **How the AI coach's instructions shape its answers.** I wrote my own coaching rules
  into the coach's instructions (like keeping reps between 5 and 10 for hypertrophy),
  because everything it says comes from those instructions plus the user's numbers.


Building KZfitness showed me how computer science can solve problems from my own life,
and it made me want to get much better at programming.
## Feedback and changes

I asked 5 friends to try KZfitness and tell me what annoyed them.

**"It's way too bright."**
The app used to be light only. Now there's a dark mode: there's a switch in the menu,
and it also follows whatever your phone or laptop is set to.

**"It doesn't fit properly on my phone."**
On a phone the sidebar took up too much of the screen. Now it turns into a bar at the
bottom like most apps, and the cards stack in one column so nothing gets cut off.

## What I'm working on now

**More foods.** The app comes with 13 foods, mostly the ones I eat. I'm adding more
so people don't have to create their own as often.

**Quick add.** At the moment you can save your own food with its values per 100 g,
but sometimes you just know the totals, like a restaurant meal that's about 800 kcal
and 45 g of protein. I'm adding a way to type in the calories, protein, carbs and fat
for a meal directly, without saving it as a food first.

## What I want to improve next

**Logging food takes too many steps.** Right now you search, pick the food, type the
grams and press add. I want a "recent foods" list so something you eat every day
takes one tap.

**Error messages could be clearer.** If you type something wrong, the app says what's
wrong (like "Weight must be between 30 and 300"), but only the profile page also
outlines the wrong box in red. I want every form to point straight at the box you
need to fix.

## My Goal

I want KZfitness to be something people actually use, not just a project on GitHub.
My plan to get there:

1. **Put it online** so anyone can open it from a link, without installing anything.
2. **Finish what I'm working on now:** more foods and a quick way to log a meal's calories and protein.
3. **Test it with real people** and keep fixing whatever annoys them.
4. **Make the AI coach more like me**, by adding more of the rules I use when I train
   people, so its advice feels personal instead of generic.
5. **Check every calculation and AI answer** so people can trust the numbers.

The long-term goal is an app that combines tracking and coaching in one place, the way
I'd want it as someone who trains.

#### (I used ai tools to help write the Javascript, html and CSS code in the static and template files) 
