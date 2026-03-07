from MigrateRiversOfMud.http import generate_mongo_id
from MigrateRiversOfMud.logging import setup_logger


class Item:
    def __init__(self, area_id, data, filename='Item.log'):
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
        self.logger = setup_logger("Item", filename)

        try:
            self._parse_item_data(data)
        except ValueError as e:
            self.logger.error(f"Error while parsing item data: {e}")

    def _parse_item_data(self, lines):
        """
        Parses the item data from the given lines representing a single item.
        """
        index = 1
        self.vnum = lines[0][1:]

        # Name, short description, long description, material (each terminated with ~)
        self.name = self._parse_terminated_string(self.logger, lines, index)
        index += 1
        self.short_descr = self._parse_terminated_string(self.logger, lines, index)
        index += 1
        self.long_descr = self._parse_terminated_string(self.logger, lines, index)
        index += 1
        # Material string (terminated with ~) - often this is the long description in old format
        # In new ROM 2.4 format, this is the material field
        self.description = self._parse_terminated_string(self.logger, lines, index)
        index += 1

        # Item type (word), extra flags (flag), wear flags (flag)
        if index < len(lines):
            line = lines[index].strip()
            tokens = line.split()
            if len(tokens) >= 3:
                self.item_type = tokens[0]
                self.extra_flags = tokens[1]
                self.wear_flags = tokens[2]
                index += 1
            else:
                self.logger.warning(f"Invalid item type/flags line: {line}, setting defaults.")
                self.item_type = "unknown"
                self.extra_flags = 0
                self.wear_flags = 0

        # Value fields - this is complex in ROM, we'll read one line with values
        # The format varies by item_type, but we'll just store the raw line
        if index < len(lines):
            line = lines[index].strip()
            # Check if this is an 'A', 'F', or 'E' line (affect/flag/extra)
            if not line or line[0] in ('A', 'F', 'E'):
                self.value = ""
            else:
                self.value = line
                index += 1

        # Level, weight, cost
        if index < len(lines):
            line = lines[index].strip()
            # Check if this is an 'A', 'F', or 'E' line
            if line and line[0] not in ('A', 'F', 'E'):
                tokens = line.split()
                if len(tokens) >= 3:
                    self.level = int(tokens[0]) if tokens[0].lstrip('-').isdigit() else 0
                    self.weight = int(tokens[1]) if tokens[1].lstrip('-').isdigit() else 0
                    # tokens[2] is cost, we don't store it
                index += 1

        # Condition letter (single character like 'P', 'G', etc.)
        if index < len(lines):
            line = lines[index].strip()
            if line and len(line) == 1 and line[0].isalpha() and line[0] not in ('A', 'F', 'E'):
                # This is the condition letter, skip it
                index += 1

        # Affect data, extra descriptions, and flag modifications
        while index < len(lines):
            line = lines[index].strip()
            if line.startswith('A'):
                # Affect: A <location> <modifier>
                affect_data = self._parse_affect_data(lines, index)
                self.affect_data.append(affect_data)
                index += 1
            elif line.startswith('F'):
                # Flag modification: F <type> <location> <modifier> <bitvector>
                # We'll skip these for now
                index += 1
            elif line.startswith('E'):
                # Extra description
                extra_descr = {}
                index += 1
                extra_descr['keyword'] = self._parse_terminated_string(self.logger, lines, index)
                index += 1
                extra_descr['description'] = self._parse_terminated_string(self.logger, lines, index)
                index += 1
                self.extra_descr.append(extra_descr)
            else:
                # Unknown line, skip it
                index += 1

    @staticmethod
    def _parse_affect_data(lines, index):
        """
        Parses affect data from the given lines.
        """
        return lines[index].strip()

    @staticmethod
    def _parse_terminated_string(logger, lines, index):
        """
        Parses a string terminated with a tilde (~).
        """
        if index < len(lines):
            line = lines[index].strip()
            if line.endswith('~'):
                return line.rstrip('~').strip()
        # Handle case where tilde is missing, avoid throwing an error
        logger.error(f"Warning: Unexpected end of data while parsing item string at index {index}")
        return ""

    def to_dict(self):
        """
        Converts the Item object to a dictionary for payload purposes.
        """
        return {
            'areaId': self.area_id,
            'vnum': self.vnum,
            'name': self.name or "unnamed",
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
            'extraDescr': [ed['keyword'] for ed in self.extra_descr],  # Convert extra descriptions to list of keywords
            'id': self.id
        }
