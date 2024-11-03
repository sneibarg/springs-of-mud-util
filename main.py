import os

from pyMud.migrate.Area import Area


def main():
    areas = {}
    area_dir = "C:\\Users\\scott\\CLionProjects\\rom24-quickmud\\area"
    for filename in os.listdir(area_dir):
        if filename.endswith('.are'):
            print("FILE: " + str(os.path.join(area_dir, filename)))
            area = Area(str(os.path.join(area_dir, filename)))
            areas[area.lines[2].replace("~", "")] = area
            break


if __name__ == '__main__':
    main()
