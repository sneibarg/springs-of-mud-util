import json
import re

from MigrateRiversOfMud.entity.Mobile import Mobile
from MigrateRiversOfMud.entity.Room import Room
from MigrateRiversOfMud.entity.Item import Item
from MigrateRiversOfMud.http import area_api, room_api, mobile_api, item_api, post, generate_mongo_id


class Area:
    def __init__(self, area_file):
        self.author = None
        self.name = None
        self.id = generate_mongo_id()
        self.total_rooms = 0
        self.suggested_level_range = None
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
        self.insert_area()
        self.insert_rooms()
        self.insert_objects()
        self.insert_mobiles()

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
        pre-generates MongoIDs for each VNUM, and parses each section independently.
        """
        sections = self._split_sections()
        room_lines = self._split_rooms(sections['ROOMS'])
        mobile_lines = self._split_entities(sections['MOBILES'], 'MOBILES')
        object_lines = self._split_entities(sections['OBJECTS'], 'OBJECTS')

        self._pre_generate_room_ids(room_lines)
        self.rooms = [self._create_room(room_data) for room_data in room_lines if self._is_valid_room(room_data)]
        self.mobiles = [self._create_mobile(mobile_data) for mobile_data in mobile_lines]
        self.objects = [self._create_object(object_data) for object_data in object_lines]
        self.shops = sections['SHOPS']
        self.resets = sections['RESETS']
        self.specials = sections['SPECIALS']

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
    def _split_entities(lines, entity_type):
        """
        Splits the entity data (e.g., mobiles or objects) into individual sections.
        Each entity is represented as a list of lines.
        """
        entities = []
        current_entity = []
        for line in lines:
            if line == f"#{entity_type}":
                continue
            is_vnum = bool(re.match(r'^#\d+$', line))
            if is_vnum and len(current_entity) > 0:
                entities.append(current_entity)
                current_entity = []
            current_entity.append(line)
        if current_entity:
            entities.append(current_entity)
        return entities

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

    def _create_mobile(self, mobile_data):
        """
        Creates a Mobile object, assigns its pre-generated MongoID, and returns the Mobile.
        """
        return Mobile(self.id, mobile_data)

    def _create_object(self, object_data):
        """
        Creates an Item object, assigns its pre-generated MongoID, and returns the Item.
        """
        return Item(self.id, object_data)

    def _create_room(self, room_data):
        """
        Creates a Room object, assigns its pre-generated MongoID, and returns the Room.
        """
        vnum = self._extract_vnum_from_room_data(room_data)
        if vnum is not None and vnum in self.room_id_mapping:
            return Room(self, room_data, self.room_id_mapping[vnum])
        else:
            print(f"Warning: VNUM {vnum} not found in room_id_mapping.")
            return None

    def insert_area(self):
        """
        Generate the payload for the area and post it to the API service.
        """
        pattern = r"{\s*(?P<level_range>[\d\s-]+)\s*}\s*(?P<author>\S+)\s+(?P<area_name>.*?)~"
        for line in self.lines:
            match = re.search(pattern, line)
            if match:
                self.suggested_level_range = match.group("level_range")
                self.author = match.group("author")
                self.name = match.group("area_name")

        payload = self.to_dict()
        payload['totalRooms'] = self.total_rooms
        response = post(payload, area_api + "areas")
        if not response:
            print(f"Failed posting to Area API endpoint: {response}")
            return None
        return json.loads(response.content)

    def insert_rooms(self):
        """
        Posts Room objects to the API endpoint.
        """
        for room in self.rooms:
            response = post(room.to_dict(), room_api + "room")
            if not response:
                print(f"Failed posting to Room API endpoint: {response}")

    def insert_mobiles(self):
        """
        Posts Mobile objects to the API endpoint.
        """
        for mobile in self.mobiles:
            response = post(mobile.to_dict(), mobile_api + "mobile")
            if not response:
                print(f"Failed posting to Mobile API endpoint: {response}")

    def insert_objects(self):
        """
        Posts Item objects to the API endpoint.
        """
        for item in self.objects:
            response = post(item.to_dict(), item_api + "item")
            if not response:
                print(f"Failed to post to Item API endpoint: "+str(response))

    def to_dict(self):
        """
        Return a payload for creating a new area document in MongoDB.
        """
        payload = {
            'id': self.id,
            'name': self.name,
            'author': self.author,
            'totalRooms': 0,
            'rooms': [],
            'suggestedLevelRange': self.suggested_level_range,
            'repopStrategy': "",
            'repopInterval': 0
        }
        return payload
