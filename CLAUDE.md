# SGPL Movies

A Discord bot + website for tracking movies shared by friends.

## Project Structure

```
SGPL-movies/
├── bot/
│   ├── main.py           # Discord bot entry point
│   ├── link_parser.py    # Extract movie IDs from IMDb/Netflix URLs
│   ├── tmdb_client.py    # Fetch movie details from TMDB API
│   └── database.py       # Supabase operations
├── web/
│   ├── app.py            # Flask web server
│   ├── templates/
│   │   └── index.html    # Movie grid page
│   └── static/
│       ├── style.css     # Styling
│       └── app.js        # Search/filter functionality
├── requirements.txt      # Python dependencies
├── .env.example          # Template for environment variables
└── CLAUDE.md             # This file
```

## Setup

1. Copy `.env.example` to `.env` and fill in your credentials
2. Install dependencies: `pip install -r requirements.txt`
3. Create the Supabase table (see schema below)
4. Run the bot: `python bot/main.py`
5. Run the website: `python web/app.py`

## Supabase Table Schema

Run this SQL in your Supabase SQL Editor:

```sql
CREATE TABLE movies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tmdb_id INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    year INTEGER,
    poster_url TEXT,
    genres TEXT[],
    overview TEXT,
    added_by_username TEXT,
    added_by_avatar TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_url TEXT
);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE movies ENABLE ROW LEVEL SECURITY;

-- Allow anonymous read access
CREATE POLICY "Allow anonymous read" ON movies
    FOR SELECT USING (true);

-- Allow anonymous insert
CREATE POLICY "Allow anonymous insert" ON movies
    FOR INSERT WITH CHECK (true);
```

## Running

### Discord Bot
```bash
python bot/main.py
```

### Website
```bash
python web/app.py
```
Then visit http://localhost:5000

## How It Works

1. User posts an IMDb or Netflix link in Discord
2. Bot detects the link and extracts the movie identifier
3. Bot queries TMDB API for movie details
4. Bot saves the movie to Supabase (if not a duplicate)
5. Bot adds a 👀 reaction to confirm
6. Website displays all saved movies in a grid
