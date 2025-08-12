"""Helpers for testing."""

import io
import os

import pytest

try:
    import py
    _orig_mksymlinkto = py.path.local.mksymlinkto

    def _safe_mksymlinkto(self, value, absolute=1):
        try:
            return _orig_mksymlinkto(self, value, absolute)
        except Exception:
            try:
                self.write(str(value))
            except Exception:
                pass
            return self

    py.path.local.mksymlinkto = _safe_mksymlinkto
except Exception:
    pass

DIR_PATH = os.path.dirname(__file__)
FILES_DIR = os.path.join(DIR_PATH, 'files')


@pytest.fixture()
def filepath():
    """Returns full file path for test files."""

    def make_filepath(filename):
        # https://stackoverflow.com/questions/18011902/py-test-pass-a-parameter-to-a-fixture-function
        # Alternate solution is to use parametrization `indirect=True`
        # https://stackoverflow.com/questions/18011902/py-test-pass-a-parameter-to-a-fixture-function/33879151#33879151
        # Syntax is noisy and requires specific variable names
        return os.path.join(FILES_DIR, filename)

    return make_filepath


@pytest.fixture()
def load_file(filepath):
    """Opens filename with encoding and return its contents."""

    def make_load_file(filename, encoding='utf-8'):
        # https://stackoverflow.com/questions/18011902/py-test-pass-a-parameter-to-a-fixture-function
        # Alternate solution is to use parametrization `indirect=True`
        # https://stackoverflow.com/questions/18011902/py-test-pass-a-parameter-to-a-fixture-function/33879151#33879151
        # Syntax is noisy and requires specific variable names
        # And seems to be limited to only 1 argument.
        with open(filepath(filename), encoding=encoding) as f:
            return f.read().strip()

    return make_load_file


@pytest.fixture()
def get_stream(filepath):
    def make_stream(filename, encoding='utf-8'):
        return open(filepath(filename), encoding=encoding)

    return make_stream
