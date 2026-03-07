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
        self.room = area.rooms[room_index]
        self.connections = self.room.get_connections()

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

        # Draw the central room with its name
        room_rect = self.draw_room(x, y, self.room.name)
        neighbor_rectangles = {}

        # Draw neighbor rooms only if they have connections
        for direction, coords in self.neighbors.items():
            if coords != (0, 0) and self.connections.get(direction) is not None:
                nx, ny = coords
                # Get the connected room's name
                connected_room_id = self.connections[direction]
                connected_room = next((r for r in self.area.rooms if r.id == connected_room_id), None)
                label = connected_room.name if connected_room else direction
                neighbor_rectangles[direction] = self.draw_room(nx, ny, label)

        # Draw connections only where they exist
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
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        else:
            raise TypeError("Filename must be a string.")

        self.cleanup()

    def cleanup(self):
        """Clean up matplotlib resources to free memory"""
        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
            self._ax = None

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
        # Wrap text if too long
        if len(label) > 15:
            label = label[:13] + "..."
        self.ax.text(center_x, center_y, label, ha="center", va="center", fontsize=5, wrap=True)
        return rect

    @staticmethod
    def draw_curved_connection(ax, source_rect: Rectangle, dest_rect: Rectangle, direction: str):
        """
        Draw a curved line (PathPatch) for up/down connections to indicate vertical movement.
        Uses cubic Bezier curves for smooth arcs.
        """
        src_bbox = source_rect.get_bbox()
        dst_bbox = dest_rect.get_bbox()

        if direction == "up":
            # Start from top of source room, curve to destination
            start_x, start_y = (src_bbox.x0 + src_bbox.x1) / 2, src_bbox.y1
            end_x, end_y = (dst_bbox.x0 + dst_bbox.x1) / 2, (dst_bbox.y0 + dst_bbox.y1) / 2
            # Two control points for smooth cubic Bezier curve
            control1_x = start_x + (end_x - start_x) * 0.3
            control1_y = start_y + (end_y - start_y) * 0.7
            control2_x = start_x + (end_x - start_x) * 0.7
            control2_y = start_y + (end_y - start_y) * 0.9
        elif direction == "down":
            # Start from bottom of source room, curve to destination
            start_x, start_y = (src_bbox.x0 + src_bbox.x1) / 2, src_bbox.y0
            end_x, end_y = (dst_bbox.x0 + dst_bbox.x1) / 2, (dst_bbox.y0 + dst_bbox.y1) / 2
            # Two control points for smooth cubic Bezier curve
            control1_x = start_x + (end_x - start_x) * 0.3
            control1_y = start_y + (end_y - start_y) * 0.7
            control2_x = start_x + (end_x - start_x) * 0.7
            control2_y = start_y + (end_y - start_y) * 0.9
        else:
            return

        # Create cubic Bezier curve with 4 points
        vertices = np.array([
            (start_x, start_y),
            (control1_x, control1_y),
            (control2_x, control2_y),
            (end_x, end_y)
        ], dtype=float)
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
        path = Path(vertices, codes)
        patch = PathPatch(path, edgecolor="purple", lw=2, linestyle="--", fill=False)
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
        Creates one entity per room in the area.
        """
        entities = []

        # Create an entity for every room in the area
        for i, room in enumerate(area.rooms):
            entity = RomMapEntity(area, i)
            entities.append(entity)

        print(f"Generated {len(entities)} entities for {len(area.rooms)} rooms")
        return entities
