from MigrateRiversOfMud.http import generate_mongo_id
from MigrateRiversOfMud.logging import setup_logger


class Special:
    def __init__(self, area_id, data, filename='Special.log'):
        """
        Initializes the Special object with the area data.
        """
        self.area_id = area_id
        self.id = generate_mongo_id()
        self.mob_vnum = None
        self.special_function = None
        self.comment = None
        self.logger = setup_logger("Special", filename)

        try:
            self._parse_special_data(data)
        except ValueError as e:
            self.logger.error(f"Error while parsing special data: {e}")

    def _parse_special_data(self, line):
        """
        Parses a single line representing a special function.
        ROM 2.4 format: M <vnum> <spec_function> [comment]
        Also handles '*' comment lines and 'S' terminator
        """
        line = line.strip()

        # Skip comment lines and terminator
        if not line or line.startswith('*') or line == 'S':
            return

        tokens = line.split()

        # First token should be 'M'
        if len(tokens) >= 3 and tokens[0] == 'M':
            self.mob_vnum = int(tokens[1])
            self.special_function = tokens[2]
            # Comment starts after position 2, may or may not have '*'
            if len(tokens) > 3:
                comment_part = " ".join(tokens[3:])
                self.comment = comment_part.lstrip('*').strip()
            else:
                self.comment = ""
        else:
            self.logger.warning(f"Invalid special data line format: {line}")

    def to_dict(self):
        """
        Converts the Special object to a dictionary for payload purposes.
        """
        return {
            'areaId': self.area_id,
            'id': self.id,
            'mobVnum': self.mob_vnum,
            'specialFunction': self.special_function,
            'comment': self.comment
        }
