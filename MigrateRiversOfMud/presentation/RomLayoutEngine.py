from matplotlib import pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.gridspec import GridSpec
from MigrateRiversOfMud.presentation import (
    GameMapEntity,
    RomMapEntity,
    RoomDataProcessor
)


class RomLayoutEngine:
    def __init__(self, entities, subplots_per_row=3, subplots_per_col=3,
                 plot_width=100, plot_height=100):
        super().__init__()
        self._processor = RoomDataProcessor(entities)
        """
        Initialize the layout engine.

        Args:
            subplots_per_row: Number of subplots per row.
            subplots_per_col: Number of subplots per column.
            plot_width: Total width of the plot area.
            plot_height: Total height of the plot area.
        """
        self.subplots_per_row = subplots_per_row
        self.subplots_per_col = subplots_per_col
        self.plot_width = plot_width
        self.plot_height = plot_height
        self.fig = None  # plt.figure(figsize=(self.plot_width, self.plot_height))
        self.entities = entities

    def render_plot(self):
        """
        Render the plot using patches instead of treating subplots as Axes.
        """
        fig, ax = plt.subplots(3, 3, figsize=(10, 10))
        patches = []
        entity_list = self.entities
        index = 0
        axes = None
        while index <= 2 and len(entity_list) > 0:
            entity = entity_list.pop()
            axes = ax[index][index]
            if entity is not None:
                axes.text(
                    entity.get_x() + entity.get_width() / 2,
                    entity.get_y() + entity.get_height() / 2,
                    f"Room {entity.room_index}",
                    ha="center",
                    va="center",
                    fontsize=8,
                )
                patches.append(entity)
            index = index + 1

        collection = PatchCollection(patches, match_original=True)
        axes.add_collection(collection)

        plt.show()

    def arrange_entities(self):
        """
        Arrange the entities within the grid.

        Assigns entities to subplots in a row-major order. If the number of entities
        exceeds the grid capacity, only the first {grid_positions} entities are arranged.
        """
        rows, cols = self.subplots_per_col, self.subplots_per_row
        grid_positions = [(row, col) for row in range(rows) for col in range(cols)]

        if len(self.entities) > len(grid_positions):
            print(f"Number of entities {len(self.entities)} exceeds grid capacity of {len(grid_positions)}.")
            print(f"Only the first {len(grid_positions)} entities will be arranged.")

        for entity, (row, col) in zip(self.entities[:len(grid_positions)], grid_positions):
            subplot_center_x = col * (self.plot_width / cols) + (self.plot_width / cols) / 2
            subplot_center_y = -row * (self.plot_height / rows) - (self.plot_height / rows) / 2
            entity.set_position(subplot_center_x, subplot_center_y)

    def render_multiple_plots(self, entities_per_plot=9, filename_prefix="plot"):
        """
        Divide the entities into multiple plots and render them.

        Args:
            entities_per_plot: Number of entities per plot.
            filename_prefix: Prefix for the filenames if saving.
        """
        chunks = [self.entities[i:i + entities_per_plot] for i in range(0, len(self.entities), entities_per_plot)]

        for index, chunk in enumerate(chunks):
            fig = plt.figure(figsize=(self.plot_width, self.plot_height))
            grid = GridSpec(self.subplots_per_col, self.subplots_per_row, figure=fig)
            filename = f"{filename_prefix}_{index}.png"

            for idx, entity in enumerate(chunk):
                row, col = divmod(idx, self.subplots_per_row)
                ax = fig.add_subplot(grid[row, col])
                ax.set_xlim(0, self.plot_width / self.subplots_per_row)
                ax.set_ylim(-(self.plot_height / self.subplots_per_col), 0)
                ax.set_aspect("equal")
                ax.axis("off")
                entity.save_as_png(filename)

            plt.savefig(filename)
            plt.show()
