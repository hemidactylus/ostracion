""" zipFileUtilities.py:
    tools to interact with 'zip' files
"""

import zipfile


def makeZipFile(zipFileName, sourceFilePairs, sourceDataPairs):
    """
        fileName is the path of the zip-file to create
        sourceFilePairs is a list [
            (full_source_file_path, path_in_archive)
        ]
    """
    zipf = zipfile.ZipFile(zipFileName, 'w', zipfile.ZIP_DEFLATED)
    for fp in sourceFilePairs:
        zipf.write(
          filename=fp['path'],
          arcname=fp['zip_path'],
        )
    #
    for dp in sourceDataPairs:
        zipf.writestr(
          zinfo_or_arcname=dp['zip_path'],
          data=dp['data'],
        )
    #
    zipf.close()
