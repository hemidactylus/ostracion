""" findEngines.py
    basic functions to perform searches in boxes/files tables,
    with substring, similarity and other engines to perform search.
"""

import re

from ostracion_app.utilities.models.Box import Box
from ostracion_app.utilities.models.File import File
from ostracion_app.utilities.models.Link import Link

from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)
from ostracion_app.utilities.database.sqliteEngine import (
    dbRetrieveRecordsByKey,
    dbRetrieveAllRecords,
)

from ostracion_app.utilities.tools.formatting import (
    stripToAscii,
)

from ostracion_app.utilities.textSimilarity.similarityTools import (
    textToDVector,
    deserializeDVector,
    scalProd,
)

from config import similarityScoreThreshold


def escapeForSqlite(term):
    """ Escape chars for the SQLITE "like" query."""
    return term.replace('%', '\\%').replace('_', '\\_')


def sqliteLikeSubstringSearch(
        db, searchTerm, searchBoxes, searchFiles, searchLinks):
    """ Perform a file/box search using the sqlite "like" operator.

        Limited, but fast. No other options available in this avenue.

        See e.g.
            https://www.sqlitetutorial.net/sqlite-like/
        for escaping "like" statements.

        Returns a map
            {
                'files': [
                    {
                        'item': File object,
                        'score': number
                    },
                    ...
                ],
                'boxes': [
                    {
                        'item': Box object,
                        'score': number
                    }
                ],
            }
    """
    escapedSearchTerm = escapeForSqlite(searchTerm)
    #
    if searchFiles:
        foundFiles = [
            {
                'item': File(**fileDict),
                'score': 1.0,
            }
            for fileDict in dbRetrieveRecordsByKey(
                db,
                'files',
                {},
                whereClauses=[
                    (
                        'name LIKE ? ESCAPE \'\\\'',
                        '%' + escapedSearchTerm + '%',
                    ),
                ],
                dbTablesDesc=dbSchema,
            )
        ]
    else:
        foundFiles = []
    if searchBoxes:
        foundBoxes = [
            {
                'item': Box(**boxDict),
                'score': 1.0,
            }
            for boxDict in dbRetrieveRecordsByKey(
                db,
                'boxes',
                {},
                whereClauses=[
                    (
                        'box_name LIKE ? ESCAPE \'\\\'',
                        '%' + escapedSearchTerm + '%',
                    ),
                ],
                dbTablesDesc=dbSchema,
            )
            if boxDict['box_id'] != ''
        ]
    else:
        foundBoxes = []
    #
    return {
        'files': foundFiles,
        'boxes': foundBoxes,
    }


def _substringScore(text, tokenResLens):
    """ Given
            a text
            a list of (regex,len)
        give a score which measures:
            of how much of the text is made by the tokens

        (at the moment weights are given based on a token/text lengths formula)
        (not implemented: perhaps introduce earliness-in-text? so far no.)
    """
    tLen = len(text)
    return sum(
        len(tkRe.findall(text)) * tkLen / tLen
        for tkRe, tkLen in tokenResLens
    )


def _itemSubstringMatchScore(
        mode, tokenResLens, objDict,
        caseSensitive=False, useDescription=False):
    """ Given a found item (box/file) and its mode,
        a score is computed for the 'substring' match on the item
        to sort the results accordingly.

            mode='file','box'
            tokenResLens = a list of (regex,len)
            objDict is either a file or a box-Dict fresh from DB
            caseSensitive boolean (tokens are already normalized if need be)
            useDescription boolean

        Return zero iff NO MATCH
    """
    # preparation of source fields
    if mode in {'file', 'link'}:
        origTgtFields = [
            objDict['name'],
        ] + ([objDict['description']] if useDescription else [])
    elif mode == 'box':
        origTgtFields = [
            objDict['box_name'],
            objDict['title'],
        ] + ([objDict['description']] if useDescription else [])
    else:
        raise NotImplementedError(
            'Unknown mode "%s" in _itemSubstringMatchScore' % mode
        )
    #
    # case-normalisation
    tgtFields = [
        tF if caseSensitive else tF.lower()
        for tF in (
            stripToAscii(_tF)
            for _tF in origTgtFields
            if _tF.strip() != ''
        )
    ]
    #
    return sum(
        _substringScore(tgtF, tokenResLens=tokenResLens)
        for tgtF in tgtFields
    )


def explicitLoopSubstringSearch(
        db,
        searchTerm,
        searchBoxes=True,
        searchFiles=True,
        searchLinks=True,
        caseSensitive=True,
        useDescription=False):
    """ Explicit loop over the files/boxes tables
        and pick the substring-matching items.
        Same return object as 'sqliteLikeSubstringSearch'.

        We explicitly browse all files and all boxes
        and apply the search with the options passed.
        Not so fast but highly extendable in the future.
    """
    #
    _strippedSearchTerm = stripToAscii(searchTerm)
    _caseAdjustedSearchTerm = (
        _strippedSearchTerm if caseSensitive else _strippedSearchTerm.lower()
    )
    searchTokens = {
        itm.strip()
        for itm in _caseAdjustedSearchTerm.split(' ')
        if itm.strip() != ''
    }
    if len(searchTokens) > 0:
        #
        tokenResLens = [
            (re.compile(re.escape(tk)), len(tk))
            for tk in searchTokens
        ]
        #
        if searchFiles:
            foundFiles = [
                ffRichItem
                for ffRichItem in (
                    {
                        'item': File(**fileDict),
                        'score': _itemSubstringMatchScore(
                            'file',
                            tokenResLens,
                            fileDict,
                            caseSensitive,
                            useDescription,
                        ),
                    }
                    for fileDict in dbRetrieveAllRecords(
                        db,
                        'files',
                        dbTablesDesc=dbSchema,
                    )
                )
                if ffRichItem['score'] > 0
            ]
        else:
            foundFiles = []
        #
        if searchBoxes:
            foundBoxes = [
                fbRichItem
                for fbRichItem in (
                    {
                        'item': Box(**boxDict),
                        'score': _itemSubstringMatchScore(
                            'box',
                            tokenResLens,
                            boxDict,
                            caseSensitive,
                            useDescription,
                        ),
                    }
                    for boxDict in dbRetrieveAllRecords(
                        db,
                        'boxes',
                        dbTablesDesc=dbSchema,
                    )
                    if boxDict['box_id'] != ''
                )
                if fbRichItem['score'] > 0
            ]
        else:
            foundBoxes = []
        #
        if searchLinks:
            foundLinks = [
                flRichItem
                for flRichItem in (
                    {
                        'item': Link(**linkDict),
                        'score': _itemSubstringMatchScore(
                            'link',
                            tokenResLens,
                            linkDict,
                            caseSensitive,
                            useDescription,
                        ),
                    }
                    for linkDict in dbRetrieveAllRecords(
                        db,
                        'links',
                        dbTablesDesc=dbSchema,
                    )
                )
                if flRichItem['score'] > 0
            ]
        else:
            foundLinks = []
        #
        return {
            'files': foundFiles,
            'boxes': foundBoxes,
            'links': foundLinks,
        }
    else:
        return {
            'files': [],
            'boxes': [],
            'links': [],
            'message': 'No search terms provided',
        }


def _itemSimilarityMatchScore(
        mode,
        searchDVector,
        objDict,
        useDescription=False):
    """ Given a file/box and a (dVector of a) search,
        compute a similarity score for use by 'explicitLoopSimilaritySearch'
        ehere a sorting/trimming of the search results takes place.

            mode='file','box'
            searchDVector is {'aa': 0.2, ...}
            objDict is either a file or a box-Dict fresh from DB
            useDescription boolean

        Return (an elaboration of) the scalar product
        between the (dvectors of) search and the stuff
        extracted from the objDict (higher value ~ more similarity).
    """
    if mode in {'file', 'link'}:
        tgtSerializedDVectors = [
            objDict['dvector_name'],
        ] + ([objDict['dvector_description']] if useDescription else [])
    elif mode == 'box':
        tgtSerializedDVectors = [
            objDict['dvector_box_name'],
            objDict['dvector_title'],
        ] + ([objDict['dvector_description']] if useDescription else [])
    else:
        raise NotImplementedError(
            'Unknown mode "%s" in _itemSubstringMatchScore' % mode
        )
    #
    return max(
        scalProd(
            deserializeDVector(tgtSerializedDVector),
            searchDVector,
        )
        for tgtSerializedDVector in tgtSerializedDVectors
    )


def explicitLoopSimilaritySearch(
        db,
        searchTerm,
        searchBoxes=True,
        searchFiles=True,
        searchLinks=True,
        useDescription=False):
    """ Explicit loop over files/boxes
        and use a 'similarity' logic to pick matching results.

        Same return object as 'sqliteLikeSubstringSearch'.
    """
    searchTermDVector = textToDVector(searchTerm)
    if len(searchTermDVector) > 0:
        #
        if searchFiles:
            foundFiles = [
                ffRichItem
                for ffRichItem in (
                    {
                        'item': File(**fileDict),
                        'score': _itemSimilarityMatchScore(
                            'file',
                            searchTermDVector,
                            fileDict,
                            useDescription,
                        ),
                    }
                    for fileDict in dbRetrieveAllRecords(
                        db,
                        'files',
                        dbTablesDesc=dbSchema,
                    )
                )
                if ffRichItem['score'] >= similarityScoreThreshold
            ]
        else:
            foundFiles = []
        #
        if searchBoxes:
            foundBoxes = [
                fbRichItem
                for fbRichItem in (
                    {
                        'item': Box(**boxDict),
                        'score': _itemSimilarityMatchScore(
                            'box',
                            searchTermDVector,
                            boxDict,
                            useDescription,
                        ),
                    }
                    for boxDict in dbRetrieveAllRecords(
                        db,
                        'boxes',
                        dbTablesDesc=dbSchema,
                    )
                    if boxDict['box_id'] != ''
                )
                if fbRichItem['score'] >= similarityScoreThreshold
            ]
        else:
            foundBoxes = []
        #
        if searchLinks:
            foundLinks = [
                flRichItem
                for flRichItem in (
                    {
                        'item': Link(**linkDict),
                        'score': _itemSimilarityMatchScore(
                            'link',
                            searchTermDVector,
                            linkDict,
                            useDescription,
                        ),
                    }
                    for linkDict in dbRetrieveAllRecords(
                        db,
                        'links',
                        dbTablesDesc=dbSchema,
                    )
                )
                if flRichItem['score'] >= similarityScoreThreshold
            ]
        else:
            foundLinks = []
        #
        return {
            'files': foundFiles,
            'boxes': foundBoxes,
            'links': foundLinks,
        }
    else:
        return {
            'files': [],
            'boxes': [],
            'links': [],
            'message': 'Not enough digits/letters in search term',
        }
