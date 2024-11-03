import re
from MigrateRiversOfMud.http import generate_mongo_id
from MigrateRiversOfMud.logging import setup_logger


class Reset:
    def __init__(self, area_id, data, log_dir='logs'):
        """
        Initializes the Reset object with the area data.
        """
        self.area_id = area_id
        self.id = generate_mongo_id()
        self.reset_type = None
        self.args = []
        self.comment = ""
        self.logger = setup_logger("Reset", log_dir)

        try:
            self._parse_reset_data(data)
        except ValueError as e:
            self.logger.error(f"Error while parsing reset data: {e}")

    def _parse_reset_data(self, line):
        """
        Parses the reset data from a single line representing a reset.
        """
        tokens = re.split(r'\s+', line.strip())
        if len(tokens) < 2:
            raise ValueError("Invalid reset line: Insufficient data")

        self.reset_type = tokens[0]
        self.args = [int(token) if token.isdigit() else token for token in tokens[1:-1]]
        self.comment = tokens[-1] if tokens[-1].startswith('*') else ""

        self.logger.info(f"Parsed reset: type={self.reset_type}, args={self.args}, comment={self.comment}")

    def to_dict(self):
        """
        Converts the Reset object to a dictionary for payload purposes.
        """
        return {
            'areaId': self.area_id,
            'id': self.id,
            'resetType': self.reset_type,
            'args': self.args,
            'comment': self.comment
        }

