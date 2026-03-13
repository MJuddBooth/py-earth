# Pytest loads this first. Provide nose compatibility so tests run on Python 3.13
# where nose is incompatible (uses removed 'imp' module).
import sys
import unittest
import numpy as np

def _assert_almost_equal(a, b, **kwargs):
    np.testing.assert_almost_equal(a, b, **kwargs)

def _assert_equal(a, b, msg=None):
    if a != b:
        raise AssertionError(msg or "%r != %r" % (a, b))

def _assert_true(x, msg=None):
    if not x:
        raise AssertionError(msg or "not true")

def _assert_false(x, msg=None):
    if x:
        raise AssertionError(msg or "not false")

def _assert_not_equal(a, b, msg=None):
    if a == b:
        raise AssertionError(msg or "%r == %r" % (a, b))

def _assert_list_equal(a, b, msg=None):
    if a != b:
        raise AssertionError(msg or "lists not equal: %r != %r" % (a, b))

def _assert_raises(exc_type, callable_obj=None, *args, **kwargs):
    if callable_obj is None:
        return _AssertRaisesContext(exc_type)
    try:
        callable_obj(*args, **kwargs)
    except exc_type:
        return
    raise AssertionError("%s not raised" % exc_type)

class _AssertRaisesContext(object):
    def __init__(self, exc_type):
        self.exc_type = exc_type

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            raise AssertionError("%s not raised" % self.exc_type)
        if exc_type is not self.exc_type and not issubclass(exc_type, self.exc_type):
            return False
        return True

class _NoseTools(object):
    assert_almost_equal = staticmethod(_assert_almost_equal)
    assert_equal = staticmethod(_assert_equal)
    assert_true = staticmethod(_assert_true)
    assert_false = staticmethod(_assert_false)
    assert_not_equal = staticmethod(_assert_not_equal)
    assert_list_equal = staticmethod(_assert_list_equal)
    assert_raises = staticmethod(_assert_raises)

class _NoseModule(object):
    SkipTest = unittest.SkipTest
    tools = _NoseTools()

if "nose" not in sys.modules:
    sys.modules["nose"] = _NoseModule()
if "nose.tools" not in sys.modules:
    sys.modules["nose.tools"] = _NoseTools()
