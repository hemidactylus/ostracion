""" fileTypes.py:
    module for handling decisions based on mime type and similar.
"""

from flask import (
    url_for,
    request,
    g,
)

from ostracion_app.utilities.fileIO.mimeTypeMaps import (
    viewableMimeTypeToViewModeMap,
    textualEditableMimeTypes,
)

from ostracion_app.utilities.fileIO.textFileViewingModes import (
    textFileViewingModes,
)

from ostracion_app.utilities.database.tickets import (
    dbPunchTicket,
)

def isFileViewable(file):
    """Does the file belong to the viewable mime types?"""
    return file.mime_type in viewableMimeTypeToViewModeMap


def isFileTextEditable(file):
    """Does the file belong to the (textually) editable mime types?"""
    return file.mime_type in textualEditableMimeTypes


def fileViewingClass(file):
    """ Resolve file to the viewability class (e.g. image),
        but in particular for textual class resolve further into
        e.g. markdown vs plaintext.
    """
    vClass = viewableMimeTypeToViewModeMap.get(file.mime_type)
    if vClass != 'textual':
        return vClass
    else:
        return file.textual_mode


def produceFileViewContents(db, file, mode, viewParameters,
                            fileStorageDirectory, urlRoot=None,
                            protectBannedUserTickets=None):
    """ Prepare a <contents> structure for later in-page viewing of file.

        Act according to whether it is usual-view
        or by-ticket-view (in which case the image URL is different).

        Note: if it's an image, the ticket-punching (if required) occurs
        within the views such as 'ticket*View' used here.
        But if it is a text-viewing mode we cannot do that since downloading
        and viewing in page are different things, hence we have to punch here.
        So in general viewing and downloading are two separate punches,
        except, as usual for images, client browser caching entails a single
        punch.
    """
    fViewClass = fileViewingClass(file)
    if fViewClass in textFileViewingModes:
        fileContents = textFileViewingModes[fViewClass][
            'contentPreparer'](file, mode, viewParameters,
                               fileStorageDirectory)
        if mode in {'ticketview', 'galleryview'}:
            # we also punch a ticket
            dbPunchTicket(
                db,
                'f',
                viewParameters['ticketId'],
                viewParameters['securityCode'],
                urlRoot,
                protectBannedUserTickets,
            )

    elif fViewClass == 'image':
        if mode == 'fsview':
            imgValue = url_for(
                'fsDownloadView',
                fsPathString='/'.join(
                    viewParameters['boxPath'][1:]
                    + [viewParameters['fileName']]
                ),
            )
        elif mode == 'ticketview':
            imgValue = url_for(
                'ticketFsDownloadView',
                ticketId=viewParameters['ticketId'],
                securityCode=viewParameters['securityCode'],
            )
        elif mode == 'galleryview':
            imgValue = url_for(
                'ticketGalleryFsView',
                ticketId=viewParameters['ticketId'],
                securityCode=viewParameters['securityCode'],
                fileName=viewParameters['fileName'],
            )
        else:
            raise ValueError('Unhandled mode in produceFileViewContents')
        fileContents = {
            'mode': 'image',
            'value': imgValue,
        }
    else:
        fileContents = {
            'mode': 'error',
            'value': 'Could not show this file.',
        }
    #
    return fileContents
