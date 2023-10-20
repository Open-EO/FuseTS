# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Removed

### Fixed

## [2.0.1] - 2023-10-20

### Fixed

* Updated CropSAR notebook with the latest changes.
* Fixed the version of whittaker after a new release of the library.

## [2.0.0] - 2023-08-21

### Added

* Added CropSAR UDF for local execution
* Notebook examples for executing services through local datacube
* Notebook examples for executing services through openEO
* Notebook example used during FOSS4G
* Acknowledge and hyperparams fix (#77)

### Fixed

* Issue with executing Phenology service through openEO
* Fix Bug in Whittaker when specifying a custom prediction_period (#86)
* Fixed issue with `numpy` install (#89)
* Fixed datacube dimensions for MOGPR (#79)
