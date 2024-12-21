import re

from MigrateRiversOfMud.entity import Area
from MigrateRiversOfMud.presentation import RomDeck
from MigrateRiversOfMud.presentation.RomMapEntity import RomMapEntity


def snake_case_to_camel(snake_str):
    if snake_str is None: return None
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def lambda_match(input_str, pattern, anon_dict):
    match = re.match(pattern, input_str)
    if match:
        named_captures = {k: v for k, v in match.groupdict().items() if v is not None}
        return {**anon_dict, **named_captures}
    else:
        return anon_dict


def add_space_around_operators(code):
    operators = ['==', '!=', '<=', '>=', '<', '>', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '>>=', '<<=', '**=']
    operators = sorted(operators, key=len,
                       reverse=True)  # sort by length in descending order to match longer operators first
    pattern = '|'.join(map(re.escape, operators))  # create a pattern by joining all operators with '|'
    return re.sub('({})'.format(pattern), r' \1 ', code)


def migrate_rom(area_dir):
    from MigrateRiversOfMud.entity import Orchestrator
    orchestrator = Orchestrator(area_dir)
    orchestrator.run()


def build_presentation(area_files):
    for area_file in area_files:
        area = Area(area_file, insert=False)
        area_entity = RomMapEntity(area, 0, 0.0, 0.0, False)
        area_entity.generate_entities(area)
        break
