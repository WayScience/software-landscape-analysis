# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Gather Targeted Project Package Metrics
#
# Project package metrics (PyPI, Conda, etc.) for software landscape analysis related to Cytomining ecosystem.
#
# ## Setup
#
# Use of this notebook involves setup via https://github.com/ofek/pypinfo#installation. An environment variable is expected for pypinfo to work properly. For example: `export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json`

# +
import json
import os
import subprocess
from datetime import datetime

import awkward as ak
import numpy as np
import pandas as pd
import pytz
from box import Box

# +
# gather projects data
projects = Box.from_yaml(filename="data/target-projects.yaml").projects

# gather the lowercase loi focus project names from targets
loi_target_projects = [
    project["name"].lower()
    for project in projects.to_list()
    if "loi-focus" in project["category"]
]
loi_target_projects
# -

# form a data structure for gathering package data
pkg_metrics = [{"Project Name": project} for project in loi_target_projects]
pkg_metrics

# gather various PyPI metrics through pypinfo
pkg_metrics = [
    dict(
        project,
        **{
            # gather total downloads
            "pypi_downloads_total": json.loads(
                subprocess.run(
                    [
                        "pypinfo",
                        "--json",
                        project["Project Name"],
                    ],
                    capture_output=True,
                    check=True,
                ).stdout
            )["rows"],
            # gather downloads by python version
            "pypi_downloads_by_pyversion": json.loads(
                subprocess.run(
                    ["pypinfo", "--json", project["Project Name"], "pyversion"],
                    capture_output=True,
                    check=True,
                ).stdout
            )["rows"],
            # gather downloads by country
            "pypi_downloads_by_country": json.loads(
                subprocess.run(
                    ["pypinfo", "--json", project["Project Name"], "country"],
                    capture_output=True,
                    check=True,
                ).stdout
            )["rows"],
            # gather downloads by system and distro type
            "pypi_downloads_by_system_and_distro": json.loads(
                subprocess.run(
                    ["pypinfo", "--json", project["Project Name"], "system", "distro"],
                    capture_output=True,
                    check=True,
                ).stdout
            )["rows"],
            "pypi_downloads_by_year_and_month": json.loads(
                subprocess.run(
                    ["pypinfo", "--json", project["Project Name"], "year", "month"],
                    capture_output=True,
                    check=True,
                ).stdout
            )["rows"],
        }
    )
    for project in pkg_metrics
]
ak.Array(pkg_metrics)




