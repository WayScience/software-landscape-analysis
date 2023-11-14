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

# # Gather Targeted Publication Mentions
#
# Gather targeted mentions of software within publications (journals, preprints, etc) for software landscape analysis related to Cytomining ecosystem.
#

# +
import os
from typing import List

import awkward as ak
import duckdb
import numpy as np
import pandas as pd
from biorxiv_retriever import BiorxivRetriever
from box import Box
from scholarly import scholarly
from thefuzz import fuzz

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
loi_target_project_years["Date Created Year"] = loi_target_project_years[
    "Date Created"
].dt.year
loi_target_project_years = loi_target_project_years[
    ["Project Name", "Date Created Year"]
]
loi_target_project_years

# instantiate record data as a list of record dictionaries
pub_metrics = loi_target_project_years.to_dict(orient="records")
pub_metrics

# +
# expand the records with Google Scholar results from Scholarly pkg
pub_metrics = [
    dict(
        project,
        **{
            "google_scholar_search_results": [
                result
                for result in scholarly.search_pubs(
                    # wrap the query in quotes to isolate as exact matches only
                    query=f'"{project["Project Name"]}"',
                    # specify a minimum year for the query
                    # (we shouldn't include results which were published
                    # before the project existed)
                    year_low=project["Date Created Year"],
                )
            ]
        },
    )
    for project in pub_metrics
]

# show the len of the results for each project
{
    project["Project Name"]: len(project["google_scholar_search_results"])
    for project in pub_metrics
}

# +
# expand the records with Bioarxiv results from Scholarly pkg
bioarxiv_retriever = BiorxivRetriever()

pub_metrics = [
    dict(
        project,
        **{
            "bioarxiv_search_results": [
                # exclude full_text from the data we store (only use for filtering)
                {key: val for key, val in paper.items() if key != "full_text"}
                # gather results from bioarxiv search query
                for paper in bioarxiv_retriever.query(
                    f'"{project["Project Name"]}"', metadata=True, full_text=True
                )
                # only include the paper result if the project name is found within the full text
                if project["Project Name"].lower() in paper["full_text"].lower()
            ],
        },
    )
    for project in pub_metrics
]

# show the len of the results for each project
{
    project["Project Name"]: len(project["bioarxiv_search_results"])
    for project in pub_metrics
}
# -

# preview the nested data structure so far for the work ahead
ak.Array(pub_metrics)

# form data for total counts of publications
pub_metrics = [
    dict(
        project,
        **{
            # form a list of all unique article titles
            "all_article_titles": list(
                # convert to a set in order to dedupe exact matches
                set(
                    [
                        article
                        # use differing data structures to create the list of titles
                        for article in list(
                            [
                                article["bib"]["title"]
                                for article in project["google_scholar_search_results"]
                            ]
                            + [
                                article["title"]
                                for article in project["bioarxiv_search_results"]
                            ]
                        )
                    ]
                )
            ),
        }
    )
    for project in pub_metrics
]
pub_metrics[0]["all_article_titles"]


# +
# gather distinct data using record linkage levenshtein distance
def return_distinct_values_by_threshold(
    string_list: List[str], threshold: int
) -> List[str]:
    """
    Finds and returns a new list of distinct values based on
    record linkage via Levenshtein distance.
    """
    distinct_list = []

    # compare every value pair-wise
    for i in range(len(string_list)):
        for j in range(i + 1, len(string_list)):
            if (
                # if the value is distinct (below the threshold of similarity)
                # and not yet included in the similar list, append it to the result
                fuzz.ratio(string_list[i], string_list[j]) <= threshold
                and string_list[i] not in distinct_list
            ):
                distinct_list.append((string_list[i]))

    return distinct_list


pub_metrics = [
    dict(
        project,
        **{
            # form a list of all unique article titles
            "all_article_titles_record_linked_removed": return_distinct_values_by_threshold(
                project["all_article_titles"], threshold=90
            ),
        }
    )
    for project in pub_metrics
]
pub_metrics[0]["all_article_titles_record_linked_removed"]
# -

# gather counts from the data and export to file
pub_metrics = [
    dict(
        project,
        **{
            "google_scholar_count": len(project["google_scholar_search_results"]),
            "bioarxiv_count": len(project["bioarxiv_search_results"]),
            "total_pub_count": len(project["all_article_titles"]),
            "total_pub_count_non_record_linked": len(
                project["all_article_titles_record_linked_removed"]
            ),
        },
    )
    for project in pub_metrics
]
ak.to_parquet(
    ak.Array(pub_metrics), "data/loi-target-project-publication-metrics.parquet"
)

# depict results from the file
with duckdb.connect() as ddb:
    pub_totals = ddb.query(
        f"""
    SELECT 
        pubstats."Project Name",
        pubstats."Date Created Year",
        pubstats."Date Created Year",
        pubstats."google_scholar_count",
        pubstats."bioarxiv_count",
        pubstats."total_pub_count",
        pubstats."total_pub_count_non_record_linked"
    FROM read_parquet('data/loi-target-project-publication-metrics.parquet') as pubstats
    """,
    ).df()
pub_totals
