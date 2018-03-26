#!/usr/bin/env python

import sys
import json
import urllib.request
import os.path
import pickle
import zlib
import argparse
import re
from urllib.parse import urlencode

__version__ = '0.1.0'


class BingDictClient(object):
    URL = 'http://xtk.azurewebsites.net/BingDictService.aspx?'
    CACHE_FILE = os.path.join(os.path.expanduser("~"), '.bdcv')
    COLOR = {
        'cyan': '\033[96m',
        'purple': '\033[95m',
        'yellow': '\033[93m',
        'end': '\033[0m'
    }

    def __init__(self, lang, long, color):
        self.lang = lang
        self.long = long
        self.color = True if color == 'on' else False
        self.__cache = BingDictClient.__load_cache()

    def lookup(self, word):
        if word not in self.__cache:
            param = {'Word': word}
            full_url = BingDictClient.URL + urlencode(param)
            res = urllib.request.urlopen(full_url)
            raw_json = res.read()
            self.__cache[word] = zlib.compress(raw_json)
            self.__write_cache()
        else:
            raw_json = zlib.decompress(self.__cache[word])
        return self.__render(raw_json)

    def __render(self, raw_json):
        data = json.loads(raw_json)
        word = data['word']

        if data['pronunciation']:
            print(self.__format_entry('Pronunciation'))
            for k, p in data['pronunciation'].items():
                if not k.endswith('mp3'):
                    print('    %s. [%s]' % (k, p))

        if data['defs']:
            print(self.__format_entry('Definition'))
            for d in data['defs']:
                if d['pos'] == 'Web':
                    continue
                print('    %s %s' % (d['pos'], self.__format_explanation(d['def'])))

        if self.long:
            if data['sams']:
                print(self.__format_entry('Samples'))
                for s in data['sams']:
                    print('  - %s' % self.__format_sample(s['eng'] if self.lang == 'eng'
                                                          else self.__format_explanation(s['eng']), word))
                    print('    %s' % self.__format_sample(s['chn'] if self.lang == 'chn'
                                                          else self.__format_explanation(s['chn']), word))

    @staticmethod
    def __load_cache():
        if not os.path.exists(BingDictClient.CACHE_FILE):
            return {}
        with open(BingDictClient.CACHE_FILE, 'rb') as fin:
            return pickle.load(fin)

    def __write_cache(self):
        with open(BingDictClient.CACHE_FILE, 'wb') as fout:
            pickle.dump(self.__cache, fout)

    @staticmethod
    def __format_text(text, color_name, prefix=''):
        return (BingDictClient.COLOR[color_name] if color_name else '') + prefix + text + \
               (BingDictClient.COLOR['end'] if color_name else '')

    def __format_entry(self, text):
        return BingDictClient.__format_text(text, 'cyan' if self.color else None, '* ')

    def __format_explanation(self, text):
        return BingDictClient.__format_text(text, 'purple' if self.color else None)

    def __format_sample(self, text, word):
        m = re.search(word, text, re.IGNORECASE)
        if m:
            return text[0:m.start()] + \
                   BingDictClient.__format_text(text[m.start():m.end()], 'yellow' if self.color else None) + \
                   text[m.end():]
        else:
            return text


def detect_lang(word):
    for c in word:
        if ord(c) > 127:
            return 'chn'
    return 'eng'


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--long', help='print full explanations', action='store_true')
    parser.add_argument('--color', choices=['on', 'off'], default='on', help='print without color, default on')
    parser.add_argument('word', help='the word to lookup')
    return parser


if __name__ == '__main__':
    parser = get_parser()
    options = parser.parse_args()

    if not options.word:
        parser.print_help(sys.stderr)
        sys.exit(1)

    client = BingDictClient(detect_lang(options.word), options.long, options.color)
    client.lookup(options.word.lower())
