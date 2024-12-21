from typing import Dict, Tuple, List

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path


class RomMapEntity:
    def __init__(self, area, room_index: int, x: float, y: float, show_bounding_box: bool = False):
        """
        Represents a single room entity in an area.

        Args:
            area: The area containing the rooms.
            room_index: Index of the current room in the area.
            x, y: Coordinates for the room.
            show_bounding_box: Whether or not to make bounding box visible.
        """
        self.area = area
        self.room_index = 0  # default first room is element 0
        self.x = x
        self.y = y
        self.size = 10
        self.connections = self.area.rooms[room_index].get_connections()
        self.neighbors: Dict[str, Tuple[float, float]] = {
            "north": (x, y + 20),
            "south": (x, y - 20),
            "east": (x + 20, y),
            "west": (x - 20, y),
            "up": (0, 0),
            "down": (0, 0),
        }

        self._calculate_vertical_neighbors()
        self.bounding_box = self._calculate_bounding_box(show_bounding_box)
        self.preprocess_plot(area, x, y)

    def _calculate_vertical_neighbors(self) -> None:
        """
        Adjusts the up/down neighbor coordinates based on likely east/west connections.
        """
        vertical_placement = self._determine_vertical_placement()
        if self.connections.get("up") is not None:
            if vertical_placement == "east":
                self.neighbors["up"] = (self.x + self.size, self.y + 20)
            else:
                self.neighbors["up"] = (self.x - self.size, self.y + 20)
        if self.connections.get("down") is not None:
            if vertical_placement == "east":
                self.neighbors["down"] = (self.x + self.size, self.y - 20)
            else:
                self.neighbors["down"] = (self.x - self.size, self.y - 20)

    def _determine_vertical_placement(self) -> str:
        """
        Chooses east or west for up/down placement, considering if both sides are open.
        """
        east_connections = self.connections.get("east")
        west_connections = self.connections.get("west")
        if east_connections and not west_connections:
            return "west"
        return "east"

    def _calculate_bounding_box(self, show: bool) -> Rectangle:
        """
        Creates a bounding box that can optionally be visible.

        Args:
            show: Whether the bounding box should have an outline or not.
        """
        all_x = [self.x] + [coords[0] for coords in self.neighbors.values() if coords]
        all_y = [self.y] + [coords[1] for coords in self.neighbors.values() if coords]
        x_min, x_max = min(all_x) - self.size / 2, max(all_x) + self.size / 2
        y_min, y_max = min(all_y) - self.size / 2, max(all_y) + self.size / 2

        edge_color = "black" if show else "none"
        face_color = "none"

        return Rectangle(
            (x_min, y_min),
            width=x_max - x_min,
            height=y_max - y_min,
            edgecolor=edge_color,
            facecolor=face_color
        )

    def save_as_png(self, filename: str) -> None:
        """
        Creates and saves a PNG image of this room and its connections.
        """
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(self.x - 50, self.x + 50)
        ax.set_ylim(self.y - 50, self.y + 50)
        ax.set_aspect("equal")
        ax.axis("off")

        neighbor_rects = {}
        for direction, coords in self.neighbors.items():
            if coords and self.connections.get(direction) is not None:
                nx, ny = coords
                neighbor_rects[direction] = self._draw_room(ax, nx, ny, direction)

        room_rect = self._draw_room(ax, self.x, self.y, "Room")
        ax.add_patch(self.bounding_box)

        for direction, coords in self.neighbors.items():
            if coords and self.connections.get(direction) is not None:
                dest_rect = neighbor_rects.get(direction)
                self._draw_connection(ax, room_rect, dest_rect, direction)

        plt.savefig(filename)
        plt.close(fig)

    def _draw_connection(self, ax: plt.Axes, source_rect: Rectangle, dest_rect: Rectangle, direction: str) -> None:
        """
        Draws either a curved or straight connection, depending on direction.
        """
        if direction in ["up", "down"]:
            self._draw_curved_connection(ax, source_rect, dest_rect, direction)
        else:
            self._draw_straight_connection(ax, source_rect, dest_rect, direction)

    @staticmethod
    def _draw_curved_connection(ax: plt.Axes, source_rect: Rectangle, dest_rect: Rectangle, direction: str) -> None:
        """
        Draws a curved connection (for up/down).
        """
        s_bbox = source_rect.get_bbox()
        d_bbox = dest_rect.get_bbox()

        if direction == "up":
            start = ((s_bbox.x0 + s_bbox.x1) / 2, s_bbox.y1)
            end = (d_bbox.x1, d_bbox.y0)  # bottom-right corner of destination
            control = (start[0] + 15, (start[1] + end[1]) / 2)
        else:  # down
            start = ((s_bbox.x0 + s_bbox.x1) / 2, s_bbox.y0)
            end = ((d_bbox.x0 + d_bbox.x1) / 2, d_bbox.y1)
            control = (end[0], start[1] - 15)

        RomMapEntity._draw_bezier_curve(ax, start, control, end, color="blue", lw=1.5, linestyle="--")

    @staticmethod
    def _draw_straight_connection(ax: plt.Axes, source_rect: Rectangle, dest_rect: Rectangle, direction: str) -> None:
        """
        Draws a straight connection (for north/south/east/west).
        """
        s_bbox = source_rect.get_bbox()
        d_bbox = dest_rect.get_bbox()
        direction_offsets = {
            "north": (
                (s_bbox.x0 + s_bbox.x1) / 2, s_bbox.y1,
                (d_bbox.x0 + d_bbox.x1) / 2, d_bbox.y0
            ),
            "south": (
                (s_bbox.x0 + s_bbox.x1) / 2, s_bbox.y0,
                (d_bbox.x0 + d_bbox.x1) / 2, d_bbox.y1
            ),
            "east": (
                s_bbox.x1, (s_bbox.y0 + s_bbox.y1) / 2,
                d_bbox.x0, (d_bbox.y0 + d_bbox.y1) / 2
            ),
            "west": (
                s_bbox.x0, (s_bbox.y0 + s_bbox.y1) / 2,
                d_bbox.x1, (d_bbox.y0 + d_bbox.y1) / 2
            ),
        }

        start_x, start_y, end_x, end_y = direction_offsets[direction]
        ax.plot([start_x, end_x], [start_y, end_y], color="blue", linewidth=1.5)

    @staticmethod
    def _draw_bezier_curve(ax: plt.Axes, start: Tuple[float, float],
                           control: Tuple[float, float], end: Tuple[float, float],
                           color: str = "blue", lw: float = 1.5,
                           linestyle: str = "--", fill: bool = False) -> None:
        """
        Draws a simple quadratic Bézier curve.
        """
        vertices = np.array([start, control, end], dtype=float)
        codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
        path = Path(vertices, codes)
        patch = PathPatch(path, edgecolor=color, lw=lw, linestyle=linestyle, fill=fill)
        ax.add_patch(patch)

    @staticmethod
    def _draw_room(ax: plt.Axes, x: float, y: float, label: str) -> Rectangle:
        """
        Draws a room (a small square) with a label.
        """
        size = 10
        rect = Rectangle((x - size / 2, y - size / 2), size, size, edgecolor="black", facecolor="lightgray")
        ax.add_patch(rect)
        ax.text(x, y, label, ha="center", va="center", fontsize=8)
        return rect

    @staticmethod
    def generate_entities(area) -> List["RomMapEntity"]:
        """
        Generate unique RomMapEntity instances for all rooms in the area.
        Returns a list of RomMapEntity instances.
        """
        entities = []
        skip_list = set()
        x, y = 0, 0

        for i, room in enumerate(area.rooms):
            if i in skip_list:
                continue

            entity = RomMapEntity(area, i, x, y, show_bounding_box=False)
            # entity.save_as_png(area.name + f"_room-index-{i}")
            entities.append(entity)

            # Mark connected rooms to avoid duplicates, but be mindful of cycles
            for direction, connected_id in entity.connections.items():
                if connected_id is not None:
                    for idx, r in enumerate(area.rooms):
                        if r.id == connected_id:
                            skip_list.add(idx)
                            break

            # Move to next available coordinates for subsequent rooms
            # (This is a simple approach: picks the first neighbor direction that has a connection.)
            for direction, (nx, ny) in entity.neighbors.items():
                if entity.connections.get(direction) is not None:
                    x, y = nx, ny
                    break
        print(f"Returning {len(entities)} RomMapEntity instances.")
        return entities

    @staticmethod
    def preprocess_plot(area, plot_width: int, plot_height: int, entity_size: int = 20) -> Tuple[int, bool]:
        """
        Determines if the specified plot dimensions can fit all rooms.
        Returns (max_entities, can_fit_all).
        """
        total_plot_space = (plot_width // entity_size) * (plot_height // entity_size)
        total_rooms = len(area.rooms)
        can_fit_all = total_rooms <= total_plot_space
        if not can_fit_all:
            return total_plot_space, False
        return total_plot_space, True
