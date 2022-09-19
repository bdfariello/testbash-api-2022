from integration.booker.interfaces.auth_interface import AuthInterface
from integration.booker.interfaces.room_interface import RoomInterface
from integration.rest.rest_base import RestBase


class BookerClient(RestBase):
    base_url: str = None
    token: str = None

    def __init__(self, username: str = None, password: str = None):
        super().__init__(
            username, password, "https://automationintesting.online"
        )
        self.request_headers = {
            "accept": "*/*",
            "content-type": "application/json"
        }
        if username is not None and password is not None:
            self.auth.login(username, password)

    @property
    def auth(self) -> AuthInterface:
        return AuthInterface(self)

    @property
    def room(self) -> RoomInterface:
        return RoomInterface(self)
