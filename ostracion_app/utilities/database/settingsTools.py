""" settingsTools.py
    Tools to perform database I/O of settings,
    their de/serialisation, their enrichment upon reading from DB,
    their updating and so on.

    In particular, about rolling/unrolling and forming/deforming:
        FORMDATA            DB                      VALUE
                                --unroll--> is_default, default_value, value
                <--inform---
                ---deform-->
    where:
        - inform = prepare for display on web form/read from it back to DB
        - deform = read from the form and convert back to DB
        - unroll = read from DB and convert to the actual read setting value
    On DB all <value>s are strings.
"""

import os
import json

from flask import (
    url_for,
)

from ostracion_app.utilities.tools.dictTools import (
    convertIterableToDictOfLists,
)
from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

from ostracion_app.utilities.models.Setting import Setting

from ostracion_app.utilities.database.permissions import (
    userIsAdmin,
)

from ostracion_app.utilities.database.sqliteEngine import (
    dbRetrieveAllRecords,
    dbRetrieveRecordByKey,
    dbUpdateRecordOnTable,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToPath,
)

from ostracion_app.utilities.fileIO.thumbnails import (
    determineManagedTextImagePath,
)


def _unrollSettingValueByType(ty, vaString):
    """Unroll (db to actual value) a setting of given type."""
    if ty == 'string':
        return vaString
    elif ty == 'nonempty_string':
        return vaString
    elif ty == 'color':
        return vaString.lower()
    elif ty == 'boolean':
        return int(vaString) != 0
    elif ty == 'option':
        return vaString
    elif ty == 'text':
        return vaString
    elif ty == 'image':
        return vaString
    elif ty == 'optional_integer':
        return None if vaString == '' else int(vaString)
    elif ty == 'positive_integer':
        return int(vaString)
    elif ty == 'nonnegative_integer':
        return int(vaString)
    else:
        raise NotImplementedError('setting type "%s" unknown' % ty)


def _informSettingValueByType(ty, vaString):
    """Inform (db to web-form displayed value) a setting of given type."""
    if ty == 'string':
        return vaString
    if ty == 'nonempty_string':
        return vaString
    elif ty == 'color':
        return vaString
    elif ty == 'boolean':
        return int(vaString) != 0
    elif ty == 'option':
        return vaString
    elif ty == 'text':
        return vaString
    elif ty == 'image':
        return vaString
    elif ty == 'optional_integer':
        return vaString
    elif ty == 'positive_integer':
        return vaString
    elif ty == 'nonnegative_integer':
        return vaString
    else:
        raise NotImplementedError('setting type "%s" unknown' % ty)


def _addLeadingPound(cs):
    """Normalisation for color strings: always a leading '#' symbol."""
    if len(cs) > 0:
        return '%s%s' % (
            '#' if cs[0] != '#' else '',
            cs,
        )
    else:
        return cs


def _deformSettingValueByType(ty, vaFormData):
    """Deform (web-form displayed value to db) a setting of given type."""
    if ty == 'string':
        return vaFormData
    if ty == 'nonempty_string':
        return vaFormData
    elif ty == 'color':
        return _addLeadingPound(vaFormData.lower())
    elif ty == 'boolean':
        return '1' if vaFormData else '0'
    elif ty == 'option':
        return vaFormData
    elif ty == 'text':
        return vaFormData
    elif ty == 'image':
        return vaFormData
    elif ty == 'optional_integer':
        return '' if vaFormData.strip() == '' else str(int(vaFormData))
    elif ty == 'positive_integer':
        return str(int(vaFormData)) if vaFormData.strip() != '' else ''
    elif ty == 'nonnegative_integer':
        return str(int(vaFormData)) if vaFormData.strip() != '' else ''
    else:
        raise NotImplementedError('setting type "%s" unknown' % ty)


def getFormValueFromSetting(st):
    """A wrapper for the <inform> operation."""
    return _informSettingValueByType(
        st.type,
        st.value,
    )


def _getValueFromSetting(st):
    """A wrapper for the <unroll> operation."""
    return _unrollSettingValueByType(
        st.type,
        st.value if st.value != '' else st.default_value,
    )


def _getDefaultValueFromSetting(st):
    """ A wrapper for the <unroll> operation,
        specific for the default value.
    """
    return _unrollSettingValueByType(
        st.type,
        st.default_value,
    )


def _loadPossibleSettingMetadata(metadataString):
    """ Unpack the (possibly stored) setting
        metadata, a json-blob if present.
    """
    if metadataString is not None and metadataString != '':
        return json.loads(metadataString)
    else:
        return {}


def _enrichSettingObject(st):
    """ Wrap a setting, as read from DB, with unrolled value
        and other useful info such as metadata and is-default.
    """
    val = _getValueFromSetting(st)
    dval = _getDefaultValueFromSetting(st)
    return {
        'setting': st,
        'is_default': st.value == '',
        'metadata': _loadPossibleSettingMetadata(st.metadata),
        'value': val,
        'default_value': dval,
    }


def dbLoadAllSettings(db, user):
    """ Load all settings and arrange them in a tree:
            klass -> group_id -> id -> SETTING_STUFF
        where SETTING_STUFF is the enriched form:
            {
                'setting': Setting object as from db
                + more on-the-fly calculated things
            }
        .
    """
    richSettingTree = {
        klass: {
            groupId: {
                st.id: _enrichSettingObject(st)
                for st in kgSettingList
            }
            for groupId, kgSettingList in convertIterableToDictOfLists(
                kSettingList,
                keyer=lambda st: st.group_id,
                valuer=lambda st: st,
            ).items()
        }
        for klass, kSettingList in convertIterableToDictOfLists(
            (
                Setting(**sDict)
                for sDict in dbRetrieveAllRecords(
                    db,
                    'settings',
                    dbTablesDesc=dbSchema,
                )
            ),
            keyer=lambda st: st.klass,
            valuer=lambda st: st,
        ).items()
    }
    #
    return richSettingTree


def dbGetSetting(db, sgKlass, sgId, sId, user):
    """Load a given setting and return it as enriched."""
    return _enrichSettingObject(
        Setting(**dbRetrieveRecordByKey(
            db,
            'settings',
            {
                'klass':    sgKlass,
                'group_id': sgId,
                'id':       sId,
            },
            dbTablesDesc=dbSchema,
        ))
    )


def makeSettingImageUrl(g, sgId, sId):
    """ Prepare the URL for the setting of type 'image'.
        Resolve either on the default or on the customized setting.
        Re-route on a setting imageUrl endpoint in all cases.
    """
    st = g.settings['image'].get(sgId, {}).get(sId, {}).get('setting')
    if st is not None:
        return url_for(
            'settingThumbnailView',
            dummyId=st.value + '_',
            settingGroupId=st.group_id,
            settingId=st.id,
        )
    else:
        # At the moment this is the "general image fallback":
        return ''


def makeSettingSubmapIntoListForConfigViews(settingSubMap):
    """ Given a map of settings for a specific "admin/config" page,
        group them according to group (sorting the groups)
        and sort the settings within each group, in a 1:1 with
        what will be displayed on the page.

        The return value is a (sorted) list of tuples:
            [(group_information, list_of_settings),...]
    """
    # first a map group_id -> sorted list of settings
    inGroupSorteds = {
        gId: sorted(
            groupSMap.values(),
            key=lambda s: s['setting'].ordering,
        )
        for gId, groupSMap in settingSubMap.items()
    }
    # then sorting the group_ids and preparing their description.
    return [
        (
            {
                'group_id': igId,
                'group_title': gSList[0]['setting'].group_title,
            },
            gSList,
        )
        for igId, gSList in sorted(
            inGroupSorteds.items(),
            key=lambda kv: kv[1][0]['setting'].group_ordering
        )
    ]


def updateSettingThumbnail(db, richSetting, tId, tMT, user,
                           fileStorageDirectory, skipCommit=False):
    """ Update the image in a setting of type Image. This returns
        the (actual) filesystem deletion queue after taking care of
        the DB part.
        The new thumbnail ID is passed to this function ('' to reset).
        richSetting['setting'] is the DB object, at top-level we
        have enrichment info (such as the default/value resolved etc)
    """
    prevId = richSetting['setting'].value
    if prevId != '':
        delQueue = [
            fileIdToPath(prevId, fileStorageDirectory=fileStorageDirectory)
        ]
    else:
        delQueue = []
    #
    newSettingDict = recursivelyMergeDictionaries(
        {
            'value': tId if tId is not None else '',
            'icon_mime_type': tMT if tMT is not None else '',
        },
        defaultMap={
            k: v
            for k, v in richSetting['setting'].asDict().items()
            if k in {'value', 'icon_mime_type', 'group_id', 'id'}
        },
    )
    dbUpdateRecordOnTable(
        db,
        'settings',
        newSettingDict,
        dbTablesDesc=dbSchema,
        allowPartial=True,
    )
    #
    if not skipCommit:
        db.commit()
    return delQueue


def dbUpdateStandardSettingDict(db, enrichedSetting, newFormValue,
                                user, skipCommit=False):
    """ Update a non-image setting with a new value (taking care of
        deforming before the actual writing to DB).
    """
    if userIsAdmin(db, user):
        deformedValue = _deformSettingValueByType(
            enrichedSetting['setting'].type,
            newFormValue,
        )
        newSettingDict = recursivelyMergeDictionaries(
            {
                'value': deformedValue,
            },
            defaultMap={
                k: v
                for k, v in enrichedSetting['setting'].asDict().items()
                if k in {'value', 'icon_mime_type', 'group_id', 'id'}
            }
        )
        #
        if (enrichedSetting['setting'].type == 'string' and
                enrichedSetting['metadata'].get('is_text_image', False)):
            # we handle the special case of deleting outdated
            # image-text that may have been produced
            #
            # this largerSettingDict is used only to determine the nextValue
            largerNextSettingDict = recursivelyMergeDictionaries(
                {
                    'value': deformedValue,
                },
                defaultMap={
                    k: v
                    for k, v in enrichedSetting['setting'].asDict().items()
                    if k in {'value', 'type', 'default_value'}
                }
            )
            #
            prevValue = enrichedSetting['value']
            nextValue = _getValueFromSetting(Setting(**largerNextSettingDict))
            # if there is a picture-with-text to be superseded, delete it
            prevPath, prevTitle, prevTag = determineManagedTextImagePath(
                prevValue,
                prefix='%s/%s' % (
                    enrichedSetting['setting'].group_id,
                    enrichedSetting['setting'].id,
                ),
            )
            nextPath, nextTitle, nextTag = determineManagedTextImagePath(
                nextValue,
                prefix='%s/%s' % (
                    enrichedSetting['setting'].group_id,
                    enrichedSetting['setting'].id,
                ),
            )
            if prevTag != nextTag:
                prevFileName = os.path.join(
                    prevPath,
                    prevTitle,
                )
                if os.path.isfile(prevFileName):
                    # delete the old, unused file
                    os.remove(prevFileName)
        #
        dbUpdateRecordOnTable(
            db,
            'settings',
            newSettingDict,
            dbTablesDesc=dbSchema,
            allowPartial=True
        )
        if not skipCommit:
            db.commit()
    else:
        raise OstracionError('Insufficient permissions')
