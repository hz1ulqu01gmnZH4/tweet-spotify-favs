# coding: utf-8
import json
import tweepy
import time
import functools
import spotipy
import os
import random
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load previous results
try:
    with open('favourite.json', 'r') as f:
        results = json.load(f)
except FileNotFoundError:
    results = {'items': []}

# Twitter client setup with automatic rate limit handling
client = tweepy.Client(
    bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
    consumer_key=os.getenv('TWITTER_CONSUMER_KEY'),
    consumer_secret=os.getenv('TWITTER_CONSUMER_SECRET'),
    access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
    access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
    wait_on_rate_limit=True  # Automatically handle standard rate limits
)

# Spotify client setup
scope = "user-library-read"
sp = spotipy.Spotify(
    auth_manager=spotipy.SpotifyOAuth(
        scope=scope,
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI')
    )
)

try:
    results_new = sp.current_user_saved_tracks(limit=50)
except Exception as e:
    print(f"Error fetching Spotify tracks: {e}")
    exit(1)

# Find new tracks
print([x['track']['name'] for x in results_new['items'] if x not in results['items']])
diff_track_ids = [x['track']['id'] for x in results['items']]
diff = [x for x in results_new['items'] if x['track']['id'] not in diff_track_ids]

def post_tweet_with_retry(client, text, max_retries=5):
    """Post a tweet with retry logic for rate limiting."""
    for attempt in range(max_retries):
        try:
            result = client.create_tweet(text=text)
            return result
        except tweepy.TooManyRequests as e:
            if attempt == max_retries - 1:
                logger.error(f"Max retries exceeded for tweet: {text[:50]}...")
                raise
            
            # Try to get wait time from headers
            wait_time = 60  # Default wait time
            if hasattr(e, 'response') and e.response:
                headers = e.response.headers
                
                # Check for Retry-After header
                retry_after = headers.get('retry-after') or headers.get('Retry-After')
                if retry_after:
                    try:
                        wait_time = float(retry_after) + random.uniform(1, 3)
                        logger.info(f"Using Retry-After header: waiting {wait_time:.1f}s")
                    except (ValueError, TypeError):
                        pass
                else:
                    # Check for rate limit reset time
                    reset_time = headers.get('x-rate-limit-reset')
                    if reset_time:
                        try:
                            current_time = int(time.time())
                            reset_timestamp = int(reset_time)
                            calculated_wait = max(0, reset_timestamp - current_time) + random.uniform(1, 3)
                            if calculated_wait > 0:
                                wait_time = calculated_wait
                                logger.info(f"Using x-rate-limit-reset: waiting {wait_time:.1f}s")
                        except (ValueError, TypeError):
                            pass
                
                # If no headers, use exponential backoff
                if wait_time == 60:
                    wait_time = min(60 * (2 ** attempt) + random.uniform(0, 10), 300)
                    logger.info(f"Using exponential backoff: waiting {wait_time:.1f}s")
            
            logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
            
        except tweepy.errors.Forbidden:
            logger.error(f"Forbidden: Cannot tweet - {text[:50]}...")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    return None

try:
    # Tweet new tracks
    for idx, item in enumerate(reversed(diff)):
        artists = ','.join([artist['name'] for artist in item['track']['artists']])
        tweet = "Liked on Spotify: " + "\"" + item['track']['name'] + "\"" + " by {} ".format(artists) + item['track']['external_urls']['spotify']
        hashtags = ["#"+''.join(ch for ch in ''.join(artist['name'].split(" ")) if ch.isalnum()).lower() for artist in item['track']['artists']]
        
        try:
            tweet = functools.reduce(lambda y, x: y + (" " + x), hashtags, tweet)
            logger.info(f"Tweeting: {tweet}")
            
            # Post tweet with retry logic
            result = post_tweet_with_retry(client, tweet)
            if result:
                logger.info(f"Successfully tweeted track {idx + 1}/{len(diff)}")
            else:
                logger.warning(f"Failed to tweet track {idx + 1}/{len(diff)}")
            
            # Wait between tweets to avoid rate limiting
            if idx < len(diff) - 1:  # Don't wait after the last tweet
                time.sleep(60)
                
        except Exception as e:
            logger.error(f"Error processing track: {e}")
            continue
            
finally:
    # Always save the latest results, even if there's an exception
    with open('favourite.json', 'w') as f:
        json.dump(results_new, f, indent=2)
    logger.info("Saved latest tracks to favourite.json")
