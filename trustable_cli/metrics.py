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

from __future__ import annotations

import datetime
import logging
import re
import typing

from collections import Counter

import certifi

from opensearchpy import OpenSearch, Search


logging.getLogger("opensearch").setLevel(logging.WARNING)


if typing.TYPE_CHECKING:
    from typing import Any


COMMIT_EVENT_TYPE = "org.grimoirelab.events.git.commit"
AUTHOR_FIELD = "Author"
FILE_TYPE_CODE = (
    r"\.bazel$|\.bazelrc$|\.bzl$|\.c$|\.cc$|\.cp$|\.cpp$|\.cxx$|\.c\+\+$|"
    r"\.go$|\.h$|\.js$|\.mjs$|\.java$|\.py$|\.rs$|\.sh$|\.tf$|\.ts$"
)


class GitEventsAnalyzer:
    def __init__(self):
        self.total_commits: int = 0
        self.contributors: Counter = Counter()
        self.companies: Counter = Counter()
        self.file_types: dict = Counter()
        self.added_lines: int = 0
        self.removed_lines: int = 0
        self.messages_sizes: list = []

    def process_events(self, events: iter(dict[str, Any])):
        for event in events:
            if event["type"] != COMMIT_EVENT_TYPE:
                continue

            event_data = event.get("data")

            self.total_commits += 1
            self.contributors[event_data[AUTHOR_FIELD]] += 1
            self._update_companies(event_data)
            self._update_file_metrics(event_data)
            self._update_message_size_metrics(event_data)

    def get_commit_count(self):
        return self.total_commits

    def get_contributor_count(self):
        return len(self.contributors)

    def get_pony_factor(self):
        """Number of individuals producing up to 50% of the total number of code contributions"""

        partial_contributions = 0
        pony_factor = 0

        if len(self.contributors) == 0:
            return 0

        for _, contributions in self.contributors.most_common():
            partial_contributions += contributions
            pony_factor += 1
            if partial_contributions / self.total_commits > 0.5:
                break

        return pony_factor

    def get_elephant_factor(self):
        """Number of companies producing up to 50% of the total number of code contributions"""

        partial_contributions = 0
        elephant_factor = 0

        if len(self.companies) == 0:
            return 0

        for _, contributions in self.companies.most_common():
            partial_contributions += contributions
            elephant_factor += 1
            if partial_contributions / self.total_commits > 0.5:
                break

        return elephant_factor

    def get_file_type_metrics(self):
        """Get the file type metrics"""

        return dict(self.file_types)

    def get_commit_size_metrics(self):
        """Get the commit size metrics"""

        metrics = {
            "added_lines": self.added_lines,
            "removed_lines": self.removed_lines,
        }
        return metrics

    def get_message_size_metrics(self):
        """Get the message size metrics"""

        total = sum(self.messages_sizes)
        number = len(self.messages_sizes)
        mean = 0
        median = 0
        if number > 0:
            mean = total / number
            median = sorted(self.messages_sizes)[number // 2]

        metrics = {
            "total": total,
            "mean": mean,
            "median": median,
        }
        return metrics

    def get_commits_week_mean(self, days_interval: int):
        """
        Get the average (mean) number of commits per week

        :param days_interval: Interval of days to calculate the mean
        """
        return self.total_commits / days_interval / 7

    def get_developer_categories(self):
        """Return the number of core, regular and casual developers"""

        core = 0
        regular = 0
        casual = 0
        regular_threshold = int(0.8 * self.total_commits)
        casual_threshold = int(0.95 * self.total_commits)
        acc_commits = 0
        last_core_contribution = 0

        for _, contributions in self.contributors.most_common():
            acc_commits += contributions

            if acc_commits <= regular_threshold or contributions > last_core_contribution:
                last_core_contribution = contributions
                core += 1
            elif acc_commits <= casual_threshold or contributions == last_core_contribution:
                regular += 1
            else:
                casual += 1

        return {
            "core": core,
            "regular": regular,
            "casual": casual,
        }

    def _update_companies(self, event):
        try:
            author = event[AUTHOR_FIELD]
            company = author.split("@")[1][:-1]
            self.companies[company] += 1
        except (IndexError, KeyError):
            pass

    def _update_file_metrics(self, event):
        if "files" not in event:
            return

        for file in event["files"]:
            if not file["file"]:
                continue
            # File type metrics
            if re.search(FILE_TYPE_CODE, file["file"]):
                self.file_types["code"] += 1
            else:
                self.file_types["other"] += 1

            # Line added/removed metrics
            if "added" in file:
                try:
                    self.added_lines += int(file["added"])
                except ValueError:
                    pass
            if "removed" in file:
                try:
                    self.removed_lines += int(file["removed"])
                except ValueError:
                    pass

    def _update_message_size_metrics(self, event):
        message = event.get("message", "")
        self.messages_sizes.append(len(message))


def get_repository_metrics(
    repository: str,
    opensearch_url: str,
    opensearch_index: str,
    from_date: datetime.datetime = None,
    to_date: datetime.datetime = None,
    verify_certs: bool = True,
):
    """
    Get the metrics from a repository.

    :param repository: Repository URI
    :param opensearch_url: URL of the OpenSearch instance
    :param opensearch_index: Name of the index where the data is stored
    :param verify_certs: Boolean, verify SSL/TLS certificates, default True
    :param from_date: Start date, by default None
    :param to_date: End date, by default None
    """
    os_conn = connect_to_opensearch(opensearch_url, verify_certs=verify_certs)

    metrics = {"metrics": {}}

    events = get_repository_events(os_conn, opensearch_index, repository, from_date, to_date)

    analyzer = GitEventsAnalyzer()
    analyzer.process_events(events)

    metrics["metrics"]["total_commits"] = analyzer.get_commit_count()
    metrics["metrics"]["total_contributors"] = analyzer.get_contributor_count()
    metrics["metrics"]["pony_factor"] = analyzer.get_pony_factor()
    metrics["metrics"]["elephant_factor"] = analyzer.get_elephant_factor()

    if from_date and to_date:
        days = (to_date - from_date).days
    else:
        days = 365
    metrics["metrics"]["commits_week_mean"] = analyzer.get_commits_week_mean(days)

    # Flatten two-level metrics
    metrics_to_flatten = {
        "file_types": analyzer.get_file_type_metrics(),
        "commit_size": analyzer.get_commit_size_metrics(),
        "message_size": analyzer.get_message_size_metrics(),
        "developer_categories": analyzer.get_developer_categories(),
    }

    for prefix, metrics_set in metrics_to_flatten.items():
        for name, value in metrics_set.items():
            metrics["metrics"][prefix + "_" + name] = value

    return metrics


def get_repository_events(
    connection: OpenSearch,
    index_name: str,
    repository: str,
    from_date: datetime.datetime = None,
    to_date: datetime.datetime = None,
) -> iter(dict[str, Any]):
    """
    Returns the events between start_date and end_date for a repository.

    :param connection: OpenSearch connection object
    :param index_name: Name of the alias where Git data is stored in BAP
    :param repository: Name of the repository to filter commits
    :param from_date: Start date, by default None
    :param to_date: End date, by default None
    """
    s = Search(using=connection, index=index_name).filter("match", source=repository).filter("term", type=COMMIT_EVENT_TYPE)

    date_range = _format_date(from_date, to_date)
    if date_range:
        s = s.filter("range", time=date_range)

    return s.scan()


def connect_to_opensearch(
    url: str,
    verify_certs: bool = True,
    max_retries: int = 3,
) -> OpenSearch:
    """
    Connect to an OpenSearch instance using the given parameters.

    :param url: URL of the OpenSearch instance
    :param verify_certs: Boolean, verify SSL/TLS certificates
    :param max_retries: Maximum number of retries in case of timeout

    :return: OpenSearch connection
    """
    os_conn = OpenSearch(
        hosts=[url],
        http_compress=True,
        verify_certs=verify_certs,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        ca_cert=certifi.where,
        max_retries=max_retries,
        retry_on_timeout=True,
    )

    return os_conn


def _format_date(from_date: datetime.datetime, to_date: datetime.datetime) -> dict:
    """
    Format the date range for the OpenSearch query.

    :param from_date: Start date
    :param to_date: End date
    """
    date_range = {}
    if from_date:
        date_range["gte"] = from_date
    if to_date:
        date_range["lt"] = to_date

    return date_range
