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
# Seeking GitHub project and other data entries for software landscape analysis related to Cytomining ecosystem.
#
# ## Setup
#
# Set an environment variable named `LANDSCAPE_ANALYSIS_GH_TOKEN` to a [GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens). E.g.: `export LANDSCAPE_ANALYSIS_GH_TOKEN=token_here`

# +
import os
from datetime import datetime

import numpy as np
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

# setup a reference for target project urls to ignore as additions to avoid duplication
target_project_html_urls = [
    project["repo_url"]
    for project in Box.from_yaml(filename="data/target-projects.yaml").projects
]
target_project_html_urls

# gather repo data from GitHub based on the results of search queries
results = [
    {
        "name": result.name,
        "homepage_url": result.homepage,
        "repo_url": result.html_url,
        "category": ["related-tools-github-query-result"],
    }
    for query in queries
    for result in github_client.search_repositories(
        query=query, sort="stars", order="desc"
    )
    if result.html_url not in target_project_html_urls
]
len(results)

# +
# read and display rough content of scRNA-Tools content
df_scrna_tools = pd.read_csv("data/scRNA-Tools-tableExport-2023-10-12.csv")
print(df_scrna_tools.shape)

# replace none-like values for citations with 0's for the purpose of sorting
df_scrna_tools["Citations"] = (
    df_scrna_tools["Citations"].replace("-", "0").replace("'-", "0")
).astype("int64")

# drop rows where we don't have a repository
df_scrna_tools = df_scrna_tools.dropna(subset=["Code"])

df_scrna_tools["name"] = df_scrna_tools["Name"]
df_scrna_tools["repo_url"] = df_scrna_tools["Code"]

df_scrna_tools["category"] = np.tile(
    ["cytomining-ecosystem-adjacent-tools"], (len(df_scrna_tools), 1)
).tolist()

# filter results to only those with a github link and sort values by number of citations
df_scrna_tools = df_scrna_tools[
    df_scrna_tools["Code"].str.contains("https://github.com")
].sort_values(by=["Citations"], ascending=False)

# show a previow of the results
df_scrna_tools.head(5)[["name", "repo_url", "category"]]
# -

# convert top 100 results to projects-like dataset
df_scrna_tools_records = df_scrna_tools.head(100)[
    ["name", "repo_url", "category"]
].to_dict(orient="records")
df_scrna_tools_records[:5]

# append results from both datasets together
results = df_scrna_tools_records + results

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

# append target projects to the results
results = Box.from_yaml(filename="data/target-projects.yaml").projects + results

# export the results to a yaml file for later processing
Box({"projects": results}).to_yaml("data/projects.yaml")
