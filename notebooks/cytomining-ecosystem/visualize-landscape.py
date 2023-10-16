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
import os
import random
from datetime import datetime

import pandas as pd
import plotly.colors as pc
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pytz
from box import Box
from plotly.offline import plot
from plotly.subplots import make_subplots

# set plotly default theme
pio.templates.default = "simple_white"

# get the current datetime
tz = pytz.timezone("UTC")
current_datetime = datetime.now(tz)

# set common str's
title_prefix = "Cytomining Ecosystem Software Landscape Analysis"

# export locations relative to this notebook
export_dir = "../../docs/reports/cytomining-ecosystem/"
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
    color="category",  # Color bars based on the "category" column
    text="Count",  # Display the count as labels on the bars
    title="Number of Projects by Primary Programming Language and Category",
    orientation="h",  # Horizontal orientation for the bars
    category_orders={
        "Primary language": programming_language_counts["Primary language"].tolist()
    },  # Sort bars by programming language counts
    width=1200,
    height=500,
)

# Customize layout to display count labels properly
fig_languages.update_traces(
    texttemplate="%{text}",
    textposition="inside",
)
fig_languages.update_layout(
    title=f"{title_prefix}: Project Primary Language Count",
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

# set a minimum size for the plot points
# fig_user_base.update_traces(marker=dict(sizemin=20))

# customize the chart layout
fig_usage_stars.update_layout(
    title=f"{title_prefix}: Project Star Count and Age in Years",
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

# set a minimum size for the plot points
# fig_user_base.update_traces(marker=dict(sizemin=20))

# customize the chart layout
fig_contributors_and_issues.update_layout(
    title=f"{title_prefix}: Project Open Issues and Contributors",
    # xaxis_title="Project Age (years)",
    # yaxis_title="GitHub Stars Count",
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
    <title>Way Lab: Software Landscape Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta charset="UTF-8">
</head>

<body>
    """
    )
    for fig in fig_collection:
        f.write(
            fig.to_html(
                full_html=False, include_plotlyjs="cdn" if not cdn_included else False
            )
        )
    f.write("</body></html>")

# +
# bubble scatter plot
fig = px.scatter(
    df_projects,
    hover_name="Project Name",
    x="Duration Created to Now in Years",
    y="GitHub Forks",
    size="GitHub Contributors",
    color="category",
    width=1250,
    height=500,
)

# set a minimum size for the plot points
fig.update_traces(marker=dict(sizemin=5))

# customize the chart layout
fig.update_layout(
    title=f"{title_prefix}: User Base Size",
    xaxis_title="Project Age (years)",
    yaxis_title="GitHub Forks Count",
    # set legend placement over chart for space conservation
    legend=dict(x=0.005, y=1.0005, traceorder="normal", bgcolor="rgba(0,0,0,0)"),
)

# export to html
plot(fig, filename=f"{export_dir}/maturity.html", auto_open=False)

# Show the chart
fig.show()
# -


