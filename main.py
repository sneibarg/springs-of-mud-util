import os

from pyMud import *


def main():
    areas = {}
    area_dir = "C:\\Users\\scott\\CLionProjects\\rom24-quickmud\\area"
    for filename in os.listdir(area_dir):
        if filename.endswith('.are'):
            sections, area_id = load_area(areas, os.path.join(area_dir, filename))
            rooms = load_rooms(area_id, extract_rooms(sections['ROOMS']))
            print("ROOMS: "+str(rooms))
            mobiles = extract_mobiles(sections['MOBILES'])
            print("MOBILES: " + str(mobiles))
            objects = extract_objects(sections['OBJECTS'])
            print("OBJECTS: " + str(objects))
            break


if __name__ == '__main__':
    main()
