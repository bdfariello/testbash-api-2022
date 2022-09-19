import logging
from requests import Response
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from integration.booker.booker_client import BookerClient

log = logging.getLogger("auth_interface")


class AuthInterface(object):
    _client = None

    def __init__(self, client: "BookerClient"):
        self._client = client

    def login(self, username, password) -> Response:
        uri = "/auth/login"
        data = {
            "username": username,
            "password": password
        }
        response = self._client.post(uri, data)
        if response.status_code == 200:
            self._client.__username = username
            self._client.__password = password
            try:
                response_cookie = response.headers["set-cookie"]
                token = response_cookie.split(";")[0].split("=")[1]
                self._client.request_headers["cookie"] = response_cookie
                self._client.token = token
            except KeyError:
                log.exception("KeyError when trying to get token from /auth/login response")
                log.debug(f"Response headers: {response.headers}")
        else:
            log.error(
                f"Login attempt failed for user {username} with status code {response.status_code}"
            )
        return response

    def validate(self, token: Optional[str] = None) -> Response:
        """
        Validate whether a token is valid
        :param token: Auth token retrieved from /auth/login resource. Optional.
        If unspecified, taken from BookerClient object
        :return: requests.Response object. 200 status_code if valid, 403 otherwise.
        """
        uri = "/auth/validate"
        validate_token = token if token else self._client.token
        data = {
            "token": validate_token
        }
        return self._client.post(uri, json_data=data)

    def logout(self, token: Optional[str] = None) -> Response:
        """

        :param token: Auth token retrieved from /auth/login resource. Optional.
        If unspecified, taken from BookerClient object
        :return: requests.Response object. 200 status_code if it was valid, 404 otherwise.
        """
        uri = "/auth/logout"
        logout_token = token if token else self._client.token
        data = {
            "token": logout_token
        }
        return self._client.post(uri, json_data=data)
