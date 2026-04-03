import re

from MigrateRiversOfMud.http.SOMClient import generate_mongo_id
from MigrateRiversOfMud.logging import setup_logger


class Shop:
    def __init__(self, area_id, data, filename='Shop.log'):
        """
        Initializes the Shop object with the area data.
        """
        self.area_id = area_id
        self.id = generate_mongo_id()
        self.keeper = None  # Renamed from vnum to match C code
        self.buy_type = []  # Renamed from trade_items to match C code (MAX_TRADE = 5)
        self.profit_buy = None
        self.profit_sell = None
        self.open_hour = None
        self.close_hour = None
        self.comment = None  # Renamed from owner_name to be more generic
        self.logger = setup_logger("Shop", filename)

        try:
            self._parse_shop_data(data)
            # self.logger.info("SHOP-PAYLOAD="+str(self.to_dict()))
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error while parsing shop data: {e}")

    def _parse_shop_data(self, lines):
        """
        Parses the shop data from the given lines representing a single shop.
        ROM 2.4 format: <keeper> <buy_type[0..4]> <profit_buy> <profit_sell> <open_hour> <close_hour> [* comment]

        Matches the C code in db.c load_shops() function:
        - keeper = fread_number (mob vnum)
        - buy_type[0..4] = fread_number (5 item types)
        - profit_buy = fread_number
        - profit_sell = fread_number
        - open_hour = fread_number
        - close_hour = fread_number
        - fread_to_eol (consumes rest of line including comment)
        """
        if isinstance(lines, list) and len(lines) > 0:
            line = lines[0].strip()
        elif isinstance(lines, str):
            line = lines.strip()
        else:
            raise TypeError("Expected a string or list with shop data line")

        # Check for end marker (keeper = 0)
        if line == "0":
            raise ValueError("Invalid shop line: End marker")

        # Extract comment (everything after '*')
        comment_idx = line.find('*')
        if comment_idx > 0:
            self.comment = line[comment_idx+1:].strip()
            line = line[:comment_idx].strip()
        else:
            self.comment = ""

        tokens = re.split(r'\s+', line)

        # Need at least 10 tokens: keeper + 5 buy_types + profit_buy + profit_sell + open_hour + close_hour
        if len(tokens) < 10:
            raise ValueError(f"Invalid shop data line: expected at least 10 tokens, got {len(tokens)}")

        self.keeper = int(tokens[0])  # keeper vnum

        # buy_type[0] through buy_type[4] - store all 5 values (including 0s per C code)
        self.buy_type = [int(tokens[i]) for i in range(1, 6)]

        self.profit_buy = int(tokens[6])
        self.profit_sell = int(tokens[7])
        self.open_hour = int(tokens[8])
        self.close_hour = int(tokens[9])

        self.logger.debug(f"Parsed shop: keeper={self.keeper}, buy_type={self.buy_type}, profit_buy={self.profit_buy}, profit_sell={self.profit_sell}, open={self.open_hour}, close={self.close_hour}")

    def to_dict(self):
        """
        Converts the Shop object to a dictionary for payload purposes.
        """
        return {
            'areaId': self.area_id,
            'keeper': self.keeper,
            'buyType0': self.buy_type[0] if len(self.buy_type) > 0 else 0,
            'buyType1': self.buy_type[1] if len(self.buy_type) > 1 else 0,
            'buyType2': self.buy_type[2] if len(self.buy_type) > 2 else 0,
            'buyType3': self.buy_type[3] if len(self.buy_type) > 3 else 0,
            'buyType4': self.buy_type[4] if len(self.buy_type) > 4 else 0,
            'profitBuy': self.profit_buy,
            'profitSell': self.profit_sell,
            'openHour': self.open_hour,
            'closeHour': self.close_hour,
            'comment': self.comment,
            'id': self.id
        }
