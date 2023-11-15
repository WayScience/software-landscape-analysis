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
import condastats.cli as condastats_cli
import duckdb
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

# +
# create a str for targeting the specific projects
project_sql_str = ", ".join(["'" + project + "'" for project in loi_target_projects])

# filter results of github stats to find the project creation date for use in filtering below
with duckdb.connect() as ddb:
    loi_target_project_years = ddb.query(
        f"""
    SELECT
        ghstats."Project Name",
        ghstats."Date Created"
    FROM read_parquet('data/project-github-metrics.parquet') as ghstats
    WHERE LOWER(ghstats."Project Name") in ({project_sql_str})
    """,
    ).df()

loi_target_project_years
# -

# add a year created
loi_target_project_years["Date Created YYYY-MM"] = loi_target_project_years[
    "Date Created"
].dt.strftime("%Y-%m")
pkg_metrics = loi_target_project_years[
    ["Project Name", "Date Created YYYY-MM"]
].to_dict(orient="records")
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
            # gather downloads by year and month, ordered by month
            "pypi_downloads_by_month": json.loads(
                subprocess.run(
                    [
                        "pypinfo",
                        "--json",
                        "--start-date",
                        project["Date Created YYYY-MM"],
                        "--order",
                        "download_month",
                        project["Project Name"],
                        "month",
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
        }
    )
    for project in pkg_metrics
]
ak.Array(pkg_metrics)

# gather various conda metrics through condastats (seeks conda-forge and bioconda data)
pkg_metrics = [
    dict(
        project,
        **{
            # gather total downloads
            "conda_downloads_total": condastats_cli.overall(
                package=project["Project Name"],
                start_month=project["Date Created YYYY-MM"],
            ).to_dict(),
            # gather downloads by month
            "conda_downloads_by_month": condastats_cli.overall(
                package=project["Project Name"],
                start_month=project["Date Created YYYY-MM"],
                monthly=True,
            ).to_dict(),
            # gather downloads by python version
            "conda_downloads_by_pyversion": condastats_cli.pkg_python(
                package=project["Project Name"],
                start_month=project["Date Created YYYY-MM"],
            ).to_dict(),
            # gather downloads by version
            "conda_downloads_by_version": condastats_cli.pkg_version(
                package=project["Project Name"],
                start_month=project["Date Created YYYY-MM"],
            ).to_dict(),
            # gather downloads by system and distro type
            "conda_downloads_by_platform": condastats_cli.pkg_platform(
                package=project["Project Name"],
                start_month=project["Date Created YYYY-MM"],
            ).to_dict(),
        }
    )
    for project in pkg_metrics
]
ak.Array(pkg_metrics)


