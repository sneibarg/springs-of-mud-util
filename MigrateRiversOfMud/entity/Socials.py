import json

from MigrateRiversOfMud.http import generate_mongo_id, post, api_endpoints
from MigrateRiversOfMud.logging import setup_logger


class Social:
    def __init__(self, name, lines):
        self.id = generate_mongo_id()
        self.name = name
        self.char_no_arg = self._normalize(lines[0] if len(lines) > 0 else None)
        self.others_no_arg = self._normalize(lines[1] if len(lines) > 1 else None)
        self.char_found = self._normalize(lines[2] if len(lines) > 2 else None)
        self.others_found = self._normalize(lines[3] if len(lines) > 3 else None)
        self.vict_found = self._normalize(lines[4] if len(lines) > 4 else None)
        self.char_not_found = self._normalize(lines[5] if len(lines) > 5 else None)
        self.char_auto = self._normalize(lines[6] if len(lines) > 6 else None)
        self.others_auto = self._normalize(lines[7] if len(lines) > 7 else None)

    @staticmethod
    def _normalize(value):
        if value is None:
            return None
        cleaned = value.strip()
        return None if cleaned == "$" else cleaned

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "charNoArg": self.char_no_arg,
            "othersNoArg": self.others_no_arg,
            "charFound": self.char_found,
            "othersFound": self.others_found,
            "victFound": self.vict_found,
            "charNotFound": self.char_not_found,
            "charAuto": self.char_auto,
            "othersAuto": self.others_auto
        }


class Socials:
    def __init__(self, socials_file, insert=True, filename="Socials.log"):
        self.socials_file = socials_file
        self.insert = insert
        self.socials = []
        self.logger = setup_logger("Socials", filename)
        self._load_socials_file()
        self.insert_socials()

    def _load_socials_file(self):
        with open(self.socials_file, "r", encoding="utf-8", errors="replace") as f:
            lines = [line.rstrip("\r\n") for line in f.readlines()]

        start_index = 0
        for i, line in enumerate(lines):
            if line.strip().upper() == "#SOCIALS":
                start_index = i + 1
                break

        index = start_index
        while index < len(lines):
            current = lines[index].strip()

            if not current:
                index += 1
                continue

            if current in ("#0", "#$"):
                break

            if current == "#" or current.startswith("*"):
                index += 1
                continue

            # Social header format in ROM files can be "name" or "name 0 0".
            name = current.split()[0]
            index += 1
            message_lines = []

            while index < len(lines):
                value = lines[index].strip()

                if value in ("#0", "#$"):
                    break

                if value == "#":
                    index += 1
                    break

                if not value:
                    index += 1
                    if len(message_lines) >= 8:
                        break
                    continue

                message_lines.append(value)
                index += 1

                if len(message_lines) >= 8:
                    break

            self.socials.append(Social(name=name, lines=message_lines))

            if index < len(lines) and lines[index].strip() in ("#0", "#$"):
                break

        self.logger.info(f"Parsed {len(self.socials)} socials from {self.socials_file}")

    def insert_socials(self):
        for social in self.socials:
            payload = social.to_dict()
            if not self.insert:
                self.logger.info(f"[DRY RUN] Social payload: {json.dumps(payload, indent=2)}")
                continue
            response = post(payload, api_endpoints["social"] + "socials")
            if not response:
                self.logger.error("Failed posting to Social API endpoint: {response}")
