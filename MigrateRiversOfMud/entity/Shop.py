import re

from MigrateRiversOfMud.http import generate_mongo_id
from MigrateRiversOfMud.logging import setup_logger


class Shop:
    def __init__(self, area_id, data, filename='Shop.log'):
        """
        Initializes the Shop object with the area data.
        """
        self.area_id = area_id
        self.id = generate_mongo_id()
        self.vnum = None
        self.trade_items = []
        self.profit_buy = None
        self.profit_sell = None
        self.open_hour = None
        self.close_hour = None
        self.owner_name = None
        self.logger = setup_logger("Shop", filename)

        try:
            self._parse_shop_data(data)
            self.logger.info("SHOP-PAYLOAD="+str(self.to_dict()))
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error while parsing shop data: {e}")

    def _parse_shop_data(self, lines):
        """
        Parses the shop data from the given lines representing a single shop.
        ROM 2.4 format: <keeper> <buy_type[0..4]> <profit_buy> <profit_sell> <open_hour> <close_hour> [comment]
        """
        if isinstance(lines, list) and len(lines) > 0:
            line = lines[0].strip()
        elif isinstance(lines, str):
            line = lines.strip()
        else:
            raise TypeError("Expected a string or list with shop data line")

        if line == "0":
            return

        # Split line, but preserve comment if it starts with '*'
        comment_idx = line.find('*')
        if comment_idx > 0:
            comment = line[comment_idx:].strip()
            line = line[:comment_idx].strip()
            self.owner_name = comment.lstrip('*').strip()
        else:
            self.owner_name = ""

        self.logger.info("LINE=" + line)
        tokens = re.split(r'\s+', line)

        # Need at least 9 tokens: keeper + 5 buy_types + profit_buy + profit_sell + open_hour + close_hour
        if len(tokens) >= 9:
            self.vnum = int(tokens[0])  # keeper vnum
            # buy_type[0] through buy_type[4] - filter out 0 values
            self.trade_items = [int(tokens[i]) for i in range(1, 6) if int(tokens[i]) != 0]
            self.profit_buy = int(tokens[6])
            self.profit_sell = int(tokens[7])
            self.open_hour = int(tokens[8])
            self.close_hour = int(tokens[9]) if len(tokens) > 9 else 0
        else:
            raise ValueError(f"Invalid shop data line: expected at least 9 tokens, got {len(tokens)}")

    def to_dict(self):
        """
        Converts the Shop object to a dictionary for payload purposes.
        """
        return {
            'areaId': self.area_id,
            'vnum': self.vnum,
            'tradeItems': self.trade_items,
            'profitBuy': self.profit_buy,
            'profitSell': self.profit_sell,
            'openHour': self.open_hour,
            'closeHour': self.close_hour,
            'ownerName': self.owner_name,
            'id': self.id
        }
