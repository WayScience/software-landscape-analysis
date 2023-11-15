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

# # Gather Targeted Project GitHub Metrics
#
# Project GitHub dependant, visitor, and contributor network metrics for software landscape analysis related to Cytomining ecosystem.
#
# Namely, we're seeking data which backs up the following:
# - Software projects that depend on the project
# - Monthly visitors to project’s website
# - List of software projects to which key personnel are contributing
#
# ## Setup
#
# Set an environment variable named `LANDSCAPE_ANALYSIS_GH_TOKEN` to a [GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens). E.g.: `export LANDSCAPE_ANALYSIS_GH_TOKEN=token_here`

# +
import json
import os
import subprocess
from datetime import datetime

import awkward as ak
import pandas as pd
import pytz
from box import Box
from github import Auth, Github

# set github authorization and client
github_client = Github(
    auth=Auth.Token(os.environ.get("LANDSCAPE_ANALYSIS_GH_TOKEN")), per_page=100
)
# get the current datetime
tz = pytz.timezone("UTC")
current_datetime = datetime.now(tz)

# +
# gather projects data
projects = Box.from_yaml(filename="data/target-projects.yaml").projects

# gather the lowercase loi focus project names from targets
loi_target_projects = [
    project for project in projects.to_list() if "loi-focus" in project["category"]
]
loi_target_projects
# -

# gather targeted data from GitHub
tgt_github_metrics = [
    {
        "Project Name": repo.name,
        # gather repo data from github API
        "GitHub Repository ID": repo.id,
        "GitHub Stars": repo.stargazers_count,
        "GitHub Network Count": repo.network_count,
        "Github Top Referrers": [
            {
                "uniques": referrer.uniques,
                "referrer": referrer.referrer,
                "count": referrer.count,
            }
            for referrer in repo.get_top_referrers()
        ],
        # gather github dependent data scraped from github-dependents-info
        # (github api information otherwise appears to be private or undocumented)
        "GitHub Dependents": json.loads(
            subprocess.run(
                [
                    "github-dependents-info",
                    "--repo",
                    "cytomining/pycytominer",
                    "--json",
                ],
                capture_output=True,
                check=True,
            ).stdout
        ),
    }
    # make a request for github repo data with pygithub
    for project, repo in [
        (
            project,
            github_client.get_repo(
                project["repo_url"].replace("https://github.com/", "")
            ),
        )
        for project in loi_target_projects
    ]
]
ak.Array(tgt_github_metrics)

# +
listing = [
    {
        "name": contributor.name,
        "login": contributor.login,
        "contributions_push_nonfork_limited": list(
            set(
                [
                    event.repo.name
                    for event in contributor.get_events()
                    if event.type == "PushEvent" and event.repo and not event.repo.fork
                ]
            )
        ),
    }
    for contributor in github_client.get_repo("cytomining/cytotable").get_contributors()
]


listing
