from MigrateRiversOfMud.logging import setup_logger


class RoomDataProcessor:
    def __init__(self, area, log_dir="logs"):
        self.area = area
        self.logger = setup_logger("RoomDataProcessor", log_dir)
        self.entities = []
        for room in area.rooms:
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

    def process_room_data(self):
        """Process room data and return positioned entities"""

        # Determine vertical placement for down/up connections
        processed_entities = []
        for entity in self.entities:
            if not entity['position']:
                # Calculate position based on connections
                middle_entity = self._get_middle_entity()
                print(str(middle_entity))
                if entity['room'] == middle_entity['room'] and middle_entity['position'] is not None:
                    # Set initial position of current entity
                    x, y = middle_entity['position']
                else:
                    # Determine position based on connections
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

        while queue:
            current_entity, (current_x, current_y) = queue.popleft()

            for direction in ['north', 'south', 'east', 'west', 'up', 'down']:
                if entity.get(direction) is None:
                    continue

                connected_room_id = entity[direction]
                if connected_room_id not in self.room_dict_by_id:
                    continue  # Room not found, skip this connection
                connected_entity = self.room_dict_by_id[connected_room_id]

                # Check if the connected room has already been positioned
                if (connected_entity['room'].id, connected_room_id) in visited:
                    continue

                delta_x, delta_y = self._direction_delta(direction)
                new_x = current_x + delta_x
                new_y = current_y + delta_y

                # Assign positions to both current and connected entities
                entity.update({
                    'position': (new_x, new_y),
                    **self._determine_vertical_neighbors()
                })

                visited.add((current_entity['room'].id,))
                queue.append((connected_entity, (new_x, new_y)))

    def _determine_vertical_neighbors(self):
        """Determine vertical neighbor positions based on east/west placement"""
        # TODO: Implement actual neighbor determination
        return {
            'up': (0, 20),
            'down': (0, -20)
        }
