import pytest
import sys

if __name__ == "__main__":
    print("Running tests with test_mode parameter...")
    sys.exit(pytest.main(["-v", "tests/test_discovery.py::test_search_doctors", "tests/test_database.py::test_search_doctors"])) 