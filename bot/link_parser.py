"""
Link parser for extracting movie identifiers from IMDb and Netflix URLs.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedLink:
    """Result of parsing a movie link."""
    source: str  # 'imdb', 'netflix', or 'rottentomatoes'
    imdb_id: Optional[str] = None  # e.g., 'tt1375666'
    netflix_title: Optional[str] = None  # Extracted title for Netflix
    rt_slug: Optional[str] = None  # e.g., 'inception' from rottentomatoes.com/m/inception
    original_url: str = ""


# IMDb URL patterns
# Matches: imdb.com/title/tt1234567, www.imdb.com/title/tt1234567, m.imdb.com/title/tt1234567
IMDB_PATTERN = re.compile(
    r'https?://(?:www\.|m\.)?imdb\.com/title/(tt\d+)',
    re.IGNORECASE
)

# Netflix URL patterns
# Matches: netflix.com/title/12345678, netflix.com/watch/12345678
# Also handles locale prefixes like /ro-en/, /en-gb/, /ro/
NETFLIX_PATTERN = re.compile(
    r'https?://(?:www\.)?netflix\.com/(?:[a-z]{2}(?:-[a-z]{2})?/)?(?:title|watch)/(\d+)',
    re.IGNORECASE
)

# Rotten Tomatoes URL patterns
# Matches: rottentomatoes.com/m/movie_name
ROTTENTOMATOES_PATTERN = re.compile(
    r'https?://(?:www\.)?rottentomatoes\.com/m/([a-zA-Z0-9_]+)',
    re.IGNORECASE
)


def find_movie_links(text: str) -> list[ParsedLink]:
    """
    Find all movie links in a text message.

    Args:
        text: Message text that may contain movie URLs

    Returns:
        List of ParsedLink objects for each found link
    """
    links = []

    # Find IMDb links
    for match in IMDB_PATTERN.finditer(text):
        imdb_id = match.group(1)
        links.append(ParsedLink(
            source='imdb',
            imdb_id=imdb_id,
            original_url=match.group(0)
        ))

    # Find Netflix links
    for match in NETFLIX_PATTERN.finditer(text):
        netflix_id = match.group(1)
        links.append(ParsedLink(
            source='netflix',
            netflix_title=None,  # Will need to fetch title separately
            original_url=match.group(0)
        ))

    # Find Rotten Tomatoes links
    for match in ROTTENTOMATOES_PATTERN.finditer(text):
        rt_slug = match.group(1)
        links.append(ParsedLink(
            source='rottentomatoes',
            rt_slug=rt_slug,
            original_url=match.group(0)
        ))

    return links


def extract_imdb_id(url: str) -> Optional[str]:
    """
    Extract IMDb ID from a URL.

    Args:
        url: IMDb URL

    Returns:
        IMDb ID (e.g., 'tt1375666') or None if not found
    """
    match = IMDB_PATTERN.search(url)
    return match.group(1) if match else None


def is_movie_link(text: str) -> bool:
    """
    Check if text contains any movie links.

    Args:
        text: Text to check

    Returns:
        True if text contains IMDb, Netflix, or Rotten Tomatoes links
    """
    return bool(IMDB_PATTERN.search(text) or NETFLIX_PATTERN.search(text) or ROTTENTOMATOES_PATTERN.search(text))
