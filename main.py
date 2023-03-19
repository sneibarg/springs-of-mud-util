import os

from pyMud import *
from pyMud.globals import area_api, room_api
from pyMud.rest import *


def load_rooms(area_id, rooms):
    new_rooms = []
    for room in rooms:
        room_payload = generate_room_payload(room, generate_mongo_id())
        room_payload['areaId'] = area_id
        response = post(room_payload, room_api + "room")
        content = json.loads(response.content)
        new_rooms.append(content)
    return new_rooms


def load_area(areas, area_file):
    sections = parse_area_file(area_file)
    area_info = extract_area_fields(sections['AREA'][2])
    areas[area_info['name']] = area_info
    area = new_area_payload(area_info)
    response = post(area, area_api + "areas")
    content = json.loads(response.content)
    return sections, str(content['id'])


def main():
    areas = {}
    area_dir = "C:\\Users\\scott\\CLionProjects\\rom24-quickmud\\area"
    for filename in os.listdir(area_dir):
        if filename.endswith('.are'):
            sections, area_id = load_area(areas, os.path.join(area_dir, filename))
            load_rooms(area_id, extract_rooms(sections['ROOMS']))
            mobiles = extract_mobiles(sections['MOBILES'])
            print("MOBILES: " + str(mobiles))
            objects = extract_objects(sections['OBJECTS'])
            print("OBJECTS: " + str(objects))
            break


if __name__ == '__main__':
    main()
