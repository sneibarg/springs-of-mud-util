import json
import time
import random
import requests


def generate_mongo_id():
    timestamp = int(time.time()).to_bytes(4, 'big')
    machine_id = random.getrandbits(24).to_bytes(3, 'big')
    process_id = random.getrandbits(16).to_bytes(2, 'big')
    counter = random.getrandbits(24).to_bytes(3, 'big')
    return (timestamp + machine_id + process_id + counter).hex()


def do_request(method, url, payload):
    headers = {'Content-Type': 'application/json'}
    resp = method(url, data=json.dumps(payload), headers=headers)
    if resp.status_code in [200, 201]:
        return resp
    print(f'Error: {resp.text}')
    return None


def get(payload, url):
    return do_request(requests.get, url, payload)


def post(payload, url):
    return do_request(requests.post, url, payload)


def put(payload, url):
    return do_request(requests.put, url, payload)


def delete(payload, url):
    return do_request(requests.delete, url, payload)


def new_area_payload(area):
    payload = {
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
    return payload
