from requests import Response
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from integration.booker.booker_client import BookerClient


class RoomInterface(object):
    _client = None

    def __init__(self, client: "BookerClient"):
        self._client = client

    def get_rooms(self) -> Response:
        return self._client.get("/room/")

    def get_room(self, room_id: int) -> Response:
        return self._client.get(f"/room/{room_id}")

    def create_room(self, room_data: dict) -> Response:
        return self._client.post("/room/", json_data=room_data)

    def delete_room(self, room_id: int) -> Response:
        return self._client.delete(f"/room/{room_id}")
