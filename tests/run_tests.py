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

import os
import sys
import unittest
import click


@click.command()
@click.argument("module", required=False, default="unit")
def test(module):
    test_suite = unittest.TestLoader().discover(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), module),
        pattern="test_*.py",
    )
    result = unittest.TextTestRunner(buffer=True).run(test_suite)
    sys.exit(not result.wasSuccessful())


if __name__ == "__main__":
    test()
