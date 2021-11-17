from .earl import EarlReporter

pytest_plugins = [EarlReporter.__module__]

# import pytest
# import os


# @pytest.fixture(scope="session", autouse=True)
# def do_something(request):
#     os.linesep = "\r\n"
