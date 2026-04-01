import os
from MigrateRiversOfMud import migrate_rom, build_presentation

area_directory = "C:\\Users\\scott\\CLionProjects\\rom24-quickmud\\area"
presentation = False

# Feature Flags
COMPACT_MODE = True  # Set to True for tighter spacing and more content per sheet
PARALLEL_PROCESSING = False  # Set to True to process areas in parallel
OUTPUT_FORMAT = 'html'  # 'pdf' or 'html' - Choose output format for presentation
MIGRATE_TYPE = "helps"  # all, areas, socials, helps


def main():
    if presentation:
        area_files = [os.path.join(area_directory, file) for file in os.listdir(area_directory) if file.endswith('.are')]
        build_presentation(
            area_files,
            compact_mode=COMPACT_MODE,
            parallel=PARALLEL_PROCESSING,
            output_format=OUTPUT_FORMAT
        )
    else:
        migrate_rom(
            "C:\\Users\\scott\\CLionProjects\\rom24-quickmud\\area",
            dry_run=False,
            delete_first=True,
            migrate_type=MIGRATE_TYPE
        )


if __name__ == '__main__':
    main()
