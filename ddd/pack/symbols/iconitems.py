'''
'''

import os

from ddd.ddd import ddd
from ddd.core import settings
import logging
import sys
import gzip

# Catalog path
# TODO: Read from setting
ICONITEM_CATALOG_ROOT_PATH = settings.DDD_DATADIR + "/vector"

# Cached catalog
ICONITEM_CATALOG = None

ICONITEM_TERM_REPLACE = {
    'combate': 'fist-raised',
    'dinoseto': 'otter',
    'memorial': 'landmark',
    'rei': 'king',
    'rey': 'king',
    'sereo': 'fish',
    'sirena': 'fish',
    'sireno': 'fish',
    'sol': 'sun',
    'guitarra': 'guitar',
    'del': None,
}


# Get instance of logger for this module
logger = logging.getLogger(__name__)



def iconitem(path, size=(1, 1), depth=0.2, bisel=None):

    item = ddd.load(path)
    item = ddd.align.anchor(item, ddd.ANCHOR_BOTTOM_CENTER)
    item = ddd.geomops.resize(item, size)

    result = ddd.group3(name="Icon Item")

    #print(piece3)
    #print(piece3.is_empty())
    #sys.exit(1)

    for piece in item.union().individualize(always=True).flatten().children:
        piece3 = None
        #piece = piece.clean(0)

        if bisel:
            piece_smaller = piece.buffer(-bisel)
            try:
                piece3 = piece_smaller.extrude_step(piece, bisel, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                piece3 = piece3.extrude_step(piece, depth - bisel * 2, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                piece3 = piece3.extrude_step(piece_smaller, bisel, method=ddd.EXTRUSION_METHOD_SUBTRACT)
            except:
                piece3 = None

        if not piece3 or piece3.is_empty() or piece3.extra['_extrusion_steps'] < 3:
            try:
                piece3 = piece.extrude(depth)
            except:
                logger.warn("Could not create iconitem for: %s", path)
                return None

        result.append(piece3)

    result = result.rotate(ddd.ROT_FLOOR_TO_FRONT)
    result = result.combine()
    result.name = "Icon Item"

    return result


def iconitem_auto(text, size=(1, 1), depth=0.2, bisel=None):
    path = iconitem_catalog_search(text)
    if not path:
        return None
    item = iconitem(path, size, depth, bisel)
    if not item:
        return None
    item.name = "Icon Item: %s" % (text)
    return item


def iconitem_catalog_list():

    global ICONITEM_CATALOG

    if ICONITEM_CATALOG:
        return ICONITEM_CATALOG

    icons = {}
    extensions = ['.svg']

    for root, dirs, files in os.walk(ICONITEM_CATALOG_ROOT_PATH):
        for name in files:

            path = str(os.path.join(root, name))
            _, extension = os.path.splitext(path)
            if extension.lower() not in extensions:
                continue

            plainname = name[:-len(extension)]
            icons[path] = [plainname] + plainname.split("-")

    ICONITEM_CATALOG = icons
    return ICONITEM_CATALOG


TRANSLATE_DICTS = {}

def dictionary_load(path):
    if path in TRANSLATE_DICTS:
        return  TRANSLATE_DICTS[path]

    f = gzip.open(path,'rb')
    file_content = f.read().decode()

    dictdata = file_content.split("\n")
    dictindex = {term: line for line, term in enumerate(dictdata)}

    TRANSLATE_DICTS[path] = (dictdata, dictindex)
    return TRANSLATE_DICTS[path]

def translate(term, dictionary_path):
    # dict -d fd-spa-eng cruz
    result = []
    term = term.lower()
    dictdata, dictindex = dictionary_load(dictionary_path)

    for t in (term, term[:-1]):
        line = dictindex.get(t, None)
        if line is not None:
            trans = dictdata[line + 1]
            if trans.startswith("1. "): trans = trans[3:]
            trans = trans.split(", ")
            result.extend(trans)

    return result


def iconitem_catalog_search(text):
    terms = [t.lower() for t in text.split()]
    catalog = iconitem_catalog_list()

    try_terms_es = []
    for term in terms:
        if len(term) < 3: continue
        if term in ICONITEM_TERM_REPLACE and ICONITEM_TERM_REPLACE[term] is None: continue
        term_translations = translate(term, "/usr/share/dictd/freedict-spa-eng.dict.dz")
        if term_translations:
            try_terms_es.extend(term_translations)
    #try_terms_fr = [translate(term, "fra", "eng") for term in temrs]

    allterms = [t for t in terms + try_terms_es if t is not None]
    #logger.info("Item text: %s  Terms: %s", text, allterms)

    for term in allterms:
        term = term.lower()
        if term in ICONITEM_TERM_REPLACE:
            term = ICONITEM_TERM_REPLACE[term]
        if term is None or len(term) <= 2:
            continue
        for icon, icon_terms in catalog.items():
            for icon_term in icon_terms:
                if term == icon_term:  # or (len(term) >= 4 and (term in icon_term)) or (len(icon_term) >= 4 and (icon_term in term)):
                    logger.debug("Selecting icon '%s' for: '%s'", icon_terms, text)
                    return icon

    return None



