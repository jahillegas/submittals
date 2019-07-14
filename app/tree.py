# coding=utf-8
import re
from lxml import html

from app.analyzer import is_similar, analyze_structure
from app.datas import *


RE_BEGIN_SECTION = \
    re.compile(r'^\s*?SECTION\s+(?P<spec>\d{2}\s*?\d{2}\s*?\d{2}(?:\.\d+)?([A-Z])?)(\s+\W+(?P<name>(.*)))?')

RE_END_SECTION = re.compile(r'^\s*([+ ]+)?\s*?END\s+OF\s+SECTION\s*?')

#RE_BEGIN_TARGET_SUBSECTION = re.compile(r'^\s*?(?P<para>\d+\.\d+)\s+?(?P<heading>SUBMITTALS)\s*?')

RE_END_TARGET_SUBSECTION = re.compile(r'^\s*?(?P<para>\d+\.\d+)\s+?')

RE_SECTION_PART = re.compile(r'^\s*?PART\s+(?P<part>\d+)[ -\u2013]*?(.*)')           # \u2013 - EN DASH or –

RE_SUB_SECTION_TYPE = re.compile(r'^\s*?(?P<point>[A-Z])\.\s+(?P<type>[^:\n]+?)(?:[:\n](\s+)?(?P<descr>.*?))?$', re.DOTALL)

RE_SUB_SECTION_DESCR = re.compile(r'[:\n]\s*')

RE_HEADER_PAGE = re.compile(r'\s+?Page\s+', re.IGNORECASE)


def is_start_section(line):
    match = RE_BEGIN_SECTION.match(line)
    if match:
        return [match.group('spec') or '', match.group('name') or '']


def is_end_section(line):
    match = RE_END_SECTION.match(line)
    if match:
        return True


def is_target_subsection(line, pattern):
    match = pattern.match(line)
    if match:
        return [match.group('para') or '', match.group('heading') or '']


def is_end_target_subsection(line):
    r = RE_END_TARGET_SUBSECTION.search(line)
    if r:
        return r.group('para') or ''

    r = RE_SECTION_PART.search(line)
    if r:
        return r.group('part') or ''


def get_section_name(line):
    return line.split('\n')[0].strip()


def is_pg_header(line, name, spec, page=0):
    if name and spec:
        pattern = r'\s*?' + re.escape(name) + r'\s+[-\u2013 \t\n\r\f\v]*?' + re.escape(spec) + r'\s+[-\u2013 \t\n\r\f\v]*?\d+'
        r = re.search(pattern, line, re.IGNORECASE)
        if r:
            return True

        if page:
            pattern = r'^\s*?\w+(\s+?\w+)*?\s+[-\u2013 \t\n\r\f\v]*?' + re.escape(spec) + r'\s+[-\u2013 \t\n\r\f\v]*?' + re.escape(str(page))
            r = re.search(pattern, line, re.IGNORECASE)
            if r:
                return True

            r = re.search(r'\s+' + re.escape(spec) + r'\s+', line)
            if r:
                r = RE_HEADER_PAGE.search(line)
                if r:
                    return True


def is_start_point(line):
    match = RE_SUB_SECTION_TYPE.match(line)
    if match:
        return [match.group('point') or '', match.group('type') or '', match.group('descr') or '']


def traversal(content, target_subsection, writer):

    def __dump():
        ok = data_exists
        if cur_section_spec and (data_exists or cur_target_subsection_descr):
            writer.write({
                F_SPEC: cur_section_spec,
                F_NAME: cur_section_name,
                F_PARA: cur_target_subsection_para + '-' +
                        cur_target_subsection_point if cur_target_subsection_point else cur_target_subsection_para,
                F_HEADING: cur_target_subsection_heading,
                F_TYPE: cur_target_subsection_type,
                F_DESCR: '\n'.join(cur_target_subsection_descr)
            })
            ok = False
        return ok

    RE_BEGIN_TARGET_SUBSECTION = re.compile(r'^\s*?(?P<para>\d+\.\d+)\s+?(?P<heading>' + target_subsection + r')\s*?')

    root = html.document_fromstring(content)
    # elements = root.xpath(".//p//..")  # all div + p
    elements = root.xpath(".//p[string-length(normalize-space(text()))>0]//..")     # div + p except empty
    print("\n\nElements: %s" % len(elements))

    print("\nAnalyzing document structure in order to recognize header...")
    headers = analyze_structure(elements)

    skip_lines = 0
    data_exists = False
    cur_section_spec = ''
    cur_section_name = ''
    cur_target_subsection_para = ''
    cur_target_subsection_heading = ''
    cur_target_subsection_point = ''
    cur_target_subsection_type = ''
    cur_target_subsection_descr = []
    cur_section_page_number = 0

    # Counters for debugging purposes
    counter_section = 0  # DEBUG
    counter_end_section = 0  # DEBUG
    counter_target = 0  # DEBUG
    counter_rows = 0  # DEBUG

    for element in elements:
        if element.tag not in ['div', 'p']:     # skip all tags except div, p
            continue
        elif element.tag == 'div':              # new page - prepare to skip next page header tags
            skip_lines = len(headers)
            cur_section_page_number += 1
            continue
        elif not element.text:                  # skip empty tags
            continue

        # split element.text by lines (\n) and process each line separately
        element_text = element.text.strip()
        if not element_text:
            continue

        lines = element_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue
            elif skip_lines:                       # skip page header
                h = headers[-skip_lines]
                skip_lines -= 1
                if h and is_similar(h, line):
                    continue
                if not is_start_section(line):
                    continue
            elif cur_section_name and cur_section_spec:
                if is_pg_header(line, cur_section_name, cur_section_spec, cur_section_page_number):
                    continue

            new_section = is_start_section(line)

            # new section ?
            if new_section:
                data_exists = __dump()
                if cur_section_spec: print("------------------------------ %s \n" % cur_section_spec)
                cur_section_spec = new_section[0].strip()
                cur_section_name = new_section[1].strip()
                cur_target_subsection_para = ''
                cur_section_page_number = 1

                counter_section += 1
                print("SECTION %s %s" % (new_section, cur_section_name), end='\n' if cur_section_name else '')  # DEBUG
                continue

            # process lines ONLY in the section
            if not cur_section_spec:
                continue

            # end of section ?
            if is_end_section(line):
                data_exists = __dump()
                if not cur_section_spec: print("------------------------------")    # DEBUG
                print("%s \t %s \n" % (line.strip(), cur_section_spec)) # DEBUG
                print("")   # DEBUG
                cur_section_spec = ''
                cur_section_name = ''
                cur_target_subsection_para = ''
                cur_target_subsection_type = ''
                cur_target_subsection_descr.clear()
                cur_section_page_number = 0

                counter_end_section += 1
                continue

            # get section name
            if not cur_section_name:
                cur_section_name = get_section_name(line)
                print("%s" % cur_section_name, end='\n')    # DEBUG
                continue

            target = is_target_subsection(line, RE_BEGIN_TARGET_SUBSECTION)
            # new target subsection ?
            if target:
                data_exists = __dump()
                cur_target_subsection_para = target[0]
                cur_target_subsection_heading = target[1]
                cur_target_subsection_point = ''
                cur_target_subsection_type = ''
                cur_target_subsection_descr.clear()
                counter_target += 1
                print("%s %s" % (cur_target_subsection_para, cur_target_subsection_heading))
                continue

            # process lines in the target subsection
            if not cur_target_subsection_para:
                continue

            # end of target subsection?
            if is_end_target_subsection(line):
                data_exists = __dump()
                cur_target_subsection_para = ''
                cur_target_subsection_heading = ''
                cur_target_subsection_point = ''
                cur_target_subsection_type = ''
                cur_target_subsection_descr.clear()
                continue

            # new point?
            new_point = is_start_point(line)
            if new_point:
                data_exists = __dump()
                counter_rows += 1  # DEBUG
                cur_target_subsection_point = new_point[0]
                cur_target_subsection_type = new_point[1]
                descr = new_point[2].strip()
                cur_target_subsection_descr.clear()
                print("%s-%s %s" % (cur_target_subsection_para, cur_target_subsection_point, cur_target_subsection_type))   # DEBUG
                if descr:
                    cur_target_subsection_descr.append(descr)
                    print("::\t%s" % cur_target_subsection_descr[0].encode('utf-8'))        # DEBUG
                data_exists = True
                continue

            if cur_target_subsection_type:
                if not cur_target_subsection_descr and not cur_target_subsection_type[-1] in '.!?:' \
                        and line[0].islower() and line[1] != '.':
                    cur_target_subsection_type = cur_target_subsection_type + '\n' + line
                else:
                    cur_target_subsection_descr.append(line)
                print("::\t%s" % line.encode('utf-8'))  # DEBUG
            else:
                descr_list = RE_SUB_SECTION_DESCR.split(line, maxsplit=1)
                if descr_list:
                    cur_target_subsection_type = descr_list[0]
                    if len(descr_list) > 1:
                        descr = descr_list[1]
                        cur_target_subsection_descr.append(descr)
                        print("::\t%s" % descr.encode('utf-8'))  # DEBUG

    print("Sections: %s"% counter_section)  # DEBUG
    print("Closed sections: %s"% counter_end_section)  # DEBUG
    print("Target subsections: %s"% counter_target)  # DEBUG
    print("CSV Rows: %s"% counter_rows)  # DEBUG


if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument('content_file', help='xhtml file')
    args = argparser.parse_args()
    print("File: %s" % args.content_file)     # DEBUG
    with open(args.content_file, 'r', encoding='utf-8') as f:
        content = f.read()
    with DataWriter(args.content_file + '.csv') as writer:
        traversal(content, 'SUBMITTALS', writer)      #  , delimiter=u';'
