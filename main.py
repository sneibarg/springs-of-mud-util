import os

from pyMud import *
from pyMud.globals import area_api, room_api
from pyMud.rest import *


def main():
    areas = {}
    area_dir = "C:\\Users\\scott\\CLionProjects\\rom24-quickmud\\area"
    for filename in os.listdir(area_dir):
        if filename.endswith('.are'):
            area_file = os.path.join(area_dir, filename)
            sections = parse_area_file(area_file)
            area_id = None
            # for section in sections:
            #     if "AREA" == section:
            area_info = extract_area_fields(sections['AREA'][2])
            areas[area_info['name']] = area_info
            area = new_area_payload(area_info)
            response = post(area, area_api+"areas")
            content = json.loads(response.content)
            area_id = str(content['id'])
                # if "MOBILES" == section:
                #     # print("MOBILES: "+str(sections[section]))
                #     mobiles = extract_mobiles(sections[section])
                #     print("MOBILES: " + str(mobiles))
                # if "OBJECTS" == section:
                #     objects = extract_objects(sections[section])
                #     print("OBJECTS: " + str(objects))
                # if "ROOMS" == section:
            rooms = extract_rooms(sections['ROOMS'])
            print("ROOMS: " + str(rooms))
            for room in rooms:
                print("ROOM: "+str(room))
                room_payload = generate_room_payload(room, generate_mongo_id())
                room_payload['areaId'] = area_id
                print("ROOM_PAYLOAD: "+str(room_payload))
                response = post(room_payload, room_api+"room")
                content = json.loads(response.content)
                print("NEW_ROOM: "+str(content))
            break


if __name__ == '__main__':
    main()
