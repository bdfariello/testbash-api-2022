from requests import Response
from typing import List, Union
import logging
import pytest

log = logging.getLogger("test_auth")

min_price = 1
max_price = 999
valid_room_types = ["Single", "Double", "Twin", "Family", "Suite"]


@pytest.fixture(scope="class")
def starting_room_id_list(client) -> List[int]:
    rooms = []
    response = client.room.get_rooms()
    assert (
            200 == response.status_code
    ), f"Unexpected status code getting rooms. Expected 200. Got {response.status_code}"

    # Store valid Room ID's for later
    for room in response.json()["rooms"]:
        rooms.append(room["roomid"])
    yield rooms


@pytest.fixture(scope="class")
def created_room_ids(client) -> List[int]:
    created_room_ids_list = []
    yield created_room_ids_list
    # After a test class completes, iterate through the list of rooms
    # created during test execution and delete all these rooms
    for room_id in created_room_ids_list:
        client.room.delete_room(room_id)


@pytest.mark.smoke
class TestRoomSmoke(object):
    @staticmethod
    def validate_room_attribute(
            room: dict, attr_name: str, expected: Union[str, int]
    ) -> List[str]:
        if attr_name not in room:
            return [f"Expected attribute {attr_name} not found in room {room}"]
        elif room[attr_name] != expected:
            return [f"Room {attr_name} had value {room[attr_name]}. Expected: {expected}"]
        else:
            return []

    def test_get_all_rooms(self, client, starting_room_id_list):
        assert starting_room_id_list, f"No rooms found in response to /room/"

    def test_get_valid_room(self, client, starting_room_id_list):
        if not starting_room_id_list:
            pytest.skip("No rooms found in GET /room/ endpoint. Cannot continue")
        test_room_id = starting_room_id_list[0]
        response = client.room.get_room(test_room_id)
        assert (
            200 == response.status_code
        ), f"Expected response code 200. Got {response.status_code}"
        assert (
            response.json().get("roomid") == test_room_id
        ), f"Expected roomid {test_room_id}. Got wrong room back: {response.text}"

    @pytest.mark.negative
    def test_get_invalid_room(self, client, starting_room_id_list):
        max_room_id = 100
        for test_room_id in range(1, max_room_id + 1):
            if test_room_id in starting_room_id_list:
                continue
            # Now we have a test_room_id NOT in the known list of room IDs
            response = client.room.get_room(test_room_id)
            assert (
                500 == response.status_code
            ), f"Expected response code 500. Got {response.status_code}"
            break
        else:
            # If we never found an invalid room ID
            pytest.skip(f"All IDs from 1 to {max_room_id} are valid. Cannot test invalid ID")

    def test_create_room_smoke(self, client, created_room_ids):
        test_name = "foo"
        test_type = "Suite"
        test_accessible = False
        test_image = "test image url"
        test_description = "Test description!"
        test_feature = "Working Toilet"
        test_price = 42

        room_data = {
            "roomName": test_name,
            "type": test_type,
            "accessible": test_accessible,
            "image": test_image,
            "description": test_description,
            "features": [
                test_feature
            ],
            "roomPrice": test_price
        }
        response = client.room.create_room(room_data)
        assert (
            201 == response.status_code
        ), f"Creating room returned HTTP {response.status_code} response: {response.text}"
        room = response.json()
        created_room_ids.append(room.get("roomid"))
        errors = []
        errors.extend(self.validate_room_attribute(room, "roomName", test_name))
        errors.extend(self.validate_room_attribute(room, "type", test_type))
        errors.extend(self.validate_room_attribute(room, "accessible", test_accessible))
        errors.extend(self.validate_room_attribute(room, "image", test_image))
        errors.extend(self.validate_room_attribute(room, "description", test_description))
        errors.extend(self.validate_room_attribute(room, "roomPrice", test_price))
        if test_feature not in room.get("features"):
            errors.append(f"Did not find {test_feature} in room features: {room.get('features')}")
        # The list should be empty after all these checks
        assert not errors, errors

    @pytest.mark.parametrize("room_type", valid_room_types)
    def test_all_valid_room_types(self, room_type, client, created_room_ids):
        room_data = {
            "type": room_type,
            "roomPrice": min_price,
            "roomName": f"Room name with type {room_type}"
        }
        resp = client.room.create_room(room_data)
        assert (
            201 == resp.status_code
        ), f"Creating room returned HTTP {resp.status_code} response: {resp.text}"
        room = resp.json()
        created_room_ids.append(room.get("roomid"))
        errors = self.validate_room_attribute(room, "type", room_type)
        assert not errors, errors

    def test_max_room_price(self, client, created_room_ids):
        room_data = {
            "type": "Single",
            "roomName": "Room name",
            "roomPrice": max_price
        }
        resp = client.room.create_room(room_data)
        assert (
            resp.status_code == 201
        ), f"Expected status code 201. Got: {resp.status_code}"
        room = resp.json()
        created_room_ids.append(room.get("roomid"))
        price = room.get("roomPrice")
        assert (
            max_price == price
        ), f"Expected roomPrice == {max_price}. Actual: {price}"


@pytest.mark.negative
class TestRoomNegative(object):
    @staticmethod
    def create_room_with_cleanup(client, room, created_room_ids):
        resp = client.room.create_room(room)
        if "roomid" in resp.json():
            created_room_ids.append(resp.json().get("roomid"))
        return resp

    @staticmethod
    def validate_error_message(
            resp: Response, expected_error: str, expected_status_code: int = 400
    ):
        assert (
            expected_status_code == resp.status_code
        ), f"Expected status code {expected_status_code}. Got: {resp.status_code}"
        assert expected_error in resp.json().get("fieldErrors")

    def test_missing_room_name(self, client, created_room_ids):
        room = {
            "type": "Single",
            "roomPrice": min_price
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        self.validate_error_message(resp, "Room name must be set")

    def test_null_room_name(self, client, created_room_ids):
        room = {
            "type": "Single",
            "roomPrice": min_price,
            "roomName": None
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        self.validate_error_message(resp, "must not be null")

    def test_missing_room_type(self, client, created_room_ids):
        room = {
            "roomPrice": min_price,
            "roomName": "Room name"
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        self.validate_error_message(resp, "Type must be set")

    @pytest.mark.skip(reason=f"Known issue? fieldErrors did not contain "
                             f"'must not be null' for a null room type")
    def test_null_room_type(self, client, created_room_ids):
        room = {
            "type": None,
            "roomPrice": min_price,
            "roomName": "Room name"
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        self.validate_error_message(resp, "must not be null")

    def test_invalid_room_type(self, client, created_room_ids):
        room = {
            "type": "Invalid",
            "roomPrice": min_price,
            "roomName": "Room name"
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        expected_error = (
            f"Type can only contain the room options "
            f"Single, Double, Twin, Family or Suite"
        )
        self.validate_error_message(resp, expected_error)

    @pytest.mark.skip(reason=f"Known issue? When Client does not send "
                             f"roomPrice internal API defaults it invalid value: 0")
    def test_missing_room_price(self, client, created_room_ids):
        room = {
            "type": "Single",
            "roomName": "Room name"
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        self.validate_error_message(resp, "roomPrice must be set")

    def test_room_price_less_than_one(self, client, created_room_ids):
        room = {
            "type": "Single",
            "roomName": "Room name",
            "roomPrice": 0
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        self.validate_error_message(resp, f"must be greater than or equal to {min_price}")

    def test_over_max_price(self, client, created_room_ids):
        too_high_price = max_price + 1
        room = {
            "type": "Single",
            "roomName": "Room name",
            "roomPrice": too_high_price
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        self.validate_error_message(resp, f"must be less than or equal to {max_price}")

    @pytest.mark.skip(reason=f"Known issue? API schema defines roomPrice"
                             f"as int but accepts a float. Decimals truncated")
    def test_non_integer_room_price(self, client, created_room_ids):
        room = {
            "type": "Single",
            "roomName": "Room name",
            "roomPrice": 42.5
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        self.validate_error_message(resp, "roomPrice must be an integer")
