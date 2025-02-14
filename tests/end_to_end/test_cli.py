import json
import logging
import unittest

from trustable_cli.cli import trustable_grimoirelab_score
from end_to_end.base import EndToEndTestCase

GRIMOIRELAB_URL = "http://localhost:8000"


class TestMetrics(EndToEndTestCase):
    """End to end tests for Trustable CLI metrics"""

    def test_commit_count(self):
        """Check if it returns the number of commits of one repository from a valid file"""

        with self.assertLogs(logging.getLogger()) as logger:
            result = self.runner.invoke(
                trustable_grimoirelab_score,
                [
                    "./data/archived_repos.spdx.xml",
                    "--grimoirelab-url",
                    GRIMOIRELAB_URL,
                    "--grimoirelab-user",
                    "admin",
                    "--grimoirelab-password",
                    "admin",
                    "--opensearch-url",
                    self.opensearch_url,
                    "--opensearch-index",
                    "events",
                    "--output",
                    self.temp_file.name,
                    "--from-date=2000-01-01",
                ],
            )
            self.assertEqual(result.exit_code, 0)
            # Check logs
            self.assertIn("INFO:root:Parsing file ./data/archived_repos.spdx.xml", logger.output)
            self.assertIn("INFO:root:Found 2 git repositories", logger.output)
            self.assertIn("INFO:root:Scheduling tasks", logger.output)
            self.assertIn("INFO:root:Generating metrics", logger.output)

            # Check metrics
            with open(self.temp_file.name) as f:
                metrics = json.load(f)
                self.assertEqual(len(metrics["repositories"]), 2)
                self.assertIn("https://github.com/angular/quickstart", metrics["repositories"])
                self.assertEqual(metrics["repositories"]["https://github.com/angular/quickstart"]["metrics"]["num_commits"], 164)
                self.assertIn("https://github.com/angular/angular-seed", metrics["repositories"])
                self.assertEqual(
                    metrics["repositories"]["https://github.com/angular/angular-seed"]["metrics"]["num_commits"], 207
                )

    def test_from_date(self):
        """Check if it returns the number of commits of one repository from a particular date"""

        with self.assertLogs(logging.getLogger()) as logger:
            result = self.runner.invoke(
                trustable_grimoirelab_score,
                [
                    "./data/archived_repos.spdx.xml",
                    "--grimoirelab-url",
                    GRIMOIRELAB_URL,
                    "--grimoirelab-user",
                    "admin",
                    "--grimoirelab-password",
                    "admin",
                    "--opensearch-url",
                    self.opensearch_url,
                    "--opensearch-index",
                    "events",
                    "--output",
                    self.temp_file.name,
                    "--from-date=2017-01-01",
                ],
            )
            self.assertEqual(result.exit_code, 0)
            # Check logs
            self.assertIn("INFO:root:Parsing file ./data/archived_repos.spdx.xml", logger.output)
            self.assertIn("INFO:root:Found 2 git repositories", logger.output)
            self.assertIn("INFO:root:Scheduling tasks", logger.output)
            self.assertIn("INFO:root:Generating metrics", logger.output)

            # Check metrics
            with open(self.temp_file.name) as f:
                metrics = json.load(f)
                self.assertEqual(len(metrics["repositories"]), 2)
                self.assertIn("https://github.com/angular/quickstart", metrics["repositories"])
                self.assertEqual(metrics["repositories"]["https://github.com/angular/quickstart"]["metrics"]["num_commits"], 22)
                self.assertIn("https://github.com/angular/angular-seed", metrics["repositories"])
                self.assertEqual(metrics["repositories"]["https://github.com/angular/angular-seed"]["metrics"]["num_commits"], 11)

    def test_to_date(self):
        """Check if it returns the number of commits of one repository up to a particular date"""

        with self.assertLogs(logging.getLogger()) as logger:
            result = self.runner.invoke(
                trustable_grimoirelab_score,
                [
                    "./data/archived_repos.spdx.xml",
                    "--grimoirelab-url",
                    GRIMOIRELAB_URL,
                    "--grimoirelab-user",
                    "admin",
                    "--grimoirelab-password",
                    "admin",
                    "--opensearch-url",
                    self.opensearch_url,
                    "--opensearch-index",
                    "events",
                    "--output",
                    self.temp_file.name,
                    "--from-date=2000-01-01",
                    "--to-date=2017-01-01",
                ],
            )
            self.assertEqual(result.exit_code, 0)
            # Check logs
            self.assertIn("INFO:root:Parsing file ./data/archived_repos.spdx.xml", logger.output)
            self.assertIn("INFO:root:Found 2 git repositories", logger.output)
            self.assertIn("INFO:root:Scheduling tasks", logger.output)
            self.assertIn("INFO:root:Generating metrics", logger.output)

            # Check metrics
            with open(self.temp_file.name) as f:
                metrics = json.load(f)
                print(metrics)
                self.assertEqual(len(metrics["repositories"]), 2)
                self.assertIn("https://github.com/angular/quickstart", metrics["repositories"])
                self.assertEqual(metrics["repositories"]["https://github.com/angular/quickstart"]["metrics"]["num_commits"], 142)
                self.assertIn("https://github.com/angular/angular-seed", metrics["repositories"])
                self.assertEqual(
                    metrics["repositories"]["https://github.com/angular/angular-seed"]["metrics"]["num_commits"], 196
                )

    def test_duplicate_repo(self):
        """Check if it ignores duplicated URLs"""

        with self.assertLogs(logging.getLogger()) as logger:
            result = self.runner.invoke(
                trustable_grimoirelab_score,
                [
                    "./data/duplicate_repo.spdx.xml",
                    "--grimoirelab-url",
                    GRIMOIRELAB_URL,
                    "--grimoirelab-user",
                    "admin",
                    "--grimoirelab-password",
                    "admin",
                    "--opensearch-url",
                    self.opensearch_url,
                    "--opensearch-index",
                    "events",
                    "--output",
                    self.temp_file.name,
                    "--from-date=2000-01-01",
                ],
            )
            self.assertEqual(result.exit_code, 0)
            # Check logs
            self.assertIn("INFO:root:Parsing file ./data/duplicate_repo.spdx.xml", logger.output)
            self.assertIn("INFO:root:Found 1 git repositories", logger.output)
            self.assertIn("INFO:root:Scheduling tasks", logger.output)
            self.assertIn("INFO:root:Generating metrics", logger.output)

            # Check metrics
            with open(self.temp_file.name) as f:
                metrics = json.load(f)
                self.assertEqual(len(metrics["repositories"]), 1)
                self.assertIn("https://github.com/angular/quickstart", metrics["repositories"])
                self.assertEqual(metrics["repositories"]["https://github.com/angular/quickstart"]["metrics"]["num_commits"], 164)

    def test_non_git_repo(self):
        """Check if it flags non-git dependencies"""

        with self.assertLogs(logging.getLogger()) as logger:
            result = self.runner.invoke(
                trustable_grimoirelab_score,
                [
                    "./data/mercurial_repo.spdx.xml",
                    "--grimoirelab-url",
                    GRIMOIRELAB_URL,
                    "--grimoirelab-user",
                    "admin",
                    "--grimoirelab-password",
                    "admin",
                    "--opensearch-url",
                    self.opensearch_url,
                    "--opensearch-index",
                    "events",
                    "--output",
                    self.temp_file.name,
                    "--from-date=2000-01-01",
                ],
            )
            self.assertEqual(result.exit_code, 0)
            # Check logs
            self.assertIn("INFO:root:Parsing file ./data/mercurial_repo.spdx.xml", logger.output)
            self.assertIn("WARNING:root:Could not find a git repository for sql-dk", logger.output)
            self.assertIn("INFO:root:Found 1 git repositories", logger.output)
            self.assertIn("INFO:root:Scheduling tasks", logger.output)
            self.assertIn("INFO:root:Generating metrics", logger.output)

            # Check metrics
            with open(self.temp_file.name) as f:
                metrics = json.load(f)
                self.assertEqual(len(metrics["repositories"]), 1)
                self.assertIn("https://github.com/angular/quickstart", metrics["repositories"])
                self.assertEqual(metrics["repositories"]["https://github.com/angular/quickstart"]["metrics"]["num_commits"], 164)


if __name__ == "__main__":
    unittest.main()
