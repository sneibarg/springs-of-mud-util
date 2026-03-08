import json
import os
from jinja2 import Environment, FileSystemLoader


class RomHtmlEngine:
    """
    HTML Layout Engine for ROM area maps.
    Generates interactive HTML pages using Plotly for visualization.
    """

    def __init__(self, entities, area_name=None, compact_mode=False, vnum_to_area_map=None):
        """
        Initialize the HTML layout engine.

        Args:
            entities: List of RomMapEntity objects to render.
            area_name: Name of the area for page title.
            compact_mode: If True, use tighter spacing.
            vnum_to_area_map: Dictionary mapping VNUM to area name for cross-area references.
        """
        self.area_name = area_name or "Unknown_Area"
        self.compact_mode = compact_mode
        self.vnum_to_area_map = vnum_to_area_map or {}
        self.entities = entities

    def render_html(self):
        """
        Render the area map as an interactive HTML file.
        Creates a single HTML file with all sheets accessible via dropdown.
        """
        if not self.entities:
            print("No entities to render.")
            return

        # Calculate spatial positions for all rooms (same algorithm as PDF)
        positioned_rooms = self._calculate_spatial_layout()

        # Group rooms into sheets based on spatial proximity
        sheets = self._create_spatial_sheets(positioned_rooms)

        # Build room data map for navigation and info panel
        room_data_map = self._build_room_data_map(sheets)

        # Generate Plotly data for each sheet
        sheet_plotly_data = []
        for sheet_num, sheet_rooms in enumerate(sheets):
            plotly_data = self._create_plotly_sheet(sheet_num, sheet_rooms, len(sheets))
            sheet_plotly_data.append(plotly_data)

        # Render HTML file
        self._create_html_file(sheet_plotly_data, len(sheets), room_data_map)

    def _calculate_spatial_layout(self):
        """
        Calculate spatial (x, y) positions for all rooms based on directional connections.
        Uses BFS to place rooms relative to each other.
        (Same algorithm as RomLayoutEngine)
        """
        if not self.entities:
            return {}

        positioned = {}
        visited = set()

        # Start with first entity at origin
        start_entity = self.entities[0]
        queue = [(start_entity, 0, 0)]
        positioned[start_entity.room.id] = {'entity': start_entity, 'x': 0, 'y': 0}
        visited.add(start_entity.room.id)

        # Direction offsets
        direction_deltas = {
            'north': (0, 1),
            'south': (0, -1),
            'east': (1, 0),
            'west': (-1, 0),
            'up': (0, 0),
            'down': (0, 0)
        }

        while queue:
            current_entity, curr_x, curr_y = queue.pop(0)

            for direction, connected_room_id in current_entity.connections.items():
                if not connected_room_id or connected_room_id in visited:
                    continue

                connected_entity = next((e for e in self.entities if e.room.id == connected_room_id), None)
                if not connected_entity:
                    continue

                dx, dy = direction_deltas.get(direction, (0, 0))
                new_x, new_y = curr_x + dx, curr_y + dy

                # Collision detection
                position_occupied = any(r['x'] == new_x and r['y'] == new_y for r in positioned.values())

                if position_occupied:
                    # Spiral search for free spot
                    offsets = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1),
                              (2, 0), (-2, 0), (0, 2), (0, -2)]
                    for offset_dx, offset_dy in offsets:
                        test_x, test_y = new_x + offset_dx, new_y + offset_dy
                        if not any(r['x'] == test_x and r['y'] == test_y for r in positioned.values()):
                            new_x, new_y = test_x, test_y
                            break

                positioned[connected_room_id] = {'entity': connected_entity, 'x': new_x, 'y': new_y}
                visited.add(connected_room_id)
                queue.append((connected_entity, new_x, new_y))

        # Position any remaining unconnected rooms
        unpositioned_count = 0
        for entity in self.entities:
            if entity.room.id not in positioned:
                positioned[entity.room.id] = {'entity': entity, 'x': unpositioned_count, 'y': -10}
                unpositioned_count += 1

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
            seed_room_id = next(iter(remaining))
            seed_data = positioned_rooms[seed_room_id]

            sheet_rooms = self._gather_sheet_rooms(positioned_rooms, remaining, seed_data['x'], seed_data['y'])

            if sheet_rooms:
                sheets.append(sheet_rooms)
                remaining -= set(r['entity'].room.id for r in sheet_rooms)

        return sheets

    def _gather_sheet_rooms(self, positioned_rooms, remaining, center_x, center_y):
        """
        Gather rooms for a sheet centered around the given position.
        """
        max_extent = 3 if self.compact_mode else 2

        sheet_rooms = []
        for room_id in list(remaining):
            room_data = positioned_rooms[room_id]
            dx = abs(room_data['x'] - center_x)
            dy = abs(room_data['y'] - center_y)

            if dx <= max_extent and dy <= max_extent:
                sheet_rooms.append(room_data)

        return sheet_rooms

    def _build_room_data_map(self, sheets):
        """
        Build a comprehensive map of all room data for JavaScript navigation.
        Returns dict mapping VNUM to room data including exits and sheet number.
        """
        room_map = {}

        for sheet_num, sheet_rooms in enumerate(sheets):
            for room_data in sheet_rooms:
                entity = room_data['entity']
                room = entity.room

                # Get sector type name
                from MigrateRiversOfMud.entity.Room import SectorType
                try:
                    sector_name = SectorType(room.sector_type).name
                except ValueError:
                    sector_name = f"Unknown ({room.sector_type})"

                # Build exit list with navigation data
                exits = []
                for direction in ['north', 'south', 'east', 'west', 'up', 'down']:
                    if entity.connections.get(direction):
                        connected_room_id = entity.connections[direction]
                        connected_room = next((r for r in entity.area.rooms if r.id == connected_room_id), None)

                        if connected_room:
                            # Same area connection
                            exits.append({
                                'direction': direction.capitalize(),
                                'vnum': connected_room.vnum,
                                'label': f"VNUM {connected_room.vnum}",
                                'clickable': True  # Can navigate to this room
                            })
                        else:
                            # Cross-area connection
                            from MigrateRiversOfMud.entity.Room import DirectionMapping
                            direction_map = {
                                'north': DirectionMapping.EXIT_NORTH.value,
                                'south': DirectionMapping.EXIT_SOUTH.value,
                                'east': DirectionMapping.EXIT_EAST.value,
                                'west': DirectionMapping.EXIT_WEST.value,
                                'up': DirectionMapping.EXIT_UP.value,
                                'down': DirectionMapping.EXIT_DOWN.value
                            }
                            exit_data = room.exits.get(direction_map.get(direction))
                            target_vnum = exit_data.get('to_room_vnum') if exit_data else None

                            if target_vnum and target_vnum > 0:
                                target_area = self.vnum_to_area_map.get(target_vnum, "Unknown Area")
                                exits.append({
                                    'direction': direction.capitalize(),
                                    'vnum': target_vnum,
                                    'label': f"VNUM {target_vnum} → {target_area}",
                                    'clickable': True,  # Now clickable - will navigate to other HTML file
                                    'targetArea': target_area  # Include target area name for navigation
                                })

                # Full description (not truncated)
                full_description = room.description.strip()

                room_map[room.vnum] = {
                    'vnum': room.vnum,
                    'name': room.name,
                    'sector': sector_name,
                    'description': full_description,
                    'exits': exits,
                    'sheet': sheet_num
                }

        return room_map

    def _create_plotly_sheet(self, sheet_num, sheet_rooms, total_sheets):
        """
        Create Plotly traces and layout for a single sheet.

        Returns:
            Dict with 'traces' and 'layout' for Plotly
        """
        if not sheet_rooms:
            return {'traces': [], 'layout': {}}

        traces = []

        # Find bounds
        min_x = min(r['x'] for r in sheet_rooms)
        max_x = max(r['x'] for r in sheet_rooms)
        min_y = min(r['y'] for r in sheet_rooms)
        max_y = max(r['y'] for r in sheet_rooms)

        # Add padding
        padding = 1.5
        x_range = [min_x - padding, max_x + padding]
        y_range = [min_y - padding, max_y + padding]

        # Room size
        room_size = 0.65 if self.compact_mode else 0.75

        # Draw room rectangles as shapes
        shapes = []
        annotations = []

        # Track connections to draw
        connections = []

        for room_data in sheet_rooms:
            entity = room_data['entity']
            x, y = room_data['x'], room_data['y']
            room = entity.room

            # Get sector type name
            from MigrateRiversOfMud.entity.Room import SectorType
            try:
                sector_name = SectorType(room.sector_type).name
            except ValueError:
                sector_name = f"Unknown ({room.sector_type})"

            # Build exit info for tooltip
            exit_info = []
            for direction in ['north', 'east', 'south', 'west', 'up', 'down']:
                if entity.connections.get(direction):
                    connected_room_id = entity.connections[direction]
                    connected_room = next((r for r in entity.area.rooms if r.id == connected_room_id), None)
                    if connected_room:
                        exit_info.append(f"{direction.capitalize()}: {connected_room.vnum}")
                    else:
                        from MigrateRiversOfMud.entity.Room import DirectionMapping
                        direction_map = {
                            'north': DirectionMapping.EXIT_NORTH.value,
                            'south': DirectionMapping.EXIT_SOUTH.value,
                            'east': DirectionMapping.EXIT_EAST.value,
                            'west': DirectionMapping.EXIT_WEST.value,
                            'up': DirectionMapping.EXIT_UP.value,
                            'down': DirectionMapping.EXIT_DOWN.value
                        }
                        exit_data = room.exits.get(direction_map.get(direction))
                        target_vnum = exit_data.get('to_room_vnum') if exit_data else None
                        if target_vnum and target_vnum > 0:
                            exit_info.append(f"{direction.capitalize()}: {target_vnum} (cross-area)")

            exits_text = "<br>".join(exit_info) if exit_info else "No exits"

            # Clean description for HTML
            description = room.description.replace('\n', ' ').strip()
            if len(description) > 300:
                description = description[:297] + "..."

            # Room rectangle shape
            shapes.append({
                'type': 'rect',
                'x0': x - room_size / 2,
                'y0': y - room_size / 2,
                'x1': x + room_size / 2,
                'y1': y + room_size / 2,
                'line': {'color': 'black', 'width': 2},
                'fillcolor': 'lightblue',
                'layer': 'below'
            })

            # Room name annotation (centered in room)
            room_name = room.name
            if len(room_name) > 15:
                room_name = room_name[:13] + "..."

            annotations.append({
                'x': x,
                'y': y + 0.1,
                'text': f"<b>{room_name}</b>",
                'showarrow': False,
                'font': {'size': 10 if self.compact_mode else 11, 'color': 'black'},
                'xanchor': 'center',
                'yanchor': 'middle'
            })

            # VNUM annotation (bottom of room)
            annotations.append({
                'x': x,
                'y': y - room_size / 2 + 0.08,
                'text': f"#{room.vnum}",
                'showarrow': False,
                'font': {'size': 8 if self.compact_mode else 9, 'color': 'dimgray'},
                'xanchor': 'center',
                'yanchor': 'bottom'
            })

            # Info icon circle (top-right corner)
            info_icon_size = room_size * 0.15
            info_icon_x = x + room_size / 2 - info_icon_size * 0.7
            info_icon_y = y + room_size / 2 - info_icon_size * 0.7

            shapes.append({
                'type': 'circle',
                'x0': info_icon_x - info_icon_size,
                'y0': info_icon_y - info_icon_size,
                'x1': info_icon_x + info_icon_size,
                'y1': info_icon_y + info_icon_size,
                'fillcolor': 'steelblue',
                'line': {'color': 'steelblue', 'width': 1},
                'opacity': 0.8,
                'layer': 'above'
            })

            # Info icon "i" text
            annotations.append({
                'x': info_icon_x,
                'y': info_icon_y,
                'text': '<i><b>i</b></i>',
                'showarrow': False,
                'font': {'size': 9 if self.compact_mode else 10, 'color': 'white'},
                'xanchor': 'center',
                'yanchor': 'middle'
            })

            # Add invisible scatter point for hover tooltip on info icon AND clicking
            traces.append({
                'type': 'scatter',
                'x': [info_icon_x],
                'y': [info_icon_y],
                'mode': 'markers',
                'marker': {'size': info_icon_size * 100, 'opacity': 0.0},  # Invisible
                'customdata': [room.vnum],  # Store VNUM for click handler
                'hovertemplate': (
                    f"<b>VNUM: {room.vnum}</b><br>"
                    f"<b>Name:</b> {room.name}<br>"
                    f"<b>Sector:</b> {sector_name}<br><br>"
                    f"<b>Description:</b><br>{description}<br><br>"
                    f"<b>Exits:</b><br>{exits_text}<br><br>"
                    f"<i>Click for full details and navigation</i><extra></extra>"
                ),
                'name': f'Room {room.vnum}',
                'showlegend': False
            })

            # Process connections for drawing
            for direction, connected_room_id in entity.connections.items():
                if not connected_room_id:
                    continue

                to_room_data = next((r for r in sheet_rooms if r['entity'].room.id == connected_room_id), None)

                if to_room_data:
                    # Connection on same sheet
                    to_x, to_y = to_room_data['x'], to_room_data['y']

                    # Avoid duplicate connections
                    conn_key = tuple(sorted([entity.room.id, connected_room_id]))
                    if conn_key not in [c[4] for c in connections]:
                        color = 'purple' if direction in ['up', 'down'] else 'green'
                        dash = 'dash' if direction in ['up', 'down'] else 'solid'
                        connections.append((x, y, to_x, to_y, conn_key, color, dash))
                else:
                    # Connection not on this sheet - draw indicator
                    self._add_offsheet_indicator(
                        x, y, direction, connected_room_id, entity,
                        shapes, annotations, traces
                    )

        # Draw connections as line shapes
        for x1, y1, x2, y2, _, color, dash in connections:
            shapes.append({
                'type': 'line',
                'x0': x1,
                'y0': y1,
                'x1': x2,
                'y1': y2,
                'line': {'color': color, 'width': 2, 'dash': dash},
                'layer': 'below',
                'opacity': 0.6
            })

        # Create layout
        layout = {
            'title': {
                'text': f'{self.area_name} - Sheet {sheet_num + 1} of {total_sheets}',
                'font': {'size': 18, 'color': '#495057'},
                'x': 0.5,
                'xanchor': 'center'
            },
            'xaxis': {
                'range': x_range,
                'showgrid': True,
                'gridcolor': 'rgba(0,0,0,0.1)',
                'zeroline': False,
                'showticklabels': False,
                'scaleanchor': 'y',
                'scaleratio': 1
            },
            'yaxis': {
                'range': y_range,
                'showgrid': True,
                'gridcolor': 'rgba(0,0,0,0.1)',
                'zeroline': False,
                'showticklabels': False
            },
            'shapes': shapes,
            'annotations': annotations,
            'hovermode': 'closest',
            'plot_bgcolor': 'white',
            'width': 1200,
            'height': 800,
            'margin': {'l': 50, 'r': 50, 't': 80, 'b': 50}
        }

        return {'traces': traces, 'layout': layout}

    def _add_offsheet_indicator(self, x, y, direction, connected_room_id, entity, shapes, annotations, traces):
        """
        Add visual indicator for off-sheet or cross-area connection.
        Similar to PDF implementation but using Plotly shapes and annotations.
        """
        # Direction offsets (where to place the indicator relative to room)
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
        arrow_x = x + dx
        arrow_y = y + dy

        # Check if this is same-area or cross-area
        connected_room = next((r for r in entity.area.rooms if r.id == connected_room_id), None)

        if connected_room:
            # Same area, different sheet
            arrow_color = 'orange'
            edge_color = 'orange'
            bg_color = 'yellow'
            label_text = str(connected_room.vnum)
            area_label = None
        else:
            # Cross-area connection
            from MigrateRiversOfMud.entity.Room import DirectionMapping
            direction_map = {
                'north': DirectionMapping.EXIT_NORTH.value,
                'south': DirectionMapping.EXIT_SOUTH.value,
                'east': DirectionMapping.EXIT_EAST.value,
                'west': DirectionMapping.EXIT_WEST.value,
                'up': DirectionMapping.EXIT_UP.value,
                'down': DirectionMapping.EXIT_DOWN.value
            }

            exit_data = entity.room.exits.get(direction_map.get(direction))
            target_vnum = exit_data.get('to_room_vnum') if exit_data else None

            arrow_color = 'red'
            edge_color = 'red'
            bg_color = 'yellow'
            label_text = str(target_vnum) if target_vnum and target_vnum > 0 else "?"

            # Get area name
            if target_vnum and target_vnum in self.vnum_to_area_map:
                area_name = self.vnum_to_area_map[target_vnum]
                if len(area_name) > 20:
                    area_name = area_name[:18] + "..."
                area_label = area_name
            else:
                area_label = "Unknown Area"

        # Draw arrow from room to indicator
        shapes.append({
            'type': 'line',
            'x0': x,
            'y0': y,
            'x1': arrow_x,
            'y1': arrow_y,
            'line': {'color': arrow_color, 'width': 2},
            'layer': 'above'
        })

        # Draw arrowhead (small triangle)
        arrow_size = 0.08
        shapes.append({
            'type': 'path',
            'path': f'M {arrow_x},{arrow_y} L {arrow_x-arrow_size},{arrow_y-arrow_size} L {arrow_x+arrow_size},{arrow_y-arrow_size} Z',
            'fillcolor': arrow_color,
            'line': {'color': arrow_color, 'width': 1},
            'layer': 'above'
        })

        # Draw circle with VNUM at arrow end
        circle_size = 0.15
        shapes.append({
            'type': 'circle',
            'x0': arrow_x - circle_size,
            'y0': arrow_y - circle_size,
            'x1': arrow_x + circle_size,
            'y1': arrow_y + circle_size,
            'fillcolor': bg_color,
            'line': {'color': edge_color, 'width': 2},
            'layer': 'above'
        })

        # Add VNUM text in circle
        annotations.append({
            'x': arrow_x,
            'y': arrow_y,
            'text': f'<b>{label_text}</b>',
            'showarrow': False,
            'font': {'size': 8, 'color': 'black'},
            'xanchor': 'center',
            'yanchor': 'middle'
        })

        # Add area name label for cross-area connections
        if area_label:
            label_x = arrow_x + dx * 0.8
            label_y = arrow_y + dy * 0.8

            # Small rectangle background for area name
            rect_width = len(area_label) * 0.08
            rect_height = 0.2
            shapes.append({
                'type': 'rect',
                'x0': label_x - rect_width / 2,
                'y0': label_y - rect_height / 2,
                'x1': label_x + rect_width / 2,
                'y1': label_y + rect_height / 2,
                'fillcolor': 'white',
                'line': {'color': 'red', 'width': 1},
                'layer': 'above'
            })

            # Area name text
            annotations.append({
                'x': label_x,
                'y': label_y,
                'text': f'<b>{area_label}</b>',
                'showarrow': False,
                'font': {'size': 7, 'color': 'red'},
                'xanchor': 'center',
                'yanchor': 'middle'
            })

        # Add invisible clickable point for navigation
        if connected_room:
            # Same area - navigate within this HTML file
            vnum_for_click = connected_room.vnum
            area_for_click = None
        else:
            # Cross area - navigate to other HTML file
            vnum_for_click = target_vnum if target_vnum and target_vnum > 0 else 0
            area_for_click = area_label

        if vnum_for_click and vnum_for_click > 0:
            traces.append({
                'type': 'scatter',
                'x': [arrow_x],
                'y': [arrow_y],
                'mode': 'markers',
                'marker': {'size': 15, 'opacity': 0.0},  # Invisible but clickable
                'customdata': [[vnum_for_click, area_for_click]],  # Include both vnum and area
                'hovertemplate': (
                    f"<b>{'Off-sheet' if connected_room else 'Cross-area'} Connection</b><br>"
                    f"Direction: {direction.capitalize()}<br>"
                    f"Target VNUM: {vnum_for_click}<br>"
                    f"{'Area: ' + area_for_click if area_for_click else ''}<br>"
                    f"<i>Click to navigate</i><extra></extra>"
                ),
                'name': f'Connection to {vnum_for_click}',
                'showlegend': False
            })

    def _create_html_file(self, sheet_plotly_data, total_sheets, room_data_map):
        """
        Create the final HTML file using Jinja2 template.
        """
        import re

        # Sanitize area name for filename
        area_name_clean = re.sub(r'[<>:"/\\|?*]', '_', self.area_name)
        area_name_clean = area_name_clean.replace(' ', '_')
        filename = f"map_{area_name_clean}.html"

        # Get template directory
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('area_map.html')

        # Render template
        html_content = template.render(
            area_name=self.area_name,
            total_sheets=total_sheets,
            total_rooms=len(self.entities),
            sheet_data_json=json.dumps(sheet_plotly_data),
            room_data_map=json.dumps(room_data_map)
        )

        # Write HTML file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ Saved {filename} ({total_sheets} sheets, {len(self.entities)} rooms)")
        print(f"  ✨ Features: Dark mode, clickable navigation, full room descriptions")
