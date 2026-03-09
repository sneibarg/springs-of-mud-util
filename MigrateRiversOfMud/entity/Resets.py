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
        self.command = None
        self.arg1 = None
        self.arg2 = None
        self.arg3 = None
        self.arg4 = None
        self.comment = ""
        self.logger = setup_logger("Reset", filename)

        try:
            self._parse_reset_data(data)
        except ValueError as e:
            self.logger.error(f"Error while parsing reset data: {e}")

    def _parse_reset_data(self, line):
        """
        Parses the reset data from a single line representing a reset.
        ROM 2.4 format: <command> <if_flag> <arg1> <arg2> [<arg3>] [<arg4>] [* comment]

        Matches the C code in db.c load_resets() function:
        - command = fread_letter
        - if_flag = fread_number (read but not stored)
        - arg1 = fread_number
        - arg2 = fread_number
        - arg3 = fread_number (0 for G and R commands)
        - arg4 = fread_number (only for P and M commands, else 0)
        """
        line = line.strip()

        # Skip empty lines
        if not line:
            raise ValueError(f"Invalid reset line: Empty line")

        # Skip comment lines (lines starting with *)
        if line.startswith('*'):
            raise ValueError(f"Invalid reset line: Comment line")

        # Skip 'S' end marker
        if line.strip() == 'S':
            raise ValueError(f"Invalid reset line: End marker")

        # Check for comment at the end (after the data)
        comment_idx = line.find('*')
        if comment_idx > 0:
            self.comment = line[comment_idx+1:].strip()
            line = line[:comment_idx].strip()
        else:
            self.comment = ""

        tokens = re.split(r'\s+', line)

        # Minimum: command if_flag arg1 arg2
        if len(tokens) < 4:
            raise ValueError(f"Invalid reset line: Insufficient data: {line}")

        self.command = tokens[0]
        # if_flag is tokens[1] - read but not stored per C code

        # Parse arg1 and arg2 (always present)
        self.arg1 = int(tokens[2]) if tokens[2].lstrip('-').isdigit() else 0
        self.arg2 = int(tokens[3]) if tokens[3].lstrip('-').isdigit() else 0

        # arg3 is 0 for 'G' and 'R' commands, otherwise read from tokens[4]
        if self.command in ('G', 'R'):
            self.arg3 = 0
        elif len(tokens) > 4:
            self.arg3 = int(tokens[4]) if tokens[4].lstrip('-').isdigit() else 0
        else:
            self.arg3 = 0

        # arg4 only for 'P' and 'M' commands, otherwise 0
        if self.command in ('P', 'M') and len(tokens) > 5:
            self.arg4 = int(tokens[5]) if tokens[5].lstrip('-').isdigit() else 0
        else:
            self.arg4 = 0

        self.logger.debug(f"Parsed reset: command={self.command}, arg1={self.arg1}, arg2={self.arg2}, arg3={self.arg3}, arg4={self.arg4}, comment={self.comment}")

    def to_dict(self):
        """
        Converts the Reset object to a dictionary for payload purposes.
        """
        return {
            'areaId': self.area_id,
            'id': self.id,
            'command': self.command,
            'arg1': self.arg1,
            'arg2': self.arg2,
            'arg3': self.arg3,
            'arg4': self.arg4,
            'comment': self.comment
        }

