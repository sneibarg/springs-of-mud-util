from matplotlib.patches import Rectangle


class GameMapEntity(Rectangle):
    def __init__(self, width=10, height=None, **kwargs):
        """
        A class representing a generic map entity.

        Args:
            x: The x-coordinate of the entity.
            y: The y-coordinate of the entity.
            width: The width of the rectangle entity.
            height: The height of the rectangle entity (defaults to width).
            **kwargs: Additional keyword arguments for the Rectangle superclass.
        """
        height = height if height is not None else width
        super().__init__((width, height), width, height, **kwargs)
        self.anchor = "center"  # Default anchor point
        self.neighbors = self._init_neighbors()
        self.raster_depth = 0
        self.rasterizing = False
        self._fig = None
        self._ax = None

    @property
    def fig(self):
        """Lazy initialization of figure"""
        if self._fig is None:
            import matplotlib.pyplot as plt
            self._fig, self._ax = plt.subplots(figsize=(8, 8))
        return self._fig

    @property
    def ax(self):
        """Lazy initialization of axes"""
        if self._ax is None:
            import matplotlib.pyplot as plt
            self._fig, self._ax = plt.subplots(figsize=(8, 8))
        return self._ax

    def draw(self, ax):
        """
        Add the entity to the given Axes and optionally render its label.

        Args:
            ax: The Matplotlib Axes object to draw the entity on.
        """
        ax.add_patch(self)
        ax.text(
            self.get_x() + self.get_width() / 2,
            self.get_y() + self.get_height() / 2,
            "Entity",
            ha="center",
            va="center",
            fontsize=8,
            color="black",
        )

    def set_anchor(self, anchor_point="center"):
        """
        Set the anchor point for the entity.

        Args:
            anchor_point: The anchor point for positioning (e.g., 'center', 'bottom_left').
        """
        self.anchor = anchor_point
        if anchor_point == "center":
            self.set_xy((self.get_x() - self.get_width() / 2, self.get_y() - self.get_height() / 2))
        elif anchor_point == "bottom_left":
            self.set_xy((self.get_x(), self.get_y()))
        elif anchor_point == "bottom_right":
            self.set_xy((self.get_x() - self.get_width(), self.get_y()))
        elif anchor_point == "top_left":
            self.set_xy((self.get_x(), self.get_y() - self.get_height()))
        elif anchor_point == "top_right":
            self.set_xy((self.get_x() - self.get_width(), self.get_y() - self.get_height()))

    def set_position(self, x, y):
        """
        Set the position of the entity.

        Args:
            x: The x-coordinate.
            y: The y-coordinate.
        """
        self.set_xy((x, y))

    def _init_neighbors(self) -> dict:
        """
        Initialize neighbor coordinates for each direction.

        Returns:
            A dictionary mapping directions to coordinates.
        """
        offset = 2 * self.get_width()  # Default offset for neighbors
        return {
            "north": (self.get_x() + self.get_width() / 2, self.get_y() + offset),
            "south": (self.get_x() + self.get_width() / 2, self.get_y() - offset),
            "east": (self.get_x() + offset, self.get_y() + self.get_height() / 2),
            "west": (self.get_x() - offset, self.get_y() + self.get_height() / 2),
            "up": (0, 0),
            "down": (0, 0),
        }

