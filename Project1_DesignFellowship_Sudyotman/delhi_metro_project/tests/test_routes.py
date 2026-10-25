import unittest
from backend.app import GRAPH

class RouteTests(unittest.TestCase):
    def test_gtfs_graph_loads(self):
        self.assertEqual(len(GRAPH.stations), 262)
        self.assertEqual(len(GRAPH.lines), 12)
        self.assertGreater(sum(map(len, GRAPH.adjacency.values())), 500)
    def test_real_coordinates_and_line_shapes(self):
        azadpur = GRAPH.stations['Azadpur']
        self.assertAlmostEqual(azadpur.lat, 28.707287, places=5)
        self.assertIn('Yellow Line', azadpur.lines)
        self.assertTrue(all(len(line.get('shape', [])) > 1 for line in GRAPH.lines.values()))
    def test_station_search(self):
        self.assertTrue(any(x['name'] == 'Rajiv Chowk' for x in GRAPH.search('Rajiv')))
    def test_azadpur_to_iffco_chowk(self):
        r = GRAPH.route('Azadpur', 'IFFCO Chowk')
        self.assertEqual(r['station_names'][0], 'Azadpur')
        self.assertEqual(r['station_names'][-1], 'IFFCO Chowk')
        self.assertIn('Yellow Line', r['lines'])
        self.assertGreater(r['travel_time_minutes'], 0)
    def test_transfer_route(self):
        r = GRAPH.route('Rithala', 'AIIMS')
        self.assertTrue(r['interchanges'])
        self.assertEqual(r['station_names'][0], 'Rithala')
    def test_missing_station(self):
        with self.assertRaises(ValueError): GRAPH.route('Made Up Station', 'AIIMS')
    def test_same_station(self):
        with self.assertRaises(ValueError): GRAPH.route('AIIMS', 'AIIMS')

if __name__ == '__main__': unittest.main()
