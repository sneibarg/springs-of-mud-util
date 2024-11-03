from pyMud.rest import generate_mongo_id


class Item:
    def __init__(self, area_id, data):
        """
        Initializes the Item object with the area data.
        """
        self.area_id = area_id
        self.id = generate_mongo_id()
        self.vnum = None
        self.name = None
        self.short_descr = None
        self.long_descr = None
        self.description = None
        self.type = None
        self.extra_flags = None
        self.wear_flags = None
        self.value = None
        self.weight = None
        self.level = None
        self.affects = []
        self.extra_descr = []
        self._parse_item_data(data)
        print("NEW-ITEM="+str(self.to_dict()))

    def _parse_item_data(self, lines):
        """
        Parses the item data from the given lines representing a single item.
        """
        index = 0
        num_lines = len(lines)
        vnum_line = lines[index].strip()
        if vnum_line.startswith('#'):
            self.vnum = int(vnum_line[1:])
            index += 1
        else:
            raise ValueError("Invalid item definition: Missing VNUM")

        # Name, short description, long description, description (each terminated with ~)
        self.name = self._parse_terminated_string(lines, index)
        index += 1
        self.short_descr = self._parse_terminated_string(lines, index)
        index += 1
        self.long_descr = self._parse_terminated_string(lines, index)
        index += 1
        self.description = self._parse_terminated_string(lines, index)
        index += 1

        # Item type, extra flags, wear flags
        if index < num_lines:
            tokens = lines[index].split()
            if len(tokens) >= 3:
                self.type = tokens[0]
                self.extra_flags = tokens[1]
                self.wear_flags = tokens[2]
                index += 1
            else:
                raise ValueError("Invalid item flags line")

        # Value, weight, level, and affects
        if index < num_lines:
            tokens = lines[index].split()
            if len(tokens) >= 3:
                self.value = tokens[0]
                self.weight = tokens[1]
                self.level = tokens[2]
                index += 1
            else:
                raise ValueError("Invalid item attributes line")

        # Affects and extra descriptions
        while index < num_lines:
            line = lines[index].strip()
            if line == 'A':  # Affect data
                index += 1
                if index < num_lines:
                    self.affects.append(lines[index].strip())
                    index += 1
            elif line == 'E':  # Extra description
                index += 1
                extra_descr = {'keyword': self._parse_terminated_string(lines, index)}
                index += 1
                extra_descr['description'] = self._parse_terminated_string(lines, index)
                index += 1
                self.extra_descr.append(extra_descr)
            else:
                index += 1

    @staticmethod
    def _parse_terminated_string(lines, index):
        """
        Parses a string terminated with a tilde (~).
        """
        if index < len(lines):
            line = lines[index].strip()
            if line.endswith('~'):
                return line.rstrip('~').strip()
        print(f"Warning: Unexpected end of data while parsing item string at index {index}")
        return ""

    def to_dict(self):
        """
        Converts the Item object to a dictionary for payload purposes.
        """
        return {
            'areaId': self.area_id,
            'vnum': self.vnum,
            'name': self.name,
            'shortDescription': self.short_descr,
            'longDescription': self.long_descr,
            'description': self.description,
            'type': self.type,
            'extraFlags': self.extra_flags,
            'wearFlags': self.wear_flags,
            'value': self.value,
            'weight': self.weight,
            'level': self.level,
            'affects': self.affects,
            'extraDescriptions': self.extra_descr,
            'id': self.id
        }
