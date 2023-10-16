# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.2] - 2023-10-16
### Changed
- Update API submodule to prep for tomcat upgrade in 2023R4

## [2.0.1] - 2023-08-10
### Removed
- Removed logic for updating the notices due to product support
### Changed
- Update requirements for 3.6.8 common env

## [1.3.0] - 2023-03-21
### Changed
- Common registration script with registration_config.json file

## [1.2.0] - 2023-02-02
### Changed
- Logo branding update

## [1.1.1] - 2022-08-30
### Changed
- Updated RESTAPIs
- Make False default value for override option

## [1.1.0] - 2022-06-15
### Fixed
- Use custom project fields for application name/version vs project if available

## [1.0.7] - 2022-05-23
### Fixed
- Registration updates

## [1.0.6] - 2022-05-18
### Changed
- Change way to handle common license and prepend with notice text details and never update inventory item

## [1.0.5] - 2022-05-11
### Fixed
- Handle case when no license text is acquired
- Small logging change to highligh components vs licenses collected

## [1.0.4] - 2022-02-24
### Added
- Option to supress inventory version

## [1.0.3] - 2022-01-23
### Added
- Support for self signed certificates
### Changed
- Data services auth changes

## [1.0.2] - 2022-01-23
### Added
- Text version of report created
### Changed
- Migrated to Data Services API

## [1.0.1] - 2022-01-05
### Added
- Initial release of Third Party Notices report
- HTML version of report created
- Notice information via direct DB query

