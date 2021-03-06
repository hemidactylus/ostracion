""" treeTools.py
    Tools to handle generation of directory trees
    by browsing the Ostracion file system.
"""

import urllib.parse

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries
)

from ostracion_app.utilities.viewTools.pathTools import (
    isFileViewable,
)

from ostracion_app.utilities.database.fileSystem import (
    getBoxesFromParent,
    getFilesFromBox,
    getLinksFromBox,
)


def _collectTreeContentsFromBox(db, parentBox, user, admitFiles,
                                collectedPath, depth, fileOrBoxEnricher,
                                predicate):
    """ Browse a box and prepare a structure describing
        what was found in it, subject to limitations and enrichments.
    """
    if admitFiles:
        files = [
            recursivelyMergeDictionaries(
                fileOrBoxEnricher(fileRichMap),
                defaultMap=fileRichMap,
            )
            for fileRichMap in (
                {
                    'viewable': isFileViewable(file),
                    'file': file,
                }
                for file in sorted(
                    getFilesFromBox(db, parentBox),
                    key=lambda fl: fl.name,
                )
            )
            if predicate(fileRichMap)
        ]
        links = [
            recursivelyMergeDictionaries(
                fileOrBoxEnricher(linkRichMap),
                defaultMap=linkRichMap,
            )
            for linkRichMap in (
                {
                    'link': link,
                }
                for link in sorted(
                    getLinksFromBox(db, parentBox),
                    key=lambda li: li.name,
                )
            )
            if predicate(linkRichMap)
        ]
    else:
        files = []
        links = []
    #
    return {
        'files': files,
        'links': links,
        'boxes': [
            recursivelyMergeDictionaries(
                fileOrBoxEnricher(boxPredicatedRichMap),
                defaultMap=boxPredicatedRichMap,
            )
            for boxPredicatedRichMap in (
                recursivelyMergeDictionaries(
                    {
                        'predicate': predicate(boxRichMap),
                        'has_predicated_children': any(
                            c['has_predicated_children']
                            for c in boxRichMap['contents']['boxes']
                        ) or predicate(boxRichMap),
                    },
                    defaultMap=boxRichMap,
                )
                for boxRichMap in (
                    {
                        'path': collectedPath + [box.box_name],
                        'box': box,
                        'contents': _collectTreeContentsFromBox(
                            db,
                            box,
                            user,
                            admitFiles,
                            collectedPath + [box.box_name],
                            depth + 1,
                            fileOrBoxEnricher=fileOrBoxEnricher,
                            predicate=predicate,
                        ),
                        'depth': depth + 1,
                        'obj_path': urllib.parse.quote_plus(
                            '/'.join(collectedPath + [box.box_name])
                        ),
                    }
                    for box in sorted(
                        getBoxesFromParent(db, parentBox, user),
                        key=lambda bx: bx.box_name if bx is not None else '',
                    )
                    if box is not None
                    if box.box_id != ''
                )
            )
            if boxPredicatedRichMap['has_predicated_children']
        ],
    }


def collectTreeFromBox(db, parentBox, user, admitFiles, collectedPath=[],
                       depth=0, fileOrBoxEnricher=lambda richFileOrBox: {},
                       predicate=lambda richFileOrBox: True):
    """Start from a box and collect the whole sub-tree contained therein."""
    bareTree = {
        'box': parentBox,
        'contents': _collectTreeContentsFromBox(
            db=db,
            parentBox=parentBox,
            user=user,
            admitFiles=admitFiles,
            collectedPath=collectedPath,
            depth=depth,
            fileOrBoxEnricher=fileOrBoxEnricher,
            predicate=predicate,
        ),
        'path': [],
        'obj_path': urllib.parse.quote_plus(''),
        'depth': 0,
    }
    return recursivelyMergeDictionaries(
        {
            'predicate': predicate(bareTree),
            'has_predicated_children': any(
                c['has_predicated_children']
                for c in bareTree['contents']['boxes']
            )
        },
        defaultMap=bareTree,
    )


def getMaxTreeDepth(tTree, d=0):
    """Calculate the depth of a tree at its deepest leaf."""
    if len(tTree['contents']['boxes']) > 0:
        return max([
            d,
            max(
                getMaxTreeDepth(b, d)
                for b in tTree['contents']['boxes']
            ),
        ])
    else:
        return max([tTree['depth'], d])


def treeAny(tTree, property):
    """Is there at least an item in the tree satisfying 'property'?"""
    return (property(tTree) or
            any(
                treeAny(c, property)
                for c in tTree.get('contents', {}).get('files', [])
            ) or
            any(
                treeAny(c, property)
                for c in tTree.get('contents', {}).get('boxes', [])
            ))


def treeSum(f, tTree):
    """
        Accumulate values over all items in a tree (branches, leaves).

        f must accept a (type, item) and return a value for summing
        type = 'box', 'file', ... (a string)
        item is an istance of Box, File, ...
    """
    contributions = [
        f(tTree['box'], 'box')
    ] + [
        f(contFile, 'file')
        for contFile in tTree['contents']['files']
    ] + [
        f(contLink, 'link')
        for contLink in tTree['contents']['links']
    ] + [
        treeSum(f, contBox)
        for contBox in tTree['contents']['boxes']
    ]
    #
    return sum(contributions)


def treeSize(tTree):
    """
        Given a tree, approximate the overall size of items contained
        therein. This still does a rough estimate on links, with a fixed
        number of bytes.
    """
    def itemSizer(itm, tp):
        if tp == 'box':
            return 0
        elif tp == 'file':
            return itm['file'].size
        elif tp == 'link':
            return 50
        else:
            raise NotImplementedError('unknown object type in tree [%s]' % tp)
    #
    return treeSum(itemSizer, tTree)
