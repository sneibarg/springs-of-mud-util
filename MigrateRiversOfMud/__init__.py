import re


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
