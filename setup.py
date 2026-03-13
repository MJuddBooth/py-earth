"""
Minimal setup.py for Cython extensions and versioneer cmdclass.
All package metadata lives in pyproject.toml.
"""
from setuptools import setup, Extension
import sys
import versioneer

# Build from .pyx when --cythonize is passed, else from pre-generated .c
if "--cythonize" in sys.argv:
    cythonize_switch = True
    sys.argv.remove("--cythonize")
else:
    cythonize_switch = False


def get_ext_modules():
    import numpy
    local_inc = "pyearth"
    numpy_inc = numpy.get_include()

    if cythonize_switch:
        from Cython.Build import cythonize
        return cythonize(
            [
                Extension("pyearth._util", ["pyearth/_util.pyx"], include_dirs=[local_inc, numpy_inc]),
                Extension(
                    "pyearth._basis",
                    ["pyearth/_basis.pyx"],
                    include_dirs=[local_inc, numpy_inc],
                    extra_compile_args=["-Wno-incompatible-pointer-types"],
                ),
                Extension("pyearth._record", ["pyearth/_record.pyx"], include_dirs=[local_inc, numpy_inc]),
                Extension("pyearth._pruning", ["pyearth/_pruning.pyx"], include_dirs=[local_inc, numpy_inc]),
                Extension("pyearth._forward", ["pyearth/_forward.pyx"], include_dirs=[local_inc, numpy_inc]),
                Extension("pyearth._knot_search", ["pyearth/_knot_search.pyx"], include_dirs=[local_inc, numpy_inc]),
                Extension("pyearth._qr", ["pyearth/_qr.pyx"], include_dirs=[local_inc, numpy_inc]),
                Extension("pyearth._types", ["pyearth/_types.pyx"], include_dirs=[local_inc, numpy_inc]),
            ]
        )
    else:
        return [
            Extension("pyearth._util", ["pyearth/_util.c"], include_dirs=[numpy_inc]),
            Extension("pyearth._basis", ["pyearth/_basis.c"], include_dirs=[numpy_inc]),
            Extension("pyearth._record", ["pyearth/_record.c"], include_dirs=[numpy_inc]),
            Extension("pyearth._pruning", ["pyearth/_pruning.c"], include_dirs=[local_inc, numpy_inc]),
            Extension("pyearth._forward", ["pyearth/_forward.c"], include_dirs=[local_inc, numpy_inc]),
            Extension("pyearth._knot_search", ["pyearth/_knot_search.c"], include_dirs=[local_inc, numpy_inc]),
            Extension("pyearth._qr", ["pyearth/_qr.c"], include_dirs=[local_inc, numpy_inc]),
            Extension("pyearth._types", ["pyearth/_types.c"], include_dirs=[local_inc, numpy_inc]),
        ]


def is_special_command():
    special = ("--help-commands", "egg_info", "--version", "clean")
    return "--help" in sys.argv[1:] or (len(sys.argv) >= 2 and sys.argv[1] in special)


if __name__ == "__main__":
    kwargs = {}
    if not is_special_command():
        kwargs["ext_modules"] = get_ext_modules()

    if cythonize_switch:
        from Cython.Distutils import build_ext
        kwargs["cmdclass"] = versioneer.get_cmdclass({"build_ext": build_ext})
    else:
        kwargs["cmdclass"] = versioneer.get_cmdclass()

    setup(**kwargs)
