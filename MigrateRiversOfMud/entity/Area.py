import json
import re

from MigrateRiversOfMud.entity.Mobile import Mobile
from MigrateRiversOfMud.entity.Resets import Reset
from MigrateRiversOfMud.entity.Room import Room
from MigrateRiversOfMud.entity.Item import Item
from MigrateRiversOfMud.entity.Shop import Shop
from MigrateRiversOfMud.entity.Special import Special
from MigrateRiversOfMud.http.SOMClient import *
from MigrateRiversOfMud.logging import setup_logger


class Area:
    def __init__(self, area_file, insert=True, filename='Area.log'):
        self.area_file = area_file
        self.author = None
        self.name = None
        self.vnum = None
        self.insert = insert
        self.id = generate_mongo_id()
        self.suggested_level_range = None
        self.lines = []
        self.rooms = []
        self.mobiles = []
        self.objects = []
        self.shops = []
        self.resets = []
        self.specials = []
        self.room_id_mapping = {}
        self.logger = setup_logger("Area", filename)
        self._initialize_file(area_file)
        self._initialize_sections()
        self._populate_self()
        self.insert_area()
        self.insert_rooms()
        self.insert_objects()
        self.insert_mobiles()
        self.insert_shops()
        self.insert_specials()
        self.insert_resets()

    def _initialize_file(self, area_file):
        with open(area_file, 'r') as f:
            self.lines = [line.strip() for line in f.readlines()]

    def _populate_self(self):
        # Updated pattern to handle text level ranges like "All" as well as numeric ones
        pattern = r"{\s*(?P<level_range>[^}]+)\s*}\s*(?P<author>\S+)\s+(?P<area_name>.*?)~"
        for line in self.lines:
            match = re.search(pattern, line)
            if match:
                self.suggested_level_range = match.group("level_range").strip()
                self.author = match.group("author")
                self.name = match.group("area_name").strip() or "Unnamed Area"
                if self.name == "Unnamed Area":
                    print(f"line={line}")
        self.vnum = self._extract_area_vnum()

    def _extract_area_vnum(self):
        """
        Extract area vnum from the ROM #AREA header line "<min_vnum> <max_vnum>".
        Uses min_vnum as the AreaDocument vnum, with file stem fallback.
        """
        for line in self.lines:
            match = re.match(r'^\s*(\d+)\s+(\d+)\s*$', line)
            if match:
                return match.group(1)
        return self.area_file.split("\\")[-1].split(".")[0]

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

            if current_section in sections:
                sections[current_section].append(line)
        if current_section == "RESETS":
            del sections[current_section][0]
        return sections

    def _initialize_sections(self):
        """
        Extracts each section of the area by splitting it into individual sections;
        pre-generates MongoIDs for each VNUM, and parses each section independently.
        """
        sections = self._split_sections()
        room_lines = self._split_rooms(sections['ROOMS'])
        mobile_lines = self._split_entities(sections['MOBILES'], 'MOBILES')
        object_lines = self._split_entities(sections['OBJECTS'], 'OBJECTS')
        shop_lines = self._split_entities(sections['SHOPS'], 'SHOPS')

        self._pre_generate_room_ids(room_lines)
        self.logger.info(f"Parsing {len(object_lines)} objects from OBJECTS section")
        self.rooms = [self._create_room(room_data) for room_data in room_lines]  # if self._is_valid_room(room_data)]
        self.mobiles = [self._create_mobile(mobile_data) for mobile_data in mobile_lines]
        self.objects = [obj for obj in [self._create_object(object_data) for object_data in object_lines] if obj is not None]
        self.logger.info(f"Successfully created {len(self.objects)} object instances")
        self.shops = [self._create_shop(shop_data) for shop_data in shop_lines]
        self.resets = [self._create_reset(line) for line in sections['RESETS'][1:]]
        self.specials = [self._create_special(line) for line in sections['SPECIALS'][1:]]

    def _pre_generate_room_ids(self, room_sections):
        """
        Iterates through all the rooms and pre-generates a MongoID for each VNUM.
        """
        for room_data in room_sections:
            vnum = self._extract_vnum(room_data)
            if vnum is not None:
                self.room_id_mapping[vnum] = generate_mongo_id()

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
            if line == '#0':
                # End of entities marker
                if len(current_entity) > 0:
                    entities.append(current_entity)
                break
            if bool(re.match(r'^#\d+$', line)):
                if len(current_entity) > 0:
                    entities.append(current_entity)
                current_entity = [line]
            else:
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
    def _extract_vnum(room_data):
        """
        Extracts the VNUM from the room data.
        """
        vnum_pattern = re.compile(r'^#(\d+)$')
        for line in room_data:
            match = vnum_pattern.match(line.strip())
            if match:
                return int(match.group(1))
        return None

    def _create_special(self, special_data):
        """
        Creates a Special object, assigns its pre-generated MongoID, and returns the Special.
        """
        return Special(self.id, special_data)

    def _create_reset(self, reset_data):
        """
        Creates a Reset object, assigns its pre-generated MongoID, and returns the Reset.
        """
        return Reset(self.id, reset_data)

    def _create_shop(self, shop_data):
        """
        Creates a Shop object, assigns its pre-generated MongoID, and returns the Shop.
        """
        return Shop(self.id, shop_data)

    def _create_mobile(self, mobile_data):
        """
        Creates a Mobile object, assigns its pre-generated MongoID, and returns the Mobile.
        """
        return Mobile(self.id, mobile_data)

    def _create_object(self, object_data):
        """
        Creates an Item object, assigns its pre-generated MongoID, and returns the Item.
        """
        try:
            return Item(self.id, object_data)
        except Exception as e:
            self.logger.error(f"Failed to create item from data: {object_data[:3] if len(object_data) > 3 else object_data}")
            self.logger.error(f"Error: {e}")
            return None

    def _create_room(self, room_data):
        """
        Creates a Room object, assigns its pre-generated MongoID, and returns the Room.
        """
        vnum = self._extract_vnum(room_data)
        if vnum is not None and vnum in self.room_id_mapping:
            return Room(self, room_data, self.room_id_mapping[vnum])
        else:
            self.logger.warning(f"VNUM {vnum} not found in room_id_mapping.")
            return None

    def insert_area(self):
        """
        Generate the payload for the area and post it to the API service.
        """
        payload = self.to_dict()
        payload['totalRooms'] = len(self.rooms)
        if not self.insert:
            self.logger.info(f"[DRY RUN] Area payload: {json.dumps(payload, indent=2)}")
            return None
        response = post(payload, api_endpoints['area'] + "areas")
        if not response:
            self.logger.error("Failed posting to Area API endpoint: {response}")
            return None
        return json.loads(response.content)

    def insert_rooms(self):
        """
        Posts Room objects to the API endpoint.
        """
        for room in self.rooms:
            payload = room.to_dict()
            if not self.insert:
                self.logger.info(f"[DRY RUN] Room payload: {json.dumps(payload, indent=2)}")
                continue
            response = post(payload, api_endpoints['room'] + "rooms")
            if not response:
                self.logger.error("Failed posting to Room API endpoint: {response}")

    def insert_mobiles(self):
        """
        Posts Mobile objects to the API endpoint.
        """
        for mobile in self.mobiles:
            payload = mobile.to_dict()
            if not self.insert:
                self.logger.info(f"[DRY RUN] Mobile payload: {json.dumps(payload, indent=2)}")
                continue
            response = post(payload, api_endpoints['mobile'] + "mobiles")
            if not response:
                self.logger.error("Failed posting to Mobile API endpoint: {response}")

    def insert_objects(self):
        """
        Posts Item objects to the API endpoint.
        """
        for item in self.objects:
            payload = item.to_dict()
            if not self.insert:
                self.logger.info(f"[DRY RUN] Item payload: {json.dumps(payload, indent=2)}")
                continue
            self.logger.info(f"Inserting item: {payload}")
            response = post(payload, api_endpoints['item'] + "items")
            if not response:
                self.logger.error("Failed to post to Item API endpoint: " + str(response))

    def insert_shops(self):
        """
        Posts Shop objects to the API endpoint.
        """
        for shop in self.shops:
            payload = shop.to_dict()
            if not self.insert:
                self.logger.info(f"[DRY RUN] Shop payload: {json.dumps(payload, indent=2)}")
                continue
            response = post(payload, api_endpoints['shop'] + "shops")
            if not response:
                self.logger.error("Failed to post to Shop API endpoint: " + str(response))

    def insert_resets(self):
        """
        Posts Reset objects to the API endpoint.
        """
        for reset in self.resets:
            payload = reset.to_dict()
            if not self.insert:
                self.logger.info(f"[DRY RUN] Reset payload: {json.dumps(payload, indent=2)}")
                continue
            response = post(payload, api_endpoints['reset'] + "resets")
            if not response:
                self.logger.error("Failed to post to Shop API endpoint: " + str(response))

    def insert_specials(self):
        """
        Posts Special objects to the API endpoint.
        """
        for special in self.specials:
            payload = special.to_dict()
            if not self.insert:
                self.logger.info(f"[DRY RUN] Special payload: {json.dumps(payload, indent=2)}")
                continue
            response = post(payload, api_endpoints['special'] + "specials")
            if not response:
                self.logger.error("Failed to post to Special API endpoint: " + str(response))

    def to_dict(self):
        """
        Return a payload for creating a new area document in MongoDB.
        """
        if not self.name:
            print(f"{self.vnum}; {self.id}; {self.author}; {self.suggested_level_range}")
        return {
            'id': self.id,
            'name': self.name or "Unnamed Area",
            'author': self.author,
            'vnum': self.vnum,
            'totalRooms': 0,
            'rooms': [],
            'suggestedLevelRange': self.suggested_level_range,
            'repopStrategy': "",
            'repopInterval': 0
        }
