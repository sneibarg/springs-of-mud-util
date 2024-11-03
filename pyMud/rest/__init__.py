import json
import random
import time
import requests

area_api = "http://dragon:8082/api/v1/"
room_api = "http://dragon:8083/api/v1/"
mobile_api = "http://dragon:8084/api/v1/"
item_api = "http://dragon:8085/api/v1/"


def generate_mongo_id() -> str:
    """
    Generate a unique MongoDB ObjectId as a hexadecimal string.
    """
    timestamp = int(time.time()).to_bytes(4, 'big')
    machine_id = random.getrandbits(24).to_bytes(3, 'big')
    process_id = random.getrandbits(16).to_bytes(2, 'big')
    counter = random.getrandbits(24).to_bytes(3, 'big')
    return (timestamp + machine_id + process_id + counter).hex()


def get(payload, url):
    """
    Make an HTTP GET request with the given payload to the specified URL.
    """
    headers = {'Content-Type': 'application/json'}
    resp = requests.get(url, data=json.dumps(payload), headers=headers)
    if resp.status_code in [200, 201]:
        return resp
    print(f'Error: {resp.text}')
    return None


def post(payload, url):
    """
    Make an HTTP POST request with the given payload to the specified URL.
    """
    headers = {'Content-Type': 'application/json'}
    resp = requests.post(url, data=json.dumps(payload), headers=headers)
    if resp.status_code in [200, 201]:
        return resp
    print(f'Error: {resp.text}')
    return None


def put(payload, url):
    """
    Make an HTTP PUT request with the given payload to the specified URL.
    """
    headers = {'Content-Type': 'application/json'}
    resp = requests.put(url, data=json.dumps(payload), headers=headers)
    if resp.status_code in [200, 201]:
        return resp
    print(f'Error: {resp.text}')
    return None


def new_object_payload(obj):
    """
    Return a payload for creating a new object document in MongoDB.
    """
    payload = {
        "name": obj['name'],
        "shortDescription": obj['short_descr'].replace("", ""),
        "longDescription": obj['long_descr'].replace("", ""),
        "description": obj['description'].replace("", ""),
        "type": obj['item_type'],
        "extraFlags": obj['extra_flags'],
        "wearFlags": obj['wear_flags'],
        "value": obj['value'],
        "weight": obj['weight'].replace("", ""),
        "level": obj['level'],
        "affectData": obj['affect_data'].replace("~", "")
    }
    return payload
