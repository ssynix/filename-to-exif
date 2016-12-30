#!/usr/bin/env python3
"""
blah
"""

import os
import re
import sys
import imghdr
import argparse
import exiftool
import dateutil.parser
from collections import namedtuple
from operator import attrgetter, itemgetter
from datetime import date, datetime, timedelta

__author__ = 'Shayan Sayahi'


'''
Params:
    regex: the timestamp pattern to find in a file's name
    format: the format string to use with the parser to parse the matched timestamp
    parser: the parse to use (defaults to datetime.strptime)
    standardize: any string transformation before passing the match to the parser (defaults to identity)
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


def eprint(*obj): print(*obj, file=sys.stderr)

def do(iterable):  # I mainly use it to simplify for loops with a single function call
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
                    raise ValueError('Timestamp pattern not found')
                timestamp = timestamp.group()
                timestamp = rule.parser(rule.standardize(timestamp), rule.format)
                success.append((file, timestamp))
                exceptions = []
                break
            except Exception as e:
                exceptions.append(e)
        if len(exceptions) != 0:
            failed.append((file, exceptions))
    return success, failed


def write_metadata(timestamped_files, args):
    '''
    Seems like Google Photos parses EXIF:DateTimeOriginal regardless of whether
    that's standard for a file type. Easier for us! We just have to go over each file
    and write its timestamp to its EXIF date if it doesn't already have one.

    Args:
        files: list of ((basepath, filename), timestamp)
    Returns:
        (failed, skipped) where:
            failed: list of (filepath, exception)
            skipped: list of (filepath, reason)
    Throws:
        Exceptions if ExifTool runs into a problem
    '''
    workspace, delete_originals, adb_root = args.workspace, args.delete_originals, args.adb_root

    filepaths_to_times = {os.path.join(*file): timestamp for file, timestamp in timestamped_files}
    filepaths = (os.path.join(*file) for file in map(itemgetter(0), timestamped_files))
    with exiftool.ExifTool() as et:
        date_tags = ['EXIF:DateTimeOriginal', 'TIFF:DateTime', 'IPTC:DateCreated']  # Common ones
        metadata = et.get_tags_batch(date_tags, filepaths)

    # The result is a list of dicts where each dict contains the requested tags (if available) and the filepath.
    # We'd like to filter out the files that already have valid metadata
    def _valid_metadata(json):
        '''Ensure the metadata is within ±2 days of our parsed timestamp'''
        # return False
        parsed_date = filepaths_to_times[json['SourceFile']]
        tags = filter(lambda x: x != 'SourceFile', json.keys())
        for date_tag in tags:
            try:
                meta_date = datetime.strptime(json[date_tag], '%Y:%m:%d %H:%M:%S')
            except:
                try:
                    meta_date = dateutil.parser.parse(json[date_tag])
                except Exception as e:
                    eprint('Ignoring: ', e)
                    continue
            if timedelta(days=-2) < meta_date - parsed_date < timedelta(days=2):
                return True

        eprint('Metadata will be overriden as:', parsed_date, json)
        return False


    blank_date_filepaths, skipped = [], []
    for json in metadata:
        preexisting_meta = len(json) > 1 and _valid_metadata(json)
        exiftools_backup = json['SourceFile'].endswith('original')
        if exiftools_backup:
            skipped.append((json, 'Created as backup by exiftools'))
        elif preexisting_meta:
            skipped.append((json, 'Metadata already exists'))
        else:
            blank_date_filepaths.append(json['SourceFile'])

    failed = []
    with exiftool.ExifTool() as et, open('adb.log', 'w') as adb_log:
        for filepath in blank_date_filepaths:
            timestamp = filepaths_to_times[filepath]
            if adb_root is not None:
                print('touch -amd "{}" "{}"'.format(
                    timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
                    os.path.join(adb_root, os.path.relpath(filepath, workspace))),
                    file=adb_log
                )
            params = ('-EXIF:DateTimeOriginal=' + timestamp.strftime('%Y:%m:%d %H:%M:%S'),
                      '-FileModifyDate=' + datetime.now().strftime('%Y:%m:%d %H:%M:%S'),  # to trigger Google Drive sync
                      filepath)
            if delete_originals:
                params += ('-overwrite_original_in_place',)
            try:
                result = et.execute(*map(str.encode, params))  # execute expects parameters in bytes
                if not re.search(r'1.*(updated|unchanged)', result.decode()):
                    raise RuntimeError(result)
            except Exception as e:
                failed.append((filepath, e))

    return failed, skipped


def filename_to_metadata(args):
    print('Grabbing list of all available images...')
    pictures = get_pictures(args.workspace)

    print('Parsing timestamps out of filenames...')
    timestamped_files, failed = parse_dates(pictures)
    do(map(eprint, failed))

    print('Writing missing metadata to images...')
    try:
        failed, skipped = write_metadata(timestamped_files, args)
        do(eprint('Skipped writing metadata:', *file) for file in skipped)
        do(map(eprint, failed))
    except Exception as e:
        eprint('Unexpected error while writing metadata:', e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Filename-to-EXIF')
    parser.add_argument('-w', '--workspace', metavar='<IMAGE_DIR>', required=True,
                        help='path to image directory')

    parser.add_argument('--delete-originals', action='store_true',
                        help='''edit files in place (trying to preserve create dates, and avoiding the
                                creation of '*_original' files. Make sure you have a backup of all files.''')

    parser.add_argument('--adb-root', metavar='<DEVICE_DIR>')

    args = parser.parse_args()
    filename_to_metadata(args)
