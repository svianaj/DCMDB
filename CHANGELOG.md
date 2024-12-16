# CHANGELOG

## unreleased

### Infrastructure
- Sunset mambaforge installer in favour of miniforge. [#73](https://github.com/destination-earth-digital-twins/dcmdb/pull/73)

## v0.0.0

- Add missing dependencies and check installation accordingly. [#60](https://github.com/destination-earth-digital-twins/dcmdb/pull/60)
- Remove dependency on availability of eccodes shell commands. [#60](https://github.com/destination-earth-digital-twins/dcmdb/pull/60)
- Fix duplicate file listings for cases with non-resolved `path_templates` [#68](https://github.com/destination-earth-digital-twins/dcmdb/pull/68)
- Allow more granual specification of experiments by supporting several `path_templates` in meta.yaml with explicit dates [#66](https://github.com/destination-earth-digital-twins/dcmdb/pull/66)
- Improve help message for `dcmdb chase -scan` [#57](https://github.com/destination-earth-digital-twins/dcmdb/pull/57)
- Improve find_files speed significantly by using recursive file listing caching introduced in latest ecmwfspec [#47](https://github.com/destination-earth-digital-twins/dcmdb/pull/47)
- Improve find_files speed and progress [#45](https://github.com/destination-earth-digital-twins/dcmdb/pull/45)
- Fix link of test badge in README.md [#44](https://github.com/destination-earth-digital-twins/dcmdb/pull/44)
- Fix PR case availability test for PRs coming from forked branches [#42](https://github.com/destination-earth-digital-twins/dcmdb/pull/42)
- Add test if meta.yaml files match defined schema [#23](https://github.com/destination-earth-digital-twins/dcmdb/pull/23)
- Run weekly test on the availability of all cataloged cases [#41](https://github.com/destination-earth-digital-twins/dcmdb/pull/41)
- Test availability of cases being modified by PR [#40](https://github.com/destination-earth-digital-twins/dcmdb/pull/40)
- Fix empty file retrieval for TOC generation [#38](https://github.com/destination-earth-digital-twins/dcmdb/pull/38)
- Switch to eccodes API for the creation of grib_ls based TOC to allow usage of fsspec backend [#37](https://github.com/destination-earth-digital-twins/dcmdb/pull/37)
- Add test for accessibility of submitted cases on ATOS [#37](https://github.com/destination-earth-digital-twins/dcmdb/pull/37)
- Package dcmdb (incl. pyproject.toml, move source files to src, pypi release action) [#37](https://github.com/destination-earth-digital-twins/dcmdb/pull/37)
- Improve filesystem generalization by moving to fsspec (incl. ecmwfspec for ECFS access) [#37](https://github.com/destination-earth-digital-twins/dcmdb/pull/37)
- Add option to create TOC with gribscan [#37](https://github.com/destination-earth-digital-twins/dcmdb/pull/37)
- Add linting. [#36](https://github.com/destination-earth-digital-twins/dcmdb/pull/36)
