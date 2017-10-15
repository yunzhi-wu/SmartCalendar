
debug_level_info = 1
debug_level_verbose = 2
debug_level_debug = 3

debug_level = debug_level_debug


def print_level(level, *argv):
    global debug_level
    if level <= debug_level:
        print(*argv)