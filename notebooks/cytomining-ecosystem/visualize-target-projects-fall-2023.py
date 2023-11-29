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

# # Visualize Cytomining Ecosystem Target Software Data
#
# Visualizations related to Cytomining ecosystem software targeted project data.
#

# +
import asyncio
import itertools
import os
import pathlib
import random
import re
import shutil
from datetime import datetime

import duckdb
import nest_asyncio
import networkx as nx
import netwulf as nw
import numpy as np
import pandas as pd
import plotly
import plotly.colors as pc
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pytz
import pyvis
from box import Box
from IPython.display import IFrame
from itables import to_html_datatable
from pandas.api.types import CategoricalDtype
from plotly.offline import plot
from plotly.subplots import make_subplots
from pyppeteer import launch
from pyvis.network import Network
from ydata_profiling import ProfileReport

# set plotly default theme
pio.templates.default = "simple_white"

# get the current datetime
tz = pytz.timezone("UTC")
current_datetime = datetime.now(tz)

# set common str's
title_prefix = "Cytomining Ecosystem Target Software Analysis"

# export locations relative to this notebook
export_dir = "../../docs/cytomining-ecosystem"

# set a color sequence for general use
category_color_sequence = pc.qualitative.Dark2

# set a color sequence for project-specific colors
project_color_sequence = [
    pc.qualitative.Dark2[3],
    pc.qualitative.Dark2[0],
    pc.qualitative.Dark2[1],
]

# set section descriptions
section_descriptions = {
    "Scholarly Papers": """
    This section helps visualize data related to how many
    scholarly papers mention or cite the target software.
    """,
    "Package Usage": """
    This section helps depict usage of the target software
    by leveraging package data from PyPI and Conda.
    """,
    "Software dependents": """
    This section helps show community dependents of the
    targeted software.
    """,
    "Project Visitors": """
    This section helps show how many visitors have
    have interacted with the project over time.
    """,
}
# -

# read data from various files
with duckdb.connect() as ddb:
    tgt_software_df = ddb.query(
        f"""
    SELECT
        pkgstats."Project Name",
        pubstats."Date Created Year",
        pubstats."google_scholar_count",
        pubstats."biorxiv_count",
        pubstats."total_pub_count",
        pubstats."total_pub_count_non_record_linked",
        pkgstats.pypi_downloads_total_unnested AS pypi_downloads_total,
        pkgstats.pypi_downloads_by_month,
        pkgstats.pypi_downloads_monthly_average,
        pkgstats.pypi_downloads_monthly_median,
        pkgstats.conda_downloads_total,
        pkgstats.conda_downloads_by_month,
        pkgstats.conda_downloads_monthly_average,
        pkgstats.conda_downloads_monthly_median,
        ghstats."GitHub Stars",
        ghstats."GitHub Contributor Total Count",
        ghstats."GitHub Network Count",
        ghstats."GitHub Code Search Used By",
        ghstats."GitHub Dependents",
        ghstats."GitHub Dependency Graph Dependents Count",
        ghstats."GitHub Code Search Dependents Count",
        ghstats."GitHub Total Dependents Count",
        ghstats."GitHub Stargazers Count by Month",
        ghstats."GitHub Stargazers Count by Month Average",
        ghstats."GitHub Stargazers Count by Month Median",
        ghstats."GitHub Stargazers Count by Year Average",
        ghstats."GitHub Stargazers Count by Year Median"
    FROM read_parquet('data/loi-target-project-package-metrics.parquet') as pkgstats
    JOIN read_parquet('data/loi-target-project-github-metrics.parquet') as ghstats ON
        pkgstats."Project Name" = ghstats."Project Name"
    JOIN read_parquet('data/loi-target-project-publication-metrics.parquet') as pubstats ON
        pkgstats."Project Name" = pubstats."Project Name"
    """,
    ).df()
tgt_software_df.info()

tgt_software_df.head()

# create list to collect the figures for later display together
fig_collection = []

# +
# Publications for target projects

fig_publications = px.pie(
    title="Pycytominer Publication Mentions or Citations",
    data_frame=tgt_software_df[["google_scholar_count", "biorxiv_count"]].T,
    values=0,
    names=["Google Scholar Results", "BioRxiv Preprints"],
    hover_name=["Google Scholar Results", "BioRxiv Preprints"],
    width=500,
    height=500,
)
fig_publications.update_traces(textinfo="value")

fig_collection.append(
    {
        "plot": fig_publications,
        "description": """
        This plot shows how many publications mention or cite Pycytominer
        as a reference. We used Google Scholar and BioRxiv as search resources
        for this work. Google Scholar is a scholarly article aggregator and search service.
        BioRxiv is a pre-print server with biological focus.
        """,
        "findings": """
        We observe that Pycytominer appears in 22 Google Scholar results and 14 BioRxiv
        preprints. This demonstrates how Pycytominer is already being used in both
        previous and ongoing research efforts.
        """,
        "section": "Scholarly Papers",
    }
)

fig_publications.show()

# +
# visualize package data

# Create a horizontal bar chart using Plotly Express
fig_packages = px.bar(
    data_frame=tgt_software_df.sort_values("Project Name"),
    x=["pypi_downloads_total", "conda_downloads_total"],
    y="Project Name",
    orientation="h",
    width=1200,
    height=500,
    color_discrete_sequence=[category_color_sequence[2], category_color_sequence[0]],
)

fig_packages.update_layout(
    title="PyPI and Conda Package Downloads by Project",
    xaxis_title="Package Downloads",
    showlegend=False,
)

fig_collection.append(
    {
        "plot": fig_packages,
        "description": """This plot shows the total number of PyPI and Conda downloads by project.
        PyPI (Python Package Index) is a platform which is commonly used to download Python packages.
        Conda is an environment and package management service which is commonly used for data science
        projects.
        """,
        "findings": """This plot demonstrates how pycytominer has many downloads through both PyPI and Conda
        (with slightly more Conda downloads). CytoTable and CytoSnake are shown with strong early download counts
        at a much lower level (perhaps in alignment with their project age, which is less than pycytominer).
        """,
        "section": "Package Usage",
    }
)

# Show the plot
fig_packages.show()

# +
pypi_monthly_data = pd.concat(
    pd.DataFrame(
        [
            dict(month_entry, **{"Project Name": project_name})
            for month_entry in monthly_data
        ]
    )
    for project_name, monthly_data in zip(
        tgt_software_df["Project Name"], tgt_software_df["pypi_downloads_by_month"]
    )
)
fig_pypi_monthly = px.line(
    data_frame=pypi_monthly_data,
    title=f"Project PyPI Package Downloads by Month",
    x="download_month",
    y="download_count",
    color="Project Name",
    width=1200,
    height=500,
    markers=True,
    symbol_sequence=["square"],
    color_discrete_sequence=[project_color_sequence[0], project_color_sequence[2]],
)
fig_pypi_monthly.update_layout(
    xaxis_title="Month",
    yaxis_title="Downloads",
)

fig_collection.append(
    {
        "plot": fig_pypi_monthly,
        "description": """This plot shows how many PyPI package downloads per month by project.
        CytoSnake is excluded from this plot as it is not available on PyPI.
        """,
        "findings": """Pycytominer has a consistent and trending upward number of monthly PyPI package downloads.
        CytoTable shows activity in this area, possibly trending upwards.
        """,
        "section": "Package Usage",
    }
)


fig_pypi_monthly.show()

# +
conda_monthly_data = pd.concat(
    pd.DataFrame(
        [
            dict(month_entry, **{"Project Name": project_name})
            for month_entry in [
                {"download_month": key, "download_count": val}
                for key, val in monthly_data.items()
            ]
        ]
    )
    for project_name, monthly_data in zip(
        tgt_software_df["Project Name"], tgt_software_df["conda_downloads_by_month"]
    )
    if isinstance(monthly_data, dict)
)
fig_conda_monthly = px.line(
    data_frame=conda_monthly_data,
    title=f"Project Conda Package Downloads by Month",
    x="download_month",
    y="download_count",
    color="Project Name",
    width=1200,
    height=500,
    markers=True,
    symbol_sequence=["diamond"],
    color_discrete_sequence=[project_color_sequence[0], project_color_sequence[1]],
)
fig_conda_monthly.update_layout(
    xaxis_title="Month",
    yaxis_title="Downloads",
)

fig_collection.append(
    {
        "plot": fig_conda_monthly,
        "description": """This plot shows how many Conda package downloads per month by project.
        CytoTable is excluded from this plot as it is not available on Conda.
        """,
        "findings": """We can observe from this plot that pycytominer is actively downloaded on monthly basis.
        There is a large spike in download count for pycytominer in 2022 with lower counts in 2023.
        CytoSnake shows strong signs of good adoption for a relatively young project (in comparison with pycytominer).
        """,
        "section": "Package Usage",
    }
)

fig_conda_monthly.show()

# +
# visualize dependents data

# Create a horizontal bar chart using Plotly Express
fig_dependents_count = px.bar(
    data_frame=tgt_software_df[
        tgt_software_df["GitHub Total Dependents Count"] != 0
    ].sort_values("Project Name"),
    x="GitHub Total Dependents Count",
    y="Project Name",
    orientation="h",
    width=1200,
    height=500,
    color_discrete_sequence=[pc.qualitative.Vivid[2]],
)

fig_dependents_count.update_layout(
    title="GitHub Dependency Graph and Code Search Dependents Count by Project",
    xaxis_title="Dependents",
    legend_title_text="Dependent Type",
)

fig_collection.append(
    {
        "plot": fig_dependents_count,
        "description": """This plot shows dependents counts of the projects by leveraging the Dependency Graph and
        code search features of GitHub. Overlaps by organization and project name are removed to help count unique
        dependents.
        """,
        "findings": """We observe that Pycytominer has many existing dependents on GitHub.
        CytoTable has a smaller number of dependents which may be relative to the project age.
        """,
        "section": "Software dependents",
    }
)

# Show the plot
fig_dependents_count.show()

# +
# create a dependent graph to visualize project connections
dependent_data = pd.concat(
    pd.DataFrame(
        [
            {
                "Project Name": project_name,
                "dependent": dependent.replace("cytomining/CytoTable", "CytoTable"),
                "color": "#E7358A"
                if project_name == "pycytominer"
                else "#D9651D"
                if project_name == "CytoTable"
                else "#698DC7",
            }
            for dependent in list(
                set(
                    code_search
                    + [
                        repo["name"]
                        for repo in graph_results["all_public_dependent_repos"]
                    ]
                )
            )
        ]
    )
    for project_name, code_search, graph_results in zip(
        tgt_software_df["Project Name"],
        tgt_software_df["GitHub Code Search Used By"],
        tgt_software_df["GitHub Dependents"],
    )
)

dependent_data

nx_dependent_data = nx.from_pandas_edgelist(
    df=dependent_data, source="dependent", target="Project Name", edge_attr=["color"]
)

nt_dependents = Network(height="500px", width="1200px")
# populates the nodes and edges data structures
nt_dependents.from_nx(nx_dependent_data)
nt_dependents.nodes = [
    dict(node, **{"color": "#E7358A"})
    if node["id"] == "pycytominer"
    else dict(node, **{"color": "#D9651D"})
    if node["id"] == "CytoTable"
    else node
    for node in nt_dependents.nodes
]
nt_dependents.toggle_physics(True)
nt_dependents.html_export_loc = "target-project-dependents.html"
nt_dependents.html_plot_title = "Project dependents Graph"
nt_dependents.show(nt_dependents.html_export_loc)


fig_collection.append(
    {
        "plot": nt_dependents,
        "description": """This graph shows how pycytominer and CytoTable are used as
        dependencies of existing projects on GitHub (from Dependency Graph and code search by name).
        Pycytominer is included as a pink node with edges in the same color. CytoTable is shown similarly in orange.
        """,
        "findings": """We observe pycytominer as being connected to many existing projects.
        CytoTable is also connected to many Pycytominer projects. This interconnection in part shows
        how these components are used together in related landscape projects.
            """,
        "section": "Software dependents",
    }
)


IFrame(src=nt_dependents.html_export_loc, height=520, width=1110)

# +
# alternative network graph for dependents
dependent_data = pd.concat(
    pd.DataFrame(
        [
            {
                "Project Name": project_name,
                "dependent": dependent.replace("cytomining/CytoTable", "CytoTable"),
                "color": "#E7358A"
                if project_name == "pycytominer"
                else "#D9651D"
                if project_name == "CytoTable"
                else "#698DC7",
            }
            for dependent in list(
                set(
                    code_search
                    + [
                        repo["name"]
                        for repo in graph_results["all_public_dependent_repos"]
                    ]
                )
            )
        ]
    )
    for project_name, code_search, graph_results in zip(
        tgt_software_df["Project Name"],
        tgt_software_df["GitHub Code Search Used By"],
        tgt_software_df["GitHub Dependents"],
    )
)

dependent_data

nx_dependent_data = nx.from_pandas_edgelist(
    df=dependent_data, source="dependent", target="Project Name", edge_attr=["color"]
)

nx.set_node_attributes(
    nx_dependent_data,
    values={
        node: "#E7358A"
        if node == "pycytominer"
        else "#D9651D"
        if node == "CytoTable"
        else "#698DC7"
        for node in nx_dependent_data.nodes
    },
    name="group",
)

"""stylized_network, config = nw.visualize(
    network=nx_dependent_data,
    config={"zoom": 2},
    is_test=True,
    plot_in_cell_below=False,
)"""

# +
# form monthly github star visual
star_monthly_data = pd.concat(
    pd.DataFrame(
        [
            dict(month_entry, **{"Project Name": project_name})
            for month_entry in [
                {"star_month": key, "star_count": val}
                for key, val in monthly_data.items()
            ]
        ]
    )
    for project_name, monthly_data in zip(
        tgt_software_df["Project Name"],
        tgt_software_df["GitHub Stargazers Count by Month"],
    )
    if isinstance(monthly_data, dict)
)
fig_stars_monthly = px.line(
    data_frame=star_monthly_data,
    title=f"Project GitHub Stars by Month",
    x="star_month",
    y="star_count",
    color="Project Name",
    markers=True,
    width=1200,
    height=500,
    symbol_sequence=["star"],
    color_discrete_sequence=project_color_sequence,
)
fig_stars_monthly.update_layout(
    xaxis_title="Month",
    yaxis_title="Stars",
)

fig_collection.append(
    {
        "plot": fig_stars_monthly,
        "description": """This plot shows GitHub stars as a way to understand visitor activity on a
        monthly basis for the target projects.
        GitHub stars are an indication of unique users whom are interested in and likely use the project somehow.
        """,
        "findings": """We can observe pycytominer has having a relatively consistent number of added GitHub stars
        since mid-2019. We also show that CytoSnake and CytoTable somewhat mimic the earlier growth in this area
        which pycytominer demonstrated.
        """,
        "section": "Project Visitors",
    }
)

fig_stars_monthly.show()

# +
# form cumulative sum outlook of the monthly star data
star_monthly_data["star_count_cumulative_sum"] = star_monthly_data.groupby(
    "Project Name"
)["star_count"].transform(pd.Series.cumsum)

fig_stars_monthly_cumulative_sum = px.line(
    data_frame=star_monthly_data,
    title=f"Project GitHub Stars by Month (cumulative)",
    x="star_month",
    y="star_count_cumulative_sum",
    color="Project Name",
    markers=True,
    width=1200,
    height=500,
    symbol_sequence=["star"],
    color_discrete_sequence=project_color_sequence,
)
fig_stars_monthly_cumulative_sum.update_layout(
    xaxis_title="Month",
    yaxis_title="Stars (cumulative)",
)

fig_collection.append(
    {
        "plot": fig_stars_monthly_cumulative_sum,
        "description": """This plot shows GitHub stars as a way to understand visitor activity on a
        monthly basis for the target projects.
        This plot differs from the one above in that the star counts are shown as cumulative.
        GitHub stars are an indication of unique users whom are interested in and likely use the project somehow.
        """,
        "findings": """We can observe pycytominer has having a relatively consistent number of added GitHub stars
        since mid-2019. We also show that CytoSnake and CytoTable somewhat mimic the earlier growth in this area
        which pycytominer demonstrated.
        """,
        "section": "Project Visitors",
    }
)

fig_stars_monthly_cumulative_sum.show()
# -

# organize figures by their sections and the order in which they appeared in this notebook
fig_collection_grouped = {
    key: [
        {
            "plot": entry["plot"],
            "description": entry["description"],
            "findings": entry["findings"],
        }
        for entry in group
    ]
    for key, group in itertools.groupby(fig_collection, key=lambda x: x["section"])
}
fig_collection_grouped.keys()

cdn_included = False
with open(f"{export_dir}/target-project-report.html", "w") as f:
    f.write(
        """
<html>
<!-- referenced with modifications from example work on: https://github.com/KrauseFx/markdown-to-html-github-style -->

<head>
    <title>Cytomining Ecosystem | Way Lab: Software Landscape Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta charset="UTF-8">
    <link rel="stylesheet" href="../css/style.css">
</head>

<body>
    <div id='content'>
        <h1>Cytomining Ecosystem Software Landscape Analysis - Target Project Report</h1>

        <p>This is a targeted report to help describe three Cytomining Ecosystem software projects
        in terms of scholarly paper mentions, package usage, software dependents, and project visitors.</p>

        <p>Code related to this effort may be found at: <a
                href="https://github.com/WayScience/software-landscape-analysis">https://github.com/WayScience/software-landscape-analysis</a>.
        </p>
    """
    )

    for section, figures in fig_collection_grouped.items():
        f.write(f"<h2>{section}</h2>")
        f.write(f"<p>{section_descriptions[section]}</p>")
        f.write(f"<br><br>")
        for figure in figures:
            # if working with plotly figure
            if isinstance(figure["plot"], plotly.graph_objs._figure.Figure):
                f.write(
                    figure["plot"].to_html(
                        full_html=False,
                        include_plotlyjs="cdn" if not cdn_included else False,
                    )
                )
            # if working with pyvis graph
            elif isinstance(figure["plot"], pyvis.network.Network):
                # write the network plot to docs dir
                figure["plot"].show(f"{export_dir}/{figure['plot'].html_export_loc}")

                # copy the dependencies of the work to docs dir
                try:
                    shutil.copytree(
                        src="./lib", dst=f"{export_dir}/lib", dirs_exist_ok=True
                    )
                except:
                    continue

                # use an iframe to display the result within the same page as other figures
                f.write(
                    f"""
                    <br><br>
                    <span style='font-size:1.17em'>{figure['plot'].html_plot_title} (click and scroll with mouse to interact)</span>
                    <iframe src="{figure['plot'].html_export_loc}"
                     style="overflow:hidden;width:1201px;height:520px;border:0px;">Browser not compatible with iframe rendering.</iframe>
                    <br><br>
                    """
                )

                # correct the file for invalid html
                def fix_html(
                    file_path,
                    strs_to_replace=[
                        "<h1></h1>",
                        "<center>",
                        "</center>",
                    ],
                ):
                    with open(file_path, "r") as file:
                        lines = [
                            re.sub(
                                "|".join(map(re.escape, strs_to_replace)),
                                "",
                                line.replace(
                                    "<head>",
                                    "<head><title>Cytomining Ecosystem Target Project Dependents Graph</title>",
                                ),
                            )
                            for replace_str in strs_to_replace
                            for line in file
                        ]

                    with open(file_path, "w") as file:
                        file.writelines(lines)

                fix_html(f"{export_dir}/{figure['plot'].html_export_loc}")

            else:
                raise Exception("Unknown plot type used.")

            f.write(
                f"""
            <ul>
            <li><strong>Description:</strong> {figure['description']}</li>
            <li><strong>Findings:</strong> {figure['findings']}</li>
            </ul>
            """
            )
            cdn_included = True

    f.write(
        """
        <h2>Table with selected dataset columns</h2>
        <p>The table below may be used to search and view a selected number of columns from the dataset.</p>
        """
    )

    # rename columns for visibility
    tgt_software_df = tgt_software_df.rename(
        columns={
            "google_scholar_count": "Google Scholar Count",
            "biorxiv_count": "bioRxiv Count",
            "pypi_downloads_total": "PyPI Downloads Total",
            "pypi_downloads_monthly_average": "PyPI Downloads Monthly Avg",
            "conda_downloads_total": "Conda Downloads Total",
            "conda_downloads_monthly_average": "Conda Downloads Monthly Avg",
        }
    )

    # write an itable to the page
    f.write(
        to_html_datatable(
            tgt_software_df[
                [
                    "Project Name",
                    "Date Created Year",
                    "Google Scholar Count",
                    "bioRxiv Count",
                    "PyPI Downloads Total",
                    "PyPI Downloads Monthly Avg",
                    "Conda Downloads Total",
                    "Conda Downloads Monthly Avg",
                    "GitHub Stars",
                    "GitHub Contributor Total Count",
                    "GitHub Total Dependents Count",
                ]
            ],
            style="height:600px;float:left;",
            classes="display",
            maxBytes=0,
            # fix a malformed attributes error built into the html content
        ).replace('class="display"style="', 'class="display" style="')
    )
    f.write("</div></body></html>")

# +
# capture the html page as a png export as a backup

# allow for nested asyncio ops
nest_asyncio.apply()


# define function for pyppeteer to capture image
# see: https://github.com/pyppeteer/pyppeteer#examples
async def capture_screenshot(file_path, output_path):
    browser = await launch(headless=True)
    page = await browser.newPage()
    # set the size of the capture
    await page.setViewport({"width": 1400, "height": 6500})
    await page.goto(f"file://{file_path}")
    await page.waitFor(1000)
    await page.screenshot({"path": output_path})
    await browser.close()


# Capture screenshot from html page
asyncio.get_event_loop().run_until_complete(
    capture_screenshot(
        file_path=pathlib.Path(f"{export_dir}/target-project-report.html").resolve(),
        output_path=f"{export_dir}/target-project-report.png",
    )
)
