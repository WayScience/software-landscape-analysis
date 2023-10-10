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

# # Seek GitHub Projects for Landscape Analysis
#
# Seeking GitHub project entries for software landscape analysis related to Cytomining ecosystem.
#
# ## Setup
#
# Set an environment variable named `LANDSCAPE_ANALYSIS_GH_TOKEN` to a [GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens). E.g.: `export LANDSCAPE_ANALYSIS_GH_TOKEN=token_here`

# +
import os
from datetime import datetime

import pandas as pd
from box import Box
from github import Auth, Github

# set github authorization and client
github_client = Github(
    auth=Auth.Token(os.environ.get("LANDSCAPE_ANALYSIS_GH_TOKEN")), per_page=100
)

# +
# gather projects data
queries = Box.from_yaml(filename="data/queries.yaml").queries

# observe the queries
queries.to_list()
# -

# gather repo data based on the results
results = [
    {"name": result.name, "homepage_url": result.homepage, "repo_url": result.html_url}
    for query in queries
    for result in github_client.search_repositories(query=query)
]
len(results)

# append loi focus items to the results set
results = [
    {
        "name": "pycytominer",
        "tags": ["loi-focus"],
        "homepage_url": "https://pycytominer.readthedocs.io/en/latest/",
        "repo_url": "https://github.com/cytomining/pycytominer",
    },
    {
        "name": "cyosnake",
        "tags": ["loi-focus"],
        "homepage_url": "https://cytosnake.readthedocs.io/en/latest/",
        "repo_url": "https://github.com/WayScience/CytoSnake",
    },
    {
        "name": "cytotable",
        "tags": ["loi-focus"],
        "homepage_url": "https://cytomining.github.io/CytoTable/",
        "repo_url": "https://github.com/cytomining/CytoTable",
    },
] + results

# filter the list of results to uniques
seen_url = set()
results = [
    result
    for result in results
    # check whether we have seen the result yet
    if result["repo_url"] not in seen_url
    # always returns None, so evals to True and adds to list
    and not seen_url.add(result["repo_url"])
]
len(results)

# export the results to a yaml file for later processing
Box({"projects": results}).to_yaml("data/projects.yaml")
