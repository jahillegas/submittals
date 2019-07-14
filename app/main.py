# coding=utf-8
import os
from tika import parser
from app.tree import traversal, DataWriter

import sys
import string
import unicodedata

VALID_FILENAME_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)


def __slugify(text):
    """
    >>> __slugify('TEST')
    'TEST'

    >>> __slugify('TWO WORDS')
    'TWO WORDS'

    >>> __slugify('begin 1@#$%^&*()_+ end')
    'begin 1()_ end'

    """
    text = unicodedata.normalize('NFKD', text)
    if sys.version_info < (3,):
        text = text.encode('ascii', 'ignore')
    return ''.join(c for c in text if c in VALID_FILENAME_CHARS)


def extract(pdf_file, target_subsection, debug=False, no_extract=False, delimiter=','):
    print('Convert PDF to XHTML...')
    parsed = parser.from_file(pdf_file, xmlContent=True)
    content = parsed['content']

    # DEBUG: save content to file
    if debug:
        with open(pdf_file + '_content.xhtml', 'w', encoding='utf-8') as f:
            f.write(content + u"\n")
        if no_extract:
            return

    # Tree traversal
    print('Process XHTML...')
    fname, _ = os.path.splitext(pdf_file)
    fname = '{}_{}.csv'.format(fname, __slugify(target_subsection))
    with DataWriter(fname, delimiter=delimiter) as writer:
        traversal(content, target_subsection, writer)
