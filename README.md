# Who Funds Who

A project to make campaign finance data more accessible and understandable. Data is sourced from the Federal Election Commission (FEC)
. Explore politicians and PACs to see who funds who in U.S. elections.

## Setup

**1. Download and load FEC data into SQLite:**

```sh
python scripts/load_fec_datasets.py --download
```

This downloads the four required datasets from FEC.gov into `datasets/` and loads them into `fec.db`. Re running skips already downloaded files.

**2. Export data to JSON for the frontend:**

```sh
python scripts/export_db_to_json.py
```

**3. Install frontend dependencies and run dev server:**

```sh
cd frontend
npm install
npm run dev
```

## Limitations

- This only works for national elections and does not cover state and local elections.
- For now, this is only a personal project and only has 2025–2026 data.

## Architecture

Originally, I was going to deploy this using dynamic data, where we:
1. Download several datasets from the FEC.gov website
2. Process and store them using SQLite
3. Serve them dynamically

However, in order to keep the data static and deploy on GitHub Pages, I changed the approach to pre-processing the data and embedding it in the frontend as JSON files.

## Building

```sh
cd frontend
npm run build
npm run preview
```
