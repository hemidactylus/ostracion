""" thumbnailFormatFinder.py
    tools to map various modes of thumbnail-setting
    to the corresponding thumbnail mode as modes of invoking
    the low-level (imagemagick) transformers.
"""


from ostracion_app.views.apps.appRegisteredPlugins import (
    appsSetIconModes,
)


def determineThumbnailFormatByModeAndTarget(db, mode, target):
    """ Helper function to get the 'thumbnail format'
        before resizing an image.

        Given e.g. 'u' and the user, or 'b' and the box, ...,
        find the appropriate thumbnail mode for the resizing calls.
    """
    if mode in {'f', 'b', 'l'}:
        return 'thumbnail'
    elif mode == 'u':
        return 'thumbnail'
    elif mode == 'au':
        return 'thumbnail'
    elif mode == 's':
        return target['metadata']['thumbnailFormat']
    else:
        if mode in appsSetIconModes:
            return appsSetIconModes[mode]['extractors']['thumbnailModer'](
                db,
                target,
            )
        else:
            raise NotImplementedError(
                ('Unknown mode "%s" in '
                 'determineThumbnailFormatByModeAndTarget') % mode
            )
