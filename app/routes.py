import html
import os
from functools import wraps

import markdown
import requests
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Plan, User

routes_bp = Blueprint('routes', __name__)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('routes.login'))
        return view(*args, **kwargs)

    return wrapped_view


def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return db.session.get(User, user_id)


@routes_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('routes.dashboard'))
    return redirect(url_for('routes.login'))


@routes_bp.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('routes.dashboard'))
    return render_template('login.html')


@routes_bp.post('/api/signup')
def api_signup():
    data = request.get_json(silent=True) or request.form
    required_fields = ['name', 'surname', 'email', 'phone', 'gender', 'password']
    if any(not str(data.get(field, '')).strip() for field in required_fields):
        return jsonify({'error': 'Please fill in all signup fields.'}), 400

    user = User(
        name=data['name'].strip(),
        surname=data['surname'].strip(),
        email=data['email'].strip().lower(),
        phone=data['phone'].strip(),
        gender=data['gender'].strip(),
    )
    user.set_password(data['password'])

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'A user with this email or phone already exists.'}), 409

    session['user_id'] = user.id
    return jsonify({'message': 'Signup successful.', 'redirect': url_for('routes.dashboard')})


@routes_bp.post('/api/login')
def api_login():
    data = request.get_json(silent=True) or request.form
    phone = str(data.get('phone', '')).strip()
    password = str(data.get('password', ''))
    user = User.query.filter_by(phone=phone).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid phone number or password.'}), 401

    session['user_id'] = user.id
    return jsonify({'message': 'Login successful.', 'redirect': url_for('routes.dashboard')})


@routes_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('routes.login'))


@routes_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@routes_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user())


@routes_bp.route('/my_plans')
@login_required
def my_plans():
    plans = Plan.query.filter_by(user_id=session['user_id']).order_by(Plan.id.desc()).all()
    return render_template('my_plans.html', plans=plans)


@routes_bp.post('/api/plans')
@login_required
def create_plan():
    data = request.get_json(silent=True) or request.form
    current_location = str(data.get('current_location', '')).strip()
    destinations = data.get('destinations') or data.get('destination') or []
    if isinstance(destinations, str):
        destinations = [destinations]
    destinations = [str(destination).strip() for destination in destinations if str(destination).strip()]
    trip_date = str(data.get('date', '')).strip()
    budget = str(data.get('budget', '')).strip()

    if not current_location or not destinations or not trip_date:
        return jsonify({'error': 'Current location, destination, and date are required.'}), 400

    plan = Plan(
        current_location=current_location,
        destination=', '.join(destinations),
        date=trip_date,
        budget=budget,
        user_id=session['user_id'],
    )
    db.session.add(plan)
    db.session.commit()
    return jsonify({'message': 'Plan saved.', 'plan_id': plan.id})


@routes_bp.put('/api/plans/<int:plan_id>')
@login_required
def update_plan(plan_id):
    plan = Plan.query.filter_by(id=plan_id, user_id=session['user_id']).first_or_404()
    data = request.get_json(silent=True) or {}

    plan.current_location = str(data.get('current_location', plan.current_location)).strip()
    plan.destination = str(data.get('destination', plan.destination)).strip()
    plan.date = str(data.get('date', plan.date)).strip()
    plan.budget = str(data.get('budget', plan.budget or '')).strip()
    db.session.commit()
    return jsonify({'message': 'Plan updated.'})


@routes_bp.delete('/api/plans/<int:plan_id>')
@login_required
def delete_plan(plan_id):
    plan = Plan.query.filter_by(id=plan_id, user_id=session['user_id']).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    return jsonify({'message': 'Plan deleted.'})


@routes_bp.route('/search_spots')
@login_required
def search_spots():
    return render_template(
        'search_spots.html',
    )


@routes_bp.get('/api/search-spots')
@login_required
def api_search_spots():
    destination = request.args.get('destination', '').strip()
    if not destination:
        return jsonify({'error': 'Enter a destination.'}), 400

    try:
        try:
            places = search_with_opentripmap(destination)
            source = 'OpenTripMap'
        except requests.RequestException:
            places = []
            source = 'Wikipedia'
        if not places:
            places = search_with_wikipedia(destination)
            source = 'Wikipedia'
        return jsonify({'destination': destination, 'source': source, 'places': places})
    except requests.RequestException:
        return jsonify({'error': 'The places service is temporarily unavailable. Please try again.'}), 502
    except (KeyError, IndexError, TypeError, ValueError):
        return jsonify({'error': 'The places service returned an invalid response. Please try again.'}), 502


@routes_bp.post('/api/spot-fact')
@login_required
def api_spot_fact():
    data = request.get_json(silent=True) or {}
    place = str(data.get('place', '')).strip()
    if not place:
        return jsonify({'error': 'A place is required.'}), 400

    prompt = f'Tell me one interesting, accurate travel fact about {place}. Keep it under 50 words.'
    try:
        fact = generate_ai_suggestion(prompt, place, '1', 'travel facts')
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        fact = f'{place} is a notable place to explore. Check local visitor information for current opening hours and travel advice.'
    return jsonify({'fact': fact})


def search_with_opentripmap(destination):
    api_key = os.getenv('OPENTRIPMAP_API_KEY', '').strip()
    if not api_key:
        return []

    base_url = 'https://api.opentripmap.com/0.1/en/places'
    geo_response = requests.get(
        f'{base_url}/geoname', params={'name': destination, 'apikey': api_key}, timeout=15
    )
    geo_response.raise_for_status()
    location = geo_response.json()
    if not location.get('lat') or not location.get('lon'):
        return []

    places_response = requests.get(
        f'{base_url}/radius',
        params={
            'lat': location['lat'],
            'lon': location['lon'],
            'radius': 20000,
            'kinds': 'interesting_places',
            'rate': 3,
            'limit': 12,
            'format': 'json',
            'apikey': api_key,
        },
        timeout=15,
    )
    places_response.raise_for_status()
    results = []
    for place in places_response.json() or []:
        details_response = requests.get(
            f"{base_url}/xid/{place['xid']}", params={'apikey': api_key}, timeout=15
        )
        details_response.raise_for_status()
        details = details_response.json()
        if details.get('name'):
            results.append({
                'name': details['name'],
                'description': details.get('wikipedia_extracts', {}).get('text') or 'No description available.',
                'image': details.get('preview', {}).get('source'),
            })
    return results


def search_with_wikipedia(destination):
    headers = {'User-Agent': 'TripPlanner/1.0 (local educational project)'}
    geocode_response = requests.get(
        'https://nominatim.openstreetmap.org/search',
        params={'q': destination, 'format': 'jsonv2', 'limit': 1},
        headers=headers,
        timeout=15,
    )
    geocode_response.raise_for_status()
    locations = geocode_response.json()
    if not locations:
        return []

    location = locations[0]
    search_response = requests.get(
        'https://en.wikipedia.org/w/api.php',
        params={
            'action': 'query',
            'generator': 'geosearch',
            'ggscoord': f"{location['lat']}|{location['lon']}",
            'ggsradius': 10000,
            'ggslimit': 12,
            'prop': 'extracts|pageimages',
            'exintro': 1,
            'explaintext': 1,
            'piprop': 'thumbnail',
            'pithumbsize': 600,
            'format': 'json',
        },
        headers=headers,
        timeout=15,
    )
    search_response.raise_for_status()

    pages = search_response.json().get('query', {}).get('pages', {})
    return [
        {
            'name': page.get('title'),
            'description': page.get('extract') or 'No description available.',
            'image': page.get('thumbnail', {}).get('source'),
        }
        for page in pages.values()
        if page.get('title')
    ]


@routes_bp.route('/weather', methods=['GET', 'POST'])
@login_required
def weather():
    weather_data = None
    error = None

    if request.method == 'POST':
        city = request.form.get('city', '').strip()
        if not city:
            error = 'Please enter a city name.'
        else:
            try:
                response = requests.get(f'https://wttr.in/{city}?format=j1', timeout=10)
                response.raise_for_status()
                payload = response.json()
                current = payload['current_condition'][0]
                area = payload['nearest_area'][0]
                weather_data = {
                    'city': area['areaName'][0]['value'],
                    'country': area['country'][0]['value'],
                    'temp': current['temp_C'],
                    'condition': current['weatherDesc'][0]['value'],
                    'icon': current['weatherIconUrl'][0]['value'],
                }
            except (requests.RequestException, KeyError, IndexError, ValueError):
                error = 'Unable to fetch weather for that city. Please try another location.'

    return render_template('weather.html', weather=weather_data, error=error)


@routes_bp.route('/suggestions', methods=['GET', 'POST'])
@login_required
def suggestions():
    response_html = None
    error = None

    if request.method == 'POST':
        place = request.form.get('place', '').strip()
        days = request.form.get('days', '').strip()
        interests = request.form.get('interests', '').strip()

        if not place or not days or not interests:
            error = 'Please fill in destination, duration, and interests.'
        else:
            prompt = (
                f'Create a practical {days}-day travel itinerary for {place}. '
                f'Focus on these interests: {interests}. Include morning, afternoon, '
                'and evening suggestions with concise travel tips.'
            )
            try:
                suggestion_text = generate_ai_suggestion(prompt, place, days, interests)
                response_html = markdown.markdown(suggestion_text)
            except requests.RequestException:
                error = 'Unable to generate suggestions right now. Please try again later.'

    return render_template('suggestions.html', response=response_html, error=error)


def generate_ai_suggestion(prompt, place, days, interests):
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        escaped_place = html.escape(place)
        escaped_interests = html.escape(interests)
        return (
            f'## {html.escape(days)}-Day Trip Plan for {escaped_place}\n\n'
            f'**Focus:** {escaped_interests}\n\n'
            '### Day 1\n'
            '- Morning: Visit the most popular central attraction and get familiar with the area.\n'
            '- Afternoon: Try local food and explore nearby markets or museums.\n'
            '- Evening: Choose a scenic viewpoint, waterfront, or cultural show.\n\n'
            '### Travel Tips\n'
            '- Start early to avoid crowds.\n'
            '- Keep buffer time for traffic and queues.\n'
            '- Save important places offline before leaving.'
        )

    response = requests.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}',
        json={'contents': [{'parts': [{'text': prompt}]}]},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return payload['candidates'][0]['content']['parts'][0]['text']
