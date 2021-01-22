""" settings.py """

# ledger date/time format for UI
ledgerDatetimeFormat = '%Y/%m/%d'
ledgerDatetimeFormatDesc = 'YYYY/MM/DD'

# ledger page appearance
ledgerMovementPaginationPageSize = 10
ledgerMovementPaginationShownPagesPerSide = 6

# The dot "." cannot be part of this set
categoryIdsCharacterSet = set(
    '1234567890qwertyuiopasdfghjklzxcvbnmPOIUYTREWQLKJHGFDSAMNBVCXZ'
)
