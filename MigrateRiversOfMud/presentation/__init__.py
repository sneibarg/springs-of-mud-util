import matplotlib.pyplot as plt
from MigrateRiversOfMud.logging import setup_logger
from MigrateRiversOfMud.presentation.RoomDataProcessor import RoomDataProcessor


class RomDeck:
    def __init__(self, area, log_dir="logs"):
        self.area = area
        self.logger = setup_logger("RomDeck", log_dir)
        self.room_dict_by_id = {room.id: room for room in area.rooms}
        self.room_dict_by_vnum = {room.vnum: room for room in area.rooms}
        self._processor = RoomDataProcessor(area)

    def create_deck(self, max_rooms_per_slide=15):
        entities = self._processor.process_room_data()
        slides = self._layout_slides(entities, max_rooms_per_slide)

        for i, slide in enumerate(slides):
            # Calculate dynamic figure size based on slide bounds
            slide_width = slide['bounds']['max_x'] - slide['bounds']['min_x']
            slide_height = slide['bounds']['max_y'] - slide['bounds']['min_y']
            figsize = (slide_width / 10, slide_height / 10)  # Scale factor

            self.figure, self.ax = plt.subplots(figsize=figsize)
            self.ax.set_xlim(slide['bounds']['min_x'], slide['bounds']['max_x'])
            self.ax.set_ylim(slide['bounds']['min_y'], slide['bounds']['max_y'])
            self.ax.set_aspect("equal")
            self.ax.axis("off")

            for entity in slide['entities']:
                x, y = entity['position']
                self._draw_room(x, y, entity['room'].name)
                self._draw_connections(entity, slide['entities'])

            self._save_slide(f"area_map_{self.area.name}_slide_{i + 1}.png")

    @staticmethod
    def _create_entities(rooms):
        entities = []

        for room in rooms:
            entities.append({
                'room': room,
                'connections': {
                    'north': room.exitNorth,
                    'south': room.exitSouth,
                    'east': room.exitEast,
                    'west': room.exitWest,
                    'up': room.exitUp,
                    'down': room.exitDown,
                },
                'position': None  # Will be set during layout
            })

        return entities

    def _layout_slides(self, entities, slide_size=80):
        slides = [{'entities': [], 'bounds': {'min_x': -40, 'max_x': 40, 'min_y': -40, 'max_y': 40}}]
        middle_entity = entities[0]
        middle_entity['position'] = (0, 0)
        slides[0]['entities'].append(middle_entity)

        queue = [middle_entity]
        while queue:
            current_entity = queue.pop(0)
            x, y = current_entity['position']

            for direction, neighbor_id in current_entity['connections'].items():
                if not neighbor_id:
                    continue

                neighbor = next((e for e in entities if e['room'].id == neighbor_id), None)
                if not neighbor or neighbor['position']:
                    continue

                dx, dy = self._direction_delta(direction)
                neighbor_x, neighbor_y = x + dx, y + dy

                slide = self._find_or_create_slide(slides, neighbor_x, neighbor_y, slide_size)
                neighbor['position'] = (neighbor_x, neighbor_y)
                slide['entities'].append(neighbor)
                queue.append(neighbor)
        print(f'Slides calculated: {len(slides)}')
        return slides

    @staticmethod
    def _find_or_create_slide(slides, x, y, slide_size):
        for slide in slides:
            if (slide['bounds']['min_x'] <= x <= slide['bounds']['max_x'] and
                    slide['bounds']['min_y'] <= y <= slide['bounds']['max_y']):
                return slide

        new_slide = {
            'entities': [],
            'bounds': {
                'min_x': x - slide_size // 2, 'max_x': x + slide_size // 2,
                'min_y': y - slide_size // 2, 'max_y': y + slide_size // 2
            }
        }
        slides.append(new_slide)
        return new_slide

    @staticmethod
    def _direction_delta(direction):
        return {
            'north': (0, 20),
            'south': (0, -20),
            'east': (20, 0),
            'west': (-20, 0),
            'up': (0, 10),
            'down': (0, -10),
        }.get(direction, (0, 0))

    def _draw_connections(self, entity, slide_entities):
        x1, y1 = entity['position']

        for direction, neighbor_id in entity['connections'].items():
            if not neighbor_id:
                continue

            neighbor = next((e for e in slide_entities if e['room'].id == neighbor_id), None)
            if not neighbor:
                continue

            x2, y2 = neighbor['position']
            self._draw_connection(x1, y1, x2, y2)

    def _draw_connection(self, x1, y1, x2, y2):
        self.ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), color='blue', arrowstyle='-|>', mutation_scale=10))

    def _draw_room(self, x, y, title):
        size = 10
        self.ax.add_patch(Rectangle((x - size / 2, y - size / 2), size, size, edgecolor="black", facecolor="lightgray"))
        self.ax.text(x, y, title, ha="center", va="center", fontsize=8)

    def _save_slide(self, filename):
        self.figure.savefig(filename)
        self.logger.info(f"Slide saved as {filename}")
        plt.close(self.figure)
