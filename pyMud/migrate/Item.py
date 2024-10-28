from pyMud import extract_subsection
from pyMud.rest import new_object_payload


def extract_objects(data):
    return extract_subsection(data, extract_object_fields)


def load_objects(objects):
    new_objects = []
    for mud_object in objects:
        payload = new_object_payload(mud_object)
        print("OBJECT_PAYLOAD: " + str(payload))
        # response = post(payload, item_api + "item")
        # content = json.loads(response.content)
        # new_objects.append(content)
    return new_objects


def extract_object_fields(fields):
    vnum = fields[0] if len(fields) > 0 else ''
    name = fields[1] if len(fields) > 1 else ''
    short_descr = fields[2] if len(fields) > 2 else ''
    long_descr = fields[3] if len(fields) > 3 else ''
    description = fields[4] if len(fields) > 4 else ''
    item_type = fields[5] if len(fields) > 5 else ''
    extra_flags = fields[6] if len(fields) > 6 else ''
    wear_flags = fields[7] if len(fields) > 7 else ''
    value = fields[8] if len(fields) > 8 else ''
    weight = fields[9] if len(fields) > 9 else ''
    level = fields[10] if len(fields) > 10 else ''
    affect_data = fields[11] if len(fields) > 11 else ''
    return {
        'vnum': vnum,
        'name': name,
        'short_descr': short_descr,
        'long_descr': long_descr,
        'description': description,
        'item_type': item_type,
        'extra_flags': extra_flags,
        'wear_flags': wear_flags,
        'value': value,
        'weight': weight,
        'level': level,
        'affect_data': affect_data,
    }