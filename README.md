# Trip Planner Flask App

A Flask web application for planning trips, saving itineraries, checking weather, finding famous spots, and generating travel suggestions.

## Features

- User signup and login
- Password hashing with Werkzeug
- Session-protected dashboard pages
- Create, view, edit, and delete saved trip plans
- Profile page
- Weather lookup using wttr.in
- Famous spots search using OpenTripMap
- Optional AI itinerary suggestions using Google Gemini

## Project Structure

```text
app/
  __init__.py
  models.py
  routes.py
  static/
    css/
    js/
  templates/
instance/
run.py
requirements.txt
```

## Setup

1. Create a virtual environment:

```bash
python -m venv .venv
```

2. Activate it:

```bash
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create your environment file:

```bash
copy .env.example .env
```

5. Update `.env` with your own values. `GOOGLE_API_KEY` and `OPENTRIPMAP_API_KEY` are optional, but needed for AI suggestions and famous spots search.

6. Run the app:

```bash
python run.py
```

Open `http://127.0.0.1:5000` in your browser.
