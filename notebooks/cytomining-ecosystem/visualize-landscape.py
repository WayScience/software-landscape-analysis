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

# # Visualize Cytomining Ecosystem Landscape
#
# Visualizations related to Cytomining ecosystem software landscape analysis.
#
# ## Plot Foci
#
# ### User base size
#
# Bubble scatter plot:
# - Duration Created to Most Recent Commit: distinguishing projects which have been around longer may be used more.
# - GitHub Stars: as a general metric of unique interested users.
# - GitHub Watchers: as a general metric of unique interested users.
# - Color: distinguishing categories of projects.
#
# ### Usage
#
# ### Maturity

# +
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.io as pio
import pytz
from box import Box
from plotly.offline import plot

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

# read in target project data
projects = Box.from_yaml(filename="data/target-projects.yaml").projects
df_ref_projects = pd.DataFrame(projects)
# statically set a single category
df_ref_projects["category"] = df_ref_projects["category"].str[0]
df_ref_projects.head()

# read in project metric data
df_projects = pd.read_parquet("data/project-github-metrics.parquet")
df_projects.info()

# add target project categories
df_projects = pd.merge(
    left=df_projects,
    right=df_ref_projects[["repo_url", "category"]],
    how="left",
    left_on="Project Repo URL",
    right_on="repo_url",
)
df_projects

# +
# create a duration for relative comparisons below
df_projects["Duration Created to Now"] = current_datetime - df_projects["Date Created"]

# create a years count for project time duration
df_projects["Duration Created to Now in Years"] = (
    df_projects["Duration Created to Now"].dt.days / 365
)

# +
# bubble scatter plot
fig = px.scatter(
    df_projects,
    hover_name="Project Name",
    x="Duration Created to Now in Years",
    y="GitHub Stars",
    size="GitHub Watchers",
    color="category",
    width=1250,
    height=500,
)

# set a minimum size for the plot points
fig.update_traces(marker=dict(sizemin=3))

# customize the chart layout
fig.update_layout(
    title=f"{title_prefix}: User Base Size",
    xaxis_title="Project Age (years)",
    yaxis_title="GitHub Stars Count",
    # set legend placement over chart for space conservation
    legend=dict(x=0.005, y=1.0005, traceorder="normal", bgcolor="rgba(0,0,0,0)"),
)

# Show the chart
fig.show()
# -

# export to html
plot(fig, filename=f"{export_dir}/user-base-size.html", auto_open=False)


