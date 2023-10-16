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

# # Visualize Cytomining Ecosystem Software Landscape
#
# Visualizations related to Cytomining ecosystem software landscape analysis.
#
# ## Plot Foci
#
# - User base size
# - Usage
# - Maturity

# +
import asyncio
import os
import pathlib
import random
from datetime import datetime

import nest_asyncio
import pandas as pd
import plotly.colors as pc
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pytz
from box import Box
from plotly.offline import plot
from plotly.subplots import make_subplots
from pyppeteer import launch
from ydata_profiling import ProfileReport

# set plotly default theme
pio.templates.default = "simple_white"

# get the current datetime
tz = pytz.timezone("UTC")
current_datetime = datetime.now(tz)

# set common str's
title_prefix = "Cytomining Ecosystem Software Landscape Analysis"

# export locations relative to this notebook
export_dir = "../../docs/reports/cytomining-ecosystem"
# -

# read in project metric data
df_projects = pd.read_parquet("data/project-github-metrics.parquet")
df_projects = df_projects.reset_index(drop=True)
df_projects.info()

df_projects["category"] = df_projects["Project Landscape Category"].str[0]
df_projects.head(5)

# +
# create a duration for relative comparisons below
df_projects["Duration Created to Now"] = current_datetime - df_projects["Date Created"]

# create a years count for project time duration
df_projects["Duration Created to Now in Years"] = (
    df_projects["Duration Created to Now"].dt.days / 365
)
# -

# create a ydata_profiling profile
profile = ProfileReport(df_projects, title=f"{title_prefix}: Data Profile Report")
profile.to_notebook_iframe()

profile.to_file(f"{export_dir}/data_profile.html")

# create list to collect the figures for later display together
fig_collection = []


# +
# Function to find the top language for each row
def find_top_language(languages):
    if isinstance(languages, dict):
        non_empty_languages = {
            key: value for key, value in languages.items() if value is not None
        }
        if non_empty_languages:
            return max(non_empty_languages, key=non_empty_languages.get)
    return None


# Apply the function to the "GitHub Detected Languages" column and create a new column "Primary programming language"
df_projects["Primary language"] = df_projects["GitHub Detected Languages"].apply(
    find_top_language
)
df_projects[["Project Name", "Primary language"]]

# +
# Create a pie chart using Plotly Express
grouped_data = (
    df_projects.groupby(["Primary language", "category"])
    .size()
    .reset_index(name="Count")
)

# Group by "Primary programming language" and calculate the sum of counts for each programming language
programming_language_counts = (
    grouped_data.groupby("Primary language")["Count"].sum().reset_index()
)

# Sort programming languages by the sum of counts in descending order
programming_language_counts = programming_language_counts.sort_values(
    by="Count", ascending=False
)

# Create a horizontal bar chart using Plotly Express
fig_languages = px.bar(
    grouped_data,
    y="Primary language",
    x="Count",
    color="category",
    text="Count",
    title="Number of Projects by Primary Programming Language and Category",
    orientation="h",
    # Sort bars by programming language counts
    category_orders={
        "Primary language": programming_language_counts["Primary language"].tolist()
    },
    width=1200,
    height=500,
)

# Customize layout to display count labels properly
fig_languages.update_traces(
    texttemplate="%{text}",
    textposition="inside",
)
fig_languages.update_layout(
    title=f"Project Primary Language Count",
)

fig_collection.append(fig_languages)

# Show the plot
fig_languages.show()

# +
# bubble scatter plot
fig_usage_stars = px.scatter(
    df_projects,
    hover_name="Project Name",
    x="Duration Created to Now in Years",
    y="GitHub Stars",
    width=1200,
    height=500,
    color="category",
    color_discrete_sequence=random.sample(pc.qualitative.Prism, 5),
)


# customize the chart layout
fig_usage_stars.update_layout(
    title=f"Project Star Count and Age in Years",
    xaxis_title="Project Age (years)",
    yaxis_title="GitHub Stars Count",
)

fig_collection.append(fig_usage_stars)

fig_usage_stars.show()

# +
# bubble scatter plot
fig_contributors_and_issues = px.scatter(
    df_projects,
    hover_name="Project Name",
    x="GitHub Open Issues",
    y="GitHub Contributors",
    width=1200,
    height=500,
    color="category",
    color_discrete_sequence=random.sample(pc.qualitative.Prism, 5),
)


# customize the chart layout
fig_contributors_and_issues.update_layout(
    title=f"Project Open Issues and Contributors",
)

fig_collection.append(fig_contributors_and_issues)

fig_contributors_and_issues.show()
# -

cdn_included = False
with open(f"{export_dir}/report.html", "w") as f:
    f.write(
        """
<html>

<head>
    <title>Cytomining Ecosystem Software Landscape Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta charset="UTF-8">
</head>
<style>
body {
    font-family: 'Arial', sans-serif;
}
</style>
<body>
<h1>Cytomining Ecosystem Software Landscape Analysis</h1>
<br>
    """
    )
    for fig in fig_collection:
        f.write(
            fig.to_html(
                full_html=False, include_plotlyjs="cdn" if not cdn_included else False
            )
        )
        f.write("<br><br>")
    f.write("</body></html>")

# +
# capture the html page as a png export

# allow for nested asyncio ops
nest_asyncio.apply()


# define function for pyppeteer to capture image
# see: https://github.com/pyppeteer/pyppeteer#examples
async def capture_screenshot(file_path, output_path):
    browser = await launch(headless=True)
    page = await browser.newPage()
    # set the size of the capture
    await page.setViewport({"width": 1400, "height": 1700})
    await page.goto(f"file://{file_path}")

    await page.screenshot({"path": output_path})
    await browser.close()


# Capture screenshot from html page
asyncio.get_event_loop().run_until_complete(
    capture_screenshot(
        file_path=pathlib.Path(f"{export_dir}/report.html").resolve(),
        output_path=f"{export_dir}/report.png",
    )
)

