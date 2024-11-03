from MigrateRiversOfMud.http import generate_mongo_id
from MigrateRiversOfMud.logging import setup_logger


class Special:
    def __init__(self, area_id, data, log_dir='logs'):
        """
        Initializes the Special object with the area data.
        """
        self.area_id = area_id
        self.id = generate_mongo_id()
        self.mob_vnum = None
        self.special_function = None
        self.comment = None
        self.logger = setup_logger("Special", log_dir)

        try:
            self._parse_special_data(data)
        except ValueError as e:
            self.logger.error(f"Error while parsing special data: {e}")

    def _parse_special_data(self, line):
        """
        Parses a single line representing a special function.
        """
        tokens = line.split()
        if len(tokens) >= 3:
            self.mob_vnum = int(tokens[1])
            self.special_function = tokens[2]
            self.comment = " ".join(tokens[3:]).lstrip('*').strip() if len(tokens) > 3 else ""
        else:
            self.logger.error("Invalid special data line format")

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
