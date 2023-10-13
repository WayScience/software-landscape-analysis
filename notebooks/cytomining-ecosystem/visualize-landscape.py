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


# -

def create_language_pie_chart(df_projects, category):
    # Flatten the dictionaries into a list of key-value pairs
    key_value_pairs = [
        (key, value)
        for language_dict in df_projects["GitHub Detected Languages"]
        for key, value in language_dict.items()
        if value is not None
    ]

    # Create a new DataFrame from the flattened data
    # Then group by 'Language' and calculate the total numbers for each language
    total_numbers = (
        pd.DataFrame(key_value_pairs, columns=["Language", "Value"])
        .head(10)
        .groupby("Language")["Value"]
        .sum()
        .reset_index()
    )

    # Create a pie chart using Plotly Express
    fig = px.pie(
        total_numbers,
        names="Language",
        values="Value",
        title="Pie Chart Example",
        color_discrete_sequence=random.sample(pc.qualitative.Prism, 10),
    )

    # Remove the legend
    fig.update_layout(
        title=f"{title_prefix}: {category} - Top Languages", showlegend=False
    )

    # return the plot
    return fig


def create_user_base_chart(df_projects, category):
    # bubble scatter plot
    fig = px.scatter(
        df_projects,
        hover_name="Project Name",
        x="Duration Created to Now in Years",
        y="GitHub Stars",
        size="GitHub Watchers",
        width=1250,
        height=800,
        color="category",
        color_discrete_sequence=random.sample(pc.qualitative.Prism, 2),
    )

    # set a minimum size for the plot points
    fig.update_traces(marker=dict(sizemin=4))

    # customize the chart layout
    fig.update_layout(
        title=f"{title_prefix}: {category} - User Base Size",
        xaxis_title="Project Age (years)",
        yaxis_title="GitHub Stars Count",
    )

    # return the chart
    return fig


def create_plots_for_categories(df_projects, category):
    # Create subplots with one row and two columns
    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[
            [{"type": "scatter", "colspan": 2}, None],
            [{"type": "pie"}, None],
        ],
        row_heights=[0.8, 0.2],
    )

    legendgroup_incrementor = 0

    # Add scatter plot to the second column
    scatter = create_user_base_chart(df_projects, category)
    for trace in scatter.data:
        trace.legendgroup = legendgroup_incrementor
        fig.add_trace(
            trace,
            row=1,
            col=1,
        )

    legendgroup_incrementor += 1

    # Add pie chart to the first column
    pie = create_language_pie_chart(df_projects, category)
    for trace in pie.data:
        trace.legendgroup = legendgroup_incrementor
        fig.add_trace(trace, row=2, col=1)

    # Update the subplot with custom axis labels
    fig.update_xaxes(title_text="Project Age (years)", row=1, col=1)
    fig.update_yaxes(title_text="GitHub Stars Count", row=1, col=1)

    # Update layout
    fig.update_layout(
        title_text=f"{title_prefix}: {category}",
        # title_x=0.5,  # Center the title
        # showlegend=False,
        height=1200,
        # legend=dict(x=0, y=1, traceorder="normal", orientation="h"),
        legend_tracegroupgap=800,
    )

    plot(
        fig,
        filename=f"{export_dir}/{category.replace(' ','-').lower()}.html",
        auto_open=False,
    )

    # Show the subplot
    fig.show()


for category in (
    df_projects[df_projects["category"] != "loi-focus"]["category"].dropna().unique()
):
    target_df = df_projects[df_projects["category"].isin(["loi-focus", category])]
    category_title = category.replace("-", " ").title()
    create_plots_for_categories(target_df, category_title)

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


