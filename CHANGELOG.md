# Changelog

## 0.9.1 (2026-02-18)

- Fix `from_filetime` crashing on out-of-range FILETIME values (pre-1970 dates,
  garbage timestamps); use `timedelta` arithmetic instead of `datetime.fromtimestamp`
- `from_filetime` now returns `None` for zero ("not set") and unrepresentable values

## 0.9.0 (2026-02-18)

- Drop Python 2 support; require Python ≥ 3.12
- Remove `six` dependency
- Replace `setup.py` with `pyproject.toml`
- Add `py.typed` marker (PEP 561)
- Add `pathlib.Path` support in `CfbIO`
- Add context-manager support (`with CfbIO(...) as doc:`)
- Migrate from `nosetests` to `pytest`
- Add `black`, `ruff`, and `mypy` configuration
- Add GitHub Actions CI (replaces Travis CI)
- Add type annotations throughout
- Move class definitions out of `__init__.py` files
- Use relative imports throughout the package
- Replace hand-rolled `cached` descriptor with `functools.cached_property`
- Add `pre-commit` configuration
- Add Makefile for common development tasks

## 0.8.3 (2013-11-13)

- Wheel support

## 0.8.2 (2013-10-02)

- Python 3 compatibility

## 0.8.1 (2013-10-02)

- Code documented

## 0.8.0 (2013-10-01)

- First public release
