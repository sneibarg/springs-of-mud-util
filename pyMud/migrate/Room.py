from enum import Enum
from pyMud.rest import generate_mongo_id


def parse_tilde_terminated_lines(lines, index):
    """
    Parses lines until a line ending with '~' is found.
    Returns the concatenated string and the updated index.
    """
    num_lines = len(lines)
    collected_lines = []
    while index < num_lines:
        line = lines[index]
        if line.endswith('~'):
            collected_lines.append(line.rstrip('~'))
            index += 1
            break
        collected_lines.append(line)
        index += 1
    else:
        raise ValueError("Unexpected end of data while parsing tilde-terminated lines")
    parsed_text = '\n'.join(collected_lines).strip()
    return parsed_text, index


def parse_exit_data(lines, index):
    num_lines = len(lines)
    exit_data = {
        'description': '',
        'keyword': '',
        'exit_flags': 0,
        'key': -1,
        'to_room_vnum': -1,
    }

    exit_data['description'], index = parse_tilde_terminated_lines(lines, index)
    exit_data['keyword'], index = parse_tilde_terminated_lines(lines, index)
    if index < num_lines:
        exit_info_line = lines[index].strip()
        index += 1
        tokens = exit_info_line.split()
        if len(tokens) >= 3:
            try:
                exit_data['exit_flags'] = int(tokens[0], base=16) if tokens[0].isalnum() else 0
            except ValueError:
                exit_data['exit_flags'] = 0
            exit_data['key'] = int(tokens[1]) if tokens[1].lstrip('-').isdigit() else -1
            exit_data['to_room_vnum'] = int(tokens[2]) if tokens[2].lstrip('-').isdigit() else -1
        else:
            print(f"Warning: Invalid exit info line: '{exit_info_line}'. Using default values.")
    else:
        print("Warning: Unexpected end of data while parsing exit info. Using default values.")

    return {'exit': exit_data, 'index': index}


def parse_extra_descr(lines, index):
    extra = {}
    extra['keyword'], index = parse_tilde_terminated_lines(lines, index)
    extra['description'], index = parse_tilde_terminated_lines(lines, index)
    return {'extra': extra, 'index': index}


class SectorType(Enum):
    INSIDE = 0
    CITY = 1
    FIELD = 2
    FOREST = 3
    HILLS = 4
    MOUNTAIN = 5
    WATER_SWIM = 6
    WATER_NOSWIM = 7
    UNDERWATER = 8
    AIR = 9
    DESERT = 10


class DirectionMapping(Enum):
    EXIT_NORTH = 0
    EXIT_EAST = 1
    EXIT_SOUTH = 2
    EXIT_WEST = 3
    EXIT_UP = 4
    EXIT_DOWN = 5


def _extract_vnum(lines, index):
    vnum_line = lines[index].strip()
    if not vnum_line.startswith('#'):
        raise ValueError("Invalid room definition: Missing VNUM")
    vnum = int(vnum_line[1:])
    return vnum, index + 1


def parse_sector_type(sector_str):
    """
    Parses the sector type string and returns the integer value.
    Supports both numeric and symbolic constants.
    """
    sector_str = sector_str.strip()
    if sector_str.isdigit():
        return int(sector_str)
    elif sector_str.upper() in SectorType.__members__:
        return SectorType[sector_str.upper()].value
    else:
        print(f"Warning: Unknown sector type '{sector_str}'. Using default SECTOR_TYPE 'INSIDE'.")
        return SectorType.INSIDE.value


class Room:
    """
    A class to parse room data from area files and conform to the Lombok Data class structure.
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

    def __init__(self, area, data, room_id):
        """
        Initializes the Room object with the area data.
        """
        self.area = area
        self.id = room_id or generate_mongo_id()
        self.data = data
        self.vnum = None
        self.name = ''
        self.description = ''
        self.tele_delay = 0
        self.room_flags = 0
        self.sector_type = 0
        self.extra_descr = []
        self.exits = {}
        self.exitNorth = None
        self.exitEast = None
        self.exitSouth = None
        self.exitWest = None
        self.exitUp = None
        self.exitDown = None

        self.extract_room_fields(self.data)

    def extract_room_fields(self, lines):
        """
        Extracts room data from the given lines representing a single room and sets instance variables.
        """
        index = 0
        self.vnum, index = _extract_vnum(lines, index)
        self.name, index = parse_tilde_terminated_lines(lines, index)
        self.description, index = parse_tilde_terminated_lines(lines, index)
        flags_data, index = self._extract_flags(lines, index, self.vnum)
        self.tele_delay = flags_data['tele_delay']
        self.room_flags = flags_data['room_flags']
        self.sector_type = flags_data['sector_type']
        self.exits, self.extra_descr, index = self._extract_exits_and_extras(lines, index)

    def _extract_flags(self, lines, index, vnum):
        if index >= len(lines):
            raise ValueError(f"Unexpected end of data while parsing room flags for room VNUM: {vnum}")
        tokens = lines[index].strip().split()
        if len(tokens) >= 3:
            tele_delay = int(tokens[0]) if tokens[0].isdigit() else 0
            room_flags = self.parse_room_flags(tokens[1])
            sector_type = parse_sector_type(tokens[2])
            index += 1  # Advance the index after processing the flags line
            return {'tele_delay': tele_delay, 'room_flags': room_flags, 'sector_type': sector_type}, index
        print(f"Warning: Invalid room flags line: '{lines[index]}'. Setting default values.")
        index += 1  # Advance the index even if the line is invalid
        return {'tele_delay': 0, 'room_flags': 0, 'sector_type': SectorType.INSIDE.value}, index

    @staticmethod
    def _extract_exits_and_extras(lines, index):
        exits, extra_descr = {}, []
        while index < len(lines):
            line = lines[index].strip()
            if line == 'S':
                index += 1
                break
            elif line.startswith('D') and len(line) > 1 and line[1].isdigit():
                direction = int(line[1])
                index += 1
                exit_data = parse_exit_data(lines, index)
                index = exit_data['index']
                exits[direction] = exit_data['exit']
            elif line == 'E':
                index += 1
                extra_descr_data = parse_extra_descr(lines, index)
                index = extra_descr_data['index']
                extra_descr.append(extra_descr_data['extra'])
            else:
                index += 1
        return exits, extra_descr, index

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

    def to_dict(self):
        """
        Return a payload for creating a new room document in MongoDB, conforming to the given Lombok Data class.
        """
        def get_exit_room_id(direction):
            """
            Safely retrieves the MongoDB ID for the room in the given direction.
            """
            exit_info = self.exits.get(direction)
            if exit_info:
                to_room_vnum = exit_info.get('to_room_vnum')
                if to_room_vnum is not None:
                    return self.area.room_id_mapping.get(to_room_vnum)
            return None

        payload = {
            'areaId': self.area.id,
            'vnum': self.vnum,
            'name': self.name,
            'description': self.description,
            'spawn': False,
            'spawnTimer': 60000,
            'spawnTime': 0,
            'mobiles': [],
            'alternateRoutes': [],
            'pvp': 'false',
            'id': self.id,
            'exitNorth': get_exit_room_id(DirectionMapping.EXIT_NORTH.value),
            'exitEast': get_exit_room_id(DirectionMapping.EXIT_EAST.value),
            'exitSouth': get_exit_room_id(DirectionMapping.EXIT_SOUTH.value),
            'exitWest': get_exit_room_id(DirectionMapping.EXIT_WEST.value),
            'exitUp': get_exit_room_id(DirectionMapping.EXIT_UP.value),
            'exitDown': get_exit_room_id(DirectionMapping.EXIT_DOWN.value)
        }
        return payload

