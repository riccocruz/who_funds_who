# Who Funds Who

A project to make campaign finance data more accessible and understandable. Data is sourced from the Federal Election Commission (FEC) and updated daily. Explore politicians and PACs to see who funds who in U.S. elections.

## Limitations

- This only works for national elections and does not cover state and local elections.
- For now, this is only a personal project and only has 2025–2026 data.

## Architecture

Originally, I was going to deploy this using dynamic data, where we:
1. Download several datasets from the FEC.gov website
2. Process and store them using SQLite
3. Serve them dynamically

However, in order to keep the data static and deploy on GitHub Pages, I changed the approach to pre-processing the data and embedding it in the frontend as JSON files.

## Development

```sh
npm install
npm run dev
```

## Building

```sh
npm run build
npm run preview
```
