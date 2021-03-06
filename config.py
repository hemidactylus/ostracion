""" config.py
    Main "hard" configuration for Ostracion,
    i.e. the non-settable-in-the-app part (usually never changed).
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))

# hard-constants
# for short names/descriptions (e.g. role IDs, role descriptions)
maxShortIdentifierLength = 32
# for one-liner on-DB identifiers (box names, file descriptions, usernames etc)
maxIdentifierLength = 2040
# for in-DB large blobs such as the markdown for info-page
maxStoredTextLength = 65536

# "find" tool, threshold for similarity search
similarityScoreThreshold = 0.15

# allowed characters for usernames
usernameCharacterSet = set(
    '1234567890qwertyuiopasdfghjklzxcvbnmPOIUYTREWQLKJHGFDSAMNBVCXZ_-.@'
)

# show root box as icon in breadcrumbs
breadcrumbShowRootAsIcon = True
# root box nice naming
rootBoxNiceTitle = 'Root'
rootBoxNiceName = 'root'

# reasonably unchanged definitions
lowercaseAlphabet = set('qwertyuiopasdfghjklzxcvbnm')

# version
ostracionVersion = '1.1.0'

# directories
templateDirectory = os.path.join(
    basedir,
    'ostracion_app',
    'templates',
)

resourceDirectory = os.path.join(
    basedir,
    'ostracion_app',
    'resources',
)

managedImagesDirectory = os.path.join(
    basedir,
    'ostracion_app',
    'managed_files',
)

staticDirectory = os.path.join(
    basedir,
    'ostracion_app',
    'static',
)

defaultAppImageDirectory = os.path.join(
    resourceDirectory,
    'default_app_images',
)

# relative URI path
staticFileIconsRootPath = os.path.join(
    'static',
    'file_icons',
)

# database access
dbFullName = os.path.join(
    basedir,
    'ostracion_app',
    'db',
    'ostracion.db',
)
