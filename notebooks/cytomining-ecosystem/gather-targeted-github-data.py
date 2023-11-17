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
# Project GitHub dependent, visitor, and contributor network metrics for software landscape analysis related to Cytomining ecosystem.
#
# Namely, we're seeking data which backs up the following:
# - Software projects that depend on the project
# - Monthly visitors to project’s website
# - List of software projects to which key personnel are contributing
#
# ## Setup
#
# Set an environment variable named `LANDSCAPE_ANALYSIS_GH_TOKEN` to a [GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens). E.g.: `export LANDSCAPE_ANALYSIS_GH_TOKEN=token_here`
#
# Use of this notebook also involves setup via https://github.com/ofek/pypinfo#installation. An environment variable is expected for pypinfo to work properly. For example: `export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json`

# +
import json
import os
import pathlib
import statistics
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Optional

import awkward as ak
import duckdb
import pandas as pd
import pytz
from box import Box
from github import Auth, Github, Repository
from google.cloud import bigquery

# set github authorization and client
github_client = Github(
    auth=Auth.Token(os.environ.get("LANDSCAPE_ANALYSIS_GH_TOKEN")), per_page=100
)

# create google big query client
gcbq_client = bigquery.Client()

# get the current datetime
tz = pytz.timezone("UTC")
current_datetime = datetime.now(tz)

# Get the last two digits of the current year
current_year_last_two_digits = current_datetime.strftime("%y")
current_year_month = current_datetime.strftime("%Y-%m")

# Get the last two digits of the previous year
previous_year_last_two_digits = (current_datetime - timedelta(days=365)).strftime("%y")

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
        "GitHub Repo Full Name": repo.full_name,
        # gather repo data from github API
        "GitHub Repository ID": repo.id,
        "GitHub Repo Created Month": repo.created_at.strftime("%Y-%m"),
        "GitHub Stars": repo.stargazers_count,
        # find github stars for project by date
        "GitHub Stars by Date": [
            # convert to str to avoid datatyping issues
            result.starred_at.strftime("%Y-%m-%d %H:%M:%S %Z")
            for result in repo.get_stargazers_with_dates()
        ],
        # this aligns with number of forks and is labeled the network count
        "GitHub Network Count": repo.network_count,
        # find where the project is used via targeted github code search
        "GitHub Code Search Used By": list(
            # gather distinct results (avoid repeats)
            set(
                [
                    # include the full name of the repository
                    code.repository.full_name
                    # search code by project name
                    for code in github_client.search_code(query=repo.name.lower())
                    # check that the result isn't the project itself of this analysis
                    if code.repository.full_name.lower()
                    not in (
                        repo.full_name.lower(),
                        "wayscience/software-landscape-analysis",
                    )
                    # check that the code file is of .py or .ipynb type
                    and pathlib.Path(code.name).suffix in (".py", ".ipynb")
                    # check that the repository is not a fork
                    and not code.repository.fork
                ]
            )
        ),
        # find all contributors to the project
        "GitHub Contributors": [
            {
                "id": contributor.id,
                "name": contributor.name,
                "login": contributor.login,
            }
            for contributor in repo.get_contributors()
        ],
        # gather details for target personnel
        "GitHub Target Key Personnel": [
            {"id": ghuser.id, "name": ghuser.name, "login": ghuser.login}
            for ghuser in [
                github_client.get_user(user)
                for user in project["target-key-personnel-gh-login"]
            ]
        ],
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
# gather key personnel contribution data from GitHub and gharchive
def safely_query_github_repo_from_archive_data(
    repo_full_name: str,
) -> Optional[Repository.Repository]:
    """
    Safely queries for github repo from archive data,
    avoiding errors when exceptions are encountered by
    returning None.
    """

    try:
        return github_client.get_repo(repo_full_name)
    except:
        return None


tgt_github_metrics = [
    dict(
        project,
        **{
            # query for where the key personnel are contributing to
            "GitHub Target Key Personnel Contributing To": [
                {
                    "repo.full_name": repo.full_name,
                    "repo.stargazers_count": repo.stargazers_count,
                }
                for repo in [
                    # gather data about the key personnel contributing repo
                    safely_query_github_repo_from_archive_data(
                        contribution_repo["repo.full_name"]
                    )
                    for contribution_repo in [
                        # form a data structure which can help reference the repo full name
                        {"repo.full_name": row[0]}
                        # gather data from gharchive about the key personnel contributions
                        for row in gcbq_client.query(
                            f"""
                            /* gather distinct results for repositories */
                            SELECT DISTINCT
                                /* note: repo.name here corresponds to org/repo_name
                                or aka 'full_name' */
                                repo.name
                            /* wildcard monthly references to seek last two years
                            using the where clause below */
                            FROM `githubarchive.month.20*`
                            WHERE
                                /* only look at users which are in target key personnel id's */
                                actor.id IN ({', '.join([str(user['id']) for user in project['GitHub Target Key Personnel']])})
                                /* only look at push and pull request events */
                                AND type IN ('PushEvent', 'PullRequestEvent')
                                /* only look at the last two years of data */
                                AND (_TABLE_SUFFIX BETWEEN '{previous_year_last_two_digits}01'
                                    AND '{current_year_last_two_digits}12')
                                /* filter out repos which match the target project full name */
                                AND repo.name NOT IN ('{project['GitHub Repo Full Name']}')
                            """
                        ).result()
                    ]
                ]
                # only keep non-null results
                if repo is not None
                # only keep results which are not forks
                and not repo.fork
                # only keep results which have more than 0 stars
                and repo.stargazers_count > 1
            ],
        },
    )
    for project in tgt_github_metrics
]
ak.Array(tgt_github_metrics)
# -

# gather dependents data from GitHub
tgt_github_metrics = [
    dict(
        project,
        **{
            # gather github dependent data scraped from github-dependents-info
            # (github api information otherwise appears to be private or undocumented)
            "GitHub Dependents": json.loads(
                subprocess.run(
                    [
                        "github-dependents-info",
                        "--repo",
                        project["GitHub Repo Full Name"],
                        "--json",
                    ],
                    capture_output=True,
                    check=True,
                ).stdout
            ),
        },
    )
    for project in tgt_github_metrics
]
ak.Array(tgt_github_metrics)

# +
# add calculations for ease of analysis
find_average = lambda nums: sum(nums) / len(nums) if len(nums) > 0 else None
find_median = lambda nums: statistics.median(nums) if len(nums) > 0 else None


def add_missing_months(
    months_data: Dict[str, int], date_minimum: str, date_max: str
) -> Dict[str, int]:
    """
    Adds and updates missing months data for
    GitHub stargazer data (which only has records for non-zero counts)
    """

    start_date = datetime.strptime(date_minimum, "%Y-%m")
    end_date = datetime.strptime(date_max, "%Y-%m")

    current_date = start_date

    result = {}

    while current_date <= end_date:
        # Create a dictionary with YYYY-MM format
        result[current_date.strftime("%Y-%m")] = 0

        # Move to the next month
        current_date += timedelta(days=32)
        current_date = datetime(current_date.year, current_date.month, 1)

    # Update the new dictionary with the values from the original dictionary
    result.update(months_data)

    return result


def add_missing_years(
    years_data: Dict[str, int], date_minimum: str, date_max: str
) -> Dict[str, int]:
    """
    Adds and updates missing years data for GitHub stargazer data
    (which only has records for non-zero counts)
    """

    start_date = int(datetime.strptime(date_minimum, "%Y-%m").year)
    end_date = int(datetime.strptime(date_max, "%Y-%m").year)

    current_year = start_date

    result = {}

    while current_year <= end_date:
        # Create a dictionary with YYYY format
        result[str(current_year)] = 0

        # Move to the next year
        current_year += 1

    # Update the new dictionary with the values from the original dictionary
    result.update(years_data)

    return result


tgt_github_metrics = [
    dict(
        project,
        **{
            # convert a list of dates when stargazers were added to
            # dictionary of months and star count for later calculations
            "GitHub Stargazers Count by Month": add_missing_months(
                {
                    date_object.strftime("%Y-%m"): sum(
                        1
                        for d in (
                            datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S %Z")
                            for timestamp in project["GitHub Stars by Date"]
                        )
                        if d.strftime("%Y-%m") == date_object.strftime("%Y-%m")
                    )
                    for date_object in (
                        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S %Z")
                        for timestamp in project["GitHub Stars by Date"]
                    )
                },
                project["GitHub Repo Created Month"],
                current_year_month,
            ),
            # convert a list of dates when stargazers were added to
            # dictionary of years and star count for later calculations
            "GitHub Stargazers Count by Year": add_missing_years(
                {
                    date_object.strftime("%Y"): sum(
                        1
                        for d in (
                            datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S %Z")
                            for timestamp in project["GitHub Stars by Date"]
                        )
                        if d.strftime("%Y") == date_object.strftime("%Y")
                    )
                    for date_object in (
                        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S %Z")
                        for timestamp in project["GitHub Stars by Date"]
                    )
                },
                project["GitHub Repo Created Month"],
                current_year_month,
            ),
        },
    )
    for project in tgt_github_metrics
]
tgt_github_metrics = [
    dict(
        project,
        **{
            "GitHub Contributor Total Count": len(project["GitHub Contributors"]),
            "GitHub Dependency Graph Dependents Count": project["GitHub Dependents"][
                "total_dependents_number"
            ],
            "GitHub Code Search Dependents Count": len(
                project["GitHub Code Search Used By"]
            ),
            "GitHub Total Dependents Count": len(
                # create a list of unique repo full_name entries
                # from all dependents queries
                list(
                    set(
                        project["GitHub Code Search Used By"]
                        + [
                            repo["name"]
                            for repo in project["GitHub Dependents"][
                                "all_public_dependent_repos"
                            ]
                        ]
                    )
                )
            ),
            "GitHub Stargazers Count by Month Average": find_average(
                [
                    count
                    for count in project["GitHub Stargazers Count by Month"].values()
                ]
            ),
            "GitHub Stargazers Count by Month Median": find_median(
                [
                    count
                    for count in project["GitHub Stargazers Count by Month"].values()
                ]
            ),
            "GitHub Stargazers Count by Year Average": find_average(
                [count for count in project["GitHub Stargazers Count by Year"].values()]
            ),
            "GitHub Stargazers Count by Year Median": find_median(
                [count for count in project["GitHub Stargazers Count by Year"].values()]
            ),
        },
    )
    for project in tgt_github_metrics
]
ak.Array(tgt_github_metrics)
# -

# export to parquet file
ak.to_parquet(
    array=ak.Array(tgt_github_metrics),
    destination="data/loi-target-project-github-metrics.parquet",
)

# depict results from the file
with duckdb.connect() as ddb:
    ghstats_totals = ddb.query(
        f"""
    SELECT
        ghstats."Project Name",
        ghstats."GitHub Stars",
        ghstats."GitHub Contributor Total Count",
        ghstats."GitHub Network Count",
        ghstats."GitHub Dependency Graph Dependents Count",
        ghstats."GitHub Code Search Dependents Count",
        ghstats."GitHub Total Dependents Count",
        ghstats."GitHub Stargazers Count by Month Average",
        ghstats."GitHub Stargazers Count by Month Median",
        ghstats."GitHub Stargazers Count by Year Average",
        ghstats."GitHub Stargazers Count by Year Median"
    FROM read_parquet('data/loi-target-project-github-metrics.parquet') as ghstats
    """,
    ).df()
ghstats_totals
