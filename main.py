import os
import sys

from pyMud import *
# import redis

# Define the list of nodes in the Redis cluster
# redis_nodes = [
#     {"host": "lucifer", "port": 6379},
#     {"host": "incubus", "port": 6379},
#     {"host": "succubus", "port": 6379}
# ]

# Create a Redis cluster client using the redis-py library
# redis_cluster = redis.RedisCluster(
#     startup_nodes=redis_nodes,
#     decode_responses=True
# )

# Run some arbitrary commands on the Redis cluster
# redis_cluster.set("key1", "value1")
# redis_cluster.set("key2", "value2")
# print(redis_cluster.get("key1"))
# print(redis_cluster.get("key2"))


def my_test_function(code):
    operators = ['==', '!=', '<=', '>=', '<', '>', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '>>=', '<<=', '**=']
    operators = sorted(operators, key=len, reverse=True)  # sort by length in descending order to match longer operators first
    pattern = '|'.join(map(re.escape, operators))  # create a pattern by joining all operators with '|'
    return re.sub('({})'.format(pattern), r' \1 ', code)


def main():
    print(my_test_function("j +=1 ."))
    sys.exit(1)
    areas = {}
    # sys.exit(1)
    area_dir = "C:\\Users\\scott\\CLionProjects\\rom24-quickmud\\area"
    for filename in os.listdir(area_dir):
        if filename.endswith('.are'):
            sections, area_id = load_area(areas, os.path.join(area_dir, filename))
            rooms = load_rooms(area_id, extract_rooms(sections['ROOMS']))
            print("ROOMS: "+str(rooms))
            mobiles = extract_mobiles(sections['MOBILES'])
            load_mobiles(area_id, mobiles)
            print("MOBILES: " + str(mobiles))
            objects = extract_objects(sections['OBJECTS'])
            print("OBJECTS: "+str(objects))
            items = load_objects(objects)
            print("ITEMS: " + str(items))
            break


if __name__ == '__main__':
    main()
