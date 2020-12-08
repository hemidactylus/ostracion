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
    AccountingLedgerCategoryForm,
    AccountingLedgerSubcategoryForm,
)

from ostracion_app.views.apps.accounting.models.Ledger import Ledger
from ostracion_app.views.apps.accounting.models.Actor import Actor
from ostracion_app.views.apps.accounting.models.MovementCategory import (
    MovementCategory,
)
from ostracion_app.views.apps.accounting.models.MovementSubcategory import (
    MovementSubcategory,
)
#
from ostracion_app.views.apps.accounting.accountingUtils import (
    isLedgerId,
    extractLedgerCategoryTree,
    prepareAccountingCategoryViewFeatures,
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
    dbGetActorsForLedger,
    dbAddActorToLedger,
    dbGetActor,
    dbDeleteActor,
    dbAddCategoryToLedger,
    dbGetCategory,
    dbAddSubcategoryToLedger,
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
        if isLedgerId(db, user, form.ledgerId.data):
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
    ledger = dbGetLedger(db, user, ledgerId)
    if ledger is None:
        raise OstracionError('Unknown ledger "%s"' % ledgerId)
    else:
        usersInLedger = sorted(
            dbGetUsersForLedger(db, user, ledger),
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
    ledger = dbGetLedger(db, user, ledgerId)
    dbDeleteLedger(
        db,
        user,
        ledger,
    )
    return redirect(url_for('accountingIndexView'))


@app.route('/apps/accounting/ledgerusers/<ledgerId>')
@userRoleRequired({('system', 'admin')})
def accountingLedgerUsersView(ledgerId):
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
            'pageTitle': 'Users for ledger "%s"' % ledgerId,
            'pageSubtitle': 'Define Ostracion users with access to the ledger',
        },
        appendedItems=[{
            'kind': 'link',
            'target': None,
            'name': 'Users for ledger',
        }],
    )
    ledger = dbGetLedger(db, user, ledgerId)
    if ledger is None:
        raise OstracionError('Unknown ledger "%s"' % ledgerId)
    else:
        usersInLedger = sorted(
            dbGetUsersForLedger(db, user, ledger),
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
        return render_template(
            'apps/accounting/ledgerusers.html',
            user=user,
            #
            ledger=ledger,
            #
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


@app.route('/apps/accounting/addusertoledger/<ledgerId>/<username>')
@userRoleRequired({('system', 'admin')})
def accountingAddUserToLedgerView(ledgerId, username):
    """Add a user to an existing ledger."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingLedgerUsersView',
        ledgerId=ledgerId,
    )
    #
    ledger = dbGetLedger(db, user, ledgerId)
    userToAdd = dbGetUser(db, username)
    #
    if ledger is not None:
        if userToAdd is not None:
            # actual adding
            dbAddUserToLedger(db, user, ledger, userToAdd)
            return redirect(url_for(
                'accountingLedgerUsersView',
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
        'accountingLedgerUsersView',
        ledgerId=ledgerId,
    )
    #
    ledger = dbGetLedger(db, user, ledgerId)
    userToRemove = dbGetUser(db, username)
    #
    if ledger is not None:
        if userToRemove is not None:
            # actual adding
            dbRemoveUserFromLedger(db, user, ledger, userToRemove)
            return redirect(url_for(
                'accountingLedgerUsersView',
                ledgerId=ledgerId,
            ))
        else:
            raise OstracionError('Unknown user')
    else:
        raise OstracionError('Unknown ledger')


@app.route('/apps/accounting/ledgeractors/<ledgerId>', methods=['GET', 'POST'])
@userRoleRequired({('system', 'admin')})
def accountingLedgerActorsView(ledgerId):
    """Actors configured for a ledger."""
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
            'pageTitle': 'Actors for ledger "%s"' % ledgerId,
            'pageSubtitle': 'Configure actors taking part in the ledger',
        },
        appendedItems=[{
            'kind': 'link',
            'target': None,
            'name': 'Actors for ledger',
        }],
    )
    ledger = dbGetLedger(db, user, ledgerId)
    if ledger is None:
        raise OstracionError('Unknown ledger "%s"' % ledgerId)
    else:
        actorform = AccountingLedgerActorForm()
        if actorform.validate_on_submit():
            newActor = Actor(
                ledger_id=ledger.ledger_id,
                actor_id=actorform.actorId.data,
                name=actorform.name.data,
            )
            dbAddActorToLedger(db, user, ledger, newActor)
            return redirect(url_for(
                'accountingLedgerActorsView',
                ledgerId=ledger.ledger_id,
            ))
        else:
            #
            actorsInLedger = sorted(
                dbGetActorsForLedger(db, user, ledger),
                key=lambda a: a.actor_id.lower(),
            )
            #
            return render_template(
                'apps/accounting/ledgeractors.html',
                user=user,
                #
                ledger=ledger,
                #
                actorsInLedger=actorsInLedger,
                actorform=actorform,
                #
                bgcolor=g.settings['color']['app_colors'][
                    'accounting_main_color']['value'],
                admin_bgcolor=g.settings['color']['app_colors'][
                    'accounting_admin_color']['value'],
                backToUrl=url_for('accountingIndexView'),
                **pageFeatures,
            )


@app.route('/apps/accounting/deleteledgeractor/<ledgerId>/<actorId>')
@userRoleRequired({('system', 'admin')})
def accountingRemoveActorView(ledgerId, actorId):
    """Remove an actor from a ledger."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingIndexView',
        lsPathString='',
    )
    #
    ledger = dbGetLedger(db, user, ledgerId)
    actor = dbGetActor(db, user, ledgerId, actorId)
    #
    if ledger is not None:
        if actor is not None:
            dbDeleteActor(db, user, ledger, actor)
            return redirect(url_for(
                'accountingLedgerActorsView',
                ledgerId=ledger.ledger_id,
            ))
        else:
            raise OstracionError('Unknown actor "%s"' % actorId)
    else:
        raise OstracionError('Unknown ledger "%s"' % ledgerId)


@app.route('/apps/accounting/ledgercategories/<ledgerId>')
@userRoleRequired({('system', 'admin')})
def accountingLedgerCategoriesView(ledgerId):
    """
        Categories configured for a ledger.
        This is a GET view only, the two 'add' POSTs go to separate views
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingIndexView',
        lsPathString='',
    )
    #
    pageFeatures = prepareAccountingCategoryViewFeatures(g, ledgerId)
    ledger = dbGetLedger(db, user, ledgerId)
    if ledger is None:
        raise OstracionError('Unknown ledger "%s"' % ledgerId)
    else:
        categoryTree = extractLedgerCategoryTree(db, user, ledger)
        categoryform = AccountingLedgerCategoryForm()
        subcategoryform = AccountingLedgerSubcategoryForm()
        subcategoryform.fillCategoryChoices(
            [cObj['category'].category_id for cObj in categoryTree],
        )
        #
        return render_template(
            'apps/accounting/ledgercategories.html',
            user=user,
            #
            ledger=ledger,
            #
            categoryTree=categoryTree,
            categoryform=categoryform,
            subcategoryform=subcategoryform,
            #
            bgcolor=g.settings['color']['app_colors'][
                'accounting_main_color']['value'],
            admin_bgcolor=g.settings['color']['app_colors'][
                'accounting_admin_color']['value'],
            backToUrl=url_for('accountingIndexView'),
            **pageFeatures,
        )


@app.route('/apps/accounting/ledgercategories/addcategory/<ledgerId>',
           methods=['POST'])
@userRoleRequired({('system', 'admin')})
def accountingLedgerAddCategoryView(ledgerId):
    """
        POST-only view to receive requests to add category to ledger.
        Once processed, user is redirected to the categories view (GET).
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingLedgerCategoriesView',
        ledgerId=ledgerId,
    )
    ledger = dbGetLedger(db, user, ledgerId)
    if ledger is None:
        raise OstracionError('Unknown ledger "%s"' % ledgerId)
    else:
        pageFeatures = prepareAccountingCategoryViewFeatures(g, ledgerId)
        #
        categoryTree = extractLedgerCategoryTree(db, user, ledger)
        subcategoryform = AccountingLedgerSubcategoryForm()
        subcategoryform.fillCategoryChoices(
            [cObj['category'].category_id for cObj in categoryTree],
        )
        categoryform = AccountingLedgerCategoryForm()
        #
        if categoryform.validate_on_submit():
            if len(categoryTree) > 0:
                newSortIndex = 1 + max(
                    cO['category'].sort_index for cO in categoryTree
                )
            else:
                newSortIndex = 0
            newCategory = MovementCategory(
                ledger_id=ledger.ledger_id,
                category_id=categoryform.categoryId.data,
                description=categoryform.description.data,
                sort_index=newSortIndex,
            )
            dbAddCategoryToLedger(db, user, ledger, newCategory)
            return redirect(url_for(
                'accountingLedgerCategoriesView',
                ledgerId=ledgerId,
            ))
        else:
            return render_template(
                'apps/accounting/ledgercategories.html',
                user=user,
                #
                ledger=ledger,
                #
                categoryTree=categoryTree,
                categoryform=categoryform,
                subcategoryform=subcategoryform,
                #
                bgcolor=g.settings['color']['app_colors'][
                    'accounting_main_color']['value'],
                admin_bgcolor=g.settings['color']['app_colors'][
                    'accounting_admin_color']['value'],
                backToUrl=url_for('accountingIndexView'),
                **pageFeatures,
            )


@app.route('/apps/accounting/ledgercategories/addsubcategory/<ledgerId>',
           methods=['POST'])
@userRoleRequired({('system', 'admin')})
def accountingLedgerAddSubcategoryView(ledgerId):
    """
        POST-only view to receive requests for adding a subcategory to
        a ledger.
        The category ID is part of the POST parameters, hence read through the
        appropriate form.
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingLedgerCategoriesView',
        ledgerId=ledgerId,
    )
    ledger = dbGetLedger(db, user, ledgerId)
    if ledger is None:
        raise OstracionError('Unknown ledger "%s"' % ledgerId)
    else:
        pageFeatures = prepareAccountingCategoryViewFeatures(g, ledgerId)
        #
        categoryTree = extractLedgerCategoryTree(db, user, ledger)
        subcategoryform = AccountingLedgerSubcategoryForm()
        subcategoryform.fillCategoryChoices(
            [cObj['category'].category_id for cObj in categoryTree],
        )
        categoryform = AccountingLedgerCategoryForm()
        #
        if subcategoryform.validate_on_submit():
            categoryId = subcategoryform.categoryId.data
            # this is a hack to get the match or None if missing
            targetCategoryObj = {
                i: v
                for i, v in enumerate(
                    cObj
                    for cObj in categoryTree
                    if cObj['category'].category_id == categoryId
                )
            }.get(0)
            if targetCategoryObj is not None:
                if len(targetCategoryObj['subcategories']) > 0:
                    newSortIndex = 1 + max(
                        subCat.sort_index
                        for subCat in targetCategoryObj['subcategories']
                    )
                else:
                    newSortIndex = 0
                newSubcategory = MovementSubcategory(
                    ledger_id=ledger.ledger_id,
                    category_id=categoryId,
                    subcategory_id=subcategoryform.subcategoryId.data,
                    description=subcategoryform.description.data,
                    sort_index=newSortIndex,
                )
                dbAddSubcategoryToLedger(db, user, ledger, newSubcategory)
                return redirect(url_for(
                    'accountingLedgerCategoriesView',
                    ledgerId=ledgerId,
                ))
            else:
                raise OstracionError('Unknown category')
        else:
            return render_template(
                'apps/accounting/ledgercategories.html',
                user=user,
                #
                ledger=ledger,
                #
                categoryTree=categoryTree,
                categoryform=categoryform,
                subcategoryform=subcategoryform,
                #
                bgcolor=g.settings['color']['app_colors'][
                    'accounting_main_color']['value'],
                admin_bgcolor=g.settings['color']['app_colors'][
                    'accounting_admin_color']['value'],
                backToUrl=url_for('accountingIndexView'),
                **pageFeatures,
            )