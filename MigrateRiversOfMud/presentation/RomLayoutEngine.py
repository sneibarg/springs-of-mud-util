from matplotlib import pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.gridspec import GridSpec
from MigrateRiversOfMud.presentation import (
    GameMapEntity,
    RomMapEntity,
    RoomDataProcessor
)


class RomLayoutEngine:
    def __init__(self, entities, area_name=None, subplots_per_row=3, subplots_per_col=3,
                 plot_width=100, plot_height=100, compact_mode=False, vnum_to_area_map=None):
        super().__init__()
        self._processor = RoomDataProcessor(entities)
        """
        Initialize the layout engine.

        Args:
            entities: List of RomMapEntity objects to render.
            area_name: Name of the area for deck naming.
            subplots_per_row: Number of subplots per row.
            subplots_per_col: Number of subplots per column.
            plot_width: Total width of the plot area.
            plot_height: Total height of the plot area.
            compact_mode: If True, use tighter spacing to fit more content per sheet.
            vnum_to_area_map: Dictionary mapping VNUM to area name for cross-deck references.
        """
        self.area_name = area_name or "Unknown_Area"
        self.compact_mode = compact_mode
        self.vnum_to_area_map = vnum_to_area_map or {}
        self.subplots_per_row = subplots_per_row
        self.subplots_per_col = subplots_per_col
        self.plot_width = plot_width
        self.plot_height = plot_height
        self.fig = None  # plt.figure(figsize=(self.plot_width, self.plot_height))
        self.entities = entities

    def render_plot(self):
        """
        Render the plot using spatial layout based on room connections.
        Creates a single PDF deck with all sheets.
        """
        if not self.entities:
            print("No entities to render.")
            return

        # Calculate spatial positions for all rooms
        positioned_rooms = self._calculate_spatial_layout()

        # Group rooms into sheets based on spatial proximity
        sheets = self._create_spatial_sheets(positioned_rooms)

        # Create PDF deck with all sheets
        self._create_pdf_deck(sheets)

    def _calculate_spatial_layout(self):
        """
        Calculate spatial (x, y) positions for all rooms based on directional connections.
        Uses BFS to place rooms relative to each other.
        """
        if not self.entities:
            return {}

        positioned = {}
        visited = set()

        # Start with first entity at origin
        start_entity = self.entities[0]
        queue = [(start_entity, 0, 0)]  # (entity, x, y)
        positioned[start_entity.room.id] = {'entity': start_entity, 'x': 0, 'y': 0}
        visited.add(start_entity.room.id)

        print(f"Starting layout from room {start_entity.room.vnum} (id: {start_entity.room.id})")
        print(f"Total entities to position: {len(self.entities)}")

        # Direction offsets (matching MUD conventions: north is up, east is right)
        direction_deltas = {
            'north': (0, 1),
            'south': (0, -1),
            'east': (1, 0),
            'west': (-1, 0),
            'up': (0, 0),      # Up/down don't change position
            'down': (0, 0)
        }

        while queue:
            current_entity, curr_x, curr_y = queue.pop(0)

            # Debug: print connections for first few rooms
            if len(positioned) <= 5:
                conn_vnums = {}
                for dir_name, room_id in current_entity.connections.items():
                    if room_id:
                        conn_room = next((e for e in self.entities if e.room.id == room_id), None)
                        conn_vnums[dir_name] = conn_room.room.vnum if conn_room else "cross-area"
                print(f"  Room {current_entity.room.vnum} at ({curr_x}, {curr_y}) connects to: {conn_vnums}")

            # Process all connections
            for direction, connected_room_id in current_entity.connections.items():
                if not connected_room_id:
                    continue

                if connected_room_id in visited:
                    # Already positioned this room, skip
                    continue

                # Find the entity for this connected room
                connected_entity = next(
                    (e for e in self.entities if e.room.id == connected_room_id),
                    None
                )

                if not connected_entity:
                    # This is likely a cross-area connection
                    continue

                # Calculate position based on direction
                dx, dy = direction_deltas.get(direction, (0, 0))
                new_x, new_y = curr_x + dx, curr_y + dy

                # Check for position conflicts
                position_occupied = any(
                    r['x'] == new_x and r['y'] == new_y
                    for r in positioned.values()
                )

                if position_occupied:
                    # Position conflict! Try to find an adjacent free spot on the grid
                    # Try full grid positions in a spiral pattern around the conflict
                    offsets = [
                        (1, 0), (-1, 0), (0, 1), (0, -1),  # Adjacent on grid
                        (1, 1), (-1, -1), (1, -1), (-1, 1),  # Diagonals
                        (2, 0), (-2, 0), (0, 2), (0, -2)  # Further away
                    ]
                    original_x, original_y = new_x, new_y
                    for offset_dx, offset_dy in offsets:
                        test_x, test_y = original_x + offset_dx, original_y + offset_dy
                        if not any(r['x'] == test_x and r['y'] == test_y for r in positioned.values()):
                            new_x, new_y = test_x, test_y
                            conflicting_room = next(
                                (r['entity'].room.vnum for r in positioned.values()
                                 if r['x'] == original_x and r['y'] == original_y),
                                "unknown"
                            )
                            print(f"  ⚠ Position conflict at ({original_x}, {original_y})!")
                            print(f"    Room {conflicting_room} already there, moved room {connected_entity.room.vnum} to ({new_x}, {new_y})")
                            break

                # Store position
                positioned[connected_room_id] = {
                    'entity': connected_entity,
                    'x': new_x,
                    'y': new_y
                }
                visited.add(connected_room_id)
                queue.append((connected_entity, new_x, new_y))

        print(f"Positioned {len(positioned)} rooms out of {len(self.entities)} entities")

        # Check for position collisions in final result
        position_map = {}
        for room_id, room_data in positioned.items():
            pos_key = (room_data['x'], room_data['y'])
            if pos_key not in position_map:
                position_map[pos_key] = []
            position_map[pos_key].append(room_data['entity'].room.vnum)

        collisions = {pos: vnums for pos, vnums in position_map.items() if len(vnums) > 1}
        if collisions:
            print(f"WARNING: Found {len(collisions)} position collisions:")
            for pos, vnums in collisions.items():
                print(f"  Position {pos}: rooms {vnums}")

        # Position any remaining unconnected rooms
        unpositioned_count = 0
        for entity in self.entities:
            if entity.room.id not in positioned:
                # Place disconnected rooms in a row below the main map
                positioned[entity.room.id] = {
                    'entity': entity,
                    'x': unpositioned_count,
                    'y': -10
                }
                unpositioned_count += 1

        if unpositioned_count > 0:
            print(f"Placed {unpositioned_count} disconnected rooms at y=-10")

        return positioned

    def _create_spatial_sheets(self, positioned_rooms):
        """
        Group positioned rooms into sheets based on spatial proximity.
        """
        if not positioned_rooms:
            return []

        sheets = []
        remaining = set(positioned_rooms.keys())

        while remaining:
            # Start a new sheet with an unplaced room
            seed_room_id = next(iter(remaining))
            seed_data = positioned_rooms[seed_room_id]

            # Find all rooms within sheet bounds
            sheet_rooms = self._gather_sheet_rooms(
                positioned_rooms,
                remaining,
                seed_data['x'],
                seed_data['y']
            )

            if sheet_rooms:
                sheets.append(sheet_rooms)
                remaining -= set(r['entity'].room.id for r in sheet_rooms)

        return sheets

    def _gather_sheet_rooms(self, positioned_rooms, remaining, center_x, center_y):
        """
        Gather rooms for a sheet centered around the given position.
        """
        # Define sheet bounds (adjust based on compact mode)
        if self.compact_mode:
            max_extent = 3  # 7x7 grid
        else:
            max_extent = 2  # 5x5 grid

        sheet_rooms = []
        for room_id in list(remaining):
            room_data = positioned_rooms[room_id]
            dx = abs(room_data['x'] - center_x)
            dy = abs(room_data['y'] - center_y)

            if dx <= max_extent and dy <= max_extent:
                sheet_rooms.append(room_data)

        return sheet_rooms

    def _create_pdf_deck(self, sheets):
        """
        Create a single PDF file containing all sheets as pages.
        """
        from matplotlib.backends.backend_pdf import PdfPages
        import re
        import os

        # Sanitize area name for filename
        area_name_clean = re.sub(r'[<>:"/\\|?*]', '_', self.area_name)
        area_name_clean = area_name_clean.replace(' ', '_')
        filename = f"deck_{area_name_clean}.pdf"

        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filename)) if os.path.dirname(filename) else '.', exist_ok=True)

        print(f"Creating PDF deck: {filename} with {len(sheets)} sheets...")

        with PdfPages(filename) as pdf:
            for sheet_num, sheet_data in enumerate(sheets):
                fig = self._render_spatial_sheet_to_figure(sheet_num, sheet_data, len(sheets))
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

            # Set PDF metadata
            d = pdf.infodict()
            d['Title'] = f'{self.area_name} - Area Map'
            d['Author'] = 'RoM Map Generator'
            d['Subject'] = f'Map deck for {self.area_name}'
            d['Keywords'] = 'MUD, ROM, Area Map'

        print(f"✓ Saved {filename} ({len(sheets)} sheets)")

    def _render_spatial_sheet_to_figure(self, sheet_num, sheet_rooms, total_sheets):
        """
        Render a sheet with rooms at their calculated spatial positions and return the figure.
        Returns a matplotlib figure object.
        """
        if not sheet_rooms:
            return None

        # Create a single large plot for the map
        fig, ax = plt.subplots(figsize=(18, 18))

        # Title with sheet number and total
        fig.suptitle(f"{self.area_name} - Sheet {sheet_num + 1} of {total_sheets}",
                    fontsize=16, fontweight='bold')

        # Find bounds of this sheet
        min_x = min(r['x'] for r in sheet_rooms)
        max_x = max(r['x'] for r in sheet_rooms)
        min_y = min(r['y'] for r in sheet_rooms)
        max_y = max(r['y'] for r in sheet_rooms)

        # Add padding
        padding = 1.5
        ax.set_xlim(min_x - padding, max_x + padding)
        ax.set_ylim(min_y - padding, max_y + padding)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2, linestyle='--')
        ax.axis('on')  # Show axes to help understand positioning

        # Draw all rooms at their spatial positions
        room_patches = {}  # Store for drawing connections
        for room_data in sheet_rooms:
            entity = room_data['entity']
            x, y = room_data['x'], room_data['y']

            # Draw room rectangle
            from matplotlib.patches import Rectangle
            if self.compact_mode:
                room_size = 0.65
                name_font_size = 5
                vnum_font_size = 4
                max_name_length = 10
            else:
                room_size = 0.75
                name_font_size = 6
                vnum_font_size = 5
                max_name_length = 12

            rect = Rectangle(
                (x - room_size/2, y - room_size/2),
                room_size,
                room_size,
                edgecolor='black',
                facecolor='lightblue',
                linewidth=2,
                zorder=2
            )
            ax.add_patch(rect)
            room_patches[entity.room.id] = (x, y, rect)

            # Add room name - split into multiple lines if needed
            room_name = entity.room.name

            # Smart text wrapping
            if len(room_name) > max_name_length:
                words = room_name.split()
                if len(words) > 1:
                    # Multi-word: try to balance lines
                    lines = []
                    current_line = []
                    current_length = 0

                    for word in words:
                        if current_length + len(word) + 1 <= max_name_length:
                            current_line.append(word)
                            current_length += len(word) + 1
                        else:
                            if current_line:
                                lines.append(' '.join(current_line))
                            current_line = [word]
                            current_length = len(word)

                    if current_line:
                        lines.append(' '.join(current_line))

                    # Limit to 2 lines max
                    if len(lines) > 2:
                        lines = lines[:2]
                        lines[1] = lines[1][:max_name_length-2] + "..."

                    room_name_display = '\n'.join(lines)
                else:
                    # Single long word - truncate
                    room_name_display = room_name[:max_name_length-2] + "..."
            else:
                room_name_display = room_name

            ax.text(x, y + 0.1, room_name_display, ha='center', va='center',
                   fontsize=name_font_size, fontweight='bold', zorder=3,
                   multialignment='center', linespacing=0.9)

            # Add VNUM at bottom of room (inside the box)
            ax.text(x, y - room_size/2 + 0.08, f"#{entity.room.vnum}",
                   ha='center', va='bottom', fontsize=vnum_font_size,
                   color='dimgray', zorder=3, style='italic')

        # Draw connections between rooms on this sheet
        from matplotlib.patches import FancyArrowPatch
        drawn_connections = set()  # Avoid duplicate arrows

        for room_data in sheet_rooms:
            entity = room_data['entity']
            from_x, from_y = room_data['x'], room_data['y']

            for direction, connected_room_id in entity.connections.items():
                if not connected_room_id:
                    continue

                # Check if connected room is on this sheet
                to_room_data = next((r for r in sheet_rooms if r['entity'].room.id == connected_room_id), None)
                if not to_room_data:
                    # Draw indicator for off-sheet connection
                    self._draw_offsheet_indicator(ax, from_x, from_y, direction, connected_room_id, entity.area, entity.room, self.vnum_to_area_map)
                    continue

                to_x, to_y = to_room_data['x'], to_room_data['y']

                # Avoid drawing same connection twice
                connection_key = tuple(sorted([entity.room.id, connected_room_id]))
                if connection_key in drawn_connections:
                    continue
                drawn_connections.add(connection_key)

                # Determine arrow color
                arrow_color = 'green'  # Same area

                # Draw connection
                if direction in ['up', 'down']:
                    # Curved line for vertical connections
                    linestyle = '--'
                    arrow_color = 'purple'
                else:
                    linestyle = '-'

                arrow = FancyArrowPatch(
                    (from_x, from_y),
                    (to_x, to_y),
                    arrowstyle='-',
                    color=arrow_color,
                    linewidth=2,
                    linestyle=linestyle,
                    alpha=0.6,
                    zorder=1
                )
                ax.add_patch(arrow)

        # Add legend
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D
        legend_elements = [
            Patch(facecolor='lightblue', edgecolor='black', label='Room'),
            Line2D([0], [0], color='green', linewidth=2, label='Horizontal Connection'),
            Line2D([0], [0], color='purple', linewidth=2, linestyle='--', label='Up/Down Connection'),
            Patch(facecolor='yellow', edgecolor='orange', label='Off-Sheet (same deck)'),
            Patch(facecolor='yellow', edgecolor='red', label='Cross-Deck (other area)')
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=10)

        plt.tight_layout()
        return fig

    def _draw_offsheet_indicator(self, ax, x, y, direction, connected_room_id, area, source_room, vnum_to_area_map):
        """
        Draw an indicator showing connection to room not on this sheet.
        Orange = same deck (different sheet), Red = different deck (cross-area).
        """
        # Small arrow pointing in the direction
        direction_offsets = {
            'north': (0, 0.5),
            'south': (0, -0.5),
            'east': (0.5, 0),
            'west': (-0.5, 0),
            'up': (0.35, 0.35),
            'down': (-0.35, -0.35)
        }

        if direction not in direction_offsets:
            return

        dx, dy = direction_offsets[direction]

        # Check if connected room is in same area (same deck) or different area (cross-deck)
        connected_room = next((r for r in area.rooms if r.id == connected_room_id), None)

        from matplotlib.patches import FancyArrowPatch

        if connected_room:
            # Same deck, different sheet
            arrow_color = 'orange'
            edge_color = 'orange'
            label = str(connected_room.vnum)
            secondary_label = None
        else:
            # Cross-deck (different area)
            # Try to get the target VNUM from the exit data
            from MigrateRiversOfMud.entity.Room import DirectionMapping
            direction_map = {
                'north': DirectionMapping.EXIT_NORTH.value,
                'south': DirectionMapping.EXIT_SOUTH.value,
                'east': DirectionMapping.EXIT_EAST.value,
                'west': DirectionMapping.EXIT_WEST.value,
                'up': DirectionMapping.EXIT_UP.value,
                'down': DirectionMapping.EXIT_DOWN.value
            }

            exit_data = source_room.exits.get(direction_map.get(direction))
            target_vnum = exit_data.get('to_room_vnum') if exit_data else None

            arrow_color = 'red'
            edge_color = 'red'
            label = str(target_vnum) if target_vnum and target_vnum > 0 else "?"

            # Look up the area name from the VNUM map
            if target_vnum and target_vnum in vnum_to_area_map:
                target_area_name = vnum_to_area_map[target_vnum]
                # Truncate long area names
                if len(target_area_name) > 20:
                    target_area_name = target_area_name[:18] + "..."
                secondary_label = target_area_name
            else:
                secondary_label = "Unknown\nArea"

        # Small arrow
        arrow = FancyArrowPatch(
            (x, y),
            (x + dx, y + dy),
            arrowstyle='->',
            color=arrow_color,
            linewidth=1.5,
            mutation_scale=10,
            zorder=2
        )
        ax.add_patch(arrow)

        # Label with VNUM
        ax.text(x + dx * 1.2, y + dy * 1.2, label,
               ha='center', va='center', fontsize=5,
               bbox=dict(boxstyle='circle', facecolor='yellow', edgecolor=edge_color, linewidth=1.5),
               zorder=3)

        # Add secondary label for cross-deck connections (area name)
        if secondary_label:
            ax.text(x + dx * 1.8, y + dy * 1.8, secondary_label,
                   ha='center', va='center', fontsize=4,
                   color='red', fontweight='bold', zorder=3,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='red', linewidth=1))

    def _render_sheet(self, sheet_num, entities):
        """
        Render a single sheet with entities arranged in a grid.
        """
        fig, axes = plt.subplots(
            self.subplots_per_col,
            self.subplots_per_row,
            figsize=(15, 15)
        )

        # Create deck-style title with area name
        import re
        # Sanitize area name for filename (remove/replace invalid characters)
        area_name_clean = re.sub(r'[<>:"/\\|?*]', '_', self.area_name)
        area_name_clean = area_name_clean.replace(' ', '_')
        fig.suptitle(f"{self.area_name} - Sheet {sheet_num + 1}", fontsize=16, fontweight='bold')

        # Flatten axes array for easier indexing
        if self.subplots_per_row == 1 and self.subplots_per_col == 1:
            axes = [[axes]]
        elif self.subplots_per_row == 1 or self.subplots_per_col == 1:
            axes = axes.reshape(self.subplots_per_col, self.subplots_per_row)

        for row in range(self.subplots_per_col):
            for col in range(self.subplots_per_row):
                idx = row * self.subplots_per_row + col
                ax = axes[row, col]

                if idx < len(entities):
                    entity = entities[idx]
                    self._draw_entity_in_subplot(ax, entity)
                else:
                    ax.axis('off')

        # Add legend for connection colors
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D
        legend_elements = [
            Patch(facecolor='green', edgecolor='green', label='Same Area (shows VNUM)'),
            Patch(facecolor='red', edgecolor='red', label='Cross-Area (shows X)'),
            Line2D([0], [0], color='purple', linestyle='--', linewidth=2, label='Up/Down Connection')
        ]
        fig.legend(handles=legend_elements, loc='lower center', ncol=3, fontsize=9,
                  bbox_to_anchor=(0.5, -0.01))

        plt.tight_layout()
        filename = f"deck_{area_name_clean}_sheet_{sheet_num + 1}.png"

        # Ensure the file can be written (create directory if needed)
        import os
        os.makedirs(os.path.dirname(os.path.abspath(filename)) if os.path.dirname(filename) else '.', exist_ok=True)

        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Saved {filename}")
        plt.close(fig)  # Close figure to free memory

    def _draw_entity_in_subplot(self, ax, entity):
        """
        Draw a single room entity with its connections in a subplot.
        """
        # Adjust plot limits based on compact mode
        if self.compact_mode:
            ax.set_xlim(-12, 12)
            ax.set_ylim(-12, 12)
        else:
            ax.set_xlim(-20, 20)
            ax.set_ylim(-20, 20)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

        # Draw the main room as a rectangle
        from matplotlib.patches import Rectangle, FancyArrowPatch

        # Adjust sizes based on compact mode
        if self.compact_mode:
            room_size = 6
            font_size = 5
            max_name_length = 15
        else:
            room_size = 8
            font_size = 6
            max_name_length = 20

        room_rect = Rectangle(
            (-room_size/2, -room_size/2),
            room_size,
            room_size,
            edgecolor='black',
            facecolor='lightblue',
            linewidth=2
        )
        ax.add_patch(room_rect)

        # Add room name as label
        room_name = entity.room.name
        # Truncate if too long
        if len(room_name) > max_name_length:
            room_name = room_name[:max_name_length - 2] + "..."
        ax.text(0, 0, room_name, ha='center', va='center', fontsize=font_size, fontweight='bold', wrap=True)

        # Draw connection indicators
        # Adjust spacing multipliers for compact mode
        if self.compact_mode:
            up_down_offset = 1.5
            arrow_multiplier = 1.3
            label_multiplier = 1.7
            arrow_scale = 12
            label_fontsize = 5
            title_fontsize = 7
        else:
            up_down_offset = 2
            arrow_multiplier = 1.5
            label_multiplier = 2
            arrow_scale = 15
            label_fontsize = 6
            title_fontsize = 8

        connection_positions = {
            'north': (0, room_size/2),
            'south': (0, -room_size/2),
            'east': (room_size/2, 0),
            'west': (-room_size/2, 0),
            'up': (room_size/2 + up_down_offset, room_size/2 + up_down_offset),
            'down': (-room_size/2 - up_down_offset, -room_size/2 - up_down_offset)
        }

        for direction, (dx, dy) in connection_positions.items():
            if entity.connections.get(direction) is not None:
                connected_room_id = entity.connections[direction]

                # Check if connection is to another area
                connected_room = next((r for r in entity.area.rooms if r.id == connected_room_id), None)

                if connected_room:
                    # Same area connection - green arrow
                    arrow_color = 'green'
                    label_text = str(connected_room.vnum)  # Show connected room VNUM
                    label_bgcolor = 'white'
                else:
                    # Cross-area connection - red arrow with area indicator
                    arrow_color = 'red'
                    label_text = "X"  # Cross-area indicator
                    label_bgcolor = 'yellow'  # Yellow background indicates cross-area

                # Draw arrow indicating connection
                arrow = FancyArrowPatch(
                    (0, 0), (dx * arrow_multiplier, dy * arrow_multiplier),
                    arrowstyle='->', mutation_scale=arrow_scale,
                    color=arrow_color, linewidth=1.5, alpha=0.7
                )
                ax.add_patch(arrow)

                # Label with VNUM in a circle
                label_x, label_y = dx * label_multiplier, dy * label_multiplier
                ax.text(label_x, label_y, label_text,
                       ha='center', va='center', fontsize=label_fontsize,
                       bbox=dict(boxstyle='circle', facecolor=label_bgcolor, alpha=0.9, edgecolor=arrow_color, linewidth=1.5))

        ax.set_title(f"vnum: {entity.room.vnum}", fontsize=title_fontsize)
        ax.axis('off')

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

            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close(fig)  # Close figure to free memory
