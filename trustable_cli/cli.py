from __future__ import annotations

import datetime
import json
import logging
import re
import sys
import time
import typing

import click
import requests

from spdx_tools.spdx.model import SpdxNone, SpdxNoAssertion
from spdx_tools.spdx.parser.error import SPDXParsingError
from spdx_tools.spdx.parser.parse_anything import parse_file

from trustable_cli.grimoirelab_client import GrimoireLabClient
from trustable_cli.metrics import get_repository_metrics

if typing.TYPE_CHECKING:
    from typing import Any

GIT_REPO_REGEX = r"((git|http(s)?)|(git@[\w\.]+))://?([\w\.@\:/\-~]+)(\.git)(/)?"


@click.command()
@click.argument("filename")
@click.option(
    "--grimoirelab-url",
    help="GrimoireLab URL server",
    show_default=True,
)
@click.option("--grimoirelab-user", help="GrimoireLab API user")
@click.option("--grimoirelab-password", help="GrimoireLab API password")
@click.option(
    "--opensearch-url",
    help="OpenSearch URL server",
    default="http://localhost:9200/",
)
@click.option("--opensearch-index", help="OpenSearch index", default="events")
@click.option("--output", help="File where the scores will be written", type=click.File("w"), default=sys.stdout)
@click.option(
    "--from-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date, by default last year",
    default=(datetime.datetime.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d"),
)
@click.option(
    "--to-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date",
)
@click.option("--verify-certs", is_flag=True, default=False, help="Verify SSL/TLS certificates")
@click.option("--verbose", is_flag=True, default=False, help="Increase output verbosity")
def trustable_grimoirelab_score(
    filename: str,
    grimoirelab_url: str,
    grimoirelab_user: str,
    grimoirelab_password: str,
    opensearch_url: str,
    opensearch_index: str,
    output: str,
    from_date: datetime.datetime | None = None,
    to_date: datetime.datetime | None = None,
    verify_certs: bool = False,
    verbose: bool = False,
) -> None:
    """Calculate metrics for Trustable using GrimoireLab.

    Given a SPDX SBOM file with git repositories as input, this tool will generate
    a set of Project Health metrics. These metrics are calculated using the data
    stored on GrimoireLab about those repositories.

    If any of the listed repositories is not available on GrimoireLab, the tool
    will add it to GrimoireLab to have it analyzed.

    FILENAME: SPDX SBoM file with git repositories
    """
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        logging.info(f"Parsing file {filename}")

        grimoirelab_client = GrimoireLabClient(grimoirelab_url, grimoirelab_user, grimoirelab_password)
        grimoirelab_client.connect()

        package_urls = get_sbom_repositories(filename)

        if len(package_urls) > 0:
            logging.info(f"Found {len(package_urls)} git repositories")
        else:
            logging.info("Could not find any git repositories to analyze")
            sys.exit(0)

        schedule_repositories(package_urls, grimoirelab_client)

        metrics = generate_metrics_when_ready(
            grimoirelab_client, package_urls, opensearch_url, opensearch_index, from_date, to_date, verify_certs
        )

        output.write(json.dumps(metrics, indent=4))
    except SPDXParsingError as e:
        logging.error(e.messages[0])
        sys.exit(1)
    except OSError as e:
        logging.error(e)
        sys.exit(1)


def get_repository(download_location: str) -> str | None:
    if is_valid(download_location):
        git_regex = re.search(GIT_REPO_REGEX, download_location)
        if git_regex:
            uri = f"https://{git_regex.group(5)}"
            return uri


def get_sbom_repositories(file: str) -> list[str]:
    """Extract git repositories from SPDX SBoM file.

    :param file: SPDX SBoM file.

    :return: List of git repositories.
    """
    repositories = []
    document = parse_file(file)
    for package in document.packages:
        repository = get_repository(package.download_location)
        if repository:
            repositories.append(repository)
        else:
            logging.warning(f"Could not find a git repository for {package.name}")

    return list(set(repositories))


def schedule_repositories(repositories: list[str], grimoirelab_client: GrimoireLabClient) -> None:
    """Schedule tasks to collect data from a list of repositories.

    :param repositories: List of git repositories.
    :param grimoirelab_client: GrimoireLab API client.
    """
    logging.info("Scheduling tasks")
    for package_url in repositories:
        logging.debug(f"Scheduling task to fetch commits from {package_url}")
        try:
            schedule_repository(grimoirelab_client=grimoirelab_client, uri=package_url, datasource="git", category="commit")
        except (requests.HTTPError, requests.ConnectionError) as e:
            logging.error(f"Error scheduling task: {e}")
            raise e


def generate_metrics_when_ready(
    grimoirelab_client: GrimoireLabClient,
    repositories: list[str],
    opensearch_url: str,
    opensearch_index: str,
    from_date: datetime.datetime | None = None,
    to_date: datetime.datetime | None = None,
    verify_certs: bool = False,
) -> dict[str:Any]:
    """Generate metrics once the repositories have finished the collection.

    :param grimoirelab_client: GrimoireLab API client.
    :param repositories: List of repositories.
    :param opensearch_url: OpenSearch URL.
    :param opensearch_index: OpenSearch index.
    :param from_date: Start date for metrics.
    :param to_date: End date for metrics.
    :param verify_certs: Verify SSL/TLS certificates.
    """
    logging.info("Generating metrics")

    after_date = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)
    pending_repositories = set(repositories)
    metrics = {"repositories": {}}

    while pending_repositories:
        processed = set()
        for repository in pending_repositories:
            if repository_ready(grimoirelab_client, repository, after_date):
                metrics["repositories"][repository] = get_repository_metrics(
                    repository,
                    opensearch_url,
                    opensearch_index,
                    from_date,
                    to_date,
                    verify_certs,
                )
                processed.add(repository)

        pending_repositories -= processed

        if pending_repositories:
            logging.info(f"Waiting for {len(pending_repositories)} repositories to be ready")
            time.sleep(5)

    return metrics


def repository_ready(grimoirelab_client: GrimoireLabClient, repository: str, after_date: datetime.datetime) -> bool:
    """
    Check if the task related to the repository has finished.

    :param grimoirelab_client: GrimoireLab API client.
    :param repository: Repository URI
    :param after_date: Date to check if the task has finished
    """
    try:
        r = grimoirelab_client.get("/datasources/repositories/", params={"uri": repository})
    except requests.HTTPError as e:
        logging.warning(f"Error checking repository status: {e}")
        return False

    repo_data = r.json()

    last_run = repo_data["results"][0]["task"]["last_run"]
    if last_run:
        last_run_dt = datetime.datetime.fromisoformat(last_run)
        return last_run_dt > after_date

    return False


def is_valid(repository: str) -> bool:
    """Check that the value is not empty nor invalid."""

    return repository and not isinstance(repository, SpdxNone) and not isinstance(repository, SpdxNoAssertion)


def schedule_repository(grimoirelab_client: GrimoireLabClient, uri: str, datasource: str, category: str) -> Any:
    """Schedule a task to fetch a Git repository.

    :param grimoirelab_client: GrimoireLab API client.
    :param uri: Repository URI.
    :param datasource: Data source type.
    :param category: Data source category.

    :return: Scheduled task.
    """
    data = {
        "uri": uri,
        "datasource_type": datasource,
        "datasource_category": category,
    }
    res = grimoirelab_client.post("datasources/add_repository", json=data)
    try:
        res.raise_for_status()
    except requests.HTTPError as e:
        if res.status_code == 405 and "already exists" in res.json()["error"]:
            pass
        else:
            raise e


if __name__ == "__main__":
    trustable_grimoirelab_score()
