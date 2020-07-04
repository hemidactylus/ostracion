""" tickets.py
    These function form a driver, for use by views,
    to load/enrich/create/redeem/punch tickets on DB.
"""

import json
import datetime

import hashlib
from uuid import uuid4

from flask import url_for

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries
)

from ostracion_app.utilities.database.permissions import (
    userIsAdmin,
)
from ostracion_app.utilities.database.userTools import (
    dbGetUser,
)
from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.models.Ticket import Ticket

from ostracion_app.utilities.tools.securityCodes import makeSecurityCode

from ostracion_app.utilities.database.sqliteEngine import (
    dbRetrieveRecordByKey,
    dbRetrieveRecordsByKey,
    dbAddRecordToTable,
    dbDeleteRecordsByKey,
    dbUpdateRecordOnTable,
)
from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)

from ostracion_app.utilities.database.userTools import (
    getUserFullName,
)

from ostracion_app.utilities.tools.comparisonTools import (
    optionNumberLeq,
)

ticketTargetTypeToModeNameMap = {
    'user': 'u',
    'password': 'p',
    'file': 'f',
    'upload': 'c',
    'gallery': 'g',
}


def makeTicketMagicLink(ticket, urlRoot):
    """Prepare the magic link for a ticket given the url root of this app."""
    return '%s%s' % (
        urlRoot[:-1] if urlRoot[-1] == '/' else urlRoot,
        url_for(
            'redeemTicketView',
            mode=ticketTargetTypeToModeNameMap[ticket.target_type],
            ticketId=ticket.ticket_id,
            securityCode=ticket.security_code,
        ),
    )


def randomTicketNumbers(user):
    """Generate a random ticket number/security code."""
    ticketId = uuid4().hex
    securityCode = '%s-%s' % (
        makeSecurityCode(),
        hashlib.md5(
            ('%s_%s' % (user.username, ticketId)).encode()
        ).hexdigest()[:3],
    )
    return ticketId, securityCode


def richTicketSorter(t):
    """ A function returning a sortable (tuple of) feature(s) from a ticket,
        for properly-sorted display in lists.
    """
    return (
        0 if t['redeemable'] else 1,
        1 if t['expired'] else 0,
        t['ticket'].issue_date,
    )


def isTicketIssuablePerSettings(validityHours, multiplicity, settings):
    """
        Check per-config limitations on multiplicity and validityhours
        and return True iff the ticket can be issued as it is.
    """
    maxMultiplicity = settings['behaviour']['behaviour_tickets'][
        'max_ticket_multiplicity']['value']
    maxValidityHours = settings['behaviour']['behaviour_tickets'][
        'max_ticket_validityhours']['value']
    #
    return all([
        optionNumberLeq(maxMultiplicity, multiplicity),
        optionNumberLeq(maxValidityHours, validityHours),
    ])


def enrichTicket(db, t, urlRoot):
    """ Wrap a ticket as read from DB with an outer layer of dict
        rich with info such as expired, uses still available, etc.
    """
    expired = (t.expiration_date is not None and
               datetime.datetime.now() >= t.expiration_date)
    exhausted = (t.multiplicity is not None and
                 t.times_redeemed >= t.multiplicity)
    metadata = json.loads(t.metadata)
    if t.target_type == 'password':
        target = metadata['username']
        targetUrl = None
    elif t.target_type == 'user':
        target = metadata.get('username')
        targetUrl = None
    elif t.target_type == 'file':
        target = metadata.get('file_name', metadata['file_id'])
        if metadata.get('file_mode', 'direct') == 'view':
            targetUrl = url_for(
                'fsView',
                fsPathString='/'.join(metadata['path'][1:])
            )
        else:
            targetUrl = url_for(
                'fsDownloadView',
                fsPathString='/'.join(metadata['path'][1:])
            )
    elif t.target_type == 'upload':
        _target = metadata.get(
            'box_title',
            metadata.get('box_name', metadata['box_id']),
        )
        target = _target if _target != '' else 'Root'
        targetUrl = url_for(
            'lsView',
            lsPathString='/'.join(metadata['box_path'][1:])
        )
    elif t.target_type == 'gallery':
        _target = metadata.get(
            'box_title',
            metadata.get('box_name', metadata['box_id']),
        )
        target = _target if _target != '' else 'Root'
        targetUrl = url_for(
            'fsGalleryView',
            fsPathString='/'.join(metadata['box_path'][1:]),
            top=1,
        )
    else:
        target = None
        targetUrl = None
    #
    return {
        'ticket': t,
        'expired': expired,
        'metadata': metadata,
        'redeemed': t.times_redeemed > 0,
        'exhausted': exhausted,
        'redeemable': not expired and not exhausted,
        'magic_link': makeTicketMagicLink(t, urlRoot),
        'issuer_full_name': getUserFullName(db, t.username),
        'target': target,
        'target_url': targetUrl,
    }


def dbGetEnrichAndCheckTicket(db, mode, ticketId, securityCode, urlRoot):
    """ Check validity (proper codes, existence) of a ticket
        and return it enriched.
    """
    ticketDict = dbRetrieveRecordByKey(
        db,
        'tickets',
        {'ticket_id': ticketId},
        dbTablesDesc=dbSchema,
    )
    if ticketDict is None:
        return None
    else:
        ticket = Ticket(**ticketDict)
        if all([
            ticketTargetTypeToModeNameMap[ticket.target_type] == mode,
            ticket.security_code == securityCode,
        ]):
            return enrichTicket(db, ticket, urlRoot)
        else:
            return None


def dbPunchTicket(db, mode, ticketId, securityCode, urlRoot,
                  protectBannedUserTickets):
    """Retrieve/enrich a ticket and punch it with dbPunchRichTicket."""
    richTicket = dbGetEnrichAndCheckTicket(
        db,
        mode,
        ticketId,
        securityCode,
        urlRoot,
    )
    issuer = (dbGetUser(db, richTicket['ticket'].username)
              if richTicket is not None
              else None)
    if (issuer is not None and
            (not protectBannedUserTickets or issuer.banned == 0)):
        dbPunchRichTicket(db, richTicket)
    else:
        raise OstracionError('Not allowed to punch ticket')


def dbPunchRichTicket(db, richTicket, numPunches=1, skipCommit=False):
    """
        Punch a ticket, i.e. mark it as been used once more.

        We assume the ticket has been read during this database
        session, i.e. it reflects current DB data.
    """
    if richTicket['redeemable']:
        #
        newTicketDict = recursivelyMergeDictionaries(
            {
                'times_redeemed': (
                    richTicket['ticket'].times_redeemed + numPunches
                ),
                'last_redeemed': datetime.datetime.now(),
            },
            defaultMap=richTicket['ticket'].asDict(),
        )
        dbUpdateRecordOnTable(
            db,
            'tickets',
            newTicketDict,
            dbTablesDesc=dbSchema,
        )
        #
        if not skipCommit:
            db.commit()
    else:
        if richTicket['exhausted']:
            raise OstracionError('Ticket is exhausted')
        else:
            raise OstracionError('Cannot punch a non-redeemable ticket')


def dbDeleteTicket(db, ticketId, user, mode, skipCommit=False):
    """ Remove a ticket from DB."""
    ticketDict = dbRetrieveRecordByKey(
        db,
        'tickets',
        {'ticket_id': ticketId},
        dbTablesDesc=dbSchema,
    )
    if (ticketDict is not None and
            ticketTargetTypeToModeNameMap[ticketDict['target_type']] == mode):
        ticket = Ticket(**ticketDict)
        if userIsAdmin(db, user) or user.username == ticket.username:
            #
            dbDeleteRecordsByKey(
                db,
                'tickets',
                {'ticket_id': ticketId},
                dbTablesDesc=dbSchema,
            )
            if not skipCommit:
                db.commit()
        else:
            raise OstracionError('Insufficient permissions')
    else:
        raise OstracionWarning('Ticket unavailable')


def dbMakeGalleryTicket(db, ticketName, validityHours, multiplicity,
                        ticketMessage, box, boxPath, user, urlRoot, settings):
    """ Generate a gallery-view ticket on a
        box (with the specified ticket settings).
    """
    if isTicketIssuablePerSettings(validityHours, multiplicity, settings):
        ticketId, securityCode = randomTicketNumbers(user)
        issueDate = datetime.datetime.now()
        metadata = {
            k: v
            for k, v in {
                'box_id': box.box_id,
                'box_path': boxPath,
                'box_name': box.box_name,
                'box_title': box.title,
                'message': ticketMessage,
            }.items()
            if v is not None
        }
        expirationDate = None if validityHours is None else (
            issueDate + datetime.timedelta(hours=validityHours)
        )
        newTicket = Ticket(
            ticket_id=ticketId,
            name=ticketName,
            security_code=securityCode,
            username=user.username,
            issue_date=issueDate,
            expiration_date=expirationDate,
            multiplicity=multiplicity,
            target_type='gallery',
            metadata=json.dumps(metadata),
            last_redeemed=None,
            times_redeemed=0,
        )
        #
        dbAddRecordToTable(
            db,
            'tickets',
            newTicket.asDict(),
            dbTablesDesc=dbSchema,
        )
        db.commit()
        return makeTicketMagicLink(newTicket, urlRoot)
    else:
        raise OstracionError(
            'Ticket parameters not allowed under the current settings'
        )


def dbMakeUploadTicket(db, ticketName, validityHours, multiplicity,
                       ticketMessage, box, boxPath, user, urlRoot, settings):
    """Generate an upload ticket to upload into a box."""
    if isTicketIssuablePerSettings(validityHours, multiplicity, settings):
        ticketId, securityCode = randomTicketNumbers(user)
        issueDate = datetime.datetime.now()
        metadata = {
            k: v
            for k, v in {
                'box_id': box.box_id,
                'box_path': boxPath,
                'box_title': box.title,
                'box_name': box.box_name,
                'message': ticketMessage,
            }.items()
            if v is not None
        }
        expirationDate = None if validityHours is None else (
            issueDate + datetime.timedelta(hours=validityHours)
        )
        newTicket = Ticket(
            ticket_id=ticketId,
            name=ticketName,
            security_code=securityCode,
            username=user.username,
            issue_date=issueDate,
            expiration_date=expirationDate,
            multiplicity=multiplicity,
            target_type='upload',
            metadata=json.dumps(metadata),
            last_redeemed=None,
            times_redeemed=0,
        )
        #
        dbAddRecordToTable(
            db,
            'tickets',
            newTicket.asDict(),
            dbTablesDesc=dbSchema,
        )
        db.commit()
        return makeTicketMagicLink(newTicket, urlRoot)
    else:
        raise OstracionError(
            'Ticket parameters not allowed under the current settings'
        )


def dbMakeFileTicket(db, ticketName, validityHours, multiplicity,
                     ticketMessage, file, fileMode, lsPath,
                     user, urlRoot, settings):
    """Generate a ticket to read-access a file."""
    if isTicketIssuablePerSettings(validityHours, multiplicity, settings):
        ticketId, securityCode = randomTicketNumbers(user)
        issueDate = datetime.datetime.now()
        metadata = {
            k: v
            for k, v in {
                'file_id': file.file_id,
                'path': lsPath,
                'file_name': file.name,
                'message': ticketMessage,
                'file_mode': fileMode,
            }.items()
            if v is not None
        }
        expirationDate = None if validityHours is None else (
            issueDate + datetime.timedelta(hours=validityHours)
        )
        newTicket = Ticket(
            ticket_id=ticketId,
            name=ticketName,
            security_code=securityCode,
            username=user.username,
            issue_date=issueDate,
            expiration_date=expirationDate,
            multiplicity=multiplicity,
            target_type='file',
            metadata=json.dumps(metadata),
            last_redeemed=None,
            times_redeemed=0,
        )
        #
        dbAddRecordToTable(
            db,
            'tickets',
            newTicket.asDict(),
            dbTablesDesc=dbSchema,
        )
        db.commit()
        return makeTicketMagicLink(newTicket, urlRoot)
    else:
        raise OstracionError(
            'Ticket parameters not allowed under the current settings'
        )


def dbMakeUserInvitationTicket(db, ticketName, validityHours, userName,
                               userFullName, userEmail, ticketMessage, user,
                               urlRoot, settings):
    """ Generate a ticket to be used to create a user
        (with/out username pre-specified.

        This is an admin-only operation.
    """
    if isTicketIssuablePerSettings(validityHours, 1, settings):
        '''
            only admins can do this by design
        '''
        if userIsAdmin(db, user):
            ticketId, securityCode = randomTicketNumbers(user)
            issueDate = datetime.datetime.now()
            metadata = {
                k: v
                for k, v in {
                    'username': userName,
                    'fullname': userFullName,
                    'email':    userEmail,
                    'message':  ticketMessage,
                }.items()
                if v is not None
            }
            expirationDate = None if validityHours is None else (
                issueDate + datetime.timedelta(hours=validityHours)
            )
            newTicket = Ticket(
                ticket_id=ticketId,
                name=ticketName,
                security_code=securityCode,
                username=user.username,
                issue_date=issueDate,
                expiration_date=expirationDate,
                multiplicity=1,
                target_type='user',
                metadata=json.dumps(metadata),
                last_redeemed=None,
                times_redeemed=0,
            )
            #
            dbAddRecordToTable(
                db,
                'tickets',
                newTicket.asDict(),
                dbTablesDesc=dbSchema,
            )
            db.commit()
            return makeTicketMagicLink(newTicket, urlRoot)
        else:
            raise OstracionError('Insufficient permissions')
    else:
        raise OstracionError(
            'Ticket parameters not allowed under the current settings'
        )


def dbMakeUserChangePasswordTicket(db, ticketName, validityHours, userName,
                                   ticketMessage, user, urlRoot, settings):
    """ Generate a change-password ticket to deliver to a user.
        This is an admin-only operation.
    """
    if isTicketIssuablePerSettings(validityHours, 1, settings):
        if userIsAdmin(db, user):
            ticketId, securityCode = randomTicketNumbers(user)
            issueDate = datetime.datetime.now()
            metadata = {
                k: v
                for k, v in {
                    'username': userName,
                    'message':  ticketMessage,
                }.items()
                if v is not None
            }
            expirationDate = None if validityHours is None else (
                issueDate + datetime.timedelta(hours=validityHours)
            )
            newTicket = Ticket(
                ticket_id=ticketId,
                name=ticketName,
                security_code=securityCode,
                username=user.username,
                issue_date=issueDate,
                expiration_date=expirationDate,
                multiplicity=1,
                target_type='password',
                metadata=json.dumps(metadata),
                last_redeemed=None,
                times_redeemed=0,
            )
            #
            dbAddRecordToTable(
                db,
                'tickets',
                newTicket.asDict(),
                dbTablesDesc=dbSchema,
            )
            db.commit()
            return makeTicketMagicLink(newTicket, urlRoot)
        else:
            raise OstracionError('Insufficient permissions')
    else:
        raise OstracionError(
            'Ticket parameters not allowed under the current settings'
        )


def dbGeneralisedGetTickets(db, user, query):
    """A generic ticket-reading query from DB, specialized in many ways."""
    return (
        Ticket(**ticDoc)
        for ticDoc in dbRetrieveRecordsByKey(
            db,
            'tickets',
            query,
            dbTablesDesc=dbSchema,
        )
    )


def dbGetAllUserInvitationTickets(db, user):
    """Get all tickets of type 'user'."""
    return dbGeneralisedGetTickets(
        db,
        user,
        {'target_type': 'user'},
    )


def dbGetAllFileTickets(db, user):
    """Get all tickets of type 'file'."""
    return dbGeneralisedGetTickets(
        db,
        user,
        {'target_type': 'file'},
    )


def dbGetAllUploadTickets(db, user):
    """Get all tickets of type 'upload'."""
    return dbGeneralisedGetTickets(
        db,
        user,
        {'target_type': 'upload'},
    )


def dbGetAllGalleryTickets(db, user):
    """Get all tickets of type 'gallery'."""
    return dbGeneralisedGetTickets(
        db,
        user,
        {'target_type': 'gallery'},
    )


def dbGetAllUserChangePasswordTickets(db, user):
    """Get all tickets of type 'password'."""
    return dbGeneralisedGetTickets(
        db,
        user,
        {'target_type': 'password'},
    )


def dbGetAllFileTicketsByUser(db, user):
    """Get all tickets of type 'file' by the calling user."""
    return dbGeneralisedGetTickets(
        db,
        user,
        {'target_type': 'file', 'username': user.username},
    )


def dbGetAllUploadTicketsByUser(db, user):
    """Get all tickets of type 'upload' by the calling user."""
    return dbGeneralisedGetTickets(
        db,
        user,
        {'target_type': 'upload', 'username': user.username},
    )


def dbGetAllGalleryTicketsByUser(db, user):
    """Get all tickets of type 'gallery' by the calling user."""
    return dbGeneralisedGetTickets(
        db,
        user,
        {'target_type': 'gallery', 'username': user.username},
    )
