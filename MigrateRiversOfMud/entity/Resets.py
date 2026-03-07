import re
from MigrateRiversOfMud.http import generate_mongo_id
from MigrateRiversOfMud.logging import setup_logger


class Reset:
    def __init__(self, area_id, data, filename='Reset.log'):
        """
        Initializes the Reset object with the area data.
        """
        self.area_id = area_id
        self.id = generate_mongo_id()
        self.reset_type = None
        self.args = []
        self.comment = ""
        self.logger = setup_logger("Reset", filename)

        try:
            self._parse_reset_data(data)
        except ValueError as e:
            self.logger.error(f"Error while parsing reset data: {e}")

    def _parse_reset_data(self, line):
        """
        Parses the reset data from a single line representing a reset.
        ROM 2.4 format: <command> <if_flag> <arg1> <arg2> [<arg3>] [<arg4>] [comment]
        """
        line = line.strip()

        # Check for comment at the end
        comment_idx = line.find('*')
        if comment_idx > 0:
            self.comment = line[comment_idx:].strip()
            line = line[:comment_idx].strip()
        else:
            self.comment = ""

        tokens = re.split(r'\s+', line)
        if len(tokens) < 4:
            raise ValueError(f"Invalid reset line: Insufficient data: {line}")

        self.reset_type = tokens[0]

        # Parse: if_flag arg1 arg2 [arg3] [arg4]
        # We skip if_flag (tokens[1]) as ROM does
        arg1 = int(tokens[2]) if tokens[2].lstrip('-').isdigit() else 0
        arg2 = int(tokens[3]) if tokens[3].lstrip('-').isdigit() else 0

        # arg3 is 0 for 'G' and 'R' commands, otherwise read it
        if self.reset_type in ('G', 'R'):
            arg3 = 0
            arg4 = 0
        elif len(tokens) > 4:
            arg3 = int(tokens[4]) if tokens[4].lstrip('-').isdigit() else 0
            # arg4 only for 'P' and 'M' commands
            if self.reset_type in ('P', 'M') and len(tokens) > 5:
                arg4 = int(tokens[5]) if tokens[5].lstrip('-').isdigit() else 0
            else:
                arg4 = 0
        else:
            arg3 = 0
            arg4 = 0

        self.args = [arg1, arg2, arg3, arg4]

        self.logger.debug(f"Parsed reset: type={self.reset_type}, args={self.args}, comment={self.comment}")

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

