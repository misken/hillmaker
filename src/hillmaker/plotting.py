# Copyright 2022 Mark Isken, Jacob Norman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import matplotlib.pyplot as plt
import seaborn as sns; sns.set_style('darkgrid')
from pathlib import Path


def export_dow_plot(dow_df, scenario_name, metric, export_path, cap=None, size=(15, 10)):
    """
    Exports day of week plot for occupancy, arrival, and departure statistics

    Takes output DataFrames of `summarize.summarize` and plots mean and percentile
    values for occupancy, arrival, and departure categories. Designed to be run in
    a loop in order to isolate plot to a single day of week.

    Parameters
    ----------

    dow_df : DataFrame
        Single summary df from the output of `summarize.summarize`, split by day of week
    scenario_name : str
        Used in output filenames
    metric : str
        Name of make_hills summary df being plotted
    export_path : str or Path, optional
        Destination path for exported csv files, default is current directory
    cap : int, optional
        Capacity of area being analyzed, default is None
    size : tuple
        Width and height of output plot in centimeters, default is (15, 10)
    """

    # infer day of week from supplied df
    dow = dow_df['dow_name'].unique()[0]

    # initialize figure
    fig, ax = plt.subplots(figsize=size)

    # create bar and line plots
    sns.barplot(data=dow_df, x='bin_of_day', y='mean', color='steelblue', label='mean')
    # TODO: allow user-defined percentiles to be plotted
    sns.lineplot(data=dow_df, x='bin_of_day', y='p75', color='grey', linestyle='-.', label='p75')
    sns.lineplot(data=dow_df, x='bin_of_day', y='p99', color='grey', linestyle='-', label='p99')

    # establish capacity horizontal line if supplied
    if cap is not None:
        plt.axhline(cap, color='r', linestyle='--', label='Capacity')

    # format x-axis tick labels
    labs = dow_df['bin_of_day_str'].unique().tolist()
    major_ticks = (dow_df['bin_of_day'].max() + 1) / 24  # establish num periods in hour
    ax.set_xticklabels([j if i % major_ticks == 0 else None for i, j in enumerate(labs)], rotation=90)

    # format other plot elements
    ax.legend()
    ax.set(xlabel='Time of Day', ylabel=metric.title())
    ax.set_title(f'{metric.title()} - {dow.title()}', size=16, loc='left')

    # remove whitespace in plot border
    plt.tight_layout()

    # save figure
    dow_str = dow.lower()
    plot_png = f'{scenario_name}_{metric}_plot_{dow_str}.png'
    png_wpath = Path(export_path, plot_png)
    plt.savefig(png_wpath)


def export_week_plot(summary_df, scenario_name, metric, export_path, cap=None, h=18, ratio=0.5):
    """
    Exports week plot for occupancy, arrival, and departure statistics

    Takes output DataFrames of `summarize.summarize` and plots mean and percentile
    values for occupancy, arrival, and departure categories. Designed to be run in
    a loop in order to isolate plot to a single metric.

    Parameters
    ----------

    summary_df : DataFrame
        Single summary df from the output of `summarize.summarize`
    scenario_name : str
        Used in output filenames
    metric : str
        Name of make_hills summary df being plotted
    export_path : str or Path, optional
        Destination path for exported csv files, default is current directory
    cap : int, optional
        Capacity of area being analyzed, default is None
    h : int
        Height of output plot in centimeters, default is 15
    ratio : float
        Aspect ratio of subplot which determines the width of the subplot. Default is 0.5
    """

    # infer week range from df
    if summary_df['day_of_week'].max() > 4:
        week = 'Full Week'
    else:
        week = 'Weekdays'

    # establish order of bars to avoid warning
    order = summary_df['bin_of_day'].unique()

    # initialize facet grid and margin limits
    g = sns.FacetGrid(summary_df, col='dow_name', height=h, aspect=ratio, sharey=True)
    g.set(xmargin=0, ymargin=0.05)

    # create bar and line plots
    g.map(sns.barplot, 'bin_of_day', 'mean', color='steelblue', order=order, label='mean')
    # TODO: allow user-defined percentiles to be plotted
    g.map(sns.lineplot, 'bin_of_day', 'p75', color='grey', linestyle='-.', label='p75')
    g.map(sns.lineplot, 'bin_of_day', 'p95', color='grey', linestyle='-', label='p95')

    # establish capacity horizontal line if supplied
    if cap is not None:
        g.map(lambda y, **kw: plt.axhline(cap, color='red', linestyle='--', label='Capacity'), 'mean')

    # format x-axis tick labels
    labs = summary_df['bin_of_day_str'].unique().tolist()
    major_ticks = (summary_df['bin_of_day'].max() + 1) / 24  # establish num periods in hour
    g.set_xticklabels([j if i % major_ticks == 0 else None for i, j in enumerate(labs)], rotation=90)

    # format other plot elements
    g.add_legend()
    g.set_titles(col_template='{col_name}', fontweight='bold', size=16)
    g.set(xlabel=None, ylabel=metric.title())
    g.fig.subplots_adjust(top=0.92)
    g.fig.suptitle(f'{metric.title()} - {week.title()}', fontsize=32)

    # save figure
    week_str = week.replace(' ', '_').lower()
    plot_png = f'{scenario_name}_{metric}_plot_{week_str}.png'
    png_wpath = Path(export_path, plot_png)
    g.savefig(png_wpath, bbox_inches='tight')
