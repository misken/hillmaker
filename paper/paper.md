---
title: 'hillmaker: A Python package for occupancy analysis in discrete entity flow systems'
tags:
  - Python
  - occupancy analysis
  - capacity planning
  - healthcare
authors:
  - name: Mark W. Isken
    orcid: 0000-0001-8471-9116
    affiliation: 1
  - name: Author Without ORCID
    affiliation: 2

affiliations:
 - name: School of Business Administration, Oakland University, USA
   index: 1
 - name: Institution Name, Country
   index: 2

date: 8 November 2023
bibliography: paper.bib


---

# Summary

hillmaker is a Python package that computes time of day and day of week specific occupancy statistics from 
transaction data, in CSV or `pandas.DataFrame` formats, containing arrival and departure timestamps. Typical use is for capacity planning problems in 
places like hospital emergency departments, surgical recovery rooms or any system in which entities arrive, 
occupy capacity for some amount of time, and then depart. It gets its name from the hill-like nature of 
temporal occupancy plots.

![Weekly occupancy plot.\label{fig:example}](example1_occupancy_week.png)

Summarize the API and CLI options

# Statement of need

The original motivation for hillmaker was a series of capacity planning problems faced by a management 
engineering group at a large health care system. These problems are characterized by patient flow and capacity
use that exhibit significant and important time of day and day of week patterns. For example, one problem 
involved developing a surgical patient rerouting plan to temporarily accommodate patients while a post-surgical holding area
renovation project was underway. Proper statistical
analysis of patient arrival, departure and occupancy patterns are a critical part of such analyses.

Early versions of hillmaker were used in hundreds of projects in multiple healthcare engineering departments. It
was written in Microsoft Access and released as an open source project in the early 2000's. You can still find it
on SourceForge at [https://sourceforge.net/projects/hillmaker/](https://sourceforge.net/projects/hillmaker/). An
academic paper about this early version was published in 2002 [@Isken:2002] after the first author left industry
and joined Oakland University. `hillmaker` continued to be used both in industry as well as in patient flow
modeling related research projects.

The need for `hillmaker` was clear, but maintaining the original Access version became untenable. Given the rise of Python
in the scientific computing world, rewriting `hillmaker` in Python made a lot of sense for its future as an open source
project. The first Python version was [released on GitHub](https://github.com/misken/hillmaker/) in 2016. A series of
improvements followed over the next several years, culminating in the recent release of version 0.8.0. 

# Package overview

See https://joss.theoj.org/papers/10.21105/joss.05671 for example

# Additonal materials



# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

We acknowledge contributions from Brigitta Sipocz, Syrtis Major, and Semyeong
Oh, and support from Kathryn Johnston during the genesis of this project.

# References