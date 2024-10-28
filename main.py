import os
import re

from pyMud.migrate.Area import Area


def add_space_around_operators(code):
    operators = ['==', '!=', '<=', '>=', '<', '>', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '>>=', '<<=', '**=']
    operators = sorted(operators, key=len,
                       reverse=True)  # sort by length in descending order to match longer operators first
    pattern = '|'.join(map(re.escape, operators))  # create a pattern by joining all operators with '|'
    return re.sub('({})'.format(pattern), r' \1 ', code)


def main():
    areas = {}
    area_dir = "C:\\Users\\scott\\CLionProjects\\rom24-quickmud\\area"
    for filename in os.listdir(area_dir):
        if filename.endswith('.are'):
            print("FILE: " + str(os.path.join(area_dir, filename)))
            area = Area(str(os.path.join(area_dir, filename)))
            areas[area.lines[2].replace("~", "")] = area
            continue


if __name__ == '__main__':
    main()
