from flask import Flask, request, render_template, jsonify
from google_play_scraper import search as google_search, app as google_app , Sort, reviews_all
from app_store_scraper import AppStore
import threading
from flask_cors import CORS
import requests
import ssl
import pandas as pd
import numpy as np
import json, os, uuid

app = Flask(__name__)
CORS(app)

ssl._create_default_https_context = ssl._create_unverified_context

def fetch_google_play_apps(query, results):
    apps = google_search(query, lang='en', country='us')
    results.extend([{'title': app['title'], 'app_id': app['appId'], 'platform': 'Google Play Store'} for app in apps])
    print(f"Fetched {len(apps)} apps from Google Play Store for query '{query}'")

def fetch_app_store_apps(query, results):
    try:
        print(f"Starting search for '{query}' in Apple Store")
        response = requests.get(f'https://itunes.apple.com/search?term={query}&entity=software')
        response.raise_for_status()
        apps = response.json().get('results', [])
        
        if apps:
            for app in apps:
                results.append({
                    'title': app.get('trackName'),
                    'app_id': app.get('trackId'),
                    'platform': 'Apple Store'
                })
            print(f"Fetched {len(apps)} apps from Apple Store for query '{query}'")
        else:
            print(f"No apps found in Apple Store for query '{query}'")
    except requests.exceptions.SSLError as e:
        print(f"SSL error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


######################################################################### Fetch Reviews
def fetch_google_play_reviews(app_id):
    print("Google Reviews Clicked")
    print(app_id)
    g_reviews = reviews_all(
        app_id,
        sleep_milliseconds=0,
        lang='en',
        country='us',
        sort=Sort.NEWEST,
    )
    # print(g_reviews)
    # return [{'review': review['content']} for review in g_reviews['review_description']]
    return g_reviews

def fetch_app_store_reviews(app_name):
    print("Apple Reviews Clicked")
    app_store = AppStore(country="us", app_name = app_name)
    app_store.review(how_many=5)
    return [{'review': review['review']} for review in app_store.reviews]
####################################################################################################################

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json()
        query = data['query']
        google_results = []
        apple_results = []

        google_thread = threading.Thread(target=fetch_google_play_apps, args=(query, google_results))
        apple_thread = threading.Thread(target=fetch_app_store_apps, args=(query, apple_results))

        google_thread.start()
        apple_thread.start()

        google_thread.join()
        apple_thread.join()
        
        combined_results = google_results + apple_results
        return jsonify(results=combined_results)
    return render_template('index.html')

@app.route('/reviews', methods=['POST'])
def reviews():
    print("Review Started")
    data = request.get_json()
    print("Data: ")
    print(data)
    app_id = data['app_id']
    app_name = data['app_name']
    print(app_name)
    print(app_id)
    platform = data['platform']
    print(platform)
    
    if platform == 'Google Play Store':
        print("Google reviews")
        reviews = fetch_google_play_reviews(app_id)
        print(reviews)
    elif platform == 'Apple Store':
        print("Apple reviews")
        reviews = fetch_app_store_reviews(app_name)
        print(reviews)
    else:
        print("No Reviews")
        reviews = []
    return jsonify(reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)
