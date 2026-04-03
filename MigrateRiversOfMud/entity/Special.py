from MigrateRiversOfMud.http.SOMClient import generate_mongo_id
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
        ROM 2.4 format: M <vnum> <spec_function> [* comment]

        Matches the C code in db.c load_specials() function:
        - Reads a letter: 'S' ends, '*' is comment, 'M' is mob special
        - For 'M': vnum = fread_number, spec_fun = fread_word
        - Then fread_to_eol (consumes rest of line including comment)
        """
        line = line.strip()

        # Skip empty lines
        if not line:
            raise ValueError(f"Invalid special line: Empty line")

        # Skip comment lines (lines starting with *)
        if line.startswith('*'):
            raise ValueError(f"Invalid special line: Comment line")

        # Skip 'S' end marker
        if line == 'S':
            raise ValueError(f"Invalid special line: End marker")

        # Skip section markers
        if line.startswith('#'):
            raise ValueError(f"Invalid special line: Section marker")

        tokens = line.split()

        # Must be: M vnum spec_function [* comment]
        if len(tokens) < 3:
            raise ValueError(f"Invalid special line: Insufficient data: {line}")

        if tokens[0] != 'M':
            raise ValueError(f"Invalid special line: Expected 'M', got '{tokens[0]}'")

        self.mob_vnum = int(tokens[1]) if tokens[1].lstrip('-').isdigit() else 0
        self.special_function = tokens[2]

        # Extract comment (everything after the spec_function)
        if len(tokens) > 3:
            # Find the position after spec_function and extract the rest
            rest_of_line = line.split(tokens[2], 1)[1].strip()
            # Remove leading '*' if present
            if rest_of_line.startswith('*'):
                self.comment = rest_of_line[1:].strip()
            else:
                self.comment = rest_of_line
        else:
            self.comment = ""

        self.logger.debug(f"Parsed special: mob_vnum={self.mob_vnum}, spec_function={self.special_function}, comment={self.comment}")

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
