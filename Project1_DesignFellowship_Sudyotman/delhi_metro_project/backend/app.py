"""Delhi Metro Route Planner. GTFS-derived graph, Dijkstra, and local REST API."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json, heapq, sys, threading, webbrowser

# In a PyInstaller build, bundled assets live under sys._MEIPASS. In source mode,
# the project root is the parent of the backend directory.
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
DATA_PATH = ROOT / 'data' / 'metro_network.json'
TRANSFER_MINUTES = 4.0

class Station:
    def __init__(self, row):
        self.id = str(row['id']); self.name = row['name']
        self.lat = float(row['lat']); self.lon = float(row['lon'])
        self.lines = list(row.get('lines', []))

class Connection:
    def __init__(self, a, b, minutes, line):
        self.stationA = a; self.stationB = b
        self.travelTime = float(minutes); self.line = line

class MetroGraph:
    def __init__(self, payload):
        self.metadata = payload.get('metadata', {})
        self.stations = {s['name']: Station(s) for s in payload['stations']}
        self.by_id = {s.id: s for s in self.stations.values()}
        self.lines = payload['lines']
        self.adjacency = {name: [] for name in self.stations}
        self.name_index = {name.casefold(): name for name in self.stations}
        # Connections are derived from consecutive stops in GTFS trips. Multiple
        # observations are reduced to a median scheduled segment duration.
        for row in payload.get('connections', []):
            a = self.by_id.get(str(row['from'])); b = self.by_id.get(str(row['to']))
            if not a or not b: continue
            self.adjacency[a.name].append(Connection(a.name, b.name, row['minutes'], row['line']))
        self._deduplicate_edges()

    def _deduplicate_edges(self):
        # Keep one edge per neighbour and line; the feed can contain many trips.
        for name, edges in self.adjacency.items():
            best = {}
            for e in edges:
                k = (e.stationB, e.line)
                if k not in best or e.travelTime < best[k].travelTime: best[k] = e
            self.adjacency[name] = list(best.values())

    @staticmethod
    def station_json(s):
        return {'id': s.id, 'name': s.name, 'lat': s.lat, 'lon': s.lon, 'lines': s.lines}

    def search(self, query):
        q = query.strip().casefold()
        if not q: return []
        exact = self.name_index.get(q)
        names = [exact] if exact else [n for n in self.stations if n.casefold().startswith(q) or q in n.casefold()]
        return [self.station_json(self.stations[n]) for n in names[:15]]

    def network(self):
        return {'metadata': self.metadata,
                'stations': [self.station_json(s) for s in self.stations.values()],
                'lines': self.lines}

    def route(self, source, destination):
        if source not in self.stations: raise ValueError(f'Unknown source station: {source}')
        if destination not in self.stations: raise ValueError(f'Unknown destination station: {destination}')
        if source == destination: raise ValueError('Source and destination must be different stations.')
        # State includes current line, so line changes are explicitly priced.
        start = (source, None); distances = {start: 0.0}; previous = {}
        heap = [(0.0, source, '')]; final = None
        while heap:
            cost, station, line_key = heapq.heappop(heap)
            line = line_key or None; state = (station, line)
            if cost > distances.get(state, float('inf')) + 1e-9: continue
            if station == destination: final = state; break
            for edge in self.adjacency.get(station, []):
                transfer = TRANSFER_MINUTES if line is not None and line != edge.line else 0.0
                next_state = (edge.stationB, edge.line)
                new_cost = cost + edge.travelTime + transfer
                if new_cost + 1e-9 < distances.get(next_state, float('inf')):
                    distances[next_state] = new_cost; previous[next_state] = (state, edge)
                    heapq.heappush(heap, (new_cost, edge.stationB, edge.line))
        if final is None: return None
        edges = []; cur = final
        while cur != start:
            if cur not in previous: return None
            prior, edge = previous[cur]; edges.append(edge); cur = prior
        edges.reverse()
        names = [source] + [e.stationB for e in edges]
        interchanges = []; used = []
        for i, edge in enumerate(edges):
            if edge.line not in used: used.append(edge.line)
            if i + 1 < len(edges) and edge.line != edges[i+1].line:
                interchanges.append({'station': edge.stationB, 'from_line': edge.line, 'to_line': edges[i+1].line})
        total = sum(e.travelTime for e in edges) + TRANSFER_MINUTES * len(interchanges)
        return {'source': source, 'destination': destination,
                'stations': [self.station_json(self.stations[n]) for n in names],
                'station_names': names, 'lines': used, 'interchanges': interchanges,
                'travel_time_minutes': round(total, 1),
                'segments': [{'from': e.stationA, 'to': e.stationB, 'line': e.line,
                              'color': self.lines[e.line]['color'], 'minutes': e.travelTime} for e in edges],
                'data_note': 'Scheduled segment-time estimates from the supplied GTFS feed; not live times.'}

with open(DATA_PATH, encoding='utf-8') as f: DATA = json.load(f)
GRAPH = MetroGraph(DATA)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs): super().__init__(*args, directory=str(ROOT/'frontend'), **kwargs)
    def log_message(self, fmt, *args): pass
    def send_json(self, data, status=200):
        body = json.dumps(data).encode(); self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body))); self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers(); self.wfile.write(body)
    def do_OPTIONS(self):
        self.send_response(204); self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'); self.end_headers()
    def do_GET(self):
        u = urlparse(self.path)
        if u.path == '/api/health': return self.send_json({'status':'ok','stations':len(GRAPH.stations),'lines':len(GRAPH.lines),'metadata':GRAPH.metadata})
        if u.path == '/api/network': return self.send_json(GRAPH.network())
        if u.path == '/api/stations/search': return self.send_json({'results':GRAPH.search(parse_qs(u.query).get('q',[''])[0])})
        if u.path.startswith('/api/'): return self.send_json({'error':'API endpoint not found'},404)
        if u.path == '/': self.path = '/index.html'
        return super().do_GET()
    def do_POST(self):
        if urlparse(self.path).path != '/api/route': return self.send_json({'error':'API endpoint not found'},404)
        try:
            n = int(self.headers.get('Content-Length','0')); body = json.loads(self.rfile.read(n) or b'{}')
        except Exception: return self.send_json({'error':'Request body must be valid JSON.'},400)
        source = (body.get('source') or '').strip(); destination = (body.get('destination') or '').strip()
        if not source: return self.send_json({'error':'Please select a source station.'},400)
        if not destination: return self.send_json({'error':'Please select a destination station.'},400)
        try: result = GRAPH.route(source, destination)
        except ValueError as e: return self.send_json({'error':str(e)},400)
        if result is None: return self.send_json({'error':'No route was found between these stations.'},404)
        return self.send_json(result)

if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1',5000), Handler)
    url = 'http://127.0.0.1:5000'
    print(f'Delhi Metro Route Planner: {url}')
    # Open the browser only after the server has been created.
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: print('\nServer stopped.')
    finally: server.server_close()
