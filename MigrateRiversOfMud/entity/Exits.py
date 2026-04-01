from dataclasses import dataclass


@dataclass
class Exits:
    north: str
    south: str
    east: str
    west: str
    up: str
    down: str

    @classmethod
    def from_json(cls, data):
        return cls(**data)
