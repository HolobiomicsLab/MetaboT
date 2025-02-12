import pytest
from app.core import utils

def test_utils_module_exists():
    """
    Basic test to verify that the utils module can be imported.
    This helps ensure the test infrastructure is working properly.
    """
    assert utils is not None