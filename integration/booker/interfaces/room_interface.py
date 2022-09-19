from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from integration.booker.booker_client import BookerClient

import requests


class RoomInterface(object):
    _client = None

    def __init__(self, client: "BookerClient"):
        self._client = client

    def get_rooms(self):
        uri = "/room/"
        return self._client.get(uri)

    def get_room(self, room_id: int):
        uri = f"/room/{room_id}"
        return self._client.get(uri)

    def create_room(self, room_data: dict):
        uri = f"/room/"
        return self._client.post(uri, json_data=room_data)

    def delete_room(self, room_id: int):
        uri = f"/room/{room_id}"
        return self._client.delete(uri)