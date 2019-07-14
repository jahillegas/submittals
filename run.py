# coding=utf-8


if __name__ == '__main__':
    from app.main import extract
    import argparse

    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument('pdf_file', help='pdf file')
    argparser.add_argument('--save-xhtml', help='save xhtml file for debugging purposes', action='store_true')
    argparser.add_argument('--no-extract', help='should be used with --save-xhtml', action='store_true')
    group = argparser.add_mutually_exclusive_group()
    group.add_argument('-t', '--target', help='name of the target subsection that will be extracted',
                           metavar='SUBSECTION', dest='target', default='SUBMITTALS')
    group.add_argument('-T', '--target-pattern', help='regex pattern of the target subsection that will be extracted',
                           metavar='PATTERN', dest='target_pattern', default=None)
    argparser.add_argument('-d', '--delimiter', help='CSV fields delimiter character', type=str, default=',',
                           metavar='CHAR')

    args = argparser.parse_args()

    if args.target_pattern:
        pattern = args.target_pattern
    else:
        import re
        pattern = re.escape(args.target)

    extract(args.pdf_file, pattern, args.save_xhtml, args.no_extract, args.delimiter)

    print('Done.')
