from pyMud import extract_subsection
from pyMud.rest import new_mobile_payload


def extract_mobiles(data):
    return extract_subsection(data, extract_mobile_fields)


def load_mobiles(area_id, mobiles):
    new_mobs = []
    for mobile in mobiles:
        print("MOBILE="+str(mobile))
        payload = new_mobile_payload(mobile)
        payload['areaId'] = area_id
        print("MOBILE_PAYLOAD: " + str(payload))
        # response = post(payload, mobile_api + "mobile")
        # content = json.loads(response.content)
        # new_mobs.append(content)
    return new_mobs


def get_mobile_description(data):
    description = []
    while True:
        line = data.pop(0)
        if line == "~" and len(description) > 0:
            break
        if line == "~":
            continue
        description.append(line)
    return description, data


def extract_mobile_fields(data):
    print("EXTRACT_MOBILE_FIELDS-DATA="+str(data))
    print("SIZE="+str(len(data)))
    mobile = {}
    try:
        # 1. Extract Mob Name
        mobile_name_line = data.pop(0)
        mobile['name'] = mobile_name_line.rstrip('~').strip()

        # 2. Extract Short Description
        short_desc_line = data.pop(0)
        mobile['short_description'] = short_desc_line.rstrip('~').strip()

        # 3. Extract Long Description
        long_desc_lines = []
        while True:
            line = data.pop(0)
            if line.strip() == '~':
                break
            long_desc_lines.append(line)
        mobile['long_description'] = ' '.join(long_desc_lines).strip()

        # 4. Extract Detailed Description
        detailed_desc_lines = []
        while True:
            line = data.pop(0)
            if line.strip() == '~':
                break
            detailed_desc_lines.append(line)
        mobile['description'] = ' '.join(detailed_desc_lines).strip()

        # 5. Extract Race
        race_line = data.pop(0)
        mobile['race'] = race_line.rstrip('~').strip()

        # 6. Extract Act Flags and Affected Flags
        flags_line = data.pop(0)
        flags_parts = flags_line.split()
        mobile['act_flags'] = flags_parts[0]
        mobile['affected_flags'] = flags_parts[1]
        mobile['alignment'] = int(flags_parts[2])
        mobile['group'] = int(flags_parts[3])

        # 7. Extract Level, Hit Dice, Mana Dice, Damage Dice, Damage Type
        stats_line = data.pop(0)
        stats_parts = stats_line.split()
        mobile['level'] = int(stats_parts[0])
        mobile['thac0'] = int(stats_parts[1])
        mobile['hit_dice'] = stats_parts[2]
        mobile['mana_dice'] = stats_parts[3]
        mobile['damage_dice'] = stats_parts[4]
        mobile['damage_type'] = stats_parts[5]

        # 8. Extract Armor Class, Magic Resistance, Saves, Attacks per Round
        ac_line = data.pop(0)
        ac_parts = ac_line.split()
        mobile['armor_class'] = [int(ac) for ac in ac_parts[:3]]
        mobile['attacks_per_round'] = int(ac_parts[3])

        # 9. Extract Offense and Defense Flags
        offense_line = data.pop(0)
        offense_parts = offense_line.split()
        mobile['offense_flags'] = offense_parts[0]
        mobile['immunity'] = offense_parts[1]
        mobile['resistance'] = offense_parts[2]
        mobile['vulnerability'] = offense_parts[3]

        # 10. Extract Position Data
        position_line = data.pop(0)
        position_parts = position_line.split()
        mobile['start_position'] = position_parts[0]
        mobile['default_position'] = position_parts[1]
        mobile['sex'] = position_parts[2]
        mobile['gold'] = int(position_parts[3])

        # 11. Extract Miscellaneous Data
        misc_line = data.pop(0)
        misc_parts = misc_line.split()
        mobile['experience'] = int(misc_parts[0])
        mobile['hitroll'] = int(misc_parts[1])
        mobile['size'] = misc_parts[2]
        mobile['material'] = misc_parts[3]

        return mobile

    except IndexError as e:
        # Handle cases where data may be missing
        print(f"Error parsing mobile data: {e}")
        print(f"Current mobile data: {mobile}")
        return mobile  # or raise an exception if appropriate

    except ValueError as e:
        # Handle cases where data conversion fails
        print(f"Value error: {e}")
        print(f"Current mobile data: {mobile}")
        return mobile  # or raise an exception if appropriate

# def extract_mobile_fields(data):
#     mobiles = []
#     mobile = {}
#
#     while True:
#         if len(data) == 0:
#             break
#         line = data.pop(0)
#         if line.startswith("#"):
#             print("LINE="+line+", DATA="+str(data))
#             mobile['vnum'] = line.split('#')[1]
#             mobile['keywords'] = data.pop(0)
#             mobile['short-description'] = data.pop(0)
#             mobile['long-description'] = data.pop(0)
#             mobile['description'], data = get_mobile_description(data)
#             mobile['race'] = data.pop(0).replace("~", "")
#             mobile['act-flags'] = data.pop(0)
#             mobile['level'] = data.pop(0)
#             mobile['hit-dice'] = data.pop(0)
#             mobile['dam-dice'] = data.pop(0)
#             mobile['position'] = data.pop(0)
#             mobile['sex'] = data.pop(0)
#             mobiles.append(mobile)
#     return mobiles
