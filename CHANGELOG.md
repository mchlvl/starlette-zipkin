# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).


## 0.2.2 (March 5, 2022)

### Fixed
- [PR31](https://github.com/mchlvl/starlette-zipkin/pull/31) test tracer fixed via dependency injection



## 0.2.1 (March 5, 2022)

### Changed
- [PR28](https://github.com/mchlvl/starlette-zipkin/pull/28) fixes `az.Tracer` leak (used to create a new one with every request)


## 0.2.0 (Dec 19, 2021)

### Changed
- [PR21](https://github.com/mchlvl/starlette-zipkin/pull/21) code refactor, new functionality, added `trace` context manager to add spans easier and updated examples, tests, readme


## 0.1.4 (Dec 16, 2021)

### Changed
- [PR19](https://github.com/mchlvl/starlette-zipkin/pull/19) more native way to log span kind `span.tag("kind", "SERVER")` -> `span.kind(az.SERVER)`


## 0.1.3 (Dec 15, 2021)

### Changed
- [PR17](https://github.com/mchlvl/starlette-zipkin/pull/17) requirements changed to ranges

## 0.1.2 (July 25, 2021)

### Added
- [PR15](https://github.com/mchlvl/starlette-zipkin/pull/15) add `span.tag("kind", "SERVER")` as default

## 0.1.1 (Nov 23, 2020)
### Changed
- readme update

### Fixed
- ci

## 0.1.0 (Nov 23, 2020)

### New
- switch to semantics versioning
- CI setup
    - tests pipeline
    - quality pipeline (`black`, `isort`, `flake8`, `mypy`)
    - release pipeline