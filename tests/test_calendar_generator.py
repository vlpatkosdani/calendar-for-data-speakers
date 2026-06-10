import datetime as dt
import unittest

from calendar_generator import Event, build_html, build_ics, normalize_events


class CalendarGeneratorTests(unittest.TestCase):
    def test_normalize_events_from_nested_payload(self) -> None:
        payload = {
            "props": {
                "pageProps": {
                    "events": [
                        {
                            "name": "Data Summit",
                            "startDate": "2026-10-01",
                            "endDate": "2026-10-03",
                            "cfpDeadline": "2026-07-15",
                            "url": "https://example.com/data-summit",
                        }
                    ]
                }
            }
        }

        events = normalize_events(payload)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].title, "Data Summit")
        self.assertEqual(str(events[0].cfp_deadline), "2026-07-15")

    def test_build_ics_and_html_contains_expected_entries(self) -> None:
        event = Event(
            title="Lakehouse Conf",
            conference_start=dt.date(2026, 9, 20),
            conference_end=dt.date(2026, 9, 22),
            cfp_deadline=dt.date(2026, 6, 30),
            url="https://example.com/lakehouse",
        )

        ics = build_ics([event])
        html = build_html([event])

        self.assertIn("BEGIN:VCALENDAR", ics)
        self.assertIn("SUMMARY:CFP deadline: Lakehouse Conf", ics)
        self.assertIn("SUMMARY:Conference: Lakehouse Conf", ics)
        self.assertIn('href="calendar.ics"', html)
        self.assertIn("Lakehouse Conf", html)


if __name__ == "__main__":
    unittest.main()
