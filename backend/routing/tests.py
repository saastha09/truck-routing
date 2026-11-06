from django.test import SimpleTestCase

from .geo import sample
from .planner import _summary, rank_key
from .risk import HIGH, LOW, MODERATE, NO_TRAVEL, SEVERE, classify


class RiskTests(SimpleTestCase):
    def test_wind_bands(self):
        for wind, want in [(10, LOW), (24.9, LOW), (25, MODERATE), (34.9, MODERATE),
                           (35, HIGH), (45, SEVERE), (54.9, SEVERE), (55, NO_TRAVEL)]:
            self.assertEqual(classify(wind, 0, 0, 0), want)

    def test_rain_and_snow(self):
        self.assertEqual(classify(0, 0.09, 0, 0), LOW)
        self.assertEqual(classify(0, 0.10, 0, 0), MODERATE)
        self.assertEqual(classify(0, 0.25, 0, 0), HIGH)
        self.assertEqual(classify(0, 0.3, 0, 0), HIGH)
        self.assertEqual(classify(0, 0.50, 0, 0), SEVERE)
        self.assertEqual(classify(0, 1.0, 0, 0), SEVERE)
        self.assertEqual(classify(0, 1.1, 0, 0), NO_TRAVEL)
        self.assertEqual(classify(0, 0, 0.5, 0), MODERATE)
        self.assertEqual(classify(0, 0, 2.5, 0), SEVERE)
        self.assertEqual(classify(0, 0, 3.0, 0), SEVERE)
        self.assertEqual(classify(0, 0, 3.01, 0), NO_TRAVEL)

    def test_worst_condition_wins(self):
        self.assertEqual(classify(30, 0.3, 0, 0), HIGH)

    def test_load_rules(self):
        self.assertEqual(classify(50, 0, 0, 30000), SEVERE)
        self.assertEqual(classify(50, 0, 0, 30001), NO_TRAVEL)
        self.assertEqual(classify(40, 0, 0, 40000), HIGH)
        self.assertEqual(classify(40, 0, 0, 40001), SEVERE)
        self.assertEqual(classify(55, 0, 0, 0), NO_TRAVEL)
        self.assertEqual(classify(40, 1.1, 0, 40001), NO_TRAVEL)


class SampleTests(SimpleTestCase):
    def test_checkpoints(self):
        # ~1 degree of latitude is ~69 miles
        pts, total = sample([(0, 0), (1, 0)], 25)
        self.assertEqual([round(p["mile"]) for p in pts], [0, 25, 50, round(total)])

    def test_short_route(self):
        pts, total = sample([(0, 0), (0.01, 0)], 25)
        self.assertEqual(len(pts), 2)
        self.assertEqual(pts[0]["mile"], 0)
        self.assertAlmostEqual(pts[-1]["mile"], total)
        self.assertGreater(total, 0)

    def test_zero_length(self):
        pts, total = sample([(40.0, -88.0), (40.0, -88.0)], 10)
        self.assertEqual(total, 0)
        self.assertEqual(len(pts), 1)


class ScoreTests(SimpleTestCase):
    def test_summary_weights_miles(self):
        s = _summary([
            {"risk": SEVERE, "segment_miles": 10},
            {"risk": HIGH, "segment_miles": 20},
            {"risk": LOW, "segment_miles": 70},
        ])
        self.assertEqual(s["severe_miles"], 10)
        self.assertEqual(s["high_miles"], 20)
        self.assertEqual(s["no_travel_miles"], 0)
        self.assertAlmostEqual(s["avg_risk"], (3 * 10 + 2 * 20) / 100, places=3)

    def test_recommend_severe_beats_high_and_time(self):
        long_but_safer = {
            "id": 0, "no_travel_miles": 0, "severe_miles": 0, "high_miles": 30,
            "avg_risk": 1.2, "hours": 12,
        }
        short_but_severe = {
            "id": 1, "no_travel_miles": 0, "severe_miles": 5, "high_miles": 0,
            "avg_risk": 0.4, "hours": 8,
        }
        best = min([short_but_severe, long_but_safer], key=rank_key)
        self.assertEqual(best["id"], 0)

    def test_recommend_no_travel_beats_severe(self):
        a = {"id": 0, "no_travel_miles": 2, "severe_miles": 0, "high_miles": 0, "avg_risk": 0.1, "hours": 5}
        b = {"id": 1, "no_travel_miles": 0, "severe_miles": 8, "high_miles": 0, "avg_risk": 0.5, "hours": 9}
        self.assertEqual(min([a, b], key=rank_key)["id"], 1)
