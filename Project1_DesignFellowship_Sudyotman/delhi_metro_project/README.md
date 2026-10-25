# Delhi Metro Route Planner and Visualiser

**The Design Fellowship — CS-3810 Design Practices in Computer Science**

This runnable project uses the GTFS archive supplied for this project (`source_data/metro_gtfs_original.zip`) to build a route graph and geographic map data. It replaces the previous hand-assembled prototype dataset.

## Run on Windows
1. Install Python 3.10+ from https://www.python.org/downloads/ (enable “Add Python to PATH”). No Python packages need to be installed.
2. Extract the ZIP.
3. Double-click `run_windows.bat`.
4. Open http://127.0.0.1:5000 in your browser.

## Run on macOS/Linux
Install Python 3.10+, open a terminal in this folder, then run:
```bash
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```
Open http://127.0.0.1:5000.

## Features
- Search and select stations from the supplied GTFS stop list.
- Geographic station coordinates and actual GTFS route-shape points.
- Dijkstra's algorithm over a weighted adjacency list built from consecutive stops in GTFS trips.
- Segment weights derived from scheduled arrival/departure times observed across trips, using the median duration for each connection.
- A four-minute estimated line-change penalty in the route objective.
- Reconstructed station sequence, line list, interchange instructions, and estimated journey time.
- Leaflet map, station markers, route highlighting, pan/zoom, and validation/error feedback.
- Local REST API: `GET /api/health`, `GET /api/network`, `GET /api/stations/search?q=...`, `POST /api/route`.
- Automated tests: `python -m unittest discover -s tests -v`.

## Dataset notes
The supplied archive contains 262 stops, 12 route entries, 5,438 trips, and 128,434 stop-time records. The included GTFS calendar covers **1 January 2019 through 31 December 2025**. The source archive is retained in `source_data/`; `data/metro_network.json` is the preprocessed runtime graph and route-shape dataset.

This feed is a static schedule, not live operational data, and it should not be described as a current 2026 timetable. Route entries can include separate branches; interchange penalties are an estimate. GTFS schedule times are used as edge weights, so results are minimum estimated-time routes under this model, not guaranteed real-world journey times. The displayed base map tiles require an internet connection.

## Architecture
- `frontend/index.html`: React + Leaflet user interface.
- `backend/app.py`: station/connection model, Dijkstra route finder, interchange detection, and REST API.
- `data/metro_network.json`: GTFS-derived stations, route shapes, and scheduled connection weights.
- `source_data/metro_gtfs_original.zip`: original feed archive supplied for this build.
- `tests/test_routes.py`: graph, station search, routing, and validation tests.

## Complexity
For V stations and E direct connections, heap-based Dijkstra uses O((V + E) log V) time in the usual implementation and O(V + E) graph storage. Exact station lookup uses a hash map; partial search scans station names. Interchange detection is linear in the reconstructed path length.
