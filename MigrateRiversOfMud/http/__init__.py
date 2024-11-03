import json
import random
import time
import requests

area_api = "http://dragon:8082/api/v1/"
room_api = "http://dragon:8083/api/v1/"
mobile_api = "http://dragon:8084/api/v1/"
item_api = "http://dragon:8085/api/v1/"
shop_api = "http://dragon:8086/api/v1/"
reset_api = "http://dragon:8087/api/v1/"
specials_api = "http://dragon:8088/api/v1/"
headers = {
    'Content-Type': 'application/json'
}


def generate_mongo_id() -> str:
    """
    Generate a unique MongoDB ObjectId as a hexadecimal string.
    """
    timestamp = int(time.time()).to_bytes(4, 'big')
    machine_id = random.getrandbits(24).to_bytes(3, 'big')
    process_id = random.getrandbits(16).to_bytes(2, 'big')
    counter = random.getrandbits(24).to_bytes(3, 'big')
    return (timestamp + machine_id + process_id + counter).hex()


def handle_response(resp):
    if resp.status_code in [200, 201]:
        return resp
    print(f'Error: {resp.text}')
    return None


def get(payload, url):
    """
    Make an HTTP GET request with the given payload to the specified URL.
    """
    return handle_response(requests.get(url, data=json.dumps(payload), headers=headers))


def post(payload, url):
    """
    Make an HTTP POST request with the given payload to the specified URL.
    """
    return handle_response(requests.post(url, data=json.dumps(payload), headers=headers))


def put(payload, url):
    """
    Make an HTTP PUT request with the given payload to the specified URL.
    """
    return handle_response(requests.put(url, data=json.dumps(payload), headers=headers))
