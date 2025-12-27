# Changelog

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
