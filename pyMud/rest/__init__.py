import json
import random
import requests
import time

from pyMud import area_api


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
        'name': area['name'],
        'author': area['author'],
        'totalRooms': 0,
        'rooms': [],
        'suggestedLevelRange': area['suggested_level_range'],
        'repopStrategy': "",
        'repopInterval': 0
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(area_api + "areas", data=json.dumps(payload), headers=headers)
    content = json.loads(response.content)
    return str(content['id'])


def new_room_payload(room, area_id):
    """
    Return a payload for creating a new room document in MongoDB.
    """
    payload = {
        'areaId': area_id,
        'description': room['description'],
        'name': room['name'],
        'spawn': False,
        'spawnTimer': 60000,
        'mobiles': [],
        'east': '',
        'north': '',
        'south': '',
        'west': '',
        'spawnTime': 0,
        'alternateRoutes': [],
        'up': '',
        'down': '',
        'pvp': False
    }
    for exit_dir, exit_info in room['exits'].items():
        if exit_dir == 'north':
            payload['north'] = exit_info['to_vnum']
        elif exit_dir == 'east':
            payload['east'] = exit_info['to_vnum']
        elif exit_dir == 'south':
            payload['south'] = exit_info['to_vnum']
        elif exit_dir == 'west':
            payload['west'] = exit_info['to_vnum']
        elif exit_dir == 'up':
            payload['up'] = exit_info['to_vnum']
        elif exit_dir == 'down':
            payload['down'] = exit_info['to_vnum']
    return payload


def new_mobile_payload(mobile):
    """
    Return a payload for creating a new mobile document in MongoDB.
    """
    mobile = mobile[0]
    payload = {
        "areaId": "",
        "roomId": "",
        "name": "",
        "race": mobile['race'],
        "mobClass": "",
        "shortDescription": mobile['short-description'].replace("", ""),
        "longDescription": mobile['long-description'].replace("", ""),
        "description": '\r\n'.join(mobile['description']),
        "keywords": mobile['keywords'].replace("~", ""),
        "role": "",
        "guild": "",
        "level": mobile['level'],
        "actFlags": mobile['act-flags'],
        "hitDice": mobile['hit-dice'],
        "damDice": mobile['dam-dice'],
        "position": mobile['position'],
        "sex": mobile['sex'],
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
