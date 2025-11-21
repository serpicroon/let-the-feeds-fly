# Let the Feeds Fly 🕊️

A lightweight RSS delay proxy service built with FastAPI and SQLite.

## Features

- **Delay RSS Feeds**: Configure arbitrary delay times (e.g., "wait 12 hours before showing new posts").
- **No Data Loss**: Uses a local SQLite database to store entries, ensuring items aren't lost even if they disappear from the upstream feed during the delay period.
- **XML Pass-Through**: Stores original XML/JSON content to ensure high-fidelity feed reconstruction.
- **HTTP Caching**: Supports ETag and Last-Modified headers for both upstream (conditional requests) and downstream (304 responses) to save bandwidth.
- **Format Preservation**: Outputs the same format as the upstream feed (RSS 2.0, Atom, or JSON Feed).
