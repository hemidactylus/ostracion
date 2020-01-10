""" findTools.py
    Tools which make use of findEngines.py and offer to the caller
    an unified interface for performing DB searches for files/boxes.
"""

from ostracion_app.utilities.database.sqliteEngine import (
    dbRetrieveRecordByKey,
)

from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)

from ostracion_app.utilities.database.fileSystem import (
    getBoxFromPath,
    getFileFromParent,
    getLinkFromParent,
)

from ostracion_app.utilities.tools.formatting import (
    formatBytesSize,
)

from ostracion_app.utilities.viewTools.pathTools import (
    isFileViewable,
    prepareBoxActions,
    prepareFileActions,
    prepareLinkActions,
    prepareFileInfo,
    prepareLinkInfo,
    prepareBoxInfo,
    describePathAsNiceString,
)

from ostracion_app.utilities.database.findEngines import (
    sqliteLikeSubstringSearch,
    explicitLoopSubstringSearch,
    explicitLoopSimilaritySearch,
)

# used by _searchResultSorterKey
_sortPriorityByObjectTypeMap = {
    'file': 1,
    'box': 2,
}


def fsFind(db, searchTerm, user, options={}):
    """ Perform a fs search and return an  object
        fully describing the results

        Options is a map with the following possible keys
            options={
                'mode':     'sub_cs'/'sub_ci'/sim_ci'    DEF 'sub_cs',
                    ( = substring/similarity, case in/sensitive)
                'searchBoxes':      BOOL        DEF True,
                'searchFiles':      BOOL        DEF True,
                'useDescription':   BOOL        DEF False,
            }
    """

    searchMode = options.get('mode', 'sub_cs')
    searchSimilarity = searchMode == 'sim_ci'
    if searchSimilarity:
        fEngineResults = explicitLoopSimilaritySearch(
            db,
            searchTerm=searchTerm,
            searchBoxes=options.get('searchBoxes', True),
            searchFiles=options.get('searchFiles', True),
            searchLinks=options.get('searchLinks', True),
            useDescription=options.get('useDescription', False),
        )
    else:
        caseSensitive = searchMode == 'sub_cs'
        fEngineResults = explicitLoopSubstringSearch(
            db,
            searchTerm=searchTerm,
            searchBoxes=options.get('searchBoxes', True),
            searchFiles=options.get('searchFiles', True),
            searchLinks=options.get('searchLinks', True),
            caseSensitive=caseSensitive,
            useDescription=options.get('useDescription', False),
        )
    # This is how one would to to use the search engine based on
    # sqlite's native "like" operator:
    # (fast but limited. Perhaps to be re-enabled in the future?)
    # fEngineResults=sqliteLikeSubstringSearch(
    #     db,
    #     searchTerm=searchTerm,
    #     searchBoxes=options.get('searchBoxes',True),
    #     searchFiles=options.get('searchFiles',True),
    #     searchLinks=options.get('searchLinks', True),
    # )

    # we re-marshal the found items with a common enrich/equip/sort logic
    foundFiles = [
        fi
        for fi in (
            _resolveUponPermissions(
                db,
                _reduceFileToPath(db, fs['item']),
                user,
                'file',
                fs['score'],
            )
            for fs in fEngineResults['files']
        )
        if fi is not None
    ]
    foundBoxes = [
        bo
        for bo in (
            _resolveUponPermissions(
                db,
                _reduceBoxToPath(db, bs['item']),
                user,
                'box',
                bs['score'],
            )
            for bs in fEngineResults['boxes']
        )
        if bo is not None
    ]
    foundLinks = [
        li
        for li in (
            _resolveUponPermissions(
                db,
                _reduceLinkToPath(db, ls['item']),
                user,
                'link',
                ls['score'],
            )
            for ls in fEngineResults['links']
        )
        if li is not None
    ]
    foundItems = sorted(
        foundFiles + foundBoxes + foundLinks,
        key=_searchResultSorterKey,
    )
    return {
        'counts': {
            'files': len(foundFiles),
            'boxes': len(foundBoxes),
            'links': len(foundLinks),
        },
        'results': foundItems,
        'message': fEngineResults.get('message'),
    }


def _searchResultSorterKey(fItem):
    """ Give a triple used to sort search result, regardless of
        search mode and details."""
    if fItem['object_type'] == 'box':
        lowerTitle = fItem['box'].title
    elif fItem['object_type'] == 'file':
        lowerTitle = fItem['file'].name.lower()
    elif fItem['object_type'] == 'link':
        lowerTitle = fItem['link'].name.lower()
    else:
        raise NotImplementedError('unknown object_type')
    #
    return (
        -fItem['score'],
        lowerTitle,
        -_sortPriorityByObjectTypeMap.get(fItem['object_type'], 0),
    )


def _resolveUponPermissions(db, richObject, user, mode, score):
    """ Verify and validate the input (rich-)box/file
        against permissions, and return either a similar structure
        or a None if permissions turn out to be blocking.

        (
            richObject has keys "path" and "box/file",
            mode = 'file' / 'box'
        )
    """
    pBox = getBoxFromPath(db, richObject['path'][:-1], user)
    if mode == 'box':
        nBox = getBoxFromPath(db, richObject['path'], user)
        if nBox is not None and pBox is not None:
            return {
                'path': richObject['path'][1:],
                'box': nBox,
                'actions': prepareBoxActions(
                    db, nBox, richObject['path'][1:],
                    pBox, user, prepareParentButton=True),
                'info': prepareBoxInfo(db, nBox),
                'parentInfo': 'Parent box: "%s"' % (
                    describePathAsNiceString(richObject['path'][1:-1])
                ),
                'object_type': mode,
                'score': score,
            }
        else:
            return None
    elif mode == 'file':
        if pBox is not None:
            nFile = getFileFromParent(db, pBox, richObject['path'][-1], user)
            if nFile is not None:
                return {
                    'path': richObject['path'][1:],
                    'file': nFile,
                    'actions': prepareFileActions(
                        db, nFile, richObject['path'][1:],
                        pBox, user, prepareParentButton=True),
                    'info': prepareFileInfo(db, nFile),
                    'nice_size': formatBytesSize(nFile.size),
                    'parentInfo': 'Container box: "%s"' % (
                        describePathAsNiceString(richObject['path'][1:-1])
                    ),
                    'object_type': mode,
                    'score': score,
                }
            else:
                return None
        else:
            return None
    elif mode == 'link':
        if pBox is not None:
            nLink = getLinkFromParent(db, pBox, richObject['path'][-1], user)
            if nLink is not None:
                return {
                    'path': richObject['path'][1:],
                    'link': nLink,
                    'actions': prepareLinkActions(
                        db, nLink, richObject['path'][1:],
                        pBox, user, prepareParentButton=True),
                    'info': prepareLinkInfo(db, nLink),
                    'parentInfo': 'Container box: "%s"' % (
                        describePathAsNiceString(richObject['path'][1:-1])
                    ),
                    'object_type': mode,
                    'score': score,
                }
            else:
                return None
        else:
            return None
    else:
        raise NotImplementedError(
            'Unknown _resolveUponPermissions mode "%s"' % mode
        )


def _retraceBoxPath(db, boxId, builtPath=[]):
    """ From a box ID rebuild the corresponding
        path (by retracing the parent boxes all the way up to root.
        The id of the box itself is included in the result.
    """
    if boxId == '':
        return [''] + builtPath
    else:
        thisBox = dbRetrieveRecordByKey(
            db, 'boxes', {'box_id': boxId},
            dbTablesDesc=dbSchema)
        return _retraceBoxPath(
            db,
            thisBox['parent_id'],
            [thisBox['box_name']] + builtPath,
        )


def _reduceFileToPath(db, file):
    """ Given a file, calculate its full path and return it in a dict."""
    return {
        'path': _retraceBoxPath(db, file.box_id) + [file.name],
    }


def _reduceLinkToPath(db, link):
    """ Given a link, calculate its full path and return it in a dict."""
    return {
        'path': _retraceBoxPath(db, link.box_id) + [link.name],
    }


def _reduceBoxToPath(db, box):
    """ Given a box, calculate its full path and return it in a dict."""
    return {
        'path': _retraceBoxPath(db, box.box_id),
    }


if __name__ == '__main__':
    from ostracion_app.utilities.database.dbTools import (
        dbGetDatabase,
    )
    from ostracion_app.utilities.database.userTools import (
        dbGetUser,
    )
    db = dbGetDatabase()
    #
    user = dbGetUser(db, 'sergio')
    results = fsFind(db, 'i', user)
    print(results)
