# coding=utf-8
from functools import reduce

MIN_ALLOWABLE_SIMILARITY = 0.65


def analyze_structure(elements):
    """
    Analyze document structure in order to detect page header

    :param elements: document tree
    :return: list of header lines
    """

    # Convert list of elements --> list of pages. Each page - list of lines
    max_pages = 30
    min_page_lines = 5
    max_page_lines = 10
    pages = []
    page = []

    for element in elements:
        if element.tag not in ['div', 'p']:     # skip all tags except div, p
            continue
        elif element.tag == 'div':              # new page
            if len(page) >= min_page_lines:
                pages.append(page)
            page = []
            if len(pages) >= max_pages:
                break
            continue
        elif page and len(page) >= max_page_lines:
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
            page.append(line)
            if len(page) >= max_page_lines:
                break

    page = None

    # Calculate page lines similarity
    headers = []
    pages_count = len(pages)
    sims = [[[None for j in range(pages_count - 1)] for x in range(max_page_lines)] for i in range(pages_count - 1)]

    for i in range(pages_count - 1):
        page1 = pages[i]
        for j in range(i+1, pages_count):
            page2 = pages[j]
            count = min(len(page1), len(page2))
            for x in range(count):
                if len(page1[x]) >= 3 and len(page2[x]) >= 3:
                    sims[i][x][j-1] = dict(s=jaccard_similarity(page1[x], page2[x]), d1=page1[x], d2=page2[x], p1=i, p2=j)

    # Analyze similarities and store first similar lines as a header
    for i in range(pages_count - 1):
        for x in range(max_page_lines):
            total_sim = 0.0
            sim_cnt = 0
            for j in range(pages_count - 1):
                if sims[i][x][j]:
                    total_sim = total_sim + sims[i][x][j]['s']
                    sim_cnt += 1
            if sim_cnt:
                sims[i][x] = total_sim / sim_cnt
            else:
                sims[i][x] = 0

    sims = [y / pages_count for y in [sum(x) for x in zip(*sims)]]
    for i, value in enumerate(sims):
        if value >= MIN_ALLOWABLE_SIMILARITY:
            headers.append(pages[0][i])
        else:
            headers.append(None)

    return [x for n, x in enumerate(headers) if any(headers[n:])]


def jaccard_similarity(doc1, doc2):
    """
    Calculate similarity of two documents

    :param doc1:
    :param doc2:
    :return: Similarity belongs to [0,1]. Similarity 1.0 means its exact replica.
    """
    def __split(text):
        words = set()
        for w in text.split():
            if w and len(w) > 2:
                words.add(w)
        return words

    a = __split(doc1)
    b = __split(doc2)
    similarity = float(len(a.intersection(b))*1.0/len(a.union(b)))
    return similarity


def is_similar(doc1, doc2):
    return jaccard_similarity(doc1, doc2) >= MIN_ALLOWABLE_SIMILARITY
