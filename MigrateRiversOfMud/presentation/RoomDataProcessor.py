from MigrateRiversOfMud.logging import setup_logger


class RoomDataProcessor:
    def __init__(self, entities_or_area, filename="RoomDataProcessor.log"):
        self.logger = setup_logger("RoomDataProcessor", filename)
        self.entities = []

        # Handle both list of entities and area object
        if isinstance(entities_or_area, list):
            # Already a list of RomMapEntity objects, extract room data
            for entity in entities_or_area:
                self.entities.append({
                    'room': entity.area.rooms[entity.room_index],
                    'position': None,
                    'connections': entity.connections
                })
        else:
            # Legacy: area object with rooms
            self.area = entities_or_area
            for room in entities_or_area.rooms:
                entity = {
                    'room': room,
                    'position': None,
                    'connections': {
                        'north': room.exitNorth,
                        'south': room.exitSouth,
                        'east': room.exitEast,
                        'west': room.exitWest,
                        'up': room.exitUp,
                        'down': room.exitDown,
                    }
                }
                self.entities.append(entity)

        # Build room lookup dictionary
        self.room_dict_by_id = {entity['room'].id: entity for entity in self.entities}

        # Initialize the first entity (middle entity) with a starting position
        if self.entities:
            self.entities[0]['position'] = (0, 0)

    def process_room_data(self):
        """Process room data and return positioned entities"""

        # Determine vertical placement for down/up connections
        processed_entities = []
        for entity in self.entities:
            if not entity['position']:
                # Calculate position based on connections
                x, y = self._calculate_position(entity)

                entity.update({
                    'position': (x, y),
                    **self._determine_vertical_neighbors()
                })
            processed_entities.append(entity)

        return processed_entities

    def _get_middle_entity(self):
        """Get the middle entity from the list"""
        if not self.entities:
            raise ValueError("No entities available to determine middle")
        return self.entities[0]

    def _calculate_position(self, entity):
        """
        Calculate the position of an entity based on its connections.

        Args:
            entity (dict): The room data containing 'room' and 'connections'

        Returns:
            tuple: (x, y) coordinates for the entity
        """
        # Get the middle entity's position as the starting point
        middle_entity = self._get_middle_entity()
        if not middle_entity['position']:
            raise ValueError("Middle entity has no position defined.")

        x, y = middle_entity['position']

        # BFS to determine positions relative to the middle entity
        from collections import deque
        visited = set()

        queue = deque()
        queue.append((middle_entity, (x, y)))
        visited.add((middle_entity['room'].id,))
        target_position = None

        while queue:
            current_entity, (current_x, current_y) = queue.popleft()

            # Check if we found the target entity
            if current_entity['room'].id == entity['room'].id:
                target_position = (current_x, current_y)
                break

            for direction in ['north', 'south', 'east', 'west', 'up', 'down']:
                connected_room_id = current_entity['connections'].get(direction)
                if connected_room_id is None:
                    continue

                if connected_room_id not in self.room_dict_by_id:
                    continue  # Room not found, skip this connection

                if connected_room_id in visited:
                    continue

                connected_entity = self.room_dict_by_id[connected_room_id]

                delta_x, delta_y = self._direction_delta(direction)
                new_x = current_x + delta_x
                new_y = current_y + delta_y

                # Set position for connected entity if not already set
                if connected_entity['position'] is None:
                    connected_entity['position'] = (new_x, new_y)

                visited.add(connected_room_id)
                queue.append((connected_entity, (new_x, new_y)))

        # Return the found position or a default
        if target_position:
            return target_position
        else:
            # Entity not connected to middle entity, assign arbitrary position
            self.logger.warning(f"Room {entity['room'].id} is not connected to the graph. Assigning default position.")
            return (0, 0)

    def _direction_delta(self, direction):
        """
        Convert a direction string to coordinate deltas.

        Args:
            direction (str): Direction ('north', 'south', 'east', 'west', 'up', 'down')

        Returns:
            tuple: (delta_x, delta_y) for the given direction
        """
        direction_map = {
            'north': (0, 1),
            'south': (0, -1),
            'east': (1, 0),
            'west': (-1, 0),
            'up': (0, 0),      # Vertical directions don't change x,y position in 2D
            'down': (0, 0)
        }
        return direction_map.get(direction, (0, 0))

    def _determine_vertical_neighbors(self):
        """Determine vertical neighbor positions based on east/west placement"""
        # TODO: Implement actual neighbor determination
        return {
            'up': (0, 20),
            'down': (0, -20)
        }
