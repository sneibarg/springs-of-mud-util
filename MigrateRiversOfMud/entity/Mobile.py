from MigrateRiversOfMud.http.SOMClient import *
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
        self.group = None
        self.level = None
        self.hitroll = None
        self.hit_dice = None
        self.mana_dice = None
        self.damage_dice = None
        self.dam_type = None
        self.armor_class = None
        self.combat_flags = None
        self.start_pos = None
        self.default_pos = None
        self.sex = None
        self.gold = None
        self.form = None
        self.parts = None
        self.size = None
        self.material = None
        self.race = None
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
        # Some old-style areas include an extra tilde-terminated flags line (e.g. "unique~")
        # between race and the act/affect/alignment/group numeric line.
        if index < len(lines):
            line = lines[index].strip()
            if line.endswith('~'):
                self.flags = line.rstrip('~').strip()
                index += 1
        self.logger.debug(f"Mobile name {self.name} and short description {self.short_descr}")

        # Act flags, affect flags, alignment, group (all on one line)
        if index < len(lines):
            line = lines[index].strip()
            tokens = line.split()
            if len(tokens) >= 4:
                self.act_flags = self._safe_int(tokens[0], 0)
                self.affect_flags = self._safe_int(tokens[1], 0)
                self.alignment = self._safe_int(tokens[2], 0)
                self.group = self._safe_int(tokens[3], 0)
            else:
                self.logger.warning(f"Invalid mobile act/affect/align/group line: {line}, setting defaults.")
                self.act_flags = 0
                self.affect_flags = 0
                self.alignment = 0
                self.group = 0
            index += 1

        # Level, hitroll, hit dice, mana dice, damage dice, dam_type (all on one line)
        # Format: level hitroll NdN+N NdN+N NdN+N dam_type
        if index < len(lines):
            tokens = lines[index].split()
            if len(tokens) >= 6:
                self.level = self._safe_int(tokens[0], 0)
                self.hitroll = self._safe_int(tokens[1], 0)
                self._parse_dice(tokens[2], 'hit')
                self._parse_dice(tokens[3], 'mana')
                self._parse_dice(tokens[4], 'damage')
                self.dam_type = tokens[5]
            else:
                self.logger.warning(f"Invalid mobile level/hitroll/dice line: {tokens}, setting defaults.")
                self.level = 0
                self.hitroll = 0
                self.hit_dice = str({'number': 0, 'type': 0, 'bonus': 0})
                self.mana_dice = str({'number': 0, 'type': 0, 'bonus': 0})
                self.damage_dice = str({'number': 0, 'type': 0, 'bonus': 0})
                self.dam_type = 'none'
            index += 1

        # AC values (4 numbers: pierce, bash, slash, exotic)
        if index < len(lines):
            tokens = lines[index].split()
            self.armor_class = {}
            if len(tokens) >= 4:
                self.armor_class = str({
                    'pierce': self._safe_int(tokens[0], 0) * 10,
                    'bash': self._safe_int(tokens[1], 0) * 10,
                    'slash': self._safe_int(tokens[2], 0) * 10,
                    'exotic': self._safe_int(tokens[3], 0) * 10
                })
            else:
                self.logger.warning("Invalid AC line, setting defaults.")
                self.armor_class = str({'pierce': 0, 'bash': 0, 'slash': 0, 'exotic': 0})
            index += 1

        # Off/imm/res/vuln flags (4 flag values)
        if index < len(lines):
            tokens = lines[index].split()
            if len(tokens) >= 4:
                self.combat_flags = str({
                    'off_flags': self._parse_flag_token(tokens[0]),
                    'imm_flags': self._parse_flag_token(tokens[1]),
                    'res_flags': self._parse_flag_token(tokens[2]),
                    'vuln_flags': self._parse_flag_token(tokens[3])
                })
            else:
                self.logger.warning("Invalid flags line, setting defaults.")
                self.combat_flags = str({'off_flags': 0, 'imm_flags': 0, 'res_flags': 0, 'vuln_flags': 0})
            index += 1

        # Start pos, default pos, sex, gold (all on one line)
        if index < len(lines):
            tokens = lines[index].split()
            if len(tokens) >= 4:
                self.start_pos = self._position_lookup(tokens[0])
                self.default_pos = self._position_lookup(tokens[1])
                self.sex = self._sex_lookup(tokens[2])
                self.gold = self._safe_int(tokens[3], 0)
            else:
                self.logger.warning(f"Invalid mobile pos/sex/gold line: {tokens}, setting defaults.")
                self.start_pos = 8
                self.default_pos = 8
                self.sex = 0
                self.gold = 0
            index += 1

        # Form, parts, size, material (all on one line)
        if index < len(lines):
            tokens = lines[index].split()
            if len(tokens) >= 4:
                self.form = self._safe_int(tokens[0], 0)
                self.parts = self._safe_int(tokens[1], 0)
                self.size = tokens[2]
                self.material = tokens[3]
            else:
                self.logger.warning(f"Invalid form/parts/size/material line: {tokens}, setting defaults.")
                self.form = 0
                self.parts = 0
                self.size = 'medium'
                self.material = 'unknown'
            index += 1

        # There may be additional 'F' flag removal lines, but we'll skip those
        if self.flags is None:
            self.flags = 0

    @staticmethod
    def _safe_int(value, default=0):
        """Safely convert string token to int, returning default on failure."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _parse_flag_token(self, token):
        """Return numeric flags as int and symbolic flags as-is."""
        try:
            return int(token)
        except (TypeError, ValueError):
            return token

    def _parse_dice(self, dice_str, dice_type):
        """Parse dice notation (e.g., '2d6+3') and store components"""
        try:
            # Format: NdN+N or NdN-N
            if 'd' in dice_str:
                parts = dice_str.replace('-', '+-').split('d')
                number = int(parts[0])

                if '+' in parts[1]:
                    type_bonus = parts[1].split('+')
                    dice_type_val = int(type_bonus[0])
                    bonus = int(type_bonus[1]) if len(type_bonus) > 1 else 0
                else:
                    dice_type_val = int(parts[1])
                    bonus = 0

                if dice_type == 'hit':
                    self.hit_dice = str({'number': number, 'type': dice_type_val, 'bonus': bonus})
                elif dice_type == 'mana':
                    self.mana_dice = str({'number': number, 'type': dice_type_val, 'bonus': bonus})
                elif dice_type == 'damage':
                    self.damage_dice = str({'number': number, 'type': dice_type_val, 'bonus': bonus})
            else:
                self.logger.warning(f"Invalid dice notation: {dice_str}")
        except Exception as e:
            self.logger.warning(f"Error parsing dice '{dice_str}': {e}")

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
            if line.endswith('~'):
                description_lines.append(line[:-1].rstrip())
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
            'race': self.race,
            'actFlags': self.act_flags,
            'affectFlags': self.affect_flags,
            'alignment': self.alignment,
            'group': self.group,
            'level': self.level,
            'hitroll': self.hitroll,
            'hitDice': self.hit_dice,
            'manaDice': self.mana_dice,
            'damageDice': self.damage_dice,
            'damType': self.dam_type,
            'armorClass': self.armor_class,
            'combatFlags': self.combat_flags,
            'startPos': self.start_pos,
            'defaultPos': self.default_pos,
            'sex': self.sex,
            'gold': self.gold,
            'form': self.form,
            'parts': self.parts,
            'size': self.size,
            'material': self.material,
            'flags': self.flags,
            'id': self.id
        }
