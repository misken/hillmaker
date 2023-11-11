# Changelog

This is the list of notable changes to hillmaker between each release.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- an objected oriented API
- added many input parameters for controlling hillmaker computations and outputs, (GH0050_, #54, #51)
- can specify inputs via TOML formatted config file if desired, (#33)
- length of stay summary report,
- input validation handled via a `pydantic <https://docs.pydantic.dev/latest/>`_ model, (#34)
- documentation at https://hillmaker.readthedocs.io/en/latest/intro.html,
- unit tests for occupancy computations,
- added extensive conservation of flow checks,
- detailed logging,
- detailed docstrings.

### Changed

- CLI input arguments for controlling hillmaker computations and outputs (#55)
- function based API input arguments for controlling hillmaker computations and outputs
- enhanced plotting capabilities

### Fixed

- edge_bins = 2 (entire bin) was being treated as edge_bins = 1 (fractional arrival and departure bins) (#43)

## [0.8.0] - 2023-11-??


