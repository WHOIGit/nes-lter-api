from datetime import datetime
import re
import os

import pandas as pd


def dms_to_decimal(degrees, minutes, direction):
    decimal = float(degrees) + float(minutes) / 60.0
    if direction == 'S' or direction == 'W':
        decimal *= -1
    return decimal


def parse_hdr_file(hdr_data):
    # extract lines from hdr_data
    lines = hdr_data.splitlines()
    
    # Regular expressions for matching latitude, longitude, and time lines
    lat_pattern = r'\* NMEA Latitude = (\d{2}) (\d{2}\.\d{2}) (\w)'
    lon_pattern = r'\* NMEA Longitude = (\d{3}) (\d{2}\.\d{2}) (\w)'
    nmea_time_pattern = r'\* NMEA UTC \(Time\) = (.+)$'
    system_time_pattern = r'\* System UTC = (.+)$'

    nmea_time_iso8601 = None
    system_time_iso8601 = None
    
    for line in lines:
        # Match and extract latitude
        lat_match = re.search(lat_pattern, line)
        if lat_match:
            lat_deg, lat_min, lat_dir = lat_match.groups()
            latitude_decimal = dms_to_decimal(lat_deg, lat_min, lat_dir)
        
        # Match and extract longitude
        lon_match = re.search(lon_pattern, line)
        if lon_match:
            lon_deg, lon_min, lon_dir = lon_match.groups()
            longitude_decimal = dms_to_decimal(lon_deg, lon_min, lon_dir)
        
        # Match and extract time
        # if there is a NMEA time
        time_match = re.search(nmea_time_pattern, line)
        if time_match:
            time_str = time_match.group(1)
            time_datetime = datetime.strptime(time_str, '%b %d %Y %H:%M:%S')
            nmea_time_iso8601 = time_datetime.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'

        # if there is a system time
        time_match = re.search(system_time_pattern, line)
        if time_match:
            time_str = time_match.group(1)
            time_datetime = datetime.strptime(time_str, '%b %d %Y %H:%M:%S')
            system_time_iso8601 = time_datetime.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'

    # prefer NMEA time over system time
    if nmea_time_iso8601:
        time_iso8601 = nmea_time_iso8601
    elif system_time_iso8601:
        time_iso8601 = system_time_iso8601
    else:
        raise ValueError("No time found in HDR file")
    
    return latitude_decimal, longitude_decimal, time_iso8601


def compile_hdr_files(dir_path):
    # iterate through all hdr_files in the directory
    hdr_files = []
    for file in os.listdir(dir_path):
        if file.endswith(".hdr"):
            hdr_files.append(os.path.join(dir_path, file))
    # now parse each one and consolidate the output into a Pandas dataframe
    df = pd.DataFrame(columns=['latitude', 'longitude', 'time'])
    for file in hdr_files:
        with open(file, 'r', encoding='ISO-8859-1') as f:
            hdr_data = f.read()
        try:
            latitude, longitude, time = parse_hdr_file(hdr_data)
            row = {
                'filename': os.path.basename(file),
                'latitude': latitude,
                'longitude': longitude,
                'time': pd.to_datetime(time)
            }
            df = df.append(row, ignore_index=True)
        except Exception as e:
            print(f"Error parsing file {file}: {e}")
            row = {
                'filename': os.path.basename(file),
                'latitude': None,
                'longitude': None,
                'time': None
            }
            df = df.append(row, ignore_index=True)
    return df