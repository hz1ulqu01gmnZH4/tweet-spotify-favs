# coding: utf-8
import json
import tweepy
import time
import functools
import spotipy
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load previous results
try:
    with open('favourite.json', 'r') as f:
        results = json.load(f)
except FileNotFoundError:
    results = {'items': []}

# Twitter client setup
client = tweepy.Client(
    bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
    consumer_key=os.getenv('TWITTER_CONSUMER_KEY'),
    consumer_secret=os.getenv('TWITTER_CONSUMER_SECRET'),
    access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
    access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
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

try:
    # Tweet new tracks
    for idx, item in enumerate(reversed(diff)):
        artists = ','.join([artist['name'] for artist in item['track']['artists']])
        tweet = "Liked on Spotify: " + "\"" + item['track']['name'] + "\"" + " by {} ".format(artists) + item['track']['external_urls']['spotify']
        hashtags = ["#"+''.join(ch for ch in ''.join(artist['name'].split(" ")) if ch.isalnum()).lower() for artist in item['track']['artists']]
        try:
            tweet = functools.reduce(lambda y, x: y + (" " + x), hashtags, tweet)
            print(tweet)
            client.create_tweet(text=tweet)
        except tweepy.errors.Forbidden:
            print(f"Failed to tweet: {tweet[:50]}...")
            pass
        except Exception as e:
            print(f"Unexpected error tweeting: {e}")
            pass
        time.sleep(60)
finally:
    # Always save the latest results, even if there's an exception
    with open('favourite.json', 'w') as f:
        json.dump(results_new, f, indent=2)
    print("Saved latest tracks to favourite.json")
