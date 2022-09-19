import requests


class RestBase(object):
    __username: str = None
    __password: str = None
    base_url: str = ""
    request_headers = {}

    def __init__(self, username, password, base_url):
        self.__username = username
        self.__password = password
        self.base_url = base_url

    def get(self, uri: str, input_headers: dict = None):
        request_headers = input_headers if input_headers else self.request_headers
        response = requests.get(f"{self.base_url}{uri}", headers=request_headers)
        return response

    def post(self, uri: str, json_data: dict, input_headers: dict = None):
        request_headers = input_headers if input_headers else self.request_headers
        response = requests.post(f"{self.base_url}{uri}", json=json_data, headers=request_headers)
        return response

    def delete(self, uri, input_headers: dict = None):
        request_headers = input_headers if input_headers else self.request_headers
        response = requests.delete(f"{self.base_url}{uri}", headers=request_headers)
        return response
