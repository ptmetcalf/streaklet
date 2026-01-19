# Changelog

## [1.0.0](https://github.com/ptmetcalf/streaklet/compare/v0.7.0...v1.0.0) (2026-01-19)


### ⚠ BREAKING CHANGES

* Calendar/heatmap tab removed from Fitbit page. Users relying on 365-day heatmap view should use Trends or Compare tabs instead.

### Features

* Enhance history page tooltips with completion metrics and visual improvements ([d647afa](https://github.com/ptmetcalf/streaklet/commit/d647afabeaadacaf0ae39340be55fee2ab8da95f))
* major Fitbit enhancements and UI improvements ([0cc84ef](https://github.com/ptmetcalf/streaklet/commit/0cc84ef29797c664f670bc5e079694509332a92e))

## [0.7.0](https://github.com/ptmetcalf/streaklet/compare/v0.6.0...v0.7.0) (2026-01-11)


### Features

* **fitbit:** update chart type to line and adjust styling for better visualization ([489cbac](https://github.com/ptmetcalf/streaklet/commit/489cbac90585a47e2f26fbfa5ea29f275699c8ba))

## [0.6.0](https://github.com/ptmetcalf/streaklet/compare/v0.5.0...v0.6.0) (2026-01-10)


### Features

* **milestones:** add milestone messages and toast notifications ([00b4040](https://github.com/ptmetcalf/streaklet/commit/00b4040b23f7ae572c00df504ebe723c20b7d689))

## [0.5.0](https://github.com/ptmetcalf/streaklet/compare/v0.4.2...v0.5.0) (2026-01-10)


### Features

* **history:** edit past days from history ([6150ddf](https://github.com/ptmetcalf/streaklet/commit/6150ddf73ac1bd5fe4e87dde272d82c3137995c4))

## [0.4.2](https://github.com/ptmetcalf/streaklet/compare/v0.4.1...v0.4.2) (2025-12-28)


### Bug Fixes

* remove main branch from docker publish workflow triggers ([8ffa5ba](https://github.com/ptmetcalf/streaklet/commit/8ffa5ba995e82ee68f01a64be378a83eec171ae9))
* update release workflow to trigger on CI completion instead of push to main ([edce951](https://github.com/ptmetcalf/streaklet/commit/edce951ae7ea9817d9870b1fa0c1d0e8e401db9c))

## [0.4.1](https://github.com/ptmetcalf/streaklet/compare/v0.4.0...v0.4.1) (2025-12-28)


### Bug Fixes

* refresh fitbit tokens on 401 ([dd51915](https://github.com/ptmetcalf/streaklet/commit/dd51915801eadb9d58d1926b3aec3c898afbb2de))

## [0.4.0](https://github.com/ptmetcalf/streaklet/compare/v0.3.4...v0.4.0) (2025-12-28)


### Features

* add smart fitbit backfill sync ([ab34f67](https://github.com/ptmetcalf/streaklet/commit/ab34f6702b590ee029e768bace8db9505492d209))

## [0.3.4](https://github.com/ptmetcalf/streaklet/compare/v0.3.3...v0.3.4) (2025-12-28)


### Bug Fixes

* remove !important from modal overlay display ([64fca91](https://github.com/ptmetcalf/streaklet/commit/64fca919e4db307538da49e8aef6c76bc62831f4))

## [0.3.3](https://github.com/ptmetcalf/streaklet/compare/v0.3.2...v0.3.3) (2025-12-28)


### Bug Fixes

* prevent CASCADE migration failure from orphaned records ([f34bc4f](https://github.com/ptmetcalf/streaklet/commit/f34bc4fa8a5878274c3616fba790fb4e49d7ff2a))

## [0.3.2](https://github.com/ptmetcalf/streaklet/compare/v0.3.1...v0.3.2) (2025-12-28)


### Bug Fixes

* skip orphaned records in CASCADE migration ([8ed91cd](https://github.com/ptmetcalf/streaklet/commit/8ed91cde6edf10a0ed6fa32fdaeca602f3209c09))

## [0.3.1](https://github.com/ptmetcalf/streaklet/compare/v0.3.0...v0.3.1) (2025-12-28)


### Bug Fixes

* add production-safe migration to repair broken CASCADE state ([8c50f87](https://github.com/ptmetcalf/streaklet/commit/8c50f8790350b56a3c17d3901240c8bedd2ffc14))
* make CASCADE migration idempotent ([7c17e84](https://github.com/ptmetcalf/streaklet/commit/7c17e84a210a030cb2a043f712c7806e7442acf3))

## [0.3.0](https://github.com/ptmetcalf/streaklet/compare/v0.2.1...v0.3.0) (2025-12-28)


### Features

* replace native browser dialogs with custom modal ([5fa2b75](https://github.com/ptmetcalf/streaklet/commit/5fa2b75b8044e800f12dd30d93a51b547a33f42c))


### Bug Fixes

* add CASCADE delete to task_checks foreign key ([557806e](https://github.com/ptmetcalf/streaklet/commit/557806eb2b3e65ce0cf1879069b3a37ba0cb6727))
* evaluate Fitbit auto-checks on page load and task changes ([ae2cb13](https://github.com/ptmetcalf/streaklet/commit/ae2cb136e6b54c6653668d2318e25390f31555fc))
* validate selected profile exists on page load ([75d4047](https://github.com/ptmetcalf/streaklet/commit/75d4047f022f462b603ea3f28aee7eae910b85de))

## [0.2.1](https://github.com/ptmetcalf/streaklet/compare/v0.2.0...v0.2.1) (2025-12-28)


### Bug Fixes

* improve task deletion confirmation and error handling ([073bd7c](https://github.com/ptmetcalf/streaklet/commit/073bd7cc034c4fb8961d29aa6f5d3598cbd51a5b))

## [0.2.0](https://github.com/ptmetcalf/streaklet/compare/v0.1.1...v0.2.0) (2025-12-27)


### Features

* add comprehensive desktop and tablet responsive layouts ([1971b36](https://github.com/ptmetcalf/streaklet/commit/1971b36eb8255d8137fd1f0a60028576d5cbd375))

## [0.1.1](https://github.com/ptmetcalf/streaklet/compare/v0.1.0...v0.1.1) (2025-12-27)


### Bug Fixes

* resolve Fitbit metric discrepancies with mobile app ([b608097](https://github.com/ptmetcalf/streaklet/commit/b608097b2364bd22e5ad9e82296f15533b6bdcde))

## 0.1.0 (2025-12-27)


### ⚠ BREAKING CHANGES

* Docker image now runs as non-root user (uid 1000). Data directory must be writable by uid 1000. Run: chown -R 1000:1000 ./data

### Features

* add automated releases, Docker hardening, and MkDocs documentation ([265c28c](https://github.com/ptmetcalf/streaklet/commit/265c28c5f1e3aa31d06e244e0ba2035115c107d1))
* Add backup and import/export functionality ([b8df15b](https://github.com/ptmetcalf/streaklet/commit/b8df15bd899f483ca1f94394927c8946bc6158eb))
* Add calendar history view with monthly completion tracking ([a51f6dd](https://github.com/ptmetcalf/streaklet/commit/a51f6dd9906fd8ffd9eac16202eb4a934d98b659))
* Add multi-user profile support with complete data isolation ([7f2ed68](https://github.com/ptmetcalf/streaklet/commit/7f2ed687d944e45e5cc5070fdd49676db0aa7b9a))
* Add Progressive Web App (PWA) support ([9207b78](https://github.com/ptmetcalf/streaklet/commit/9207b78a79189af422e481c39b57109d4b7e8cc4))
* Implement task management features with checks and streak tracking ([3711c5b](https://github.com/ptmetcalf/streaklet/commit/3711c5b76644f6d5b91e329c8cf576619f531f80))


### Bug Fixes

* Add freezegun fixture to fix timezone-dependent test failures in CI ([b8262e6](https://github.com/ptmetcalf/streaklet/commit/b8262e6b87e261c0a7e860ce53686c480efc78e5))
* add misfire handling and enable logging for Fitbit scheduler ([57ff6e0](https://github.com/ptmetcalf/streaklet/commit/57ff6e0e6175156fc1a0e9a778670a144eb3077c))
* Add missing __init__.py files to web directories ([a202dbf](https://github.com/ptmetcalf/streaklet/commit/a202dbfdb5973b1427010e1f2e3f86fb71f061b5))
* Add PYTHONPATH to test job for proper module imports ([e1ba0f3](https://github.com/ptmetcalf/streaklet/commit/e1ba0f3ac0aba1778bbeacf736d61cad619b3155))
* Fix CI workflow failures and add venv documentation ([cb78c0a](https://github.com/ptmetcalf/streaklet/commit/cb78c0a12c6dbddd45595015086041fafe283a07))
* Fix profile context in settings and add profile indicator ([8704844](https://github.com/ptmetcalf/streaklet/commit/87048444e5694f967eb5d9f7104ce1c142a96a4c))
* Handle permission errors when creating data directory ([dd6b3cf](https://github.com/ptmetcalf/streaklet/commit/dd6b3cffc6ee5c96ff1718bcebc3549cae352b4e))
* Remove invalid Docker tag prefix causing build failures ([e0eabf5](https://github.com/ptmetcalf/streaklet/commit/e0eabf5acb55e309ecaaa3652bb95eb1620ff790))
* remove invalid package-name parameter from release-please workflow ([b6af4e1](https://github.com/ptmetcalf/streaklet/commit/b6af4e1f25880382464e48f9b97fd557c5f2a725))
* Update index.html to fetch data client-side ([e8649c5](https://github.com/ptmetcalf/streaklet/commit/e8649c52fafe497921fa88e1594a3d1a962ac6b6))
* use GitHub's recommended Pages workflow pattern for docs ([d8928dd](https://github.com/ptmetcalf/streaklet/commit/d8928dd429624d48d43d5c16d5e2bb3d2ba2a74e))
* Use python -m pytest for better module resolution ([90ffbaf](https://github.com/ptmetcalf/streaklet/commit/90ffbafa87a566d40245409924fbd8129114cce7))


### Documentation

* Add CI and Docker workflow status badges to README ([96c86dd](https://github.com/ptmetcalf/streaklet/commit/96c86dd28bbfd8f88f2c5bbc931f82f7d6233ad6))
* Add CLAUDE.md for future Claude Code instances ([f846e78](https://github.com/ptmetcalf/streaklet/commit/f846e78663ac149053092566def3a3f9cec5e4ee))
* Add Codecov coverage badge to README ([39445f8](https://github.com/ptmetcalf/streaklet/commit/39445f8c5c3e05a52d6661c3c998771cd1c6df25))
* add missing documentation pages for MkDocs ([06c3014](https://github.com/ptmetcalf/streaklet/commit/06c30148429667512f278627cf324c600861415d))
* Update README with multi-user profile documentation ([417451e](https://github.com/ptmetcalf/streaklet/commit/417451e87e48bc3a2ae09032ed7319faf688057b))
