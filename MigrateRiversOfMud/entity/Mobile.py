from MigrateRiversOfMud.http import generate_mongo_id
from MigrateRiversOfMud.logging import setup_logger


class Mobile:
    def __init__(self, area_id, data, log_dir='logs'):
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
        self.logger = setup_logger("Mobile", log_dir)

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
        # Name, short description, long description, description (each terminated with ~)
        self.name = self._parse_terminated_string(lines, index)
        index += 1
        self.short_descr = self._parse_terminated_string(lines, index)
        index += 1
        self.long_descr, index = self._parse_multiline_terminated_string(lines, index)
        self.description, index = self._parse_multiline_terminated_string(lines, index)
        self.logger.debug(f"Mobile name {self.name} and short description {self.short_descr}")

        # Act flags, affect flags, alignment
        if index < len(lines):
            tokens = lines[index].split()
            if len(tokens) >= 3 and tokens[0].isdigit():
                self.act_flags = int(tokens[0])
                self.affect_flags = int(tokens[1])
                self.alignment = int(tokens[2])
                index += 1
            else:
                self.logger.warning("Invalid mobile flags line, setting defaults.")
                self.act_flags = 0
                self.affect_flags = 0
                self.alignment = 0

        # Level, hitroll, damage, race, sex, gold, start_pos, default_pos, flags
        if index < len(lines):
            tokens = lines[index].split()
            if len(tokens) >= 9:
                self.level = int(tokens[0])
                self.hitroll = int(tokens[1])
                self.damage = tokens[2]  # Usually in the form of XdY+Z
                self.race = tokens[3]
                self.sex = int(tokens[4])
                self.gold = int(tokens[5])
                self.start_pos = int(tokens[6])
                self.default_pos = int(tokens[7])
                self.flags = int(tokens[8])
            else:
                self.logger.warning("Invalid mobile attributes line, setting defaults.")
                self.level = 0
                self.hitroll = 0
                self.damage = "0d0+0"
                self.race = "unknown"
                self.sex = 0
                self.gold = 0
                self.start_pos = 0
                self.default_pos = 0
                self.flags = 0

    @staticmethod
    def _parse_terminated_string(lines, index):
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
            lines.logger.warning(f"{e}")
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
            'name': self.name,
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
