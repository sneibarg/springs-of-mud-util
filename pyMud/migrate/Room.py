from pyMud.globals import room_api
from pyMud.rest import post, generate_mongo_id


def parse_exit_data(lines, index):
    num_lines = len(lines)
    exit = {}

    # Description (terminated with ~)
    description_lines = []
    while index < num_lines:
        line = lines[index]
        if line.endswith('~'):
            description_lines.append(line.rstrip('~'))
            index += 1
            break
        description_lines.append(line)
        index += 1
    else:
        raise ValueError("Unexpected end of data while parsing exit description")

    exit['description'] = '\n'.join(description_lines).strip()

    # Keywords (terminated with ~)
    keyword_lines = []
    while index < num_lines:
        line = lines[index]
        if line.endswith('~'):
            keyword_lines.append(line.rstrip('~'))
            index += 1
            break
        keyword_lines.append(line)
        index += 1
    else:
        raise ValueError("Unexpected end of data while parsing exit keywords")

    exit['keyword'] = ' '.join(keyword_lines).strip()

    # Exit flags, Key VNUM, To Room VNUM
    if index < num_lines:
        exit_info_line = lines[index].strip()
        index += 1
        tokens = exit_info_line.split()
        if len(tokens) >= 3:
            try:
                exit['exit_flags'] = int(tokens[0], base=16) if tokens[0].isalnum() else 0
            except ValueError:
                exit['exit_flags'] = 0
            exit['key'] = int(tokens[1]) if tokens[1].lstrip('-').isdigit() else -1
            exit['to_room_vnum'] = int(tokens[2]) if tokens[2].lstrip('-').isdigit() else -1
        else:
            raise ValueError(f"Invalid exit info line: '{exit_info_line}'")
    else:
        raise ValueError("Unexpected end of data while parsing exit info")

    return {'exit': exit, 'index': index}


def parse_extra_descr(lines, index):
    num_lines = len(lines)
    extra = {}

    # Keyword(s) (terminated with ~)
    keyword_lines = []
    while index < num_lines:
        line = lines[index]
        keyword_lines.append(line.rstrip('~'))
        if line.endswith('~'):
            index += 1
            break
        index += 1
    else:
        raise ValueError("Unexpected end of data while parsing extra description keywords")

    extra['keyword'] = ' '.join(keyword_lines).strip()

    # Description (terminated with ~)
    description_lines = []
    while index < num_lines:
        line = lines[index]
        description_lines.append(line.rstrip('~'))
        if line.endswith('~'):
            index += 1
            break
        index += 1
    else:
        raise ValueError("Unexpected end of data while parsing extra description")

    extra['description'] = '\n'.join(description_lines).strip()

    return {'extra': extra, 'index': index}


class Room:
    area_id = None
    room_id = None
    vnum = None
    exits = {}
    """
    A class to parse room data from area files.
    """

    ROOM_FLAG_BITS = {
        'A': 1 << 0,
        'B': 1 << 1,
        'C': 1 << 2,
        'D': 1 << 3,
        'E': 1 << 4,
        'F': 1 << 5,
        'G': 1 << 6,
        'H': 1 << 7,
        'I': 1 << 8,
        'J': 1 << 9,
        'K': 1 << 10,
        'L': 1 << 11,
        'M': 1 << 12,
        'N': 1 << 13,
        'O': 1 << 14,
        'P': 1 << 15,
        'Q': 1 << 16,
        'R': 1 << 17,
        'S': 1 << 18,
        'T': 1 << 19,
        'U': 1 << 20,
        'V': 1 << 21,
        'W': 1 << 22,
        'X': 1 << 23,
        'Y': 1 << 24,
        'Z': 1 << 25,
    }

    SECTOR_TYPES = {
        'INSIDE': 0,
        'CITY': 1,
        'FIELD': 2,
        'FOREST': 3,
        'HILLS': 4,
        'MOUNTAIN': 5,
        'WATER_SWIM': 6,
        'WATER_NOSWIM': 7,
        'UNDERWATER': 8,
        'AIR': 9,
        'DESERT': 10,
    }

    def __init__(self, area_id, data):
        """
        Initializes the RoomParser with the area data.
        """
        self.area_id = area_id
        self.room_id = generate_mongo_id()
        self.data = data
        self.exits = {}  # Initialize exits dictionary
        room = self.extract_room_fields(self.data)
        self.vnum = room['vnum']
        self.extra_descr = room['extra_descr']
        print("ROOM=" + str(room))

        # Initially create the room without exits
        room_payload = self.to_dict()  # Convert room to dictionary for payload
        room_payload['id'] = self.room_id  # Add generated Mongo ID to payload
        print("ROOM-PAYLOAD=" + str(room_payload))
        response = post(room_payload, room_api + "room")
        print("ROOM-RESPONSE=" + str(response))

    def extract_room_fields(self, lines):
        """
        Extracts room data from the given lines representing a single room.
        """
        room = {}
        index = 0
        num_lines = len(lines)
        vnum_line = lines[index].strip()
        if vnum_line.startswith('#'):
            room_vnum = int(vnum_line[1:])
            room['vnum'] = room_vnum
            print(f"Parsing room VNUM: {room_vnum}")
            index += 1
        else:
            raise ValueError("Invalid room definition: Missing VNUM")

        # Name (terminated with ~)
        name_lines = []
        while index < num_lines:
            line = lines[index]
            if line.endswith('~'):
                name_lines.append(line.rstrip('~'))
                index += 1
                break
            name_lines.append(line)
            index += 1
        else:
            raise ValueError(f"Unexpected end of data while parsing room name for room VNUM: {room_vnum}")

        room['name'] = '\n'.join(name_lines).strip()

        # Description (terminated with ~)
        description_lines = []
        while index < num_lines:
            line = lines[index]
            if line.endswith('~'):
                description_lines.append(line.rstrip('~'))
                index += 1
                break
            description_lines.append(line)
            index += 1
        else:
            raise ValueError(f"Unexpected end of data while parsing room description for room VNUM: {room_vnum}")

        room['description'] = '\n'.join(description_lines).strip()

        # Teleport Delay, Room Flags, Sector Type
        if index < num_lines:
            flags_line = lines[index].strip()
            index += 1
            tokens = flags_line.split()
            if len(tokens) >= 3:
                tele_delay_str = tokens[0]
                if tele_delay_str.isdigit():
                    tele_delay = int(tele_delay_str)
                else:
                    tele_delay = 0  # Default value if parsing fails

                room_flags = self.parse_room_flags(tokens[1])
                sector_type = self.parse_sector_type(tokens[2])

                room['tele_delay'] = tele_delay
                room['room_flags'] = room_flags
                room['sector_type'] = sector_type
            else:
                print(f"Warning: Invalid room flags line: '{flags_line}'. Setting default values.")
                room['tele_delay'] = 0
                room['room_flags'] = 0
                room['sector_type'] = self.SECTOR_TYPES['INSIDE']
        else:
            raise ValueError(f"Unexpected end of data while parsing room flags for room VNUM: {room_vnum}")

        # Initialize exits and extra descriptions
        room['exits'] = {}
        room['extra_descr'] = []

        # Parse optional extra descriptions and exits
        while index < num_lines:
            line = lines[index].strip()
            if line == 'S':  # End of room definition
                index += 1
                break
            elif line.startswith('D') and len(line) > 1 and line[1].isdigit():  # Exit definition
                direction = int(line[1])  # Door number
                index += 1  # Move to the next line for parsing exit data
                exit_data = parse_exit_data(lines, index)
                index = exit_data['index']  # Update index after parsing exit
                room['exits'][direction] = exit_data['exit']
                self.exits[direction] = exit_data['exit']  # Update the exits attribute of the Room object
            elif line == 'E':  # Extra description
                index += 1  # Move to the next line for parsing extra description
                extra_descr = parse_extra_descr(lines, index)
                index = extra_descr['index']
                room['extra_descr'].append(extra_descr['extra'])

        return room

    def parse_room_flags(self, flags_str):
        """
        Parses the room flags string and returns the combined integer value.
        Supports both numeric and alphabetical constants (letters).
        """
        flags = 0
        if flags_str.isdigit():
            flags = int(flags_str)
        else:
            for char in flags_str:
                if char.isalpha():
                    char = char.upper()
                    if char in self.ROOM_FLAG_BITS:
                        flags |= self.ROOM_FLAG_BITS[char]
                    else:
                        print(f"Warning: Unknown room flag '{char}'. Ignoring.")
                elif char in ('-', ',', "'"):
                    continue  # Ignore '-', ',', and "'" characters
                else:
                    raise ValueError(f"Unknown room flag character: {char}")
        return flags

    def parse_sector_type(self, sector_str):
        """
        Parses the sector type string and returns the integer value.
        Supports both numeric and symbolic constants.
        """
        sector_str = sector_str.strip()
        if sector_str.isdigit():
            return int(sector_str)
        elif sector_str.upper() in self.SECTOR_TYPES:
            return self.SECTOR_TYPES[sector_str.upper()]
        else:
            print(f"Warning: Unknown sector type '{sector_str}'. Using default SECTOR_TYPES['INSIDE'].")
            return self.SECTOR_TYPES['INSIDE']  # Default sector type

    def to_dict(self):
        """
        Converts the Room object to a dictionary for payload purposes.
        """
        return {
            'areaId': self.area_id,
            'vnum': self.vnum,
            'name': self.data[1],  # Corrected index for name
            'description': self.data[2],  # Corrected index for description
            'tele_delay': self.data[3],  # Corrected index for tele_delay
            'room_flags': self.data[4],  # Corrected index for room_flags
            'sector_type': self.data[5],  # Corrected index for sector_type
            'exits': {direction: {
                'to_room_vnum': exit_info.get('to_room_vnum', None),
                'exit_flags': exit_info.get('exit_flags', 0),
                'key': exit_info.get('key', -1),
                'description': exit_info.get('description', ''),
                'keyword': exit_info.get('keyword', '')
            } for direction, exit_info in self.exits.items()},
            'extra_descr': self.extra_descr
        }

    def update_exits(self, room_id_mapping):
        """
        Updates the room exits with Mongo IDs instead of VNUMs.
        """
        for direction, exit_data in self.exits.items():
            if 'to_room_vnum' in exit_data:
                to_vnum = exit_data['to_room_vnum']
                if to_vnum in room_id_mapping:
                    exit_data['to_room_id'] = room_id_mapping[to_vnum]
                    del exit_data['to_room_vnum']

        # Update the room payload with the new exits
        room_payload = self.to_dict()
        print("UPDATED-ROOM-PAYLOAD=" + str(room_payload))
        response = post(room_payload, room_api + "room")
        print("UPDATED-ROOM-RESPONSE=" + str(response))
