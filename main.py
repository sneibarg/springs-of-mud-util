import os
from MigrateRiversOfMud import migrate_rom, build_presentation

area_directory = "C:\\Users\\scott\\CLionProjects\\rom24-quickmud\\area"
presentation = True


def main():
    if presentation:
        area_files = [os.path.join(area_directory, file) for file in os.listdir(area_directory) if file.endswith('.are')]
        build_presentation(area_files)
    else:
        migrate_rom("C:\\Users\\scott\\CLionProjects\\rom24-quickmud\\area")


if __name__ == '__main__':
    main()
