import json
import unittest

from trustable_cli.metrics import commit_count


def read_file(filename):
    with open(filename) as f:
        return f.read()


class TestMetrics(unittest.TestCase):

    def test_commit_count(self):
        """Check that commit_count returns the correct number of commits."""

        events = json.loads(read_file("data/events.json"))

        self.assertEqual(commit_count(events), 9)


if __name__ == "__main__":
    unittest.main()
