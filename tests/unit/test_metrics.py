# -*- coding: utf-8 -*-
#
# Copyright (C) Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import json
import unittest

from trustable_cli.metrics import GitEventsAnalyzer


def read_file(filename):
    with open(filename) as f:
        return f.read()


class TestGitEventsAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = GitEventsAnalyzer()
        self.events = json.loads(read_file("data/events.json"))

    def test_commit_count(self):
        """Test that the commit count is calculated correctly"""

        self.analyzer.process_events(self.events)
        self.assertEqual(self.analyzer.get_commit_count(), 9)

    def test_contributor_count(self):
        """Test that the contributor count is calculated correctly"""

        self.analyzer.process_events(self.events)
        self.assertEqual(self.analyzer.get_contributor_count(), 3)

        extra_events = [
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            }
        ]
        self.analyzer.process_events(extra_events)
        self.assertEqual(self.analyzer.get_contributor_count(), 4)

    def test_get_pony_factor(self):
        """Test the computation of the pony factor is correct"""

        self.assertEqual(self.analyzer.get_pony_factor(), 0)

        self.analyzer.process_events(self.events)
        self.assertEqual(self.analyzer.get_pony_factor(), 1)

        # Include commits from another author to increase the pony factor
        extra_events = [
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
        ]
        self.analyzer.process_events(extra_events)
        self.assertEqual(self.analyzer.get_pony_factor(), 2)

    def test_get_elephant_factor(self):
        """Test the computation of the elephant factor is correct"""

        self.assertEqual(self.analyzer.get_elephant_factor(), 0)

        self.analyzer.process_events(self.events)
        self.assertEqual(self.analyzer.get_elephant_factor(), 1)

        # Include commits from another company to increase the elephant factor.
        extra_events = [
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
        ]
        self.analyzer.process_events(extra_events)
        self.assertEqual(self.analyzer.get_elephant_factor(), 2)

    def test_file_type_metrics(self):
        """Test that file type metrics are calculated correctly"""

        self.assertEqual(self.analyzer.get_file_type_metrics(), {})

        self.analyzer.process_events(self.events)

        file_metrics = self.analyzer.get_file_type_metrics()
        self.assertEqual(file_metrics.get("code", 0), 54)
        self.assertEqual(file_metrics.get("other", 0), 24)

    def test_commit_size_metrics(self):
        """Test that commit size metrics are calculated correctly"""

        self.assertEqual(self.analyzer.get_commit_size_metrics(), {"added_lines": 0, "removed_lines": 0})

        self.analyzer.process_events(self.events)

        commit_size = self.analyzer.get_commit_size_metrics()
        self.assertEqual(commit_size["added_lines"], 5352)
        self.assertEqual(commit_size["removed_lines"], 562)

    def test_message_size_metrics(self):
        """Test that message size metrics are calculated correctly"""

        self.analyzer.process_events(self.events)

        metrics = self.analyzer.get_message_size_metrics()
        self.assertEqual(metrics["total"], 1891)
        self.assertAlmostEqual(metrics["mean"], 210.11, delta=0.1)
        self.assertEqual(metrics["median"], 229)

    def test_get_commits_week_mean(self):
        """Test whether the average (mean) commits per week is calculated correctly"""

        self.analyzer.process_events(self.events)
        avg = self.analyzer.get_commits_week_mean(days_interval=30)
        self.assertAlmostEqual(avg, 9 / 30 / 7, delta=0.1)

    def test_get_developer_categories(self):
        """Test if the developer categories are calculated correctly"""

        categories = self.analyzer.get_developer_categories()
        self.assertDictEqual(categories, {"core": 0, "regular": 0, "casual": 0})

        self.analyzer.process_events(self.events)
        categories = self.analyzer.get_developer_categories()
        self.assertDictEqual(categories, {"core": 1, "regular": 1, "casual": 1})

        # Add a core developer to change the categories
        extra_events = [
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
        ]

        self.analyzer.process_events(extra_events)
        categories = self.analyzer.get_developer_categories()
        self.assertDictEqual(categories, {"core": 2, "regular": 1, "casual": 1})

    def test_get_categories_one_developer(self):
        """Test if the categories are calculated correctly when there is only one developer"""

        categories = self.analyzer.get_developer_categories()
        self.assertDictEqual(categories, {"core": 0, "regular": 0, "casual": 0})

        # Add a core developer with 100% of the contributions
        extra_events = [
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
        ]

        self.analyzer.process_events(extra_events)
        categories = self.analyzer.get_developer_categories()
        self.assertDictEqual(categories, {"core": 1, "regular": 0, "casual": 0})

    def test_get_developer_categories_tied(self):
        """Test if the categories are calculated correctly when the core developers have the same contributions"""

        categories = self.analyzer.get_developer_categories()
        self.assertDictEqual(categories, {"core": 0, "regular": 0, "casual": 0})

        # Add core developers with the same number of contributions
        extra_events = [
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 2 <author2@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 3 <author3@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 4 <author4@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 5 <author5@example_new.com>", "message": "Another commit"},
            },
        ]

        self.analyzer.process_events(extra_events)
        categories = self.analyzer.get_developer_categories()
        self.assertDictEqual(categories, {"core": 4, "regular": 1, "casual": 0})


if __name__ == "__main__":
    unittest.main()
