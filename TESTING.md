# Testing py-earth

This document describes how to run the test suite with the **current build stack** (Python 3.12 / 3.13, NumPy 2.x, Cython 3 for 3.13). For an older Python 3.8–era environment, see [Legacy test environment (Python 3.8)](#legacy-test-environment-python-38) below.

## Current build stack (Python 3.12 / 3.13)

Build and test dependencies are declared in **`pyproject.toml`** (ranges) and optionally pinned in **`requirements-py313.txt`** for a reproducible environment.

### 1. Create a virtualenv (e.g. Python 3.13)

```bash
python3.13 -m venv .venv-py313 --without-pip
.venv-py313/bin/python -m ensurepip --upgrade
```

Or use the system pip to create the venv with pip included:

```bash
python3.13 -m venv .venv-py313
```

### 2. Install dependencies and build from Cython sources

From the project root. Extensions are built from `.pyx` at build time (Cython is a build dependency; generated `.c` files are not committed).

```bash
.venv-py313/bin/pip install -r requirements-py313.txt
.venv-py313/bin/pip install -e .
```

Or build in place then install (e.g. for development):

```bash
.venv-py313/bin/pip install -r requirements-py313.txt
.venv-py313/bin/python setup.py build_ext --inplace
.venv-py313/bin/pip install -e . --no-build-isolation
```

For Python 3.13 you need NumPy 2.x, SciPy ≥ 1.14 (for Cython `.pxd` imports in `pyearth/_qr.pyx`), and Cython ≥ 3.0 (see `pyproject.toml` `[build-system] requires`). If you use **`pip install -e .`** with the default build isolation, pip installs those build deps for you.

### 3. Run the test suite

```bash
.venv-py313/bin/nosetests -sv pyearth
```

Or with the Makefile (set `PYTHON` and `NOSETESTS` to the venv binaries):

```bash
make verbose-test PYTHON=.venv-py313/bin/python NOSETESTS=.venv-py313/bin/nosetests
```

You may see one skipped test (e.g. pathological cases) and one check in `test_check_estimator` reported as an expected failure (sample-weight equivalence on dense data); the run still completes successfully.

## Quick test (any supported Python)

With a modern Python and `pip install -e ".[all_tests]"` (and Cython installed if building from `.pyx`), you can run the same tests. Some tests may be skipped or fail if the stack differs from the pinned environment above.

## Build dependencies (Cython and tooling)

Build-time dependencies are declared in **`pyproject.toml`** under `[build-system] requires`. Pip’s build isolation will install them when you run `pip install .` or `pip wheel .`.

From **`pyproject.toml`** (current):

- **setuptools** ≥ 77.0.3  
- **wheel**  
- **numpy** (range depends on Python):
  - Python &lt; 3.12: `numpy>=1.15,<1.20`
  - Python 3.12: `numpy>=1.15`
  - Python ≥ 3.13: `numpy>=2.0`
- **scipy** (must be in the build environment so Cython can `cimport scipy.linalg.cython_lapack` / `cython_blas`):
  - Python &lt; 3.12: `scipy>=0.16`
  - Python 3.12: `scipy>=1.9`
  - Python ≥ 3.13: `scipy>=1.14.0`
- **Cython**: `>=0.29.21,<0.30` for Python &lt; 3.13; **≥ 3.0** for Python ≥ 3.13 (required to build from `.pyx`)
- **versioneer** ≥ 0.29

To build extensions: `python setup.py build_ext` (or `build_ext --inplace`), or `pip install .` (Cython runs at build time).

## Cython sources

The extension modules are written in **Cython** (`.pyx`). 

- **NumPy 2.x / Python 3.13:** The `.pyx` files use `np.int_`, `np.float64`, and the `INT`/`FLOAT` aliases from `_types.pyx`. Use **Cython ≥ 3.0** for Python 3.13.
- **Older NumPy (&lt; 1.20):** The project supports older stacks (see legacy section); keep the `.pyx` as-is and build on each stack.

## Legacy test environment (Python 3.8)

If you wish to run tests on a **Python 3.8** stack with NumPy &lt; 1.20 and compatible pandas/sklearn (e.g. for reproducibility with an older CI or environment):

1. Create a virtualenv with Python 3.8 and install pip (e.g. `python3.8 -m venv .venv-py38`, or `--without-pip` then bootstrap with `get-pip.py` for 3.8 from https://bootstrap.pypa.io/3.8/get-pip.py).
2. Install from a pinned requirements file that keeps numpy &lt; 1.20 and compatible versions (e.g. a project-specific `requirements-py38-2018.txt` or similar, if maintained).
3. Install the project and run: `.venv-py38/bin/nosetests -sv pyearth`.

Build from `.pyx` on that stack requires Cython &lt; 0.30 and the NumPy range for Python &lt; 3.12 from `pyproject.toml`. The exact pinned versions (numpy, scipy, scikit-learn, pandas, etc.) are environment-specific; use a dedicated requirements file for that stack if you need byte-for-byte reproducibility.
