import json
import re

from pyMud.globals import area_api
from pyMud.migrate.Room import Room
from pyMud.rest import new_area_payload, post, generate_mongo_id


class Area:
    area_id = None
    total_rooms = 0
    lines = []
    rooms = []

    def __init__(self, area_file):
        self.area_id = generate_mongo_id()
        self.initialize_file(area_file)

    def initialize_file(self, area_file):
        with open(area_file, 'r') as f:
            self.lines = [line.strip() for line in f.readlines()]
        self.initialize_rooms()
        self.total_rooms = len(self.rooms)
        self.create_payload_and_post()

    def split_rooms(self):
        """
        Splits the area data into individual room sections.
        Each room is represented as a list of lines.
        """
        rooms = []
        current_room = []
        in_room = False
        vnum_pattern = re.compile(r'^#\d+')

        for line in self.lines:
            if line == "#0":
                continue
            if vnum_pattern.match(line.strip()):
                if current_room:
                    rooms.append(current_room)
                    current_room = []
                in_room = True
            if in_room:
                current_room.append(line)
                if line.strip() == 'S':  # Check for end of room definition
                    rooms.append(current_room)
                    current_room = []
                    in_room = False
        if current_room:
            rooms.append(current_room)
        return rooms

    def initialize_rooms(self):
        """
        Extracts rooms from the area data by splitting it into individual room sections
        and parsing each room independently.
        """
        room_sections = self.split_rooms()
        self.rooms = [Room(self.area_id, room_data) for room_data in room_sections]

    def create_payload_and_post(self):
        """
        Generate the payload for the area and post it to the API service.
        """
        area_info = self.extract_area_fields()
        payload = new_area_payload(area_info)
        payload['id'] = self.area_id
        payload['totalRooms'] = self.total_rooms
        print("AREA-PAYLOAD=" + str(payload))
        response = post(payload, area_api + "areas")
        return json.loads(response.content)

    def extract_area_fields(self):
        """
        Extract fields required for area creation from the area lines.
        """
        pattern = r"{\s*(?P<level_range>[\d\s-]+)\s*}\s*(?P<author>\S+)\s+(?P<area_name>.*?)~"
        for line in self.lines:
            match = re.search(pattern, line)
            if match:
                return {
                    "suggested_level_range": match.group("level_range"),
                    "author": match.group("author"),
                    "name": match.group("area_name")
                }
        return {
            "suggested_level_range": None,
            "author": None,
            "name": None
        }
