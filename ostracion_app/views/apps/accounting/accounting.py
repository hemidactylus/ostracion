"""
    accounting.py
        An app to manage ledgers of debts/credits among arbitrary actors
"""

# import os
# from uuid import uuid4
import datetime
# import urllib.parse
from flask import (
    redirect,
    url_for,
    render_template,
    request,
    send_from_directory,
    g,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.viewTools.messageTools import flashMessage

# from ostracion_app.utilities.tools.extraction import safeInt
# from ostracion_app.utilities.tools.formatting import applyDefault

from ostracion_app.utilities.database.permissions import (
    # userHasPermission,
    userRoleRequired,
)

from ostracion_app.utilities.database.userTools import (
    dbGetAllUsers,
    dbGetUser,
)

from ostracion_app.views.apps.appsPageTreeDescriptor import appsPageDescriptor

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

from ostracion_app.views.apps.accounting.forms import (
    AccountingBaseLedgerForm,
    AccountingLedgerActorForm,
)

from ostracion_app.views.apps.accounting.models.Ledger import Ledger
from ostracion_app.views.apps.accounting.accountingUtils import (
    isLedgerId,
)
from ostracion_app.views.apps.accounting.db.accountingTools import (
    dbGetLedger,
    dbCreateLedger,
    dbUpdateLedger,
    dbGetAllLedgers,
    dbDeleteLedger,
    dbGetUsersForLedger,
    dbAddUserToLedger,
    dbRemoveUserFromLedger,
)

from ostracion_app.app_main import app


@app.route('/apps/accounting/')
@app.route('/apps/accounting/index')
@userRoleRequired({('app', 'calendarmaker'), ('system', 'admin')})
def accountingIndexView():
    """Main accounting view."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='',
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'accounting'],
        g,
    )
    #
    ledgers = dbGetAllLedgers(db, user)
    #
    return render_template(
        'apps/accounting/index.html',
        user=user,
        bgcolor=g.settings['color']['app_colors'][
            'accounting_main_color']['value'],
        admin_bgcolor=g.settings['color']['app_colors'][
            'accounting_admin_color']['value'],
        ledgers=ledgers,
        **pageFeatures,
    )


@app.route('/apps/accounting/newledger', methods=['GET', 'POST'])
@userRoleRequired({('system', 'admin')})
def accountingNewLedgerView():
    """Add a ledger. Uses the 'basic ledger properties' form."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingIndexView',
        lsPathString='',
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'accounting', 'newledger'],
        g,
    )
    #
    form = AccountingBaseLedgerForm()
    if form.validate_on_submit():
        if isLedgerId(db, form.ledgerId.data, user):
            # for the convenience of keeping filled form fields,
            # this flashMessage is not made into a raised error
            flashMessage(
                'Warning',
                'Warning',
                'Ledger "%s" exists already' % form.ledgerId.data,
            )
            return render_template(
                'apps/accounting/editledger.html',
                user=user,
                ledgerform=form,
                # This suppresses the actor section of the form
                actorform=None,
                actors=[],
                # This prevents the add/remove-users part
                handleUsers=False,
                #
                bgcolor=g.settings['color']['app_colors'][
                    'accounting_main_color']['value'],
                admin_bgcolor=g.settings['color']['app_colors'][
                    'accounting_admin_color']['value'],
                formaction=url_for('accountingNewLedgerView'),
                backToUrl=url_for('accountingIndexView'),
                **pageFeatures,
            )
        else:
            #
            newLedger = Ledger(
                ledger_id=form.ledgerId.data,
                name=form.name.data,
                description=form.description.data,
                creator_username=user.username,
                creation_date=datetime.datetime.now(),
            )
            dbCreateLedger(db, user, newLedger)
            return redirect(url_for('accountingIndexView'))
    else:
        return render_template(
            'apps/accounting/editledger.html',
            user=user,
            ledgerform=form,
            # These two (the first) suppresses the actor section of the form
            actorform=None,
            actors=[],
            # This prevents the add/remove-users part
            handleUsers=False,
            #
            bgcolor=g.settings['color']['app_colors'][
                'accounting_main_color']['value'],
            admin_bgcolor=g.settings['color']['app_colors'][
                'accounting_admin_color']['value'],
            formaction=url_for('accountingNewLedgerView'),
            backToUrl=url_for('accountingIndexView'),
            **pageFeatures,
        )


@app.route('/apps/accounting/editledger/<ledgerId>', methods=['GET', 'POST'])
@userRoleRequired({('system', 'admin')})
def accountingEditLedgerView(ledgerId):
    """Edit an existing ledger's 'basic properties'."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingIndexView',
        lsPathString='',
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'accounting'],
        g,
        overrides={
            'pageTitle': 'Edit ledger "%s"' % ledgerId,
            'pageSubtitle': 'Change ledger properties',
        },
        appendedItems=[{
            'kind': 'link',
            'target': None,
            'name': 'Edit ledger',
        }],
    )
    #
    form = AccountingBaseLedgerForm()
    ledger = dbGetLedger(db, ledgerId)
    #
    usersInLedger = sorted(
        dbGetUsersForLedger(db, user, ledgerId),
        key=lambda u: u.username.lower(),
    )
    usernamesInLedger = {u.username for u in usersInLedger}
    usersOutsideLedger = sorted(
        [
            u
            for u in dbGetAllUsers(db, user)
            if u.username not in usernamesInLedger
        ],
        key=lambda u: u.username.lower(),
    )
    #
    if ledger is None:
        raise OstracionError('Unknown ledger "%s"' % ledgerId)
    else:
        if form.validate_on_submit():
            if form.ledgerId.data == ledgerId:
                newLedger = Ledger(**recursivelyMergeDictionaries(
                    {
                        'ledger_id': form.ledgerId.data,
                        'name': form.name.data,
                        'description': form.description.data,
                    },
                    defaultMap=ledger.asDict(),
                ))
                dbUpdateLedger(db, user, newLedger)
                return redirect(url_for('accountingIndexView'))
            else:
                raise OstracionError('Illegitimate editing of ledger')
        else:
            form.ledgerId.data = ledger.ledger_id
            form.name.data = ledger.name
            form.description.data = ledger.description
            return render_template(
                'apps/accounting/editledger.html',
                user=user,
                ledgerform=form,
                #
                ledger=ledger,
                # These two (the first) suppresses the actor section of the form
                actorform=None,
                actors=[],
                #
                handleUsers=True,
                usersInLedger=usersInLedger,
                usersOutsideLedger=usersOutsideLedger,
                #
                bgcolor=g.settings['color']['app_colors'][
                    'accounting_main_color']['value'],
                admin_bgcolor=g.settings['color']['app_colors'][
                    'accounting_admin_color']['value'],
                formaction=url_for('accountingEditLedgerView', ledgerId=ledgerId),
                lockLedgerId=True,
                backToUrl=url_for('accountingIndexView'),
                **pageFeatures,
            )


@app.route('/apps/accounting/deleteledger/<ledgerId>')
@userRoleRequired({('system', 'admin')})
def accountingDeleteLedgerView(ledgerId):
    """Delete a ledger."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingIndexView',
        lsPathString='',
    )
    dbDeleteLedger(
        db,
        user,
        ledgerId,
    )
    return redirect(url_for('accountingIndexView'))


@app.route('/apps/accounting/addusertoledger/<ledgerId>/<username>')
@userRoleRequired({('system', 'admin')})
def accountingAddUserToLedgerView(ledgerId, username):
    """Add a user to an existing ledger."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingEditLedgerView',
        ledgerId=ledgerId,
    )
    #
    ledger = dbGetLedger(db, ledgerId)
    userToAdd = dbGetUser(db, username)
    #
    if ledger is not None:
        if userToAdd is not None:
            # actual adding
            dbAddUserToLedger(db, user, ledger, userToAdd)
            return redirect(url_for(
                'accountingEditLedgerView',
                ledgerId=ledgerId,
            ))
        else:
            raise OstracionError('Unknown user')
    else:
        raise OstracionError('Unknown ledger')


@app.route('/apps/accounting/removeuserfromledger/<ledgerId>/<username>')
@userRoleRequired({('system', 'admin')})
def accountingRemoveUserFromLedgerView(ledgerId, username):
    """Remove a user from an existing ledger."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingEditLedgerView',
        ledgerId=ledgerId,
    )
    #
    ledger = dbGetLedger(db, ledgerId)
    userToRemove = dbGetUser(db, username)
    #
    if ledger is not None:
        if userToRemove is not None:
            # actual adding
            dbRemoveUserFromLedger(db, user, ledger, userToRemove)
            return redirect(url_for(
                'accountingEditLedgerView',
                ledgerId=ledgerId,
            ))
        else:
            raise OstracionError('Unknown user')
    else:
        raise OstracionError('Unknown ledger')
