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
        self.material = None
        self.item_type = None
        self.extra_flags = None
        self.wear_flags = None
        self.value0 = None
        self.value1 = None
        self.value2 = None
        self.value3 = None
        self.value4 = None
        self.level = None
        self.weight = None
        self.cost = None
        self.condition = None
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

        # Name, short description (each terminated with ~ on same line)
        self.name = self._parse_terminated_string(lines, index)
        index += 1
        self.short_descr = self._parse_terminated_string(lines, index)
        index += 1

        # Long description (can be multiline, terminated with ~)
        self.long_descr, index = self._parse_multiline_terminated_string(lines, index)

        # Material (terminated with ~ on same line)
        self.material = self._parse_terminated_string(lines, index)
        index += 1

        # Item type (word), extra flags (flag), wear flags (flag) - all on one line
        if index < len(lines):
            line = lines[index].strip()
            tokens = line.split()
            if len(tokens) >= 3:
                self.item_type = tokens[0]
                self.extra_flags = tokens[1]
                self.wear_flags = tokens[2]
            else:
                self.logger.warning(f"Invalid item type/flags line: {line}, setting defaults.")
                self.item_type = "unknown"
                self.extra_flags = "0"
                self.wear_flags = "0"
            index += 1

        # Value fields (5 values) - all on one line
        if index < len(lines):
            line = lines[index].strip()
            tokens = line.split()
            if len(tokens) >= 5:
                self.value0 = tokens[0]
                self.value1 = tokens[1]
                self.value2 = tokens[2]
                self.value3 = tokens[3]
                self.value4 = tokens[4]
            else:
                self.logger.warning(f"Invalid item values line: {line}, setting defaults.")
                self.value0 = "0"
                self.value1 = "0"
                self.value2 = "0"
                self.value3 = "0"
                self.value4 = "0"
            index += 1

        # Level, weight, cost, condition - all on one line
        if index < len(lines):
            line = lines[index].strip()
            tokens = line.split()
            if len(tokens) >= 4:
                self.level = int(tokens[0]) if tokens[0].lstrip('-').isdigit() else 0
                self.weight = int(tokens[1]) if tokens[1].lstrip('-').isdigit() else 0
                self.cost = int(tokens[2]) if tokens[2].lstrip('-').isdigit() else 0
                self.condition = tokens[3]
            else:
                self.logger.warning(f"Invalid item level/weight/cost/condition line: {line}, setting defaults.")
                self.level = 0
                self.weight = 0
                self.cost = 0
                self.condition = 'P'
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
                # Extra description: E then keyword~ then multiline description ending with ~
                extra_descr = {}
                index += 1
                if index < len(lines):
                    extra_descr['keyword'] = self._parse_terminated_string(lines, index)
                    index += 1
                if index < len(lines):
                    # Parse multiline description
                    extra_descr['description'], index = self._parse_multiline_terminated_string(lines, index)
                self.extra_descr.append(extra_descr)
            else:
                # Unknown line or end marker, break
                break

    @staticmethod
    def _parse_affect_data(lines, index):
        """
        Parses affect data from the given lines.
        """
        return lines[index].strip()

    def _parse_terminated_string(self, lines, index):
        """
        Parses a string terminated with a tilde (~) on the same line.
        """
        if index < len(lines):
            line = lines[index].strip()
            if line.endswith('~'):
                return line.rstrip('~').strip()
        # Handle case where tilde is missing, avoid throwing an error
        self.logger.warning(f"Expected tilde-terminated string at index {index}")
        return ""

    def _parse_multiline_terminated_string(self, lines, index):
        """
        Parses a string terminated with a tilde (~).
        The tilde can be on the same line as the content, or on its own line.
        Mimics fread_string from C which reads until '~' is encountered.
        """
        description_lines = []
        while index < len(lines):
            line = lines[index]

            # Check if line contains a tilde
            if '~' in line:
                # Extract content before the tilde
                content = line[:line.index('~')].strip()
                if content:
                    description_lines.append(content)
                index += 1
                break
            else:
                # No tilde on this line, add the whole line
                description_lines.append(line.strip())
                index += 1

        return "\n".join(description_lines), index

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
            'material': self.material,
            'itemType': self.item_type,
            'extraFlags': self.extra_flags,
            'wearFlags': self.wear_flags,
            'value0': self.value0,
            'value1': self.value1,
            'value2': self.value2,
            'value3': self.value3,
            'value4': self.value4,
            'level': self.level,
            'weight': self.weight,
            'cost': self.cost,
            'condition': self.condition,
            'affectData': self.affect_data,
            'extraDescr': self.extra_descr,
            'id': self.id
        }
