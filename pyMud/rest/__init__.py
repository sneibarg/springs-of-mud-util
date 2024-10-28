import json
import random
import requests
import time

from pyMud.globals import area_api


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


def new_area_payload(area):
    """
    Return a payload for creating a new area document in MongoDB.
    """
    payload = {
        'id': None,
        'name': area['name'],
        'author': area['author'],
        'totalRooms': 0,
        'rooms': [],
        'suggestedLevelRange': area['suggested_level_range'],
        'repopStrategy': "",
        'repopInterval': 0
    }
    return payload


def new_room_payload(room, area_id):
    """
    Return a payload for creating a new room document in MongoDB.
    """
    payload = {
        'areaId': area_id,
        'vnum': room['vnum'],
        'name': room['name'],
        'description': room['description'],
        'tele_delay': room['tele_delay'],
        'room_flags': room['room_flags'],
        'sector_type': room['sector_type'],
        'spawn': False,
        'spawnTimer': 60000,
        'mobiles': [],
        'exits': {},
        'extra_descr': room['extra_descr'],
        'spawnTime': 0,
        'alternateRoutes': [],
        'pvp': False
    }
    for direction, exit_info in room['exits'].items():
        payload['exits'][direction] = {
            'to_room_vnum': exit_info['to_room_vnum'],
            'exit_flags': exit_info['exit_flags'],
            'key': exit_info['key'],
            'description': exit_info['description'],
            'keyword': exit_info['keyword']
        }
    return payload


def new_mobile_payload(mobile):
    """
    Return a payload for creating a new mobile document in MongoDB.
    Handles missing keys by providing default values.
    """
    print("MOBILE_DATA=" + str(mobile))
    payload = {
        "areaId": "",
        "roomId": "",
        "name": "",
        "race": mobile.get('race', ''),
        "mobClass": "",
        "shortDescription": mobile.get('short_descr', ''),
        "longDescription": mobile.get('long_descr', ''),
        "description": mobile.get('description', ''),
        "role": "",
        "guild": "",
        "level": mobile.get('level', 0),
        "actFlags": mobile.get('act', 0),
        "hitDice": "{}d{}+{}".format(*mobile.get('hit', [0, 0, 0])),
        "damDice": "{}d{}+{}".format(*mobile.get('damage', [0, 0, 0])),
        "startPosition": mobile.get('start_pos', 0),
        "defaultPosition": mobile.get('default_pos', 0),
        "sex": mobile.get('sex', 0),
        "currentHealth": "",
        "maxHealth": "",
        "inventory": [],
        "skills": [],
        "statuses": []
    }
    return payload


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