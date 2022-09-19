import pytest
from integration.booker.booker_client import BookerClient


def pytest_addoption(parser):
    framework = parser.getgroup("framework")
    framework.addoption(
        "--username",
        default="admin",
        action="store",
        help="Username for Restful Booker API"
    )
    framework.addoption(
        "--password",
        default="password",
        action="store",
        help="Username for Restful Booker API"
    )


@pytest.fixture(scope="session")
def client(pytestconfig) -> BookerClient:
    username = pytestconfig.getoption("username")
    password = pytestconfig.getoption("password")
    booker_client = BookerClient(username, password)
    yield booker_client
    # Teardown at the end of test runtime
    booker_client.auth.logout()
