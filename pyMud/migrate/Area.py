import json
import re

from pyMud.globals import area_api, room_api
from pyMud.migrate.Room import Room
from pyMud.rest import new_area_payload, post, generate_mongo_id, new_room_payload


class Area:
    def __init__(self, area_file):
        self.area_id = generate_mongo_id()
        self.total_rooms = 0
        self.lines = []
        self.rooms = []
        self.mobiles = []
        self.objects = []
        self.shops = []
        self.resets = []
        self.specials = []
        self.room_id_mapping = {}

        self._initialize_file(area_file)
        self._initialize_sections()
        self.total_rooms = len(self.rooms)
        self._create_payload_and_post()
        self.create_rooms()

    def _initialize_file(self, area_file):
        with open(area_file, 'r') as f:
            self.lines = [line.strip() for line in f.readlines()]

    def _split_sections(self):
        """
        Splits the area data into individual sections: ROOMS, MOBILES, OBJECTS, SHOPS, RESETS, SPECIALS.
        Each section is represented as a list of lines.
        """
        sections = {
            'ROOMS': [],
            'MOBILES': [],
            'OBJECTS': [],
            'SHOPS': [],
            'RESETS': [],
            'SPECIALS': []
        }
        current_section = None

        for line in self.lines:
            if line.startswith('#AREAS'):
                current_section = None
            elif line.startswith('#MOBILES'):
                current_section = 'MOBILES'
            elif line.startswith('#OBJECTS'):
                current_section = 'OBJECTS'
            elif line.startswith('#ROOMS'):
                current_section = 'ROOMS'
            elif line.startswith('#RESETS'):
                current_section = 'RESETS'
            elif line.startswith('#SHOPS'):
                current_section = 'SHOPS'
            elif line.startswith('#SPECIALS'):
                current_section = 'SPECIALS'
            elif line == '#0':
                current_section = None

            if current_section in sections:
                sections[current_section].append(line)

        return sections

    def _initialize_sections(self):
        """
        Extracts different sections from the area data by splitting it into individual sections,
        pre-generates MongoIDs for each room VNUM, and parses each section independently.
        """
        sections = self._split_sections()
        room_sections = self._split_rooms(sections['ROOMS'])

        self._pre_generate_room_ids(room_sections) # pre-generate the Mongo ID
        self.rooms = [self._create_room(room_data) for room_data in room_sections if self._is_valid_room(room_data)]
        self.mobiles = sections['MOBILES']
        self.objects = sections['OBJECTS']
        self.shops = sections['SHOPS']
        self.resets = sections['RESETS']
        self.specials = sections['SPECIALS']

    @staticmethod
    def _split_rooms(room_lines):
        """
        Splits the room data into individual room sections.
        Each room is represented as a list of lines.
        """
        rooms = []
        current_room = []
        vnum_pattern = re.compile(r'^#\d+$')

        for line in room_lines:
            if vnum_pattern.match(line.strip()):
                if current_room:
                    rooms.append(current_room)
                    current_room = []
                current_room.append(line)
            elif current_room:
                current_room.append(line)
                if line.strip() == 'S':  # Check for end of room definition
                    rooms.append(current_room)
                    current_room = []

        if current_room:
            rooms.append(current_room)
        return rooms

    @staticmethod
    def _is_valid_room(room_data):
        """
        Checks if the given room data is valid by looking for a VNUM pattern.
        """
        vnum_pattern = re.compile(r'^#\d+$')
        return any(vnum_pattern.match(line) for line in room_data)

    def _pre_generate_room_ids(self, room_sections):
        """
        Iterates through all the rooms and pre-generates a MongoID for each VNUM.
        """
        for room_data in room_sections:
            vnum = self._extract_vnum_from_room_data(room_data)
            if vnum is not None:
                mongo_id = generate_mongo_id()
                self.room_id_mapping[vnum] = mongo_id

    @staticmethod
    def _extract_vnum_from_room_data(room_data):
        """
        Extracts the VNUM from the room data.
        """
        vnum_pattern = re.compile(r'^#(\d+)$')
        for line in room_data:
            match = vnum_pattern.match(line.strip())
            if match:
                return int(match.group(1))
        return None

    def _create_room(self, room_data):
        """
        Creates a Room object, assigns its pre-generated MongoID, and returns the room.
        """
        vnum = self._extract_vnum_from_room_data(room_data)
        if vnum is not None and vnum in self.room_id_mapping:
            room_id = self.room_id_mapping[vnum]
            room = Room(self.area_id, room_data, room_id)  # Pass the pre-generated MongoID
            return room
        else:
            print(f"Warning: VNUM {vnum} not found in room_id_mapping.")
            return None

    def _create_payload_and_post(self):
        """
        Generate the payload for the area and post it to the API service.
        """
        area_info = self._extract_area_fields()
        payload = new_area_payload(area_info)
        payload['id'] = self.area_id
        payload['totalRooms'] = self.total_rooms
        print("AREA-PAYLOAD=" + str(payload))
        response = post(payload, area_api + "areas")
        if response:
            return json.loads(response.content)
        return None

    def _extract_area_fields(self):
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

    def create_rooms(self):
        for room in self.rooms:
            room_payload = new_room_payload(room, self.area_id, self.room_id_mapping)
            # print("ROOM-PAYLOAD=" + str(room_payload))
            post(room_payload, room_api + "room")
