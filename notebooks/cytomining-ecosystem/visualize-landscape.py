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
    height=600,
)

# Customize layout to display count labels properly
fig_languages.update_traces(
    texttemplate="%{text}",
    textposition="inside",
)
fig_languages.update_layout(
    title=f"{title_prefix}: Top Languages",
)

# Show the plot
fig_languages.show()

# +
# bubble scatter plot
fig_user_base = px.scatter(
    df_projects,
    hover_name="Project Name",
    x="Duration Created to Now in Years",
    y="GitHub Stars",
    width=1000,
    height=800,
    color="category",
    color_discrete_sequence=random.sample(pc.qualitative.Prism, 3),
)

# set a minimum size for the plot points
# fig_user_base.update_traces(marker=dict(sizemin=20))

# customize the chart layout
fig_user_base.update_layout(
    title=f"{title_prefix}: User Base Size",
    xaxis_title="Project Age (years)",
    yaxis_title="GitHub Stars Count",
)

fig_user_base.show()

# +
# Create subplots with one row and two columns
fig = make_subplots(
    rows=2,
    cols=2,
    specs=[
        [{"type": "scatter"}, None],
        [{"type": "bar"}, None],
    ],
    row_heights=[0.3, 0.3],
)

legendgroup_incrementor = 0

# Add scatter plot to the second column
for trace in fig_languages.data:
    # trace.legendgroup = legendgroup_incrementor
    fig.add_trace(
        trace,
        row=2,
        col=1,
    )

legendgroup_incrementor += 1

# Add lang chart to the first column
for trace in fig_user_base.data:
    # trace.legendgroup = legendgroup_incrementor
    fig.add_trace(trace, row=1, col=1)

# Update the subplot with custom axis labels
fig.update_xaxes(title_text="Project Age (years)", row=1, col=1)
fig.update_yaxes(title_text="GitHub Stars Count", row=1, col=1)

# Update layout
fig.update_layout(
    title_text=f"{title_prefix}",
    # title_x=0.5,  # Center the title
    # showlegend=False,
    height=1200,
    # legend=dict(x=0, y=1, traceorder="normal", orientation="h"),
    # legend_tracegroupgap=800,
)

"""plot(
    fig,
    filename=f"{export_dir}/landscape.html",
    auto_open=False,
)"""

# Show the subplot
# fig.show()

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


