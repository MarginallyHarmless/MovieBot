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
from tmdb_client import TMDBClient

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

app = Flask(__name__)

# Initialize database and TMDB client
db = Database()
tmdb = TMDBClient()


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


@app.route('/api/movies/<movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    """Delete a movie from the collection."""
    # Get the movie first to find its tmdb_id
    movies = db.get_all_movies()
    movie = next((m for m in movies if m['id'] == movie_id), None)

    if not movie:
        return jsonify({'success': False, 'error': 'Movie not found'}), 404

    result = db.delete_movie(movie['tmdb_id'])
    if result:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to delete'}), 500


@app.route('/api/tmdb/search')
def search_tmdb():
    """Search TMDB for movies."""
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])

    result = tmdb.search_movies(query)
    return jsonify(result)


@app.route('/api/movies', methods=['POST'])
def add_movie():
    """Add a movie to the collection."""
    data = request.get_json()
    tmdb_id = data.get('tmdb_id')

    if not tmdb_id:
        return jsonify({'success': False, 'error': 'tmdb_id required'}), 400

    # Check if already exists
    if db.movie_exists(tmdb_id):
        return jsonify({'success': False, 'error': 'Movie already in collection'}), 409

    # Get full movie details from TMDB
    movie = tmdb.get_movie_details(tmdb_id)
    if not movie:
        return jsonify({'success': False, 'error': 'Movie not found on TMDB'}), 404

    # Add to database
    result = db.add_movie(
        tmdb_id=movie['tmdb_id'],
        title=movie['title'],
        year=movie['year'],
        poster_url=movie['poster_url'],
        genres=movie['genres'],
        overview=movie['overview'],
        added_by_username='Website',
        added_by_avatar=None,
        source_url=None
    )

    return jsonify({'success': True, 'movie': result})


if __name__ == '__main__':
    print("[STARTING] PRLN Movies Website...")
    print("           Visit http://localhost:5000 to view your collection")
    app.run(debug=True, port=5000)
