import re


def lambda_match(input_str, pattern, anon_dict):
    match = re.match(pattern, input_str)
    if match:
        named_captures = {k: v for k, v in match.groupdict().items() if v is not None}
        return {**anon_dict, **named_captures}
    else:
        return anon_dict


def extract_subsection(data, parser):
    """
    Extract subsections of data and parse each using the provided parser function.
    Handles empty lines and ensures all lines are collected for each room.
    """
    subsections = []
    lines = data
    fields = []
    collecting = False
    vnum_pattern = re.compile(r'^#\d+')
    for index, line in enumerate(lines):
        if vnum_pattern.match(line):
            if collecting:
                if fields:
                    print(f"Processing subsection starting with: {fields[0]}")
                    print(f"Fields for VNUM {fields[0][1:]}: {fields}")
                    subsections.append(parser(fields))
                    fields = []
            collecting = True
        if collecting:
            fields.append(line)
    # After processing all lines, check if any fields are left
    if fields:
        print(f"Processing final subsection starting with: {fields[0]}")
        print(f"Fields for VNUM {fields[0][1:]}: {fields}")
        print("LINES="+str(lines))
        # subsections.append(parser(fields))
    return subsections
