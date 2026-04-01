import json

from MigrateRiversOfMud.http import generate_mongo_id, post, api_endpoints
from MigrateRiversOfMud.logging import setup_logger


class Help:
    def __init__(self, level, keyword, text):
        self.id = generate_mongo_id()
        self.level = level
        self.keyword = keyword
        self.text = text

    def to_dict(self):
        return {
            "id": self.id,
            "level": self.level,
            "keyword": self.keyword,
            "text": self.text
        }


class Helps:
    def __init__(self, helps_file, insert=True, filename="Helps.log"):
        self.helps_file = helps_file
        self.insert = insert
        self.helps = []
        self.logger = setup_logger("Helps", filename)
        self._load_helps_file()
        self.insert_helps()

    def _load_helps_file(self):
        with open(self.helps_file, "r", encoding="utf-8", errors="replace") as f:
            lines = [line.rstrip("\r\n") for line in f.readlines()]

        start_index = 0
        for i, line in enumerate(lines):
            if line.strip().upper() == "#HELPS":
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

            level, keyword, index = self._parse_help_header(lines, index)
            if keyword.startswith("$"):
                break

            text, index = self._parse_tilde_string(lines, index)
            self.helps.append(Help(level=level, keyword=keyword, text=text))

        self.logger.info(f"Parsed {len(self.helps)} helps from {self.helps_file}")

    def _parse_help_header(self, lines, index):
        line = lines[index].lstrip()
        index += 1

        parts = line.split(None, 1)
        if len(parts) == 0:
            return 0, "", index

        level_token = parts[0]
        level = int(level_token) if level_token.lstrip("-").isdigit() else 0
        remainder = parts[1] if len(parts) > 1 else ""

        if remainder.endswith("~"):
            keyword = remainder[:-1].strip()
            return level, keyword, index

        keyword_lines = [remainder]
        while index < len(lines):
            chunk = lines[index]
            index += 1
            if chunk.endswith("~"):
                keyword_lines.append(chunk[:-1])
                break
            keyword_lines.append(chunk)

        keyword = "\n".join(keyword_lines).strip()
        return level, keyword, index

    def _parse_tilde_string(self, lines, index):
        text_lines = []
        while index < len(lines):
            line = lines[index]
            index += 1
            if line.endswith("~"):
                text_lines.append(line[:-1])
                break
            text_lines.append(line)
        return "\n".join(text_lines).strip(), index

    def insert_helps(self):
        for help_doc in self.helps:
            payload = help_doc.to_dict()
            if not self.insert:
                self.logger.info(f"[DRY RUN] Help payload: {json.dumps(payload, indent=2)}")
                continue
            response = post(payload, api_endpoints["help"] + "helps")
            if not response:
                self.logger.error("Failed posting to Help API endpoint: {response}")
