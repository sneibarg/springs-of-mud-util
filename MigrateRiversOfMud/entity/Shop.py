import re

from MigrateRiversOfMud.http import generate_mongo_id
from MigrateRiversOfMud.logging import setup_logger


class Shop:
    def __init__(self, area_id, data, log_dir='logs'):
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
        self.logger = setup_logger("Shop", log_dir)

        try:
            self._parse_shop_data(data)
            self.logger.info("SHOP-PAYLOAD="+str(self.to_dict()))
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error while parsing shop data: {e}")

    def _parse_shop_data(self, lines):
        """
        Parses the shop data from the given lines representing a single shop.
        """
        if isinstance(lines, list) and len(lines) > 0:
            line = lines[0].strip()
        elif isinstance(lines, str):
            line = lines.strip()
        else:
            raise TypeError("Expected a string or list with shop data line")

        if line == "0":
            return
        # Example line format: "3000  2  3  4 10  0  105  15  0 23  * the wizard"
        self.logger.info("LINE="+line)
        tokens = re.split(r'\s+', line)
        if len(tokens) >= 11:
            self.vnum = int(tokens[0])
            self.trade_items = [int(t) for t in tokens[1:6] if t != '0']
            self.profit_buy = int(tokens[6])
            self.profit_sell = int(tokens[7])
            self.open_hour = int(tokens[8])
            self.close_hour = int(tokens[9])
            self.owner_name = ' '.join(tokens[11:]).replace('*', '').strip()
        else:
            raise ValueError("Invalid shop data line")

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
