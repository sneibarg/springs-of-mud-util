import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, PathPatch
from matplotlib.path import Path
from MigrateRiversOfMud.presentation.GameMapEntity import GameMapEntity
from MigrateRiversOfMud.presentation.RoomDataProcessor import RoomDataProcessor


class RomMapEntity(GameMapEntity):
    def __init__(self, area, room_index):
        super().__init__()
        self.area = area
        self.room_index = room_index
        self.connections = self._get_room_connections()

        self._processor = RoomDataProcessor(area)
        self._processor.process_room_data()[room_index]

    def _calculate_vertical_neighbors(self):
        """Use processor for vertical neighbor calculation"""
        return self._processor._determine_vertical_neighbors()

    def _determine_vertical_placement(self) -> str:
        """
        Decide whether to place up/down neighbors to the 'east' or 'west'.
        """
        east_connections = self.connections.get("east")
        west_connections = self.connections.get("west")
        if east_connections is None and west_connections is not None:
            return "west"
        return "east"

    def draw_entity(self):
        x = self.get_width()
        y = self.get_height()
        self.ax.set_xlim(x - 50, x + 50)
        self.ax.set_ylim(y - 50, y + 50)
        self.ax.set_aspect("equal")
        self.ax.axis("off")

        room_rect = self.draw_room(x, y, f"Room {self.room_index}")
        neighbor_rectangles = {}
        for direction, coords in self.neighbors.items():
            if coords != (0, 0) and self.connections.get(direction) is not None:
                nx, ny = coords
                neighbor_rectangles[direction] = self.draw_room(nx, ny, direction)

        for direction, coords in self.neighbors.items():
            if coords != (0, 0) and self.connections.get(direction) is not None:
                dest_rect = neighbor_rectangles[direction]
                if direction in ["up", "down"]:
                    self.draw_curved_connection(self.ax, room_rect, dest_rect, direction)
                else:
                    self.draw_straight_connection(self.ax, room_rect, dest_rect, direction)
        return

    def save_as_png(self, filename: str):
        """
        Render just this entity + neighbors to a PNG image (debug or single-room view).
        """
        if isinstance(filename, str):
            plt.savefig(filename)
        else:
            raise TypeError("Filename must be a string.")

        plt.close(self.fig)

    def draw_room(self, center_x: float, center_y: float, label: str, size=10) -> Rectangle:
        """
        Draws a square 'room' at (center_x, center_y) with side= size.
        """
        half = size / 2
        rect = Rectangle(
            (center_x - half, center_y - half),
            size,
            size,
            edgecolor="black",
            facecolor="lightgray"
        )
        self.ax.add_patch(rect)
        self.ax.text(center_x, center_y, label, ha="center", va="center", fontsize=6)
        return rect

    @staticmethod
    def draw_curved_connection(ax, source_rect: Rectangle, dest_rect: Rectangle, direction: str):
        """
        Draw a curved line (PathPatch) for up/down connections.
        """
        src_bbox = source_rect.get_bbox()
        dst_bbox = dest_rect.get_bbox()

        if direction == "up":
            start_x, start_y = (src_bbox.x0 + src_bbox.x1) / 2, src_bbox.y1
            end_x, end_y = dst_bbox.x1, dst_bbox.y0
            control_x = start_x + 15
            control_y = (start_y + end_y) / 2
        elif direction == "down":
            start_x, start_y = (src_bbox.x0 + src_bbox.x1) / 2, src_bbox.y0
            end_x, end_y = (dst_bbox.x0 + dst_bbox.x1) / 2, dst_bbox.y1
            control_x = end_x
            control_y = start_y - 15
        else:
            return

        vertices = np.array([(start_x, start_y), (control_x, control_y), (end_x, end_y)], dtype=float)
        codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
        path = Path(vertices, codes)
        patch = PathPatch(path, edgecolor="blue", lw=1.5, linestyle="--", fill=False)
        ax.add_patch(patch)

    @staticmethod
    def draw_straight_connection(ax, source_rect: Rectangle, dest_rect: Rectangle, direction: str):
        """
        Draw a simple line for N/S/E/W directions.
        """
        offsets = {
            "north": lambda s, d: ((s.x0 + s.x1) / 2, s.y1, (d.x0 + d.x1) / 2, d.y0),
            "south": lambda s, d: ((s.x0 + s.x1) / 2, s.y0, (d.x0 + d.x1) / 2, d.y1),
            "east": lambda s, d: (s.x1, (s.y0 + s.y1) / 2, d.x0, (d.y0 + d.y1) / 2),
            "west": lambda s, d: (s.x0, (s.y0 + s.y1) / 2, d.x1, (d.y0 + d.y1) / 2)
        }
        src_bbox = source_rect.get_bbox()
        dst_bbox = dest_rect.get_bbox()

        if direction in offsets:
            sx, sy, ex, ey = offsets[direction](src_bbox, dst_bbox)
            ax.plot([sx, ex], [sy, ey], color="blue", linewidth=1.5, linestyle="-")

    @staticmethod
    def generate_entities(area):
        """
        Convert each of area.rooms into a RomMapEntity and return them.
        No plotting here; just create the entities.
        """
        entities = []
        x, y = 0, 0
        skip_list = set()

        for i, room in enumerate(area.rooms):
            if i in skip_list:
                continue

            entity = RomMapEntity(area, i)
            entity.set_position(x, y)
            entities.append(entity)

            # Mark connected rooms as visited if found by ID.
            for direction, connected_room_id in entity.connections.items():
                if connected_room_id is not None:
                    connected_idx = next(
                        (idx for idx, r in enumerate(area.rooms) if r.id == connected_room_id),
                        None
                    )
                    if connected_idx is not None:
                        skip_list.add(connected_idx)

            # Move the 'cursor' to the first neighbor's coords if available
            for direction, coords in entity.neighbors.items():
                if coords != (0, 0) and entity.connections.get(direction) is not None:
                    x, y = coords
                    break

        return entities

    @staticmethod
    def _get_room_connections():
        """Get connections for the current room"""
        return {
            'north': ...,
            'south': ...,
            'east': ...,
            'west': ...,
            'up': ...,
            'down': ...
        }

