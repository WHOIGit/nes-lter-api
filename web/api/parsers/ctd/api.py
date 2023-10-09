
import os

from .asc import parse_cast

class Ctd(object):
    def __init__(self, cruise, raw_dir, check_exists=True):
        self.cruise = cruise
        if check_exists:
            if not os.path.exists(raw_dir):
                raise IOError(f'cannot find directory {raw_dir}')
        self.raw_dir = raw_dir
    def cast(self, cast_number):
        return parse_cast(self.raw_dir, cast_number)
