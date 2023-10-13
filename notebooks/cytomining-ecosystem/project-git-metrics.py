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
# Project git metrics for software landscape analysis related to Cytomining ecosystem.
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
print("number of projects: ", len(projects))
# -

# show the keys available for the projects
projects[0].keys()


def try_to_detect_license(repo):
    """
    Tries to detect the license from GitHub API
    """

    try:
        return repo.get_license().license.spdx_id
    except:
        return None


def try_to_gather_commit_count(repo):
    """
    Tries to detect commit count of repo from GitHub API
    """

    try:
        return len(list(repo.get_commits()))
    except:
        return 0


def try_to_gather_most_recent_commit_date(repo):
    """
    Tries to detect most recent commit date of repo from GitHub API
    """

    try:
        return repo.pushed_at.replace(tzinfo=pytz.UTC)
    except:
        return None


# +
df_projects = pd.DataFrame(
    # create a list of repo data records for a dataframe
    [
        {
            "Project Name": repo.name,
            "Project Homepage": repo.homepage,
            "Project Repo URL": repo.html_url,
            "Project Landscape Category": project.category,
            "GitHub Stars": repo.stargazers_count,
            "GitHub Forks": repo.forks_count,
            "GitHub Watchers": repo.subscribers_count,
            "GitHub Open Issues": repo.get_issues(state="open").totalCount,
            "GitHub Contributors": repo.get_contributors().totalCount,
            "GitHub License Type": try_to_detect_license(repo),
            "GitHub Description": repo.description,
            "GitHub Topics": repo.topics,
            "GitHub Detected Languages": repo.get_languages(),
            "Date Created": repo.created_at.replace(tzinfo=pytz.UTC),
            "Date Most Recent Commit": try_to_gather_most_recent_commit_date(repo),
            # placeholders for later datetime calculations
            "Duration Created to Most Recent Commit": "",
            "Duration Created to Now": "",
            "Duration Most Recent Commit to Now": "",
            "Repository Size (KB)": repo.size,
            "GitHub Repo Archived": repo.archived,
        }
        # make a request for github repo data with pygithub
        for project, repo in [
            (
                project,
                github_client.get_repo(
                    project.repo_url.replace("https://github.com/", "")
                ),
            )
            for project in projects
        ]
    ]
)

# calculate time deltas
df_projects["Duration Created to Most Recent Commit"] = (
    df_projects["Date Most Recent Commit"] - df_projects["Date Created"]
)
df_projects["Duration Created to Now"] = current_datetime - df_projects["Date Created"]
df_projects["Duration Most Recent Commit to Now"] = (
    current_datetime - df_projects["Date Most Recent Commit"]
)

# show the result
df_projects
# -

# filter the results
df_projects = df_projects[
    # filter projects which are < 50 KB
    df_projects["Repository Size (KB)"]
    >= 50
    # filter projects which have been archived
    & ~df_projects["GitHub Repo Archived"]
][  # filter projects which have no detected programming languages
    df_projects["GitHub Detected Languages"].str.len() > 0
]
df_projects.tail()

# negate this duration value for sorting descendingly,
# with projects that have been more recently changed sorting to the top
df_projects["Negative Duration Most Recent Commit to Now"] = -df_projects[
    "Duration Most Recent Commit to Now"
]
df_projects = df_projects.sort_values(
    by=[
        "GitHub Stars",
        "GitHub Watchers",
        "GitHub Contributors",
        "GitHub Forks",
        "GitHub Open Issues",
        "Negative Duration Most Recent Commit to Now",
        "Duration Created to Most Recent Commit",
    ],
    ascending=False,
)
df_projects

# export to parquet for later use
df_projects.to_parquet("data/project-github-metrics.parquet")
