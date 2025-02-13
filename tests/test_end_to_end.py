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

import json
import os
import signal
import subprocess
import tempfile
import time
import unittest

from click.testing import CliRunner
from testcontainers.redis import RedisContainer
from testcontainers.mysql import MySqlContainer
from testcontainers.opensearch import OpenSearchContainer
from testcontainers.core.waiting_utils import wait_for_logs

from trustable_cli.cli import trustable_grimoirelab_score

GRIMOIRELAB_URL = "http://localhost:8000"


class EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_file = tempfile.NamedTemporaryFile(delete=False)
        cls.runner = CliRunner()
        cls._start_redis_container(cls)
        cls._start_database_container(cls)
        cls._start_opensearch_container(cls)
        cls._start_grimoirelab(cls)

    @classmethod
    def tearDownClass(cls):
        cls.grimoirelab_eventizers.terminate()
        cls.grimoirelab_archivists.terminate()
        time.sleep(60)
        cls.grimoirelab_server.send_signal(signal.SIGINT)
        cls.mysql_container.stop()
        cls.opensearch_container.stop()
        cls.redis_container.stop()

    def _start_database_container(self):
        self.mysql_container = MySqlContainer(image="mariadb:latest", root_password="root").with_exposed_ports(3306)
        self.mysql_container.start()

    def _start_redis_container(self):
        self.redis_container = RedisContainer().with_exposed_ports(6379)
        self.redis_container.start()

    def _start_opensearch_container(self):
        self.opensearch_container = OpenSearchContainer().with_exposed_ports(9200)
        self.opensearch_container.start()
        wait_for_logs(self.opensearch_container, ".*recovered .* indices into cluster_state.*")
        port = self.opensearch_container.get_exposed_port(9200)
        self.opensearch_url = f"http://admin:admin@localhost:{port}"

    def _start_grimoirelab(self):
        env = os.environ
        env["DJANGO_SETTINGS_MODULE"] = "grimoirelab.core.config.settings"
        env["GRIMOIRELAB_REDIS_PORT"] = self.redis_container.get_exposed_port(6379)
        env["GRIMOIRELAB_DB_PORT"] = self.mysql_container.get_exposed_port(3306)
        env["GRIMOIRELAB_DB_PASSWORD"] = self.mysql_container.root_password
        env["GRIMOIRELAB_ARCHIVIST_STORAGE_URL"] = self.opensearch_url
        env["GRIMOIRELAB_USER_PASSWORD"] = "admin"
        env["GRIMOIRELAB_ARCHIVIST_BLOCK_TIMEOUT"] = "1000"

        from grimoirelab.core.runner.cmd import grimoirelab

        self.runner.invoke(grimoirelab, "admin setup")
        subprocess.run(["grimoirelab", "admin", "create-user", "--username", "admin", "--no-interactive"])
        self.grimoirelab_server = subprocess.Popen(["grimoirelab", "run", "server", "--dev"], start_new_session=True)
        self.grimoirelab_eventizers = subprocess.Popen(
            ["grimoirelab", "run", "eventizers", "--workers", "1"], start_new_session=True
        )
        self.grimoirelab_archivists = subprocess.Popen(
            ["grimoirelab", "run", "archivists", "--workers", "1"], start_new_session=True
        )
        time.sleep(30)

    def test_commit_count(self):
        """Check if it returns the number of commits of one repository from a valid file"""

        result = self.runner.invoke(
            trustable_grimoirelab_score,
            [
                "./data/one_repo.spdx.xml",
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
            ],
        )
        self.assertEqual(result.exit_code, 0)

        with open(self.temp_file.name) as f:
            metrics = json.load(f)
            self.assertEqual(len(metrics["repositories"]), 1)
            self.assertGreater(metrics["repositories"]["https://github.com/chaoss/grimoirelab-core"]["metrics"]["num_commits"], 0)


if __name__ == "__main__":
    unittest.main()
