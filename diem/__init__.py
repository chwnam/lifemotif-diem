from os.path import isabs as path_isabs
from os import getcwd
from os.path import expanduser, realpath, join as path_join

DIEM_VERSION = '1.4.0'


def get_absolute_path(path):
    if path_isabs(path):
        abs_dir = realpath(path)
    else:
        abs_dir = realpath(expanduser(path_join(getcwd(), path)))

    return abs_dir
