import orz
import pytest


@pytest.fixture(autouse=True)
def add_orz(doctest_namespace):
        doctest_namespace["orz"] = orz

