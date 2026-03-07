import os
import re

# Set matplotlib to use non-interactive backend to reduce memory usage
import matplotlib
matplotlib.use('Agg')

from MigrateRiversOfMud.entity.Area import Area
from MigrateRiversOfMud.entity.Orchestrator import Orchestrator
from MigrateRiversOfMud.presentation import RomDeck, RomLayoutEngine, RomMapEntity



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


def migrate_rom(area_dir, dry_run=False, delete_first=False):
    orchestrator = Orchestrator(area_dir, dry_run=dry_run, delete_first=delete_first)
    orchestrator.run()


def _build_vnum_to_area_map(area_files):
    """
    Build a mapping of VNUM to area name for all areas.
    This allows cross-deck references to show the target area name.
    """
    vnum_to_area = {}
    for area_file in area_files:
        try:
            area = Area(area_file, insert=False)
            for room in area.rooms:
                vnum_to_area[room.vnum] = area.name
        except Exception as e:
            print(f"Warning: Could not process {area_file} for VNUM mapping: {e}")
    return vnum_to_area


def _process_single_area(args):
    """Process a single area file for presentation (used for parallel processing)"""
    area_file, compact_mode, vnum_to_area_map = args
    import gc
    print(f"Processing {area_file}...")
    area = Area(area_file, insert=False)
    map_entity_list = RomMapEntity.generate_entities(area)
    print(f"Entity count: {len(map_entity_list)}")

    # Process in batches to reduce memory usage, passing area name and VNUM map for deck naming
    rom_layout_engine = RomLayoutEngine(
        map_entity_list,
        area_name=area.name,
        compact_mode=compact_mode,
        vnum_to_area_map=vnum_to_area_map
    )
    rom_layout_engine.render_plot()

    # Clean up entities after rendering
    for entity in map_entity_list:
        entity.cleanup()

    # Clear references and force garbage collection
    del map_entity_list
    del rom_layout_engine
    del area
    gc.collect()
    print(f"Completed {area_file}\n")
    return area_file


def build_presentation(area_files, compact_mode=False, parallel=False):
    """
    Build presentation decks for all area files.

    Args:
        area_files: List of area file paths to process
        compact_mode: Use compact spacing mode
        parallel: Process areas in parallel using multiprocessing
    """
    import time
    start_time = time.time()

    # First pass: build VNUM to area name mapping for cross-deck references
    print("Building VNUM to area mapping...")
    vnum_to_area_map = _build_vnum_to_area_map(area_files)
    print(f"Mapped {len(vnum_to_area_map)} rooms across all areas")

    if parallel:
        import multiprocessing
        print(f"Processing {len(area_files)} areas in parallel using {multiprocessing.cpu_count()} processors...")
        with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
            pool.map(_process_single_area, [(f, compact_mode, vnum_to_area_map) for f in area_files])
    else:
        print(f"Processing {len(area_files)} areas sequentially...")
        for area_file in area_files:
            _process_single_area((area_file, compact_mode, vnum_to_area_map))

    end_time = time.time()
    print(f"\nPresentation build completed in {end_time - start_time:.2f} seconds.")

