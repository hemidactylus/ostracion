""" dbTools.py:
    Machinery to open the application database
"""

from ostracion_app.utilities.database.sqliteEngine import (
    dbOpenDatabase,
)
from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)

from config import dbFullName


def dbGetDatabase():
    """Give an instance of the opened database."""
    return dbOpenDatabase(dbFullName, dbSchema)
