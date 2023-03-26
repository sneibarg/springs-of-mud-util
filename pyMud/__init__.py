import json
import re

from pyMud.globals import area_api, room_api, mobile_api, item_api
from pyMud.rest import new_area_payload, post, generate_mongo_id, new_room_payload, new_object_payload, \
    new_mobile_payload


def lambda_match(input_str, pattern, anon_dict):
    match = re.match(pattern, input_str)
    if match:
        named_captures = {k: v for k, v in match.groupdict().items() if v is not None}
        return {**anon_dict, **named_captures}
    else:
        return anon_dict


def load_objects(objects):
    new_objects = []
    for mud_object in objects:
        payload = new_object_payload(mud_object)
        print("OBJECT_PAYLOAD: "+str(payload))
        response = post(payload, item_api + "item")
        content = json.loads(response.content)
        new_objects.append(content)
    return new_objects


def load_mobiles(area_id, mobiles):
    new_mobs = []
    for mobile in mobiles:
        payload = new_mobile_payload(mobile)
        payload['areaId'] = area_id
        print("MOBILE_PAYLOAD: "+str(payload))
        response = post(payload, mobile_api + "mobile")
        content = json.loads(response.content)
        new_mobs.append(content)
    return new_mobs


def load_rooms(area_id, rooms):
    new_rooms = []
    for room in rooms:
        payload = new_room_payload(room, generate_mongo_id())
        payload['areaId'] = area_id
        print("ROOM_PAYLOAD: "+str(payload))
        response = post(payload, room_api + "room")
        content = json.loads(response.content)
        new_rooms.append(content)
    return new_rooms


def load_area(areas, area_file):
    sections = parse_area_file(area_file)
    area_info = extract_area_fields(sections['AREA'][2])
    areas[area_info['name']] = area_info
    payload = new_area_payload(area_info)
    print("AREA_PAYLOAD: "+str(payload))
    response = post(payload, area_api + "areas")
    content = json.loads(response.content)
    return sections, str(content['id'])


def parse_area_file(filename):
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f.readlines()]

    def extract_section_lines(start_idx):
        end_idx = start_idx + 1
        while end_idx < len(lines):
            if lines[end_idx] == "#0":
                break
            if lines[end_idx] == "":
                break
            end_idx += 1
        return lines[start_idx + 1:end_idx]

    section_parsers = {
        "AREA": lambda idx: extract_section_lines(idx),
        "HELPS": lambda idx: extract_section_lines(idx),
        "MOBILES": lambda idx: extract_section_lines(idx),
        "OBJECTS": lambda idx: extract_section_lines(idx),
        "ROOMS": lambda idx: extract_section_lines(idx),
        "SHOPS": lambda idx: extract_section_lines(idx)
    }

    parsed_sections = {section: [] for section in section_parsers.keys()}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#"):
            section_name = line[1:].strip()
            if section_name in section_parsers:
                parsed_sections[section_name] = section_parsers[section_name](i)
            else:
                pass
        i += 1
    return parsed_sections


def extract_subsection(data, parser):
    subsections = []
    fields = []
    for line in data:
        line = line.strip()
        if line.startswith('#'):
            if fields:
                subsections.append(parser(fields))
                fields = []
        fields.append(line)
        if line.startswith('#0'):
            break
    if fields:
        subsections.append(parser(fields))
    return subsections


def extract_area_fields(s):
    pattern = r"{\s*(?P<level_range>[\d\s-]+)\s*}\s*(?P<author>\S+)\s+(?P<area_name>.*?)~"
    anon_dict = {"level_range": None, "author": None, "area_name": None}
    named_captures = lambda_match(str(s), pattern, anon_dict)
    level_range = named_captures.get("level_range")
    area_name = named_captures.get("area_name")
    author = named_captures.get("author")

    return {
        "suggested_level_range": level_range,
        "author": author,
        "name": area_name
    }


def extract_room_fields(lines):
    name = lines[0].strip()
    desc = '\n'.join(lines[1:-2]).strip()
    exits = {}
    for i in range(0, len(lines) - 2, 3):
        dir_desc = lines[i + 2].strip()
        exit_info = lines[i + 1].split()
        if len(exit_info) == 3:
            exits[exit_info[0]] = {
                'to_vnum': exit_info[2],
                'description': dir_desc,
            }
    extra = ''
    sector = ''
    if len(lines) >= 2:
        extra = lines[-2].strip()
    if len(lines) >= 1:
        sector = lines[-1].strip()
    return {
        'name': name,
        'description': desc,
        'exits': exits,
        'extra': extra,
        'sector': sector
    }


def extract_object_fields(fields):
    vnum = fields[0] if len(fields) > 0 else ''
    name = fields[1] if len(fields) > 1 else ''
    short_descr = fields[2] if len(fields) > 2 else ''
    long_descr = fields[3] if len(fields) > 3 else ''
    description = fields[4] if len(fields) > 4 else ''
    item_type = fields[5] if len(fields) > 5 else ''
    extra_flags = fields[6] if len(fields) > 6 else ''
    wear_flags = fields[7] if len(fields) > 7 else ''
    value = fields[8] if len(fields) > 8 else ''
    weight = fields[9] if len(fields) > 9 else ''
    level = fields[10] if len(fields) > 10 else ''
    affect_data = fields[11] if len(fields) > 11 else ''
    return {
        'vnum': vnum,
        'name': name,
        'short_descr': short_descr,
        'long_descr': long_descr,
        'description': description,
        'item_type': item_type,
        'extra_flags': extra_flags,
        'wear_flags': wear_flags,
        'value': value,
        'weight': weight,
        'level': level,
        'affect_data': affect_data,
    }


def get_mobile_description(data):
    description = []
    while True:
        line = data.pop(0)
        if line == "~" and len(description) > 0:
            break
        if line == "~":
            continue
        description.append(line)
    return description, data


def extract_mobile_fields(data):
    mobiles = []
    mobile = {}

    while True:
        if len(data) == 0:
            break
        line = data.pop(0)
        if line.startswith("#"):
            mobile['vnum'] = line.split('#')[1]
            mobile['keywords'] = data.pop(0)
            mobile['short-description'] = data.pop(0)
            mobile['long-description'] = data.pop(0)
            mobile['description'], data = get_mobile_description(data)
            mobile['race'] = data.pop(0).replace("~", "")
            mobile['act-flags'] = data.pop(0)
            mobile['level'] = data.pop(0)
            mobile['hit-dice'] = data.pop(0)
            mobile['dam-dice'] = data.pop(0)
            mobile['position'] = data.pop(0)
            mobile['sex'] = data.pop(0)
            mobiles.append(mobile)
    return mobiles


def extract_mobiles(data):
    return extract_subsection(data, extract_mobile_fields)


def extract_objects(data):
    return extract_subsection(data, extract_object_fields)


def extract_rooms(data):
    return extract_subsection(data, extract_room_fields)
