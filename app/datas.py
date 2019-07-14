# coding=utf-8
import csv


F_SPEC = 'Spec Section'
F_NAME = 'Spec Name'
F_PARA = 'Sub Section Para'
F_HEADING = 'Sub Section Heading'
F_TYPE = 'Sub Section Type'
F_DESCR = 'Sub Section Description'


class DataWriter (object):
    def __init__(self, filename, **kwargs):
        self.fd = open(filename, 'w', newline='', encoding='utf-8')
        field_names = [F_SPEC, F_NAME, F_PARA, F_HEADING, F_TYPE, F_DESCR]
        self.writer = csv.DictWriter(self.fd, fieldnames=field_names, dialect='excel', **kwargs)
        self.writer.writeheader()

    def write(self, row):
        print("dump")           # DEBUG
        self.writer.writerow(row)

    def close(self):
        self.fd.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()
