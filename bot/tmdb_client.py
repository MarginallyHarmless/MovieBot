"""
TMDB API client for fetching movie details.
"""

import os
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'


class TMDBClient:
    """Client for interacting with the TMDB API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TMDB client.

        Args:
            api_key: TMDB API key. If not provided, reads from environment.
        """
        self.api_key = api_key or TMDB_API_KEY
        if not self.api_key:
            raise ValueError("TMDB_API_KEY not found in environment variables")

    def _make_request(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """
        Make a request to the TMDB API.

        Args:
            endpoint: API endpoint (e.g., '/find/tt1375666')
            params: Additional query parameters

        Returns:
            JSON response or None if request failed
        """
        url = f"{TMDB_BASE_URL}{endpoint}"
        params = params or {}
        params['api_key'] = self.api_key

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"TMDB API error: {e}")
            return None

    def find_by_imdb_id(self, imdb_id: str) -> Optional[dict]:
        """
        Find a movie by its IMDb ID.

        Args:
            imdb_id: IMDb ID (e.g., 'tt1375666')

        Returns:
            Movie dict with standardized fields or None if not found
        """
        data = self._make_request(
            f'/find/{imdb_id}',
            params={'external_source': 'imdb_id'}
        )

        if not data:
            return None

        # TMDB returns results in different categories
        movie_results = data.get('movie_results', [])

        if not movie_results:
            return None

        movie = movie_results[0]
        return self._format_movie(movie)

    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[dict]:
        """
        Search for a movie by title.

        Args:
            title: Movie title to search for
            year: Optional release year to narrow results

        Returns:
            Best matching movie dict or None if not found
        """
        params = {'query': title}
        if year:
            params['year'] = year

        data = self._make_request('/search/movie', params=params)

        if not data or not data.get('results'):
            return None

        # Return the first (most relevant) result
        movie = data['results'][0]
        return self._format_movie(movie)

    def get_movie_details(self, tmdb_id: int) -> Optional[dict]:
        """
        Get detailed information about a movie.

        Args:
            tmdb_id: TMDB movie ID

        Returns:
            Movie dict with full details or None if not found
        """
        data = self._make_request(f'/movie/{tmdb_id}')

        if not data:
            return None

        return self._format_movie(data, include_full_genres=True)

    def _format_movie(self, movie: dict, include_full_genres: bool = False) -> dict:
        """
        Format TMDB movie data into a standardized structure.

        Args:
            movie: Raw movie data from TMDB
            include_full_genres: If True, fetch full genre names

        Returns:
            Standardized movie dict
        """
        # Extract year from release date
        release_date = movie.get('release_date', '')
        year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

        # Handle poster URL
        poster_path = movie.get('poster_path')
        poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

        # Handle genres
        if include_full_genres and 'genres' in movie:
            # Full movie details include genre objects
            genres = [g['name'] for g in movie.get('genres', [])]
        else:
            # Search results only include genre IDs
            genre_ids = movie.get('genre_ids', [])
            genres = self._get_genre_names(genre_ids)

        return {
            'tmdb_id': movie.get('id'),
            'title': movie.get('title'),
            'year': year,
            'poster_url': poster_url,
            'genres': genres,
            'overview': movie.get('overview', ''),
        }

    def _get_genre_names(self, genre_ids: list[int]) -> list[str]:
        """
        Convert genre IDs to genre names.

        Uses a static mapping for efficiency (genres rarely change).
        """
        # TMDB movie genre mapping (as of 2024)
        genre_map = {
            28: 'Action',
            12: 'Adventure',
            16: 'Animation',
            35: 'Comedy',
            80: 'Crime',
            99: 'Documentary',
            18: 'Drama',
            10751: 'Family',
            14: 'Fantasy',
            36: 'History',
            27: 'Horror',
            10402: 'Music',
            9648: 'Mystery',
            10749: 'Romance',
            878: 'Science Fiction',
            10770: 'TV Movie',
            53: 'Thriller',
            10752: 'War',
            37: 'Western',
        }

        return [genre_map.get(gid, 'Unknown') for gid in genre_ids if gid in genre_map]
