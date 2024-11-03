from MigrateRiversOfMud.http import generate_mongo_id


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
        self.item_type = None
        self.extra_flags = None
        self.wear_flags = None
        self.value = None
        self.weight = None
        self.level = None
        self.affect_data = []
        self.extra_descr = []

        try:
            self._parse_item_data(data)
        except ValueError as e:
            print(f"Error while parsing item data: {e}")

    def _parse_item_data(self, lines):
        """
        Parses the item data from the given lines representing a single item.
        """
        index = 1
        self.vnum = lines[0][1:]

        self.name = self._parse_terminated_string(lines, index)
        index += 1
        self.short_descr = self._parse_terminated_string(lines, index)
        index += 1
        self.long_descr = self._parse_terminated_string(lines, index)
        index += 1
        self.description = self._parse_terminated_string(lines, index)
        index += 1

        if index < len(lines):
            tokens = lines[index].split()
            if len(tokens) >= 3:
                self.item_type = tokens[0]
                self.extra_flags = tokens[1]
                self.wear_flags = tokens[2]
                index += 1
            else:
                print("Warning: Invalid item flags line, setting defaults.")
                self.item_type = "unknown"
                self.extra_flags = 0
                self.wear_flags = 0

        while index < len(lines):
            line = lines[index].strip()
            if line.startswith('A'):
                affect_data = self._parse_affect_data(lines, index)
                self.affect_data.append(affect_data)
                index += 1
            elif line.startswith('E'):
                extra_descr = {}
                index += 1
                extra_descr['keyword'] = self._parse_terminated_string(lines, index)
                index += 1
                extra_descr['description'] = self._parse_terminated_string(lines, index)
                index += 1
                self.extra_descr.append(extra_descr)
            else:
                tokens = line.split()
                if len(tokens) >= 3:
                    self.value = tokens[0]
                    self.weight = tokens[1]
                    self.level = tokens[2]
                index += 1

    @staticmethod
    def _parse_affect_data(lines, index):
        """
        Parses affect data from the given lines.
        """
        return lines[index].strip()

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
            'itemType': self.item_type,
            'extraFlags': self.extra_flags,
            'wearFlags': self.wear_flags,
            'value': self.value,
            'weight': self.weight,
            'level': self.level,
            'affectData': self.affect_data,
            'extraDescr': [ed['keyword'] for ed in self.extra_descr],
            'id': self.id
        }
