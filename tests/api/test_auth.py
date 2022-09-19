import pytest
from integration.booker.booker_client import BookerClient


@pytest.fixture(scope="class")
def test_auth_client() -> "BookerClient":
    yield BookerClient()


@pytest.mark.smoke
class TestAuth(object):
    @staticmethod
    def __skip_if_no_valid_login(client: "BookerClient"):
        if "cookie" not in client.request_headers:
            pytest.skip(reason="Cannot run valid token test case without valid token")

    def test_invalid_login(self, test_auth_client, client):
        test_auth_client.auth.logout()
        response = test_auth_client.auth.login("admin", "WRONG")
        assert response.status_code == 403
        assert "cookie" not in test_auth_client.request_headers

    def test_valid_login(self, test_auth_client, client):
        response = test_auth_client.auth.login("admin", "password")
        assert response.status_code == 200
        assert "cookie" in test_auth_client.request_headers

    def test_validate_valid_token(self, test_auth_client):
        self.__skip_if_no_valid_login(test_auth_client)
        response = test_auth_client.auth.validate(test_auth_client.token)
        assert (
            response.status_code == 200
        ), f"Invalid status code for valid token. Expected 200. Got {response.status_code}"

    def test_validate_invalid_token(self, test_auth_client):
        response = test_auth_client.auth.validate("foo")
        assert (
            response.status_code == 403
        ), f"Invalid status code for invalid token. Expected 403. Got {response.status_code}"

    def test_logout_function(self, test_auth_client):
        self.__skip_if_no_valid_login(test_auth_client)
        delete_response = test_auth_client.auth.logout()
        assert (
            delete_response.status_code == 200
        ), f"Invalid status code for logout. Expected 200. Got {delete_response.status_code}"
        validate_response = test_auth_client.auth.validate(
            test_auth_client.token
        )
        assert (
            validate_response.status_code == 403
        ), f"Invalid status code for token validation after logout. Expected 403. Got {validate_response.status_code}"
