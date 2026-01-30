"""
Database module for Supabase operations.
"""

import os
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


class Database:
    """Handles all database operations with Supabase."""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            url: Supabase project URL. If not provided, reads from environment.
            key: Supabase anon key. If not provided, reads from environment.
        """
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_KEY

        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

        self.client: Client = create_client(self.url, self.key)

    def add_movie(
        self,
        tmdb_id: int,
        title: str,
        year: Optional[int] = None,
        poster_url: Optional[str] = None,
        genres: Optional[list[str]] = None,
        overview: Optional[str] = None,
        added_by_username: Optional[str] = None,
        added_by_avatar: Optional[str] = None,
        source_url: Optional[str] = None,
        added_at: Optional[str] = None
    ) -> dict:
        """
        Add a movie to the database.

        Args:
            tmdb_id: TMDB movie ID
            title: Movie title
            year: Release year
            poster_url: URL to movie poster
            genres: List of genre names
            overview: Movie description
            added_by_username: Discord username who added it
            added_by_avatar: Discord avatar URL
            source_url: Original link that was shared

        Returns:
            The inserted movie record

        Raises:
            Exception: If insert fails
        """
        movie_data = {
            'tmdb_id': tmdb_id,
            'title': title,
            'year': year,
            'poster_url': poster_url,
            'genres': genres or [],
            'overview': overview,
            'added_by_username': added_by_username,
            'added_by_avatar': added_by_avatar,
            'source_url': source_url,
        }

        # Add custom timestamp if provided (e.g., from Discord message)
        if added_at:
            movie_data['added_at'] = added_at

        result = self.client.table('movies').insert(movie_data).execute()

        if result.data:
            return result.data[0]
        raise Exception("Failed to insert movie")

    def movie_exists(self, tmdb_id: int) -> bool:
        """
        Check if a movie already exists in the database.

        Args:
            tmdb_id: TMDB movie ID to check

        Returns:
            True if movie exists, False otherwise
        """
        result = self.client.table('movies').select('id').eq('tmdb_id', tmdb_id).execute()
        return len(result.data) > 0

    def get_movie_by_tmdb_id(self, tmdb_id: int) -> Optional[dict]:
        """
        Get a movie by its TMDB ID.

        Args:
            tmdb_id: TMDB movie ID

        Returns:
            Movie record or None if not found
        """
        result = self.client.table('movies').select('*').eq('tmdb_id', tmdb_id).execute()
        return result.data[0] if result.data else None

    def get_all_movies(self) -> list[dict]:
        """
        Get all movies from the database.

        Returns:
            List of all movie records, ordered by added_at descending
        """
        result = self.client.table('movies').select('*').order('added_at', desc=True).execute()
        return result.data

    def get_recent_movies(self, limit: int = 10) -> list[dict]:
        """
        Get the most recently added movies.

        Args:
            limit: Maximum number of movies to return

        Returns:
            List of recent movie records
        """
        result = (
            self.client.table('movies')
            .select('*')
            .order('added_at', desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    def get_movie_count(self) -> int:
        """
        Get the total number of movies in the database.

        Returns:
            Total movie count
        """
        result = self.client.table('movies').select('id', count='exact').execute()
        return result.count or 0

    def get_all_genres(self) -> list[str]:
        """
        Get all unique genres from the database.

        Returns:
            List of unique genre names
        """
        result = self.client.table('movies').select('genres').execute()

        # Flatten and deduplicate genres
        all_genres = set()
        for movie in result.data:
            if movie.get('genres'):
                all_genres.update(movie['genres'])

        return sorted(list(all_genres))

    def search_movies(self, query: str) -> list[dict]:
        """
        Search movies by title.

        Args:
            query: Search query

        Returns:
            List of matching movies
        """
        result = (
            self.client.table('movies')
            .select('*')
            .ilike('title', f'%{query}%')
            .order('added_at', desc=True)
            .execute()
        )
        return result.data

    def delete_movie(self, tmdb_id: int) -> bool:
        """
        Delete a movie from the database.

        Args:
            tmdb_id: TMDB movie ID to delete

        Returns:
            True if deleted, False if not found
        """
        result = self.client.table('movies').delete().eq('tmdb_id', tmdb_id).execute()
        return len(result.data) > 0

    def toggle_seen(self, movie_id: str) -> Optional[dict]:
        """
        Toggle the seen status of a movie.

        Args:
            movie_id: UUID of the movie

        Returns:
            Updated movie record or None if not found
        """
        # Get current status (select all to avoid column name issues)
        result = self.client.table('movies').select('*').eq('id', movie_id).execute()
        if not result.data:
            print(f"[DEBUG] Movie not found: {movie_id}")
            return None

        movie = result.data[0]
        # Handle both 'seen' and 'Seen' column names
        current_seen = movie.get('seen', movie.get('Seen', False))
        print(f"[DEBUG] Current seen status: {current_seen}, toggling to {not current_seen}")

        # Toggle it
        result = (
            self.client.table('movies')
            .update({'seen': not current_seen})
            .eq('id', movie_id)
            .execute()
        )

        if result.data:
            return result.data[0]
        else:
            print(f"[DEBUG] Update failed, no data returned")
            return None

    def set_seen(self, movie_id: str, seen: bool) -> Optional[dict]:
        """
        Set the seen status of a movie.

        Args:
            movie_id: UUID of the movie
            seen: True if seen, False if not seen

        Returns:
            Updated movie record or None if not found
        """
        result = (
            self.client.table('movies')
            .update({'seen': seen})
            .eq('id', movie_id)
            .execute()
        )
        return result.data[0] if result.data else None
