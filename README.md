# Tweet Spotify Favs

Automatically tweet your newly favorited Spotify tracks to Twitter/X.

## Features

- Monitors your Spotify liked tracks
- Automatically tweets new favorites with artist hashtags
- Saves state to avoid duplicate tweets
- Handles API errors gracefully

## Prerequisites

- Python 3.9+
- Twitter/X Developer Account with API access
- Spotify Developer Account with API access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tweet-spotify-favs.git
cd tweet-spotify-favs
```

2. Install dependencies using uv:
```bash
uv pip install .
```

Or using pip:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your API credentials:

### Twitter API Setup
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app or use existing one
3. Generate all required tokens and keys
4. Add them to your `.env` file

### Spotify API Setup
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add `http://localhost:8888/callback` as redirect URI
4. Copy Client ID and Client Secret to `.env`

## Usage

Run the script:
```bash
python main.py
```

On first run, you'll be redirected to Spotify for authentication. After authorizing, the script will:
1. Check for new liked tracks since last run
2. Tweet each new track with artist hashtags
3. Wait 60 seconds between tweets to avoid rate limits
4. Save the current state to `favourite.json`

## Scheduling

To run automatically, set up a cron job:
```bash
# Run every hour
0 * * * * cd /path/to/tweet-spotify-favs && python main.py
```

## Files

- `main.py` - Main script
- `favourite.json` - Stores previously processed tracks
- `.env` - Your API credentials (not tracked in git)
- `.env.example` - Template for environment variables

## Error Handling

- The script saves state even if errors occur during tweeting
- Failed tweets are logged but don't stop processing
- Rate limiting is handled with 60-second delays

## License

WTFPL - See LICENSE file for details