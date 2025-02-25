import json
import logging
import unittest

from trustable_cli.cli import trustable_grimoirelab_score
from end_to_end.base import EndToEndTestCase

GRIMOIRELAB_URL = "http://localhost:8000"


class TestMetrics(EndToEndTestCase):
    """End to end tests for Trustable CLI metrics"""

    def test_metrics(self):
        """Check whether the metrics are correctly calculated"""

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
                self.assertEqual(len(metrics["packages"]), 2)

                self.assertIn("SPDXRef-angular", metrics["packages"])
                self.assertEqual(metrics["packages"]["SPDXRef-angular"]["repository"], "https://github.com/angular/quickstart")
                quickstart_metrics = metrics["packages"]["SPDXRef-angular"]["metrics"]
                self.assertEqual(quickstart_metrics["total_commits"], 164)
                self.assertEqual(quickstart_metrics["total_contributors"], 25)
                self.assertEqual(quickstart_metrics["pony_factor"], 2)
                self.assertEqual(quickstart_metrics["elephant_factor"], 2)
                self.assertEqual(quickstart_metrics["file_types"]["Other"], 683)
                self.assertEqual(quickstart_metrics["file_types"]["Code"], 479)
                self.assertEqual(quickstart_metrics["commit_size"]["added_lines"], 53121)
                self.assertEqual(quickstart_metrics["commit_size"]["removed_lines"], 51852)
                self.assertEqual(quickstart_metrics["message_size"]["total"], 9778)
                self.assertAlmostEqual(quickstart_metrics["message_size"]["average"], 59.6219, delta=0.1)
                self.assertEqual(quickstart_metrics["message_size"]["median"], 46)
                self.assertEqual(quickstart_metrics["developer_categories"]["core"], 3)
                self.assertEqual(quickstart_metrics["developer_categories"]["regular"], 13)
                self.assertEqual(quickstart_metrics["developer_categories"]["casual"], 9)
                self.assertAlmostEqual(quickstart_metrics["average_commits_week"], 0.06418, delta=0.1)

                self.assertIn("SPDXRef-angular-seed", metrics["packages"])
                self.assertEqual(
                    metrics["packages"]["SPDXRef-angular-seed"]["repository"], "https://github.com/angular/angular-seed"
                )
                angular_metrics = metrics["packages"]["SPDXRef-angular-seed"]["metrics"]
                self.assertEqual(angular_metrics["total_commits"], 207)
                self.assertEqual(angular_metrics["total_contributors"], 58)
                self.assertEqual(angular_metrics["pony_factor"], 5)
                self.assertEqual(angular_metrics["elephant_factor"], 2)
                self.assertEqual(angular_metrics["file_types"]["Other"], 538)
                self.assertEqual(angular_metrics["file_types"]["Code"], 2129)
                self.assertEqual(angular_metrics["commit_size"]["added_lines"], 218483)
                self.assertEqual(angular_metrics["commit_size"]["removed_lines"], 245784)
                self.assertEqual(angular_metrics["message_size"]["total"], 15488)
                self.assertAlmostEqual(angular_metrics["message_size"]["average"], 74.8212, delta=0.1)
                self.assertEqual(angular_metrics["message_size"]["median"], 45)
                self.assertEqual(angular_metrics["developer_categories"]["core"], 16)
                self.assertEqual(angular_metrics["developer_categories"]["regular"], 31)
                self.assertEqual(angular_metrics["developer_categories"]["casual"], 11)
                self.assertAlmostEqual(angular_metrics["average_commits_week"], 0.08101, delta=0.1)

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
                self.assertEqual(len(metrics["packages"]), 2)

                self.assertIn("SPDXRef-angular", metrics["packages"])
                self.assertEqual(metrics["packages"]["SPDXRef-angular"]["repository"], "https://github.com/angular/quickstart")
                quickstart_metrics = metrics["packages"]["SPDXRef-angular"]["metrics"]
                self.assertEqual(quickstart_metrics["total_commits"], 22)
                self.assertEqual(quickstart_metrics["total_contributors"], 8)
                self.assertEqual(quickstart_metrics["pony_factor"], 2)
                self.assertEqual(quickstart_metrics["elephant_factor"], 1)
                self.assertEqual(quickstart_metrics["file_types"]["Other"], 37)
                self.assertEqual(quickstart_metrics["file_types"]["Code"], 17)
                self.assertEqual(quickstart_metrics["commit_size"]["added_lines"], 269)
                self.assertEqual(quickstart_metrics["commit_size"]["removed_lines"], 103)
                self.assertEqual(quickstart_metrics["message_size"]["total"], 1866)
                self.assertAlmostEqual(quickstart_metrics["message_size"]["average"], 84.8181, delta=0.1)
                self.assertEqual(quickstart_metrics["message_size"]["median"], 57)
                self.assertEqual(quickstart_metrics["developer_categories"]["core"], 3)
                self.assertEqual(quickstart_metrics["developer_categories"]["regular"], 3)
                self.assertEqual(quickstart_metrics["developer_categories"]["casual"], 2)
                self.assertAlmostEqual(quickstart_metrics["average_commits_week"], 0.00861, delta=0.1)

                self.assertIn("SPDXRef-angular-seed", metrics["packages"])
                self.assertEqual(
                    metrics["packages"]["SPDXRef-angular-seed"]["repository"], "https://github.com/angular/angular-seed"
                )
                angular_metrics = metrics["packages"]["SPDXRef-angular-seed"]["metrics"]
                self.assertEqual(angular_metrics["total_commits"], 11)
                self.assertEqual(angular_metrics["total_contributors"], 4)
                self.assertEqual(angular_metrics["pony_factor"], 1)
                self.assertEqual(angular_metrics["elephant_factor"], 1)
                self.assertEqual(angular_metrics["file_types"]["Other"], 24)
                self.assertEqual(angular_metrics["file_types"]["Code"], 13)
                self.assertEqual(angular_metrics["commit_size"]["added_lines"], 4849)
                self.assertEqual(angular_metrics["commit_size"]["removed_lines"], 149)
                self.assertEqual(angular_metrics["message_size"]["total"], 911)
                self.assertAlmostEqual(angular_metrics["message_size"]["average"], 82.8181, delta=0.1)
                self.assertEqual(angular_metrics["message_size"]["median"], 56)
                self.assertEqual(angular_metrics["developer_categories"]["core"], 1)
                self.assertEqual(angular_metrics["developer_categories"]["regular"], 2)
                self.assertEqual(angular_metrics["developer_categories"]["casual"], 1)
                self.assertAlmostEqual(angular_metrics["average_commits_week"], 0.0043, delta=0.1)

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
                self.assertEqual(len(metrics["packages"]), 2)

                self.assertIn("SPDXRef-angular", metrics["packages"])
                self.assertEqual(metrics["packages"]["SPDXRef-angular"]["repository"], "https://github.com/angular/quickstart")
                quickstart_metrics = metrics["packages"]["SPDXRef-angular"]["metrics"]
                self.assertEqual(quickstart_metrics["total_commits"], 142)
                self.assertEqual(quickstart_metrics["total_contributors"], 20)
                self.assertEqual(quickstart_metrics["pony_factor"], 2)
                self.assertEqual(quickstart_metrics["elephant_factor"], 2)
                self.assertEqual(quickstart_metrics["file_types"]["Other"], 646)
                self.assertEqual(quickstart_metrics["file_types"]["Code"], 462)
                self.assertEqual(quickstart_metrics["commit_size"]["added_lines"], 52852)
                self.assertEqual(quickstart_metrics["commit_size"]["removed_lines"], 51749)
                self.assertEqual(quickstart_metrics["message_size"]["total"], 7912)
                self.assertAlmostEqual(quickstart_metrics["message_size"]["average"], 55.71830985915493, delta=0.1)
                self.assertEqual(quickstart_metrics["message_size"]["median"], 44)
                self.assertEqual(quickstart_metrics["developer_categories"]["core"], 3)
                self.assertEqual(quickstart_metrics["developer_categories"]["regular"], 9)
                self.assertEqual(quickstart_metrics["developer_categories"]["casual"], 8)
                self.assertAlmostEqual(quickstart_metrics["average_commits_week"], 0.003266620657925006, delta=0.1)

                self.assertIn("SPDXRef-angular-seed", metrics["packages"])
                self.assertEqual(
                    metrics["packages"]["SPDXRef-angular-seed"]["repository"], "https://github.com/angular/angular-seed"
                )
                angular_metrics = metrics["packages"]["SPDXRef-angular-seed"]["metrics"]
                self.assertEqual(angular_metrics["total_commits"], 196)
                self.assertEqual(angular_metrics["total_contributors"], 56)
                self.assertEqual(angular_metrics["pony_factor"], 5)
                self.assertEqual(angular_metrics["elephant_factor"], 2)
                self.assertEqual(angular_metrics["file_types"]["Other"], 514)
                self.assertEqual(angular_metrics["file_types"]["Code"], 2116)
                self.assertEqual(angular_metrics["commit_size"]["added_lines"], 213634)
                self.assertEqual(angular_metrics["commit_size"]["removed_lines"], 245635)
                self.assertEqual(angular_metrics["message_size"]["total"], 14577)
                self.assertAlmostEqual(angular_metrics["message_size"]["average"], 74.37244897959184, delta=0.1)
                self.assertEqual(angular_metrics["message_size"]["median"], 45)
                self.assertEqual(angular_metrics["developer_categories"]["core"], 16)
                self.assertEqual(angular_metrics["developer_categories"]["regular"], 30)
                self.assertEqual(angular_metrics["developer_categories"]["casual"], 10)
                self.assertAlmostEqual(angular_metrics["average_commits_week"], 0.0045088566827697265, delta=0.1)

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
                self.assertEqual(len(metrics["packages"]), 2)
                self.assertIn("SPDXRef-angular", metrics["packages"])
                self.assertIn("SPDXRef-angular-2", metrics["packages"])
                self.assertEqual(metrics["packages"]["SPDXRef-angular"]["repository"], "https://github.com/angular/quickstart")
                self.assertEqual(metrics["packages"]["SPDXRef-angular-2"]["repository"], "https://github.com/angular/quickstart")
                quickstart_metrics = metrics["packages"]["SPDXRef-angular"]["metrics"]
                self.assertEqual(quickstart_metrics["total_commits"], 164)
                self.assertEqual(quickstart_metrics["total_contributors"], 25)
                self.assertEqual(quickstart_metrics["pony_factor"], 2)
                self.assertEqual(quickstart_metrics["elephant_factor"], 2)
                self.assertEqual(quickstart_metrics["file_types"]["Other"], 683)
                self.assertEqual(quickstart_metrics["file_types"]["Code"], 479)
                self.assertEqual(quickstart_metrics["commit_size"]["added_lines"], 53121)
                self.assertEqual(quickstart_metrics["commit_size"]["removed_lines"], 51852)
                self.assertEqual(quickstart_metrics["message_size"]["total"], 9778)
                self.assertAlmostEqual(quickstart_metrics["message_size"]["average"], 59.6219, delta=0.1)
                self.assertEqual(quickstart_metrics["message_size"]["median"], 46)
                self.assertEqual(quickstart_metrics["developer_categories"]["core"], 3)
                self.assertEqual(quickstart_metrics["developer_categories"]["regular"], 13)
                self.assertEqual(quickstart_metrics["developer_categories"]["casual"], 9)
                self.assertAlmostEqual(quickstart_metrics["average_commits_week"], 0.06418, delta=0.1)

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
                self.assertEqual(len(metrics["packages"]), 2)

                self.assertIn("SPDXRef-angular", metrics["packages"])
                self.assertEqual(metrics["packages"]["SPDXRef-angular"]["repository"], "https://github.com/angular/quickstart")
                quickstart_metrics = metrics["packages"]["SPDXRef-angular"]["metrics"]
                self.assertEqual(quickstart_metrics["total_commits"], 164)
                self.assertEqual(quickstart_metrics["total_contributors"], 25)
                self.assertEqual(quickstart_metrics["pony_factor"], 2)
                self.assertEqual(quickstart_metrics["elephant_factor"], 2)
                self.assertEqual(quickstart_metrics["file_types"]["Other"], 683)
                self.assertEqual(quickstart_metrics["file_types"]["Code"], 479)
                self.assertEqual(quickstart_metrics["commit_size"]["added_lines"], 53121)
                self.assertEqual(quickstart_metrics["commit_size"]["removed_lines"], 51852)
                self.assertEqual(quickstart_metrics["message_size"]["total"], 9778)
                self.assertAlmostEqual(quickstart_metrics["message_size"]["average"], 59.6219, delta=0.1)
                self.assertEqual(quickstart_metrics["message_size"]["median"], 46)
                self.assertEqual(quickstart_metrics["developer_categories"]["core"], 3)
                self.assertEqual(quickstart_metrics["developer_categories"]["regular"], 13)
                self.assertEqual(quickstart_metrics["developer_categories"]["casual"], 9)
                self.assertAlmostEqual(quickstart_metrics["average_commits_week"], 0.06418, delta=0.1)

                self.assertIn("SPDXRef-sql-dk", metrics["packages"])
                self.assertEqual(metrics["packages"]["SPDXRef-sql-dk"]["metrics"], None)


if __name__ == "__main__":
    unittest.main()
