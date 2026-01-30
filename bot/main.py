"""
SGPL Movies Discord Bot

A bot that detects movie links (IMDb/Netflix) and saves them to a database.
"""

import os
import re
import sys
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv

from link_parser import find_movie_links, is_movie_link
from tmdb_client import TMDBClient
from database import Database

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Set up intents (permissions)
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize services
tmdb = TMDBClient()
db = Database()


@bot.event
async def on_ready():
    """Called when bot is connected and ready."""
    print(f'[OK] Bot is online as {bot.user}')
    print(f'[INFO] Connected to {len(bot.guilds)} server(s)')


@bot.event
async def on_message(message: discord.Message):
    """Called for every message the bot can see."""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Debug: log all messages received
    try:
        print(f"[MESSAGE] From {message.author}: {message.content[:50].encode('ascii', 'replace').decode()}...")
    except:
        print(f"[MESSAGE] From {message.author}")

    # Check if message contains movie links
    if not is_movie_link(message.content):
        # Process other commands if no movie link
        await bot.process_commands(message)
        return

    print("[DETECTED] Movie link found!")

    # Parse all movie links from the message
    links = find_movie_links(message.content)

    for link in links:
        try:
            # Get movie details from TMDB
            if link.source == 'imdb' and link.imdb_id:
                movie = tmdb.find_by_imdb_id(link.imdb_id)
            elif link.source == 'rottentomatoes' and link.rt_slug:
                # Convert slug to title (replace underscores with spaces)
                # Extract year if slug ends with 4 digits (e.g., movie_name_2013)
                slug = link.rt_slug
                year_match = re.search(r'_(\d{4})$', slug)
                if year_match:
                    year = int(year_match.group(1))
                    title = slug[:year_match.start()].replace('_', ' ')
                    movie = tmdb.search_movie(title, year=year)
                else:
                    title = slug.replace('_', ' ')
                    movie = tmdb.search_movie(title)
            elif link.source == 'netflix':
                # Netflix links are harder to parse - skip silently
                continue
            else:
                continue

            if not movie:
                await message.channel.send(f"❌ Couldn't find movie for: {link.original_url}")
                continue

            # Check if already in database
            if db.movie_exists(movie['tmdb_id']):
                # Already exists - react with checkmark instead
                await message.add_reaction('✅')
                continue

            # Get user info for attribution
            user_avatar = str(message.author.display_avatar.url) if message.author.display_avatar else None

            # Save to database
            db.add_movie(
                tmdb_id=movie['tmdb_id'],
                title=movie['title'],
                year=movie['year'],
                poster_url=movie['poster_url'],
                genres=movie['genres'],
                overview=movie['overview'],
                added_by_username=message.author.display_name,
                added_by_avatar=user_avatar,
                source_url=link.original_url
            )

            # React with eyes to confirm
            await message.add_reaction('👀')

        except Exception as e:
            import traceback
            print(f"[ERROR] Processing link {link.original_url}: {e}")
            traceback.print_exc()
            await message.channel.send(f"Error processing link: {link.original_url}")

    # Process other commands
    await bot.process_commands(message)


@bot.command(name='stats')
async def stats(ctx: commands.Context):
    """Show statistics about the movie collection."""
    count = db.get_movie_count()
    await ctx.send(f"📊 We have **{count}** movies in the collection!")


@bot.command(name='recent')
async def recent(ctx: commands.Context, limit: int = 5):
    """Show recently added movies."""
    movies = db.get_recent_movies(limit=min(limit, 10))

    if not movies:
        await ctx.send("No movies in the collection yet!")
        return

    lines = ["**Recently Added Movies:**"]
    for movie in movies:
        lines.append(f"- {movie['title']} ({movie['year']}) - added by {movie['added_by_username']}")

    await ctx.send('\n'.join(lines))


@bot.command(name='scan')
async def scan(ctx: commands.Context, limit: int = 500):
    """Scan channel history for movie links and add them to the database."""
    await ctx.send(f"Scanning last {limit} messages for movie links...")

    added = 0
    skipped = 0
    errors = 0

    async for message in ctx.channel.history(limit=limit):
        # Skip bot messages
        if message.author.bot:
            continue

        # Check for movie links
        if not is_movie_link(message.content):
            continue

        links = find_movie_links(message.content)

        for link in links:
            try:
                # Get movie details from TMDB
                if link.source == 'imdb' and link.imdb_id:
                    movie = tmdb.find_by_imdb_id(link.imdb_id)
                elif link.source == 'rottentomatoes' and link.rt_slug:
                    # Extract year if slug ends with 4 digits
                    slug = link.rt_slug
                    year_match = re.search(r'_(\d{4})$', slug)
                    if year_match:
                        year = int(year_match.group(1))
                        title = slug[:year_match.start()].replace('_', ' ')
                        movie = tmdb.search_movie(title, year=year)
                    else:
                        title = slug.replace('_', ' ')
                        movie = tmdb.search_movie(title)
                else:
                    continue

                if not movie:
                    errors += 1
                    continue

                # Check if already in database
                if db.movie_exists(movie['tmdb_id']):
                    skipped += 1
                    continue

                # Get user info
                user_avatar = str(message.author.display_avatar.url) if message.author.display_avatar else None

                # Save to database with original Discord message timestamp
                db.add_movie(
                    tmdb_id=movie['tmdb_id'],
                    title=movie['title'],
                    year=movie['year'],
                    poster_url=movie['poster_url'],
                    genres=movie['genres'],
                    overview=movie['overview'],
                    added_by_username=message.author.display_name,
                    added_by_avatar=user_avatar,
                    source_url=link.original_url,
                    added_at=message.created_at.isoformat()
                )
                added += 1

                # Add reaction to original message
                try:
                    await message.add_reaction('👀')
                except:
                    pass  # May fail if message is too old

            except Exception as e:
                print(f"[ERROR] Scan error: {e}")
                errors += 1

    await ctx.send(f"Scan complete! Added: {added}, Already existed: {skipped}, Errors: {errors}")


def main():
    """Run the bot."""
    if not DISCORD_TOKEN:
        print("[ERROR] DISCORD_BOT_TOKEN not found in environment variables!")
        print("        Make sure you have a .env file with your bot token.")
        return

    print("[STARTING] SGPL Movies Bot...")
    bot.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
