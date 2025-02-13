#!/usr/bin/env python3
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
import typing

import certifi

from opensearchpy import OpenSearch, Search


logging.getLogger("opensearch").setLevel(logging.WARNING)


if typing.TYPE_CHECKING:
    from typing import Any


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

    metrics["metrics"]["num_commits"] = commit_count(events)

    return metrics


def commit_count(events: list[dict[str, Any]]) -> int:
    """
    Return the number of commits in the list of events.

    :param events: List of events
    """
    return sum(1 for event in events if event["type"] == "org.grimoirelab.events.git.commit")


def get_repository_events(
    connection: OpenSearch,
    index_name: str,
    repository: str,
    from_date: datetime.datetime = None,
    to_date: datetime.datetime = None,
) -> list[dict[str, Any]]:
    """
    Returns the events between start_date and end_date for a repository.

    :param connection: OpenSearch connection object
    :param index_name: Name of the alias where Git data is stored in BAP
    :param repository: Name of the repository to filter commits
    :param from_date: Start date, by default None
    :param to_date: End date, by default None
    """
    s = (
        Search(using=connection, index=index_name)
        .filter("match", source=repository)
        .filter("term", type="org.grimoirelab.events.git.commit")
        .source(["type"])
    )

    date_range = _format_date(from_date, to_date)
    if date_range:
        s = s.filter("range", time=date_range)

    events = s.scan()

    return [event for event in events]


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
