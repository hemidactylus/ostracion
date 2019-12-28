""" mimeTypeMaps.py:
    reading the JSON describing mime types and making them into
    ready-to-use maps.
"""

import json
import os

from config import resourceDirectory

mimeTypeClassification = json.load(open(os.path.join(
    resourceDirectory,
    'mimetype_classifier',
    'file_mimetype_classification.json',
)))

# in-module conversion of the loaded information (!)
# this is:
#   mimetype -> thumbnail rootname
#     ('img', 'pdf', ... one for each default thumbnail pic in <rootname>.png)
mimeTypeToDefaultThumbnailMap = {
    mimeType: fileType
    for fileType, mimeTypes in
    mimeTypeClassification['mime_types_by_filetype'].items()
    for mimeType in mimeTypes
}

imageMimeTypeToResizeMethodMap = mimeTypeClassification[
    'image_mime_types_by_thumbnail_method']

viewableMimeTypeToViewModeMap = {
    mimeType: viewMode
    for viewMode, mimeTypes in
    mimeTypeClassification['viewable_mime_types_by_view_mode'].items()
    for mimeType in mimeTypes
}

textualEditableMimeTypes = {
    mimeType
    for mimeType in
    mimeTypeClassification[
        'viewable_mime_types_by_view_mode'].get('textual', [])
}
