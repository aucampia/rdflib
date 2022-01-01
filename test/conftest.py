import pytest
from .earl import EarlReporter

pytest_plugins = [EarlReporter.__module__]

# NOTE: This is here so that asserts in these modules get reported with
# pytest's verbose reporter.
pytest.register_assert_rewrite("test.testutils", "test.testutils.files")
