#!/usr/bin/env python3
"""
blah
"""

import imghdr
import os
import sys
import re
from collections import namedtuple
from datetime import datetime
from operator import attrgetter

__author__ = 'Shayan Sayahi'


# workspace = '/Users/Synix/Google Drive/Android/DriveSync/'
workspace = '/Users/Synix/Google Drive/Android/DriveSync/'

FormatRule = namedtuple('FormatRule', ['regex', 'format', 'rank'])
FormatRule.__new__.__defaults__ = (0,)  # last argument is optional

DEFAULT_RULES = [
    FormatRule(r'\d{8}[-_]\d{6}',        '%Y%m%d_%H%M%S',      10),  # 20131117_145104
    FormatRule(r'\d{4}([-_]\d{2}){5}',   '%Y-%m-%d-%H-%M-%S',  20),  # 2013-11-17-14-51-04
    FormatRule(r'(\d+[- ]){3}(\d+.){3}', '%Y-%m-%d %H.%M.%S.', 30),  # 2013-11-17 14.51.04.
]

def eprint(obj): print(obj, file=sys.stderr)

def do(iterable): for _ in iterable: pass


def get_pictures(root_directory):
    '''
    Returns a generator which yields pairs of path + image filename, where os.path.join(path, image_name)
    would specify the full path to the image.

    jpg, png, and gif files are considered.
    '''
    for basepath, folders, files in os.walk(root_directory):
        yield from ((basepath, file) for file in files if file.split('.')[-1] in ['jpeg', 'gif', 'png'])
        for folder in folders:
            yield from get_pictures(folder)


def detect_format(files, rules=DEFAULT_RULES):
    rules.sort(key=attrgetter('rank'))
    skipped, success = [], []

    def _apply_rule(rule, file):
        filename = file[1]
        try:
            timestamp = re.search(rule.regex, filename).group()
            if timestamp is None:
                skipped.append((file, ValueError('Timestamp pattern not found')))
            timestamp = datetime.strptime(timestamp, rule.format)
            success.append((file, timestamp))
        except Exception as e:
            skipped.append((file, e))

    do(_apply_rule(rule, file) for file in files for rule in rules)
    return success, skipped


def write_metadata(filenames):
    do(print, filenames)


def filename_to_metadata(workspace):
    pictures = get_pictures(workspace)
    parsed_filenames, failed = parse_dates(pictures)
    do(map(eprint, failed))

    modified, failed = write_metadata(parsed_filenames)
    do(map(eprint, failed))


if __name__ == '__main__':
    # datetime.strptime
    pictures = get_pictures(workspace)
    print(list(pictures))
    print(detect_format(pictures))
