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

# # Project Git Metrics for Landscape Analysis
#
# Project git metrics for landscape analysis as part of [CZI EOSS Cycle 6](https://chanzuckerberg.com/rfa/essential-open-source-software-for-science/).
#
# ## Setup
#
# Set an environment variable named `LANDSCAPE_ANALYSIS_GH_TOKEN` to a [GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens). E.g.: `export LANDSCAPE_ANALYSIS_GH_TOKEN=token_here`

# +
import os
from datetime import datetime

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
projects = Box.from_yaml(filename="data/projects.yaml").projects

# check the number of projects
len(projects)
# -

# show the keys available for the projects
projects[0].keys()

# +
df_projects = pd.DataFrame(
    # create a list of repo data records for a dataframe
    [
        {
            "Project Name": repo.name,
            "GitHub Stars": repo.stargazers_count,
            "GitHub Forks": repo.forks_count,
            "GitHub Watchers": repo.subscribers_count,
            "GitHub Open Issues": repo.get_issues(state="open").totalCount,
            "GitHub Contributors": repo.get_contributors().totalCount,
            "GitHub License Type": repo.get_license().license.spdx_id,
            "Date Created": repo.created_at.replace(tzinfo=pytz.UTC),
            "Date Most Recent Commit": repo.get_commits()[0].commit.author.date.replace(
                tzinfo=pytz.UTC
            ),
            "Duration Created to Most Recent Commit": "",
            "Duration Most Recent Commit to Now": "",
            "Repository Size (KB)": repo.size,
        }
        # make a request for github repo data with pygithub
        for repo in [
            github_client.get_repo(project.repo_url.replace("https://github.com/", ""))
            for project in projects
        ]
    ]
)

# calculate time deltas
df_projects["Duration Created to Most Recent Commit"] = (
    df_projects["Date Most Recent Commit"] - df_projects["Date Created"]
)
df_projects["Duration Most Recent Commit to Now"] = (
    current_datetime - df_projects["Date Most Recent Commit"]
)

# show the result
df_projects