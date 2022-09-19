from typing import List, Union
import logging
import pytest

log = logging.getLogger("test_auth")

min_price = 1
max_price = 999
valid_room_types = ["Single", "Double", "Twin", "Family", "Suite"]


@pytest.fixture(scope="class")
def room_id_list() -> List[int]:
    yield []


@pytest.fixture(scope="class")
def created_room_ids(client) -> List[int]:
    created_room_ids_list = []
    yield created_room_ids_list
    for room_id in created_room_ids_list:
        client.room.delete_room(room_id)


def validate_room_attribute(
    room: dict, attr_name: str, expected: Union[str, int]
) -> list:
    if attr_name not in room:
        return [f"Expected attribute {attr_name} not found in room {room}"]
    elif room[attr_name] != expected:
        return [f"Room {attr_name} had value {room[attr_name]}. Expected: {expected}"]
    else:
        return []


@pytest.mark.smoke
class TestRoomSmoke(object):
    def test_get_rooms(self, client, room_id_list):
        response = client.room.get_rooms()
        assert (
            200 == response.status_code
        ), f"Unexpected status code getting rooms. Expected 200. Got {response.status_code}"

        # Store valid Room ID's for later
        for room in response.json()["rooms"]:
            room_id_list.append(room["roomid"])

        assert room_id_list, f"No rooms found in response: {response.text}"

    def test_get_valid_room(self, client, room_id_list):
        if not room_id_list:
            pytest.skip("No rooms found in GET /room/ endpoint. Cannot continue")
        test_room_id = room_id_list[0]
        response = client.room.get_room(test_room_id)
        assert (
            200 == response.status_code
        ), f"Expected response code 200. Got {response.status_code}"
        assert (
            response.json().get("roomid") == test_room_id
        ), f"Expected roomid {test_room_id}. Got wrong room back: {response.text}"

    def test_get_invalid_room(self, client, room_id_list):
        max_room_id = 100
        for test_room_id in range(1, max_room_id + 1):
            if test_room_id in room_id_list:
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
        errors.extend(validate_room_attribute(room, "roomName", test_name))
        errors.extend(validate_room_attribute(room, "type", test_type))
        errors.extend(validate_room_attribute(room, "accessible", test_accessible))
        errors.extend(validate_room_attribute(room, "image", test_image))
        errors.extend(validate_room_attribute(room, "description", test_description))
        errors.extend(validate_room_attribute(room, "roomPrice", test_price))
        if test_feature not in room.get("features"):
            errors.append(f"Did not find {test_feature} in room features: {room.get('features')}")
        # The list should be empty after all these checks
        assert not errors, "\n".join(errors)

    @pytest.mark.parametrize("room_type", valid_room_types)
    def test_all_valid_room_types(self, room_type, client, created_room_ids):
        room = {
            "type": room_type,
            "roomPrice": min_price,
            "roomName": f"Room name with type {room_type}"
        }
        resp = client.room.create_room(room)
        # Cleanup in case of successful creation
        assert (
                201 == response.status_code
        ), f"Creating room returned HTTP {resp.status_code} response: {resp.text}"
        room = resp.json()
        created_room_ids.append(room.get("roomid"))
        errors = validate_room_attribute(room, "type", room_type)
        assert not errors, errors


@pytest.mark.negative
class TestRoomNegative(object):
    @staticmethod
    def create_room_with_cleanup(client, room, created_room_ids):
        resp = client.room.create_room(room)
        if "roomid" in resp.json():
            created_room_ids.append(resp.json().get("roomid"))
        return resp

    def test_missing_room_name(self, client, created_room_ids):
        room = {
            "type": "Single",
            "roomPrice": min_price
        }
        resp = client.room.create_room(room)
        assert 400 == resp.status_code, f"Expected status code 400. Got: {resp.status_code}"
        assert "Room name must be set" in resp.json().get("fieldErrors")
        # Cleanup in case of successful creation
        if "roomid" in resp.json():
            created_room_ids.append(resp.json().get("roomid"))

    def test_null_room_name(self, client, created_room_ids):
        room = {
            "type": "Single",
            "roomPrice": min_price,
            "roomName": None
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        assert 400 == resp.status_code, f"Expected status code 400. Got: {resp.status_code}"
        assert "must not be null" in resp.json().get("fieldErrors")

    def test_missing_room_type(self, client, created_room_ids):
        room = {
            "roomPrice": min_price,
            "roomName": "Room name"
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        assert 400 == resp.status_code, f"Expected status code 400. Got: {resp.status_code}"
        assert "Type must be set" in resp.json().get("fieldErrors")

    def test_null_room_type(self, client, created_room_ids):
        room = {
            "type": None,
            "roomPrice": min_price,
            "roomName": "Room name"
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        assert resp.status_code == 400, f"Expected status code 400. Got: {resp.status_code}"
        # TODO this fails because error message says only "Type must be set"
        # Different behavior from when roomName is set to None
        # SQLException shows the null is rejected so it is hitting a different error than when Type is missing entirely
        assert (
            "must not be null" in resp.json().get("fieldErrors")
        ), "Known issue: fieldErrors did not contain 'must not be null' for a null room type"

    def test_invalid_room_type(self, client, created_room_ids):
        room = {
            "type": "Invalid",
            "roomPrice": min_price,
            "roomName": "Room name"
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        assert resp.status_code == 400, f"Expected status code 400. Got: {resp.status_code}"
        expected_error = (
            f"Type can only contain the room options "
            f"Single, Double, Twin, Family or Suite"
        )
        assert expected_error in resp.json().get("fieldErrors")

    def test_missing_room_price(self, client, created_room_ids):
        room = {
            "type": "Single",
            "roomName": "Room name"
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        assert resp.status_code == 400, f"Expected status code 400. Got: {resp.status_code}"
        assert (
            "roomPrice must be set" in resp.json().get("fieldErrors")
        ), "Known issue: When Client does not send roomPrice, internal API defaults it to 0, which is invalid"

    def test_room_price_less_than_one(self, client, created_room_ids):
        room = {
            "type": "Single",
            "roomName": "Room name",
            "roomPrice": 0
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        assert 400 == resp.status_code, f"Expected status code 400. Got: {resp.status_code}"
        assert f"must be greater than or equal to {min_price}" in resp.json().get("fieldErrors")

    def test_max_room_price(self, client, created_room_ids):
        room = {
            "type": "Single",
            "roomName": "Room name",
            "roomPrice": max_price
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        assert resp.status_code == 201, f"Expected status code 201. Got: {resp.status_code}"
        price = resp.json().get("roomPrice")
        assert (
            max_price == price
        ), f"Expected roomPrice == {max_price}. Actual: {price}"

    def test_over_max_price(self, client, created_room_ids):
        too_high_price = max_price + 1
        room = {
            "type": "Single",
            "roomName": "Room name",
            "roomPrice": too_high_price
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        assert resp.status_code == 400, f"Expected status code 400. Got: {resp.status_code}"
        assert f"must be less than or equal to {max_price}" in resp.json().get("fieldErrors")

    def test_non_integer_room_price(self, client, created_room_ids):
        room = {
            "type": "Single",
            "roomName": "Room name",
            "roomPrice": 42.5
        }
        resp = self.create_room_with_cleanup(client, room, created_room_ids)
        assert (
            400 == resp.status_code
        ), (
            f"Expected status code 400. Got: {resp.status_code}. "
            f"Known issue? API schema defines roomPrice as int but accepts floats. Decimals truncated"
        )
        assert (
            f"must be less than or equal to {max_price}" in resp.json().get("fieldErrors")
        ), "Known issue blocks this expected fieldErrors list"  # TODO figure out what this should be
