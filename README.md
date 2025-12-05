# Let the Feeds Fly 🕊️

A lightweight RSS delay proxy service built with FastAPI and SQLite.

## Why?

Ever subscribed to a forum's "latest posts" RSS feed, only to read threads with barely any replies? You're catching discussions too early—missing the vibrant conversations that develop hours later.

**Let the Feeds Fly** adds a configurable delay to your RSS feeds. Set a 6-hour delay for forum posts to gather thoughtful responses, or wait a day for news articles to mature their comment sections. Enjoy richer, more complete discussions.

**Perfect for:**
- 📝 Forum threads (HackerNews, Reddit, V2EX)
- 📰 News sites with active comments
- 🎯 Any feed where conversation matters

## Features

- **Delay RSS Feeds**: Configure arbitrary delay times (e.g., "wait 12 hours before showing new posts").
- **No Data Loss**: Uses a local SQLite database to store entries, ensuring items aren't lost even if they disappear from the upstream feed during the delay period.
- **XML Pass-Through**: Stores original XML/JSON content to ensure high-fidelity feed reconstruction.
- **HTTP Caching**: Supports ETag and Last-Modified headers for both upstream (conditional requests) and downstream (304 responses) to save bandwidth.
- **Format Preservation**: Outputs the same format as the upstream feed (RSS 2.0, Atom, or JSON Feed).

## Usage

```
GET /feed?url=<RSS_URL>&delay=<NUMBER>&unit=<UNIT>&limit=<NUMBER>
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `url` | ✅ | - | Original RSS feed URL |
| `delay` | - | `1` | Delay duration |
| `unit` | - | `hour` | `minute` / `hour` / `day` |
| `limit` | - | `20` | Max entries (1-200) |

**Example:** Delay a forum feed by 6 hours:
```
http://localhost:8000/feed?url=https://linux.do/latest.rss&delay=6&unit=hour
```

Add the proxy URL to your RSS reader. It returns the same format as the original feed.

## Deployment

### Docker (Recommended)

```bash
docker compose up -d
```

See [`docker-compose.yaml`](docker-compose.yaml) for configuration.

### Manual

```bash
pip install -r requirements.txt
python run.py
```

The server runs on `http://localhost:8000` by default.
