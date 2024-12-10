import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.patches import Rectangle
from matplotlib.path import Path


class RomMapEntity:
    def __init__(self, area, room_index, x, y):
        self.area = area
        self.x = x
        self.y = y
        self.connections = self.area.rooms[room_index].get_connections()
        self.size = 10  # Size of the central rectangle
        self.neighbors = {
            "north": (x, y + 20),
            "south": (x, y - 20),
            "east": (x + 20, y),
            "west": (x - 20, y),
            "up": (0, 0),  # Placeholder coordinates
            "down": (0, 0),  # Placeholder coordinates,
        }

        self._calculate_vertical_neighbors()

    def _calculate_vertical_neighbors(self):
        """Adjust the up/down neighbor coordinates based on likely east/west connections."""
        forecasted_placement = self._forecast_vertical_placement()
        if self.connections.get("up") is not None:
            if forecasted_placement == "east":
                self.neighbors["up"] = (self.x + self.size, self.y + 20)
            else:
                self.neighbors["up"] = (self.x - self.size, self.y + 20)
        if self.connections.get("down") is not None:
            if forecasted_placement == "east":
                self.neighbors["down"] = (self.x + self.size, self.y - 20)
            else:
                self.neighbors["down"] = (self.x - self.size, self.y - 20)

    def _forecast_vertical_placement(self):
        """
        Forecast the placement for up/down neighbors based on occupancy.
        Returns:
            'east' if eastward placement is more open, otherwise 'west'.
        """
        east_connections = self.connections.get("east")
        west_connections = self.connections.get("west")

        if not east_connections and west_connections:
            return "west"
        return "east"

    def save_as_png(self, filename):
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(self.x - 50, self.x + 50)
        ax.set_ylim(self.y - 50, self.y + 50)
        ax.set_aspect("equal")
        ax.axis("off")

        neighbor_rectangles = {}
        for direction, coords in self.neighbors.items():
            if coords and self.connections.get(direction) is not None:
                nx, ny = coords
                neighbor_rectangles[direction] = self._draw_neighbor(ax, nx, ny, direction)

        room_rect = self._draw_room(ax, self.x, self.y, "Room")
        for direction, coords in self.neighbors.items():
            if coords and self.connections.get(direction) is not None:
                neighbor_rect = neighbor_rectangles.get(direction)
                if direction in ["up", "down"]:
                    self._draw_curved_connection(ax, room_rect, neighbor_rect, direction)
                else:
                    self._draw_straight_connection(ax, room_rect, neighbor_rect, direction)

        plt.savefig(filename)
        plt.close(fig)

    @staticmethod
    def _draw_curved_connection(ax, source_rect: Rectangle, dest_rect: Rectangle, direction: str):
        """
        Draws a curved connection between two rectangles.

        Args:
            ax: The Matplotlib axis to draw on.
            source_rect: The source rectangle.
            dest_rect: The destination rectangle.
            direction: The direction of the connection ("up" or "down").
        """
        source_bbox = source_rect.get_bbox()
        dest_bbox = dest_rect.get_bbox()

        if direction == "up":
            start_x, start_y = (source_bbox.x0 + source_bbox.x1) / 2, source_bbox.y1
            end_x, end_y = dest_bbox.x1, dest_bbox.y0  # Bottom-right corner
            control_x = start_x + 15  # Pronounce curve eastward
            control_y = (start_y + end_y) / 2  # Middle of curve, vertically
        elif direction == "down":
            start_x, start_y = (source_bbox.x0 + source_bbox.x1) / 2, source_bbox.y0
            end_x, end_y = (dest_bbox.x0 + dest_bbox.x1) / 2, dest_bbox.y1
            control_x = end_x  # Curve towards the destination
            control_y = start_y - 15
        else:
            return

        vertices = np.array([(start_x, start_y), (control_x, control_y), (end_x, end_y)], dtype=float)
        codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
        path = Path(vertices, codes)
        patch = PathPatch(path, edgecolor="blue", lw=1.5, linestyle="--", fill=False)
        ax.add_patch(patch)

    @staticmethod
    def _draw_straight_connection(ax, source_rect: Rectangle, dest_rect: Rectangle, direction: str):
        """
        Draws a straight connection between two rectangles.

        Args:
            ax: The Matplotlib axis to draw on.
            source_rect: The source rectangle.
            dest_rect: The destination rectangle.
            direction: The direction of the connection.
        """
        source_bbox = source_rect.get_bbox()
        dest_bbox = dest_rect.get_bbox()

        if direction == "north":
            start_x, start_y = (source_bbox.x0 + source_bbox.x1) / 2, source_bbox.y1
            end_x, end_y = (dest_bbox.x0 + dest_bbox.x1) / 2, dest_bbox.y0
        elif direction == "south":
            start_x, start_y = (source_bbox.x0 + source_bbox.x1) / 2, source_bbox.y0
            end_x, end_y = (dest_bbox.x0 + dest_bbox.x1) / 2, dest_bbox.y1
        elif direction == "east":
            start_x, start_y = source_bbox.x1, (source_bbox.y0 + source_bbox.y1) / 2
            end_x, end_y = dest_bbox.x0, (dest_bbox.y0 + dest_bbox.y1) / 2
        elif direction == "west":
            start_x, start_y = source_bbox.x0, (source_bbox.y0 + source_bbox.y1) / 2
            end_x, end_y = dest_bbox.x1, (dest_bbox.y0 + dest_bbox.y1) / 2
        else:
            return

        ax.plot([start_x, end_x], [start_y, end_y], color="blue", linewidth=1.5, linestyle="-")

    @staticmethod
    def _draw_room(ax, x, y, label):
        size = 10
        rect = Rectangle((x - size / 2, y - size / 2), size, size, edgecolor="black", facecolor="lightgray")
        ax.add_patch(rect)
        ax.text(x, y, label, ha="center", va="center", fontsize=8)
        return rect

    @staticmethod
    def _draw_neighbor(ax, x, y, direction):
        size = 10  # Updated to match the size of the central rectangle
        rect = Rectangle((x - size / 2, y - size / 2), size, size, edgecolor="blue", facecolor="white")
        ax.add_patch(rect)
        ax.text(x, y, direction, ha="center", va="center", fontsize=6)
        return rect

    @staticmethod
    def generate_entities(area):
        """
        Generate unique RomMapEntity instances for all rooms in the area.

        Args:
            area: The area containing the rooms.

        Returns:
            A list of RomMapEntity instances.
        """
        entities = []
        skip_list = set()
        x, y = 0, 0  # Start coordinates

        for i, room in enumerate(area.rooms):
            if i in skip_list:
                continue

            entity = RomMapEntity(area, i, x, y)
            entity.save_as_png(area.name + "_room-index-" + str(i))
            entities.append(entity)

            # Add all connected room indices to the skip list
            for direction, connected_room_id in entity.connections.items():
                if connected_room_id is not None:
                    for index, r in enumerate(area.rooms):
                        if r.id == connected_room_id:
                            print(f'Adding index {str(index)} to skip list.')
                            skip_list.add(index)
                            break

            # Update coordinates based on the last valid connection
            for direction, (nx, ny) in entity.neighbors.items():
                if entity.connections.get(direction) is not None:
                    x, y = nx, ny
                    break

        return entities

