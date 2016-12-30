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
from datetime import date
from operator import attrgetter

__author__ = 'Shayan Sayahi'


# workspace = '/Users/Synix/Google Drive/Android/DriveSync/'
workspace = '/Users/Synix/Google Drive/Android/DriveSync/'

'''
Params:
    regex:
    format:
    parser:
    standardize:
'''
FormatRule = namedtuple('FormatRule', ['regex', 'format', 'parser', 'standardize'])
FormatRule.__new__.__defaults__ = (datetime.strptime, lambda x: x)  # last two arguments are optional

def dashifier(string): return re.sub(r'[_. :]', '-', string)

def parse_epoch(string, format='redundant'):
    epoch = int(string)
    if len(string) == 13:
        epoch /= 1000
    timestamp = datetime.fromtimestamp(epoch)
    this_year = date.today().year
    if not 1992 <= timestamp.year <= this_year + 1:  # my birth year :P
        raise ValueError('Epoch year out of expected range')
    return timestamp

DEFAULT_RULES = [
    FormatRule(r'(?<!\d)\d{8}[-_]\d{6}(?!\d)',         '%Y%m%d-%H%M%S',     standardize=dashifier),  # 20131117_145104
    FormatRule(r'(?<!\d)\d{4}([-_. :]\d{2}){5}(?!\d)', '%Y-%m-%d-%H-%M-%S', standardize=dashifier),  # 2013-11-17-14-51-04, 2013-11-17_14:51:04
    FormatRule(r'(?<!\d)\d{10}(\d{3})?(?!\d)',         '',                  parser=parse_epoch),     # 1479620366114 epoch ms, 1479620366 epoch sec
]


def eprint(obj): print(obj, file=sys.stderr)

def do(iterable):
    for _ in iterable: pass


def get_pictures(root_directory):
    '''
    Returns a generator which yields pairs of path + image filename, where os.path.join(path, image_name)
    would specify the full path to the image.

    jpg, png, and gif files are considered.
    '''
    formats = ['jpeg', 'gif', 'png']
    for basepath, folders, files in os.walk(root_directory):
        yield from ((basepath, f) for f in files if imghdr.what(os.path.join(basepath, f)) in formats)
        for folder in folders:
            yield from get_pictures(folder)


def parse_dates(files, rules=DEFAULT_RULES):
    '''
    Find the first rule that matches a timestamp in the file name, standardize the
    extracted timestamp, and parse it with the supplied parser and format of rule.
    If any of these steps fails, it moves on to the next rule.

    Args:
        files: list of (basedir, filename)
        rules: list of FormatRules, otherwise my default rules
    Returns:
        (successes, failures) where:
            successes: list of (file, timestamp): ((basedir, filename), datetime)
            failures: list of (file, [Exceptions])
    '''
    failed, success = [], []
    for file in files:
        filename = file[1]
        exceptions = []
        for rule in rules:
            try:
                timestamp = re.search(rule.regex, filename)
                if timestamp is None:
                    exceptions.append(ValueError('Timestamp pattern not found'))
                    continue
                timestamp = timestamp.group()
                timestamp = rule.parser(rule.standardize(timestamp), rule.format)
                success.append((file, timestamp))
                break
            except Exception as e:
                exceptions.append(e)
        failed.append((file, exceptions))
        # import pdb; pdb.set_trace()
    return success, failed


def write_metadata(filenames):
    # TODO: don't overwrite pre-existing metadata
    do(print, filenames)


def filename_to_metadata(workspace):
    pictures = get_pictures(workspace)
    parsed_filenames, failed = parse_dates(pictures)
    do(map(print, parsed_filenames))
    do(map(print, failed))
    return
    do(map(eprint, failed))

    modified, failed = write_metadata(parsed_filenames)
    do(map(eprint, failed))


if __name__ == '__main__':
    filename_to_metadata(workspace)
