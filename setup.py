"""
Minimal setup.py for Cython extensions and versioneer cmdclass.
Extension list is defined in pyproject.toml [tool.pyearth] ext-modules;
this script reads it, adds numpy include dir, and builds from .pyx via Cython.
"""
from setuptools import setup, Extension
import versioneer


def _load_pyproject_ext_modules():
    """Read [tool.pyearth] ext-modules from pyproject.toml."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return None
    from pathlib import Path
    with open(Path(__file__).resolve().parent / "pyproject.toml", "rb") as f:
        config = tomllib.load(f)
    return config.get("tool", {}).get("pyearth", {}).get("ext-modules")


def _pyproject_entry_to_extension(entry):
    """Convert one pyproject ext-modules entry to (name, sources, include_dirs, extra_compile_args)."""
    name = entry["name"]
    sources = list(entry["sources"])
    include_dirs = list(entry.get("include-dirs", []))
    extra_compile_args = list(entry.get("extra-compile-args", []))
    return name, sources, include_dirs, extra_compile_args


def get_ext_modules():
    import numpy
    from Cython.Build import cythonize
    numpy_inc = numpy.get_include()
    local_inc = "pyearth"

    entries = _load_pyproject_ext_modules()
    if entries is None:
        # Fallback when tomllib/tomli not available (e.g. old Python)
        entries = [
            {"name": "pyearth._util", "sources": ["pyearth/_util.pyx"], "include-dirs": [local_inc]},
            {"name": "pyearth._basis", "sources": ["pyearth/_basis.pyx"], "include-dirs": [local_inc], "extra-compile-args": ["-Wno-incompatible-pointer-types"]},
            {"name": "pyearth._record", "sources": ["pyearth/_record.pyx"], "include-dirs": [local_inc]},
            {"name": "pyearth._pruning", "sources": ["pyearth/_pruning.pyx"], "include-dirs": [local_inc]},
            {"name": "pyearth._forward", "sources": ["pyearth/_forward.pyx"], "include-dirs": [local_inc]},
            {"name": "pyearth._knot_search", "sources": ["pyearth/_knot_search.pyx"], "include-dirs": [local_inc]},
            {"name": "pyearth._qr", "sources": ["pyearth/_qr.pyx"], "include-dirs": [local_inc]},
            {"name": "pyearth._types", "sources": ["pyearth/_types.pyx"], "include-dirs": [local_inc]},
        ]

    ext_list = []
    for entry in entries:
        name, sources, include_dirs, extra_compile_args = _pyproject_entry_to_extension(entry)
        include_dirs = include_dirs + [numpy_inc]
        ext_list.append(
            Extension(name, sources, include_dirs=include_dirs, extra_compile_args=extra_compile_args or None)
        )

    return cythonize(ext_list)


def is_special_command():
    import sys
    special = ("--help-commands", "egg_info", "--version", "clean")
    return "--help" in sys.argv[1:] or (len(sys.argv) >= 2 and sys.argv[1] in special)


if __name__ == "__main__":
    from Cython.Distutils import build_ext
    kwargs = {"cmdclass": versioneer.get_cmdclass({"build_ext": build_ext})}
    if not is_special_command():
        kwargs["ext_modules"] = get_ext_modules()
    setup(**kwargs)
