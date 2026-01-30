"""
Flask web application for displaying the movie collection.
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request

# Add parent directory to path so we can import from bot/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

from dotenv import load_dotenv
from database import Database

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

app = Flask(__name__)

# Initialize database connection
db = Database()


@app.route('/')
def index():
    """Main page - display all movies in a grid."""
    movies = db.get_all_movies()
    genres = db.get_all_genres()
    return render_template('index.html', movies=movies, genres=genres)


@app.route('/api/movies')
def api_movies():
    """API endpoint to get all movies as JSON."""
    movies = db.get_all_movies()
    return jsonify(movies)


@app.route('/api/genres')
def api_genres():
    """API endpoint to get all unique genres."""
    genres = db.get_all_genres()
    return jsonify(genres)


@app.route('/api/stats')
def api_stats():
    """API endpoint to get collection statistics."""
    return jsonify({
        'total_movies': db.get_movie_count(),
        'total_genres': len(db.get_all_genres())
    })


@app.route('/api/movies/<movie_id>/toggle-seen', methods=['POST'])
def toggle_seen(movie_id):
    """Toggle the seen status of a movie."""
    result = db.toggle_seen(movie_id)
    if result:
        return jsonify({'success': True, 'seen': result.get('seen', False)})
    return jsonify({'success': False, 'error': 'Movie not found'}), 404


if __name__ == '__main__':
    print("[STARTING] SGPL Movies Website...")
    print("           Visit http://localhost:5000 to view your collection")
    app.run(debug=True, port=5000)
