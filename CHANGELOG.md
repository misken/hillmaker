# Changelog

This is the list of notable changes to hillmaker between each release.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- an objected oriented API
- added many input parameters for controlling hillmaker computations and outputs, (#50, #54, #51)
- can specify inputs via TOML formatted config file if desired,
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

### Added

- Arabic translation (#444).
- v1.1 French translation.
- v1.1 Dutch translation (#371).
- v1.1 Russian translation (#410).
- v1.1 Japanese translation (#363).
- v1.1 Norwegian Bokmål translation (#383).
- v1.1 "Inconsistent Changes" Turkish translation (#347).
- Default to most recent versions available for each languages
- Display count of available translations (26 to date!)
- Centralize all links into `/data/links.json` so they can be updated easily

### Fixed

- Improve French translation (#377).
- Improve id-ID translation (#416).
- Improve Persian translation (#457).
- Improve Russian translation (#408).
- Improve Swedish title (#419).
- Improve zh-CN translation (#359).
- Improve French translation (#357).
- Improve zh-TW translation (#360, #355).
- Improve Spanish (es-ES) transltion (#362).
- Foldout menu in Dutch translation (#371).
- Missing periods at the end of each change (#451).
- Fix missing logo in 1.1 pages
- Display notice when translation isn't for most recent version
- Various broken links, page versions, and indentations.

### Changed

- Upgrade dependencies: Ruby 3.2.1, Middleman, etc.

### Removed

- Unused normalize.css file
- Identical links assigned in each translation file
- Duplicate index file for the english version

## [1.1.0] - 2019-02-15

### Added

- Danish translation (#297).
- Georgian translation from (#337).
- Changelog inconsistency section in Bad Practices.

### Fixed
