# Testing py-earth

`setup.cfg` and `pyproject.toml` declare the project’s dependency *ranges* (e.g. `install_requires`, `extras_require`) but are not enough by themselves to reproduce this legacy test environment: you need a fixed Python version (3.8), version bounds that keep numpy &lt; 1.20 and compatible pandas/sklearn, and a known install order. The file `requirements-py38-2018.txt` plus the steps below define that environment.

## Reproducible legacy test environment (Python 3.8, 2018-era stack)

The project uses NumPy and scikit-learn APIs that predate later changes (e.g. `np.int` removal). To run the full test suite in a reproducible environment:

1. **Create a virtualenv with Python 3.8**
   ```bash
   python3.8 -m venv .venv-py38 --without-pip
   ```
   Bootstrap pip using the **versioned** get-pip script for Python 3.8 (the unversioned URL may pull a script that no longer supports 3.8):
   ```bash
   curl -sS https://bootstrap.pypa.io/3.8/get-pip.py -o get-pip-py38.py
   .venv-py38/bin/python get-pip-py38.py
   ```
   Or with wget: `wget https://bootstrap.pypa.io/3.8/get-pip.py` then `.venv-py38/bin/python get-pip.py`.

2. **Install dependencies from the pinned requirements, then the project**
   ```bash
   .venv-py38/bin/pip install -r requirements-py38-2018.txt
   .venv-py38/bin/pip install -e .
   ```

3. **Run the test suite**
   ```bash
   .venv-py38/bin/nosetests -sv pyearth
   ```

The file `requirements-py38-2018.txt` pins versions compatible with this stack (numpy &lt; 1.20, pandas 0.25.x, scikit-learn 0.22.x, etc.). Install order matters so that optional deps (e.g. pandas) do not pull in a newer numpy.

## Quick test (current Python)

With a modern Python and `pip install -e ".[all_tests]"`, you can run the same tests; some may be skipped or fail if the stack differs from the legacy environment above.

## Pinned versions (for exact reproducibility)

If you need the exact versions used in CI or a known-good run:

```text
numpy==1.19.5
scipy==1.3.3
scikit-learn==0.22.2
pandas==0.25.3
statsmodels==0.12.2
patsy==1.0.2
sympy==1.5.1
mpmath==1.3.0
nose==1.3.7
six==1.17.0
```

Use these in a dedicated `requirements-py38-pinned.txt` and install with `pip install -r requirements-py38-pinned.txt` if you want byte-for-byte reproducibility.

## Build dependencies (Cython and tooling)

Build-time dependencies (Cython version, setuptools, wheel, numpy for building extensions) are declared in **`pyproject.toml`** under `[build-system] requires`. Pip’s build isolation will install those when you run `pip install .` or `pip wheel .`.

Recorded versions (see `pyproject.toml`):

- **setuptools** ≥ 45  
- **wheel**  
- **numpy** (range depends on Python; for Python &lt; 3.12 the build uses `numpy>=1.15,<1.20` to match the legacy stack)  
- **Cython** ≥ 0.29.14, &lt; 0.30 (for regenerating `.c` from `.pyx` with `python setup.py build_ext --cythonize`)

For a reproducible build environment you can pin exact versions in `pyproject.toml` (e.g. `Cython==0.29.21`, `numpy==1.19.5`) or in a separate constraints file used at build time.

## Cython sources and generated .c files

The extension modules are written in **Cython** (`.pyx`); the checked-in `.c` files in `pyearth/` are generated from them by Cython. The **source of truth is the `.pyx` files**.

- **NumPy 1.20+ compatibility:** The `.pyx` files use `np.int_` and `np.float64` (and the `INT`/`FLOAT` aliases from `_types.pyx`) so that builds work with NumPy 1.20 and above (where `np.int`/`np.float` were removed). When building against NumPy ≥ 1.20, regenerate the `.c` files from the `.pyx` files (e.g. install Cython and run `python setup.py build_ext --cythonize`), or use a tree that already has `.c` files generated from these `.pyx` sources.
- **Legacy NumPy (&lt; 1.20):** The existing checked-in `.c` files may have been generated with older Cython and reference `np.int`; they are fine for numpy&lt;1.20. For a single codebase that works with both old and new NumPy, keep the `.pyx` as they are and regenerate `.c` when targeting the upgraded stack.
