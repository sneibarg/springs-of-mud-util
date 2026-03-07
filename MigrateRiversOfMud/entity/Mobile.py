from MigrateRiversOfMud.http import generate_mongo_id
from MigrateRiversOfMud.logging import setup_logger


class Mobile:
    def __init__(self, area_id, data, filename='Mobile.log'):
        """
        Initializes the Mobile object with the area data.
        """
        self.area_id = area_id
        self.id = generate_mongo_id()
        self.vnum = None
        self.name = None
        self.short_descr = None
        self.long_descr = None
        self.description = None
        self.act_flags = None
        self.affect_flags = None
        self.alignment = None
        self.level = None
        self.hitroll = None
        self.damage = None
        self.race = None
        self.sex = None
        self.gold = None
        self.start_pos = None
        self.default_pos = None
        self.flags = None
        self.logger = setup_logger("Mobile", filename)

        try:
            self._parse_mobile_data(data)
        except ValueError as e:
            self.logger.error(f"Error while parsing mobile data: {e}")

    def _parse_mobile_data(self, lines):
        """
        Parses the mobile data from the given lines representing a single mobile.
        """
        index = 1
        self.vnum = lines[0][1:]
        # Name, short description, long description, description, race (each terminated with ~)
        self.name = self._parse_terminated_string(lines, index)
        index += 1
        self.short_descr = self._parse_terminated_string(lines, index)
        index += 1
        self.long_descr, index = self._parse_multiline_terminated_string(lines, index)
        self.description, index = self._parse_multiline_terminated_string(lines, index)
        self.race = self._parse_terminated_string(lines, index)
        index += 1
        self.logger.debug(f"Mobile name {self.name} and short description {self.short_descr}")

        # Act flags, affect flags (these are read as flags, not simple numbers)
        if index < len(lines):
            line = lines[index].strip()
            tokens = line.split()
            if len(tokens) >= 2:
                self.act_flags = int(tokens[0]) if tokens[0].isdigit() else 0
                self.affect_flags = int(tokens[1]) if tokens[1].isdigit() else 0
                index += 1
            else:
                self.logger.warning(f"Invalid mobile act/affect flags line: {line}, setting defaults.")
                self.act_flags = 0
                self.affect_flags = 0

        # Alignment and group
        if index < len(lines):
            tokens = lines[index].split()
            if len(tokens) >= 2:
                self.alignment = int(tokens[0])
                # group is tokens[1], but we're not storing it
                index += 1
            else:
                self.logger.warning("Invalid mobile alignment/group line, setting defaults.")
                self.alignment = 0

        # Level and hitroll
        if index < len(lines):
            tokens = lines[index].split()
            if len(tokens) >= 2:
                self.level = int(tokens[0])
                self.hitroll = int(tokens[1])
                index += 1
            else:
                self.logger.warning("Invalid mobile level/hitroll line, setting defaults.")
                self.level = 0
                self.hitroll = 0

        # Hit dice (format: NdN+N)
        if index < len(lines):
            # Skip hit dice line - we don't store this
            index += 1

        # Mana dice (format: NdN+N)
        if index < len(lines):
            # Skip mana dice line - we don't store this
            index += 1

        # Damage dice (format: NdN+N) and dam_type (word)
        if index < len(lines):
            line = lines[index].strip()
            # Extract damage dice portion (e.g., "1d4+0")
            tokens = line.split()
            if tokens:
                self.damage = tokens[0]
            else:
                self.damage = "0d0+0"
            # dam_type is the second token, but we don't store it separately
            index += 1

        # AC values (4 numbers)
        if index < len(lines):
            # Skip AC line - we don't store this
            index += 1

        # Off/imm/res/vuln flags (4 flag values)
        if index < len(lines):
            # Skip flags line - we don't store this
            index += 1

        # Start pos, default pos, sex (3 words)
        if index < len(lines):
            tokens = lines[index].split()
            if len(tokens) >= 3:
                # These are words, need to map to numbers
                # For now, store as-is or use simple mapping
                self.start_pos = self._position_lookup(tokens[0])
                self.default_pos = self._position_lookup(tokens[1])
                self.sex = self._sex_lookup(tokens[2])
                index += 1
            else:
                self.logger.warning("Invalid mobile pos/sex line, setting defaults.")
                self.start_pos = 0
                self.default_pos = 0
                self.sex = 0

        # Wealth (gold)
        if index < len(lines):
            tokens = lines[index].split()
            if tokens and tokens[0].isdigit():
                self.gold = int(tokens[0])
                index += 1
            else:
                self.gold = 0

        # Form and parts flags
        if index < len(lines):
            # Skip form/parts line - we don't store this
            index += 1

        # Size and material (2 words)
        if index < len(lines):
            # Skip size/material line - we don't store this
            index += 1

        # There may be additional 'F' flag removal lines, but we'll skip those
        self.flags = 0  # Set default for flags field

    def _position_lookup(self, pos_str):
        """Map position string to number"""
        positions = {
            'dead': 0, 'mortal': 1, 'incap': 2, 'stunned': 3,
            'sleeping': 4, 'resting': 5, 'sitting': 6,
            'fighting': 7, 'standing': 8
        }
        return positions.get(pos_str.lower(), 8)

    def _sex_lookup(self, sex_str):
        """Map sex string to number"""
        sexes = {'none': 0, 'male': 1, 'female': 2, 'either': 3}
        return sexes.get(sex_str.lower(), 0)

    def _parse_terminated_string(self, lines, index):
        """
        Parses a string terminated with a tilde (~).
        """
        try:
            if index < len(lines):
                line = lines[index].strip()
                if line.endswith('~'):
                    return line.rstrip('~').strip()
                elif "'" in line:
                    return line.strip()  # Handle apostrophes gracefully
            raise ValueError("Unexpected end of data while parsing mobile string")
        except ValueError as e:
            self.logger.warning(f"{e}")
            return ""

    def _parse_multiline_terminated_string(self, lines, index):
        """
        Parses a multiline string terminated with a tilde (~).
        """
        description_lines = []
        while index < len(lines):
            line = lines[index].strip()
            if line == '~':
                index += 1
                break
            description_lines.append(line)
            index += 1

        return "\n".join(description_lines), index

    def to_dict(self):
        """
        Converts the Mobile object to a dictionary for payload purposes.
        """
        return {
            'areaId': self.area_id,
            'vnum': self.vnum,
            'name': self.name or "unnamed",
            'shortDescription': self.short_descr,
            'longDescription': self.long_descr,
            'description': self.description,
            'actFlags': self.act_flags,
            'affectFlags': self.affect_flags,
            'alignment': self.alignment,
            'level': self.level,
            'hitroll': self.hitroll,
            'damage': self.damage,
            'race': self.race,
            'sex': self.sex,
            'gold': self.gold,
            'startPos': self.start_pos,
            'defaultPos': self.default_pos,
            'flags': self.flags,
            'id': self.id
        }
