import re
import os
import glob as glob

from io import BytesIO

import pandas as pd
import numpy as np

CRUISE_IDX = 1
CAST_IDX = 2

def parse_lat_lon(ll):
    """convert deg/dec minutes into dec"""
    REGEX = r'(\d+)[^\d]+([\d.]+)[^NSEW]*([NSEW])'
    deg, mnts, hemi = re.match(REGEX, ll).groups()
    mult = 1 if hemi in ['N', 'E'] else -1
    deg, mnts = int(deg), float(mnts)
    deg = mult * (deg + (mnts / 60))
    return deg


import io

class TextParser(object):
    def __init__(self, path=None, buffer=None, parse=True, encoding='latin-1'):
        if buffer is None:
            if not os.path.exists(path):
                raise IOError(f'cannot find file {path}')
            with open(path, 'rb') as fin:
                buffer = io.BytesIO(fin.read())
        self.data = buffer
        self.encoding = encoding
        if parse:
            self.parse()

    def parse(self):
        lines = []
        with io.TextIOWrapper(self.data, encoding=self.encoding) as fin:
            for line in fin.readlines():
                lines.append(line.rstrip())
        self._lines = lines

    def _lines_that_match(self, regex):
        for line in self._lines:
            if re.match(regex, line):
                yield line

    def _line_that_matches(self, regex):
        for line in self._lines_that_match(regex):
            return line

class CtdTextParser(TextParser):
    """parent class of BtlFile and HdrFile"""
    def __init__(self, **kw):
        super(CtdTextParser, self).__init__(**kw)
    def parse(self):
        super(CtdTextParser, self).parse()
        self._parse_time()
        self._parse_lat_lon()
    def _parse_time(self):
        line = self._line_that_matches(r'\* NMEA UTC \(Time\)')
        line2 = self._line_that_matches(r'\* System UTC')
        if line is None:
            line = line2
        if line is None:
            self.time = pd.NaT
            return
        time = re.match(r'.*= (.*)', line).group(1)
        self.time = pd.to_datetime(time, utc=True)
    def _parse_lat_lon(self):
        lat_line = self._line_that_matches(r'\* NMEA Latitude')
        lon_line = self._line_that_matches(r'\* NMEA Longitude')
        split_regex = r'.*itude = (.*)'
        if lat_line is not None:
            self.lat = parse_lat_lon(re.match(split_regex, lat_line).group(1))
        else:
            self.lat = np.nan
        if lon_line is not None:
            self.lon = parse_lat_lon(re.match(split_regex, lon_line).group(1))
        else:
            self.lon = np.nan
