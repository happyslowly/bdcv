#!/usr/bin/env python

import sys
import json
import urllib.request
import os.path
import pickle
import zlib
import argparse
import re

__version__ = '0.1.0'


class BingDictClient(object):
    URL = 'http://xtk.azurewebsites.net/BingDictService.aspx?Word='
    CACHE_FILE = os.path.join(os.path.expanduser("~"), '.bdcv')
    COLOR = {
        'cyan': '\033[96m',
        'purple': '\033[95m',
        'yellow': '\033[93m',
        'end': '\033[0m'
    }

    def __init__(self):
        self.__cache = BingDictClient.load_cache()

    @staticmethod
    def load_cache():
        if not os.path.exists(BingDictClient.CACHE_FILE):
            return {}
        with open(BingDictClient.CACHE_FILE, 'rb') as fin:
            return pickle.load(fin)

    def write_cache(self):
        with open(BingDictClient.CACHE_FILE, 'wb') as fout:
            pickle.dump(self.__cache, fout)

    def lookup(self, word, long, nocolor):
        if word not in self.__cache:
            full_url = BingDictClient.URL + word
            res = urllib.request.urlopen(full_url)
            raw_json = res.read()
            self.__cache[word] = zlib.compress(raw_json)
            self.write_cache()
        else:
            raw_json = zlib.decompress(self.__cache[word])
        return BingDictClient.__render(raw_json, long, nocolor)

    @staticmethod
    def __format_text(text, color_name, prefix=''):
        return (BingDictClient.COLOR[color_name] if color_name else '') + prefix + text + \
               (BingDictClient.COLOR['end'] if color_name else '')

    @staticmethod
    def __format_entry(text, nocolor):
        return BingDictClient.__format_text(text, None if nocolor else 'cyan', '* ')

    @staticmethod
    def __format_chinese(text, nocolor):
        return BingDictClient.__format_text(text, None if nocolor else 'purple')

    @staticmethod
    def __format_english_sample(text, word, nocolor):
        words = text.split()
        sentence = []
        for w in words:
            m = re.search(word, w, re.IGNORECASE)
            if m:
                sentence.append(BingDictClient.__format_text(w[m.start():m.end()], None if nocolor else 'yellow') +
                                w[m.end():])
            else:
                sentence.append(w)
        return ' '.join(sentence)

    @staticmethod
    def __render(raw_json, long, nocolor):
        data = json.loads(raw_json)
        word = data['word']

        print(BingDictClient.__format_entry('Pronunciation', nocolor))
        for k, p in data['pronunciation'].items():
            if not k.endswith('mp3'):
                print('    %s. [%s]' % (k, p))

        print(BingDictClient.__format_entry('Definition', nocolor))
        for d in data['defs']:
            if d['pos'] == 'Web':
                continue
            print('    %s %s' % (d['pos'], BingDictClient.__format_chinese(d['def'], nocolor)))

        if long:
            print(BingDictClient.__format_entry('Samples', nocolor))
            for s in data['sams']:
                print('  - %s' % BingDictClient.__format_english_sample(s['eng'], word, nocolor))
                print('    %s' % BingDictClient.__format_chinese(s['chn'], nocolor))


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--long', help='print full explanations', action='store_true')
    parser.add_argument('--nocolor', help='print without color', action='store_true')
    parser.add_argument('word', help='the word to lookup')
    return parser


if __name__ == '__main__':
    parser = get_parser()
    options = parser.parse_args()

    if not options.word:
        parser.print_help(sys.stderr)
        sys.exit(1)

    client = BingDictClient()
    client.lookup(options.word.lower(), options.long, options.nocolor)
