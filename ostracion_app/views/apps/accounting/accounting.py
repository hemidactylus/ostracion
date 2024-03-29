"""
    accounting.py
        An app to manage ledgers of debts/credits among arbitrary actors
"""

import json
import datetime
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
    recursivelyMergeDictionaries,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.tools.formatting import (
    applyDefault,
    transformIfNotEmpty,
)

from ostracion_app.utilities.tools.extraction import safeInt

from ostracion_app.utilities.database.permissions import (
    userRoleRequired,
)

from ostracion_app.utilities.database.userTools import (
    dbGetAllUsers,
    dbGetUser,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
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
    generateAccountingMovementForm,
    generateAccountingLedgerQueryForm,
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
from ostracion_app.views.apps.accounting.settings import (
    ledgerDatetimeFormat,
    ledgerDatetimeFormatDesc,
    ledgerMovementPaginationPageSize,
    ledgerMovementPaginationShownPagesPerSide,
)
from ostracion_app.views.apps.accounting.accountingUtils import (
    isLedgerId,
    extractLedgerCategoryTree,
    prepareAccountingCategoryViewFeatures,
    prepareLedgerActions,
    prepareLedgerSummary,
    prepareLedgerInfo,
    parseNewMovementForm,
    retrieveCookiedLedgerQuery,
    setCookiedLedgerQuery,
    refreshLedgerDuesMap,
    extractUsedCategoryTreeForLedger,
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
    dbGetCategory,
    dbGetSubcategory,
    dbAddCategoryToLedger,
    dbAddSubcategoryToLedger,
    dbEraseCategoryFromLedger,
    dbDeleteSubcategoryFromLedger,
    dbMoveCategoryInLedger,
    dbMoveSubcategoryInLedger,
    dbAddFullMovementToLedger,
    dbUpdateFullMovementInLedger,
    dbGetLedgerFullMovements,
    dbCountLedgerFullMovements,
    dbGetLedgerFullMovement,
    dbDeleteLedgerFullMovement,
)
from ostracion_app.utilities.database.sqliteEngine import SqliteIntegrityError

from ostracion_app.app_main import app


@app.route('/apps/accounting/')
@app.route('/apps/accounting/index')
@userRoleRequired({('app', 'accounting'), ('system', 'admin')})
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
    ledgers = [
        {
            'ledger': ledger,
            # 'path': boxPath + [file.name],
            # 'nice_size': formatBytesSize(file.size),
            'info': prepareLedgerInfo(db, user, ledger),
            'actions': prepareLedgerActions(
                db,
                user,
                ledger,
            ),
            'summary': prepareLedgerSummary(db, user, ledger),
        }
        for ledger in dbGetAllLedgers(db, user)
    ]
    #
    return render_template(
        'apps/accounting/index.html',
        user=user,
        ledgers=ledgers,
        newLedgerImageUrl=makeSettingImageUrl(
            g,
            'custom_apps_images',
            'accounting_new_ledger',
        ),
        **pageFeatures,
    )


@app.route('/apps/accounting/newledger', methods=['GET', 'POST'])
@userRoleRequired({('system', 'admin')})
def accountingNewLedgerView():
    """Add a ledger. Uses the 'basic ledger properties' form."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('accountingIndexView')
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
                #
                formaction=url_for('accountingNewLedgerView'),
                backToUrl=url_for('accountingIndexView'),
                **pageFeatures,
            )
        else:
            #
            dateNow = datetime.datetime.now()
            newLedger = Ledger(
                ledger_id=form.ledgerId.data,
                name=form.name.data,
                description=form.description.data,
                creator_username=user.username,
                creation_date=dateNow,
                configuration_date=dateNow,
                last_edit_date=dateNow,
                last_edit_username=user.username,
                icon_file_id='',
                icon_file_id_username=user.username,
                icon_mime_type='',
                summary='{}',
                summary_date=dateNow,
            )
            dbCreateLedger(db, user, newLedger)
            return redirect(url_for('accountingIndexView'))
    else:
        return render_template(
            'apps/accounting/editledger.html',
            user=user,
            ledgerform=form,
            #
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
    request._onErrorUrl = url_for('accountingIndexView')
    #
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'accounting'],
        g,
        overrides={
            'pageTitle': 'Edit ledger "%s"' % ledgerId,
            'pageSubtitle': 'Change ledger properties',
            'iconUrl': makeSettingImageUrl(
                g,
                'custom_apps_images',
                'accounting_ledger',
            ),
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
        if form.validate_on_submit():
            if form.ledgerId.data == ledgerId:
                newLedger = Ledger(**recursivelyMergeDictionaries(
                    {
                        'ledger_id': form.ledgerId.data,
                        'name': form.name.data,
                        'description': form.description.data,
                        'configuration_date': datetime.datetime.now(),
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
                ledger=ledger,
                formaction=url_for(
                    'accountingEditLedgerView',
                    ledgerId=ledgerId,
                ),
                lockLedgerId=True,
                backToUrl=url_for('accountingIndexView'),
                **pageFeatures,
            )


@app.route('/apps/accounting/deleteledger/<ledgerId>')
@app.route('/apps/accounting/deleteledger/<ledgerId>/<int:confirm>')
@userRoleRequired({('system', 'admin')})
def accountingDeleteLedgerView(ledgerId, confirm=0):
    """Delete a ledger."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('accountingIndexView')
    ledger = dbGetLedger(db, user, ledgerId)
    if ledger is not None:
        if confirm == 0:
            pageFeatures = prepareTaskPageFeatures(
                appsPageDescriptor,
                ['root', 'accounting'],
                g,
                appendedItems=[
                    {
                        'kind': 'link',
                        'link': False,
                        'target': url_for(
                            'accountingDeleteLedgerView',
                            ledgerId=ledgerId,
                        ),
                        'name': 'Delete ledger',
                    }
                ],
                overrides={
                    'iconUrl': makeSettingImageUrl(
                        g,
                        'custom_apps_images',
                        'accounting_delete_ledger',
                    ),
                    'pageTitle': None,
                    'pageSubtitle': None,
                }
            )
            return render_template(
                'confirmoperation.html',
                contents={},
                user=user,
                confirmation={
                    'heading': (
                                'Warning: this will irreversibly delete '
                                'ledger "%s", its configuration and all '
                                'movements registered therein. It is a '
                                'destructive operation: there is no way back'
                               ) % ledger.name,
                    'forwardToUrl': url_for(
                        'accountingDeleteLedgerView',
                        ledgerId=ledgerId,
                        confirm=1,
                    ),
                    'backToUrl': url_for('accountingIndexView'),
                },
                **pageFeatures,
            )
        else:
            dbDeleteLedger(
                db,
                user,
                ledger,
            )
            flashMessage(
                'Success',
                'Success',
                'Ledger "%s" successfully deleted' % ledger.name,
            )
            return redirect(url_for('accountingIndexView'))
    else:
        raise OstracionError('Ledger not found')


@app.route('/apps/accounting/ledgerusers/<ledgerId>')
@userRoleRequired({('system', 'admin')})
def accountingLedgerUsersView(ledgerId):
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('accountingIndexView')
    #
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'accounting'],
        g,
        overrides={
            'pageTitle': 'Users for ledger "%s"' % ledgerId,
            'pageSubtitle': 'Define Ostracion users with access to the ledger',
            'iconUrl': makeSettingImageUrl(
                g,
                'custom_apps_images',
                'accounting_ledger',
            ),
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
        #
        usernamesInLedger = {u.username for u in usersInLedger}
        richUserObjects = [
            {
                'user': u,
                'in_ledger': u.username in usernamesInLedger,
            }
            for u in sorted(
                dbGetAllUsers(db, user),
                key=lambda usr: usr.username.lower(),
            )
        ]
        #
        return render_template(
            'apps/accounting/ledgerusers.html',
            user=user,
            #
            ledger=ledger,
            #
            usersInLedger=usersInLedger,
            richUserObjects=richUserObjects,
            #
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
            # record config editing
            newLedger = Ledger(**recursivelyMergeDictionaries(
                {
                    'configuration_date': datetime.datetime.now(),
                },
                defaultMap=ledger.asDict(),
            ))
            dbUpdateLedger(db, user, newLedger)
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
            # record config editing
            newLedger = Ledger(**recursivelyMergeDictionaries(
                {
                    'configuration_date': datetime.datetime.now(),
                },
                defaultMap=ledger.asDict(),
            ))
            dbUpdateLedger(db, user, newLedger)
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
    request._onErrorUrl = url_for('accountingIndexView')
    #
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'accounting'],
        g,
        overrides={
            'pageTitle': 'Actors for ledger "%s"' % ledgerId,
            'pageSubtitle': 'Configure actors taking part in the ledger',
            'iconUrl': makeSettingImageUrl(
                g,
                'custom_apps_images',
                'accounting_ledger',
            ),
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
            # record config editing
            newLedger = Ledger(**recursivelyMergeDictionaries(
                {
                    'configuration_date': datetime.datetime.now(),
                },
                defaultMap=ledger.asDict(),
            ))
            dbUpdateLedger(db, user, newLedger)
            # adding the actor
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
                backToUrl=url_for('accountingIndexView'),
                **pageFeatures,
            )


@app.route('/apps/accounting/deleteledgeractor/<ledgerId>/<actorId>')
@userRoleRequired({('system', 'admin')})
def accountingRemoveActorView(ledgerId, actorId):
    """Remove an actor from a ledger."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('accountingIndexView')
    #
    ledger = dbGetLedger(db, user, ledgerId)
    actor = dbGetActor(db, user, ledgerId, actorId)
    #
    if ledger is not None:
        if actor is not None:
            try:
                # removing the actor
                dbDeleteActor(db, user, ledger, actor)
            except SqliteIntegrityError:
                db.rollback()
                raise OstracionError('Actor is in use')
            # record config editing
            newLedger = Ledger(**recursivelyMergeDictionaries(
                {
                    'configuration_date': datetime.datetime.now(),
                },
                defaultMap=ledger.asDict(),
            ))
            dbUpdateLedger(db, user, newLedger)
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
    request._onErrorUrl = url_for('accountingIndexView')
    #
    pageFeatures = prepareAccountingCategoryViewFeatures(
        g,
        ledgerId,
        overrides={
            'iconUrl': makeSettingImageUrl(
                g,
                'custom_apps_images',
                'accounting_ledger',
            ),
        },
    )
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
        representedCategoryTree = extractUsedCategoryTreeForLedger(
            db,
            user,
            ledger,
            categoryTree,
        )
        return render_template(
            'apps/accounting/ledgercategories.html',
            user=user,
            #
            ledger=ledger,
            #
            categoryTree=categoryTree,
            categoryform=categoryform,
            subcategoryform=subcategoryform,
            representedCategoryTree=representedCategoryTree,
            #
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
            if newCategory.category_id not in {
                catObj['category'].category_id
                for catObj in categoryTree
            }:
                # record config editing
                newLedger = Ledger(**recursivelyMergeDictionaries(
                    {
                        'configuration_date': datetime.datetime.now(),
                    },
                    defaultMap=ledger.asDict(),
                ))
                dbUpdateLedger(db, user, newLedger)
                # add category
                dbAddCategoryToLedger(db, user, ledger, newCategory)
                return redirect(url_for(
                    'accountingLedgerCategoriesView',
                    ledgerId=ledgerId,
                ))
            else:
                flashMessage('Warning', 'Warning', 'Category exists already')
                return redirect(url_for(
                    'accountingLedgerCategoriesView',
                    ledgerId=ledger.ledger_id,
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
                if newSubcategory.subcategory_id not in {
                    subcat.subcategory_id
                    for subcat in targetCategoryObj['subcategories']
                }:
                    # record config editing
                    newLedger = Ledger(**recursivelyMergeDictionaries(
                        {
                            'configuration_date': datetime.datetime.now(),
                        },
                        defaultMap=ledger.asDict(),
                    ))
                    dbUpdateLedger(db, user, newLedger)
                    # add subcategory
                    dbAddSubcategoryToLedger(db, user, ledger, newSubcategory)
                    return redirect(url_for(
                        'accountingLedgerCategoriesView',
                        ledgerId=ledgerId,
                    ))
                else:
                    flashMessage(
                        'Warning',
                        'Warning',
                        'Subcategory exists already',
                    )
                    return redirect(url_for(
                        'accountingLedgerCategoriesView',
                        ledgerId=ledger.ledger_id,
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
                backToUrl=url_for('accountingIndexView'),
                **pageFeatures,
            )


@app.route((
            '/apps/accounting/ledgercategories/removecategory/'
            '<ledgerId>/<categoryId>'
          ))
@userRoleRequired({('system', 'admin')})
def accountingLedgerRemoveCategoryView(ledgerId, categoryId):
    """Removal of a category from a ledger setup. All subcats go as well."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingLedgerCategoriesView',
        ledgerId=ledgerId,
    )
    ledger = dbGetLedger(db, user, ledgerId)
    category = dbGetCategory(db, user, ledgerId, categoryId)
    if ledger is not None and category is not None:
        # erase category
        try:
            dbEraseCategoryFromLedger(db, user, ledger, category)
            # record config editing
            newLedger = Ledger(**recursivelyMergeDictionaries(
                {
                    'configuration_date': datetime.datetime.now(),
                },
                defaultMap=ledger.asDict(),
            ))
            dbUpdateLedger(db, user, newLedger)
        except SqliteIntegrityError:
            db.rollback()
            raise OstracionError('Category is in use')
        return redirect(url_for(
            'accountingLedgerCategoriesView',
            ledgerId=ledger.ledger_id,
        ))
    else:
        raise OstracionError('Ledger/category not found')


@app.route((
            '/apps/accounting/ledgercategories/removesubcategory/'
            '<ledgerId>/<categoryId>/<subcategoryId>'
          ))
@userRoleRequired({('system', 'admin')})
def accountingLedgerRemoveSubcategoryView(ledgerId, categoryId, subcategoryId):
    """Removal of a subcategory from a ledger setup. All subcats go as well."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingLedgerCategoriesView',
        ledgerId=ledgerId,
    )
    ledger = dbGetLedger(db, user, ledgerId)
    category = dbGetCategory(db, user, ledgerId, categoryId)
    subcategory = dbGetSubcategory(db, user, ledgerId, categoryId,
                                   subcategoryId)
    if ledger is not None and category is not None and subcategory is not None:
        # erase subcategory
        try:
            dbDeleteSubcategoryFromLedger(
                db,
                user,
                ledger,
                category,
                subcategory,
            )
            # record config editing
            newLedger = Ledger(**recursivelyMergeDictionaries(
                {
                    'configuration_date': datetime.datetime.now(),
                },
                defaultMap=ledger.asDict(),
            ))
            dbUpdateLedger(db, user, newLedger)
        except SqliteIntegrityError:
            db.rollback()
            raise OstracionError('Subcategory is in use')
        return redirect(url_for(
            'accountingLedgerCategoriesView',
            ledgerId=ledger.ledger_id,
        ))
    else:
        raise OstracionError('Ledger/category/subcategory not found')


@app.route((
            '/apps/accounting/ledgercategories/movecategory/'
            '<ledgerId>/<categoryId>/<direction>'
          ))
@userRoleRequired({('system', 'admin')})
def accountingLedgerMoveCategoryView(ledgerId, categoryId, direction):
    """Reshuffle of a category in a ledger setup."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingLedgerCategoriesView',
        ledgerId=ledgerId,
    )
    ledger = dbGetLedger(db, user, ledgerId)
    category = dbGetCategory(db, user, ledgerId, categoryId)
    if ledger is not None and category is not None:
        # record config editing
        newLedger = Ledger(**recursivelyMergeDictionaries(
            {
                'configuration_date': datetime.datetime.now(),
            },
            defaultMap=ledger.asDict(),
        ))
        dbUpdateLedger(db, user, newLedger)
        # move category
        dbMoveCategoryInLedger(db, user, ledger, category, direction)
        return redirect(url_for(
            'accountingLedgerCategoriesView',
            ledgerId=ledger.ledger_id,
        ))
    else:
        raise OstracionError('Ledger/category not found')


@app.route((
            '/apps/accounting/ledgercategories/movesubcategory/'
            '<ledgerId>/<categoryId>/<subcategoryId>/<direction>'
          ))
@userRoleRequired({('system', 'admin')})
def accountingLedgerMoveSubcategoryView(ledgerId, categoryId, subcategoryId,
                                        direction):
    """Reshuffle of a subcategory in a ledger setup."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'accountingLedgerCategoriesView',
        ledgerId=ledgerId,
    )
    ledger = dbGetLedger(db, user, ledgerId)
    category = dbGetCategory(db, user, ledgerId, categoryId)
    subcategory = dbGetSubcategory(db, user, ledgerId, categoryId,
                                   subcategoryId)
    if ledger is not None and category is not None and subcategory is not None:
        # record config editing
        newLedger = Ledger(**recursivelyMergeDictionaries(
            {
                'configuration_date': datetime.datetime.now(),
            },
            defaultMap=ledger.asDict(),
        ))
        dbUpdateLedger(db, user, newLedger)
        # move subcategory
        dbMoveSubcategoryInLedger(db, user, ledger, category, subcategory,
                                  direction)
        return redirect(url_for(
            'accountingLedgerCategoriesView',
            ledgerId=ledger.ledger_id,
        ))
    else:
        raise OstracionError('Ledger/category/subcategory not found')


@app.route('/apps/accounting/ledger/<ledgerId>', methods=['GET', 'POST'])
@app.route(
    '/apps/accounting/ledger/<ledgerId>/editmovement/<movementId>',
    methods=['GET', 'POST'],
)
def accountingLedgerView(ledgerId, movementId=None):
    """
        Ledger view, to act on it in various vays.
        There is a form, used either to add a new movement
        or to edit a preexisting one (which determines also the form position).
        These operations go through this single route.

        movementId is passed only when editing an existing movement.
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('accountingIndexView')
    ledger = dbGetLedger(db, user, ledgerId)
    if ledger is not None:
        categoryTree = extractLedgerCategoryTree(db, user, ledger)
        actorsInLedger = sorted(
            dbGetActorsForLedger(db, user, ledger),
            key=lambda a: a.actor_id.lower(),
        )
        #
        addmovementform = generateAccountingMovementForm(
            categoryTree,
            actorsInLedger,
        )
        queryform = generateAccountingLedgerQueryForm(
            categoryTree,
            actorsInLedger,
        )
        query = retrieveCookiedLedgerQuery(request, ledger)
        # query to queryform
        queryform.receiveValues(query)
        #
        pageIndex0 = safeInt(request.args.get('page'), default=0)
        #
        if addmovementform.validate_on_submit():
            # try to load the preexisting movement if ID provided
            # (it means we are in the edit-existing-movement flow)
            if movementId is not None:
                preexistingMovementObj = dbGetLedgerFullMovement(
                    db,
                    user,
                    ledger,
                    movementId,
                )
                if preexistingMovementObj is not None:
                    preexistingMovementId = preexistingMovementObj[
                        'movement'].movement_id
                else:
                    raise OstracionError('Unknown ledger movement')
            else:
                preexistingMovementId = None
            #
            newMovementStructure = parseNewMovementForm(
                db,
                user,
                ledger,
                addmovementform,
                categoryTree,
                actorsInLedger,
                preexistingId=preexistingMovementId
            )
            if newMovementStructure is not None:
                # perform the actual DB insertions and redirect user to ledger
                if preexistingMovementId is None:
                    # new-item insertion
                    dbAddFullMovementToLedger(
                        db,
                        user,
                        ledger,
                        newMovementStructure['movement'],
                        newMovementStructure['contributions'],
                    )
                else:
                    # update-existing-item
                    dbUpdateFullMovementInLedger(
                        db,
                        user,
                        ledger,
                        newMovementStructure['movement'],
                        newMovementStructure['contributions'],
                    )
                #
                return redirect(url_for(
                    'accountingLedgerView',
                    ledgerId=ledgerId,
                    page=pageIndex0,
                ))
            else:
                request._onErrorUrl = url_for(
                    'accountingLedgerView',
                    ledgerId=ledgerId,
                )
                raise OstracionError('Malformed movement insertion')
        else:
            return finalizeLedgerView(
                db=db,
                user=user,
                ledger=ledger,
                movementId=movementId,
                queryform=queryform,
                query=query,
                categoryTree=categoryTree,
                addmovementform=addmovementform,
                actorsInLedger=actorsInLedger,
                pageIndex0=pageIndex0,
            )
    else:
        raise OstracionError('Ledger not found')


@app.route('/apps/accounting/ledger/rmmovement/<ledgerId>/<movementId>')
def accountingLedgerDeleteMovementView(ledgerId, movementId):
    """Delete a full movement from a ledger."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('accountingIndexView')
    ledger = dbGetLedger(db, user, ledgerId)
    if ledger is not None:
        movementObj = dbGetLedgerFullMovement(db, user, ledger, movementId)
        if movementObj is not None:
            pageIndex = safeInt(request.args.get('page'), default=0)
            dbDeleteLedgerFullMovement(
                db,
                user,
                ledger,
                movementObj['movement'],
            )
            return redirect(url_for(
                'accountingLedgerView',
                ledgerId=ledgerId,
                page=pageIndex,
            ))
        else:
            raise OstracionError('Movement not found')
    else:
        raise OstracionError('Ledger not found')


@app.route('/apps/accounting/ledger/alterquery/<ledgerId>', methods=['POST'])
def accountingLedgerAlterQueryView(ledgerId):
    """
        A POST-only route that receives a 'ledger movement query' form,
        parses its arguments, alters the cookied query and redirects to
        the ledger view for display.
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('accountingLedgerView', ledgerId=ledgerId)
    ledger = dbGetLedger(db, user, ledgerId)
    if ledger is not None:
        #
        categoryTree = extractLedgerCategoryTree(db, user, ledger)
        actorsInLedger = sorted(
            dbGetActorsForLedger(db, user, ledger),
            key=lambda a: a.actor_id.lower(),
        )
        queryform = generateAccountingLedgerQueryForm(
            categoryTree,
            actorsInLedger,
        )
        #
        if queryform.validate_on_submit():
            # should set cookie with new query
            query = {
                k: v
                for k, v in {
                    'dateFrom': transformIfNotEmpty(
                        queryform.dateFrom.data,
                        tformer=lambda s: datetime.datetime.strptime(
                            s.strip(),
                            ledgerDatetimeFormat,
                        ),
                    ),
                    'dateTo': transformIfNotEmpty(
                        queryform.dateTo.data,
                        tformer=lambda s: datetime.datetime.strptime(
                            s.strip(),
                            ledgerDatetimeFormat,
                        ),
                    ),
                    'description': (
                        queryform.description.data.strip()
                        if queryform.description.data.strip() != ''
                        else None
                    ),
                    'categoryId': (
                        queryform.categoryId.data
                        if queryform.categoryId.data != ''
                        else None
                    ),
                    'subcategoryId': (
                        queryform.subcategoryId.data.split('.')[1]
                        if (
                            queryform.subcategoryId.data != '' and
                            (
                                queryform.categoryId.data
                                == queryform.subcategoryId.data.split('.')[0]
                            )
                        )
                        else None
                    ),
                }.items()
                if v is not None
            }
            response0 = redirect(url_for(
                'accountingLedgerView',
                ledgerId=ledgerId,
            ))
            response = setCookiedLedgerQuery(response0, ledger, query)
            return response
        else:
            categoryTree = extractLedgerCategoryTree(db, user, ledger)
            query = retrieveCookiedLedgerQuery(request, ledger)
            #
            addmovementform = generateAccountingMovementForm(
                categoryTree,
                actorsInLedger,
            )
            return finalizeLedgerView(
                db=db,
                user=user,
                ledger=ledger,
                movementId=None,
                queryform=queryform,
                query=query,
                categoryTree=categoryTree,
                addmovementform=addmovementform,
                actorsInLedger=actorsInLedger,
                pageIndex0=0,
            )
    else:
        raise OstracionError('Ledger not found')


@app.route('/apps/accounting/ledger/resetquery/<ledgerId>', methods=['GET'])
def accountingLedgerResetQueryView(ledgerId):
    """
        A get-and-redirect route to reset (erase) the ledger query, which
        results in the cookied query to be deleted.
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('accountingLedgerView', ledgerId=ledgerId)
    ledger = dbGetLedger(db, user, ledgerId)
    if ledger is not None:
        response0 = redirect(url_for(
            'accountingLedgerView',
            ledgerId=ledgerId,
        ))
        response = setCookiedLedgerQuery(response0, ledger, None)
        return response
    else:
        raise OstracionError('Ledger not found')


def finalizeLedgerView(db, user, ledger, movementId, queryform, query,
                       categoryTree, addmovementform, actorsInLedger,
                       pageIndex0):
    """
        Utility function where two (proper) routes end up: the set-query
        and (some cases of) the generic view-ledger.
        This expects to run within a request context, prepares pagination
        and positioning things and invokes the template for viewing a ledger.
    """
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'accounting'],
        g,
        appendedItems=[{
            'kind': 'link',
            'target': url_for(
                'accountingLedgerView',
                ledgerId=ledger.ledger_id,
            ),
            'name': ledger.ledger_id,
        }],
    )

    # pagination info preparation
    recordCount = dbCountLedgerFullMovements(db, user, ledger, query)
    totalPages = ((recordCount + ledgerMovementPaginationPageSize - 1)
                  // ledgerMovementPaginationPageSize)
    pageIndex = max(0, min(pageIndex0, totalPages - 1))
    fullMovementObjects = list(dbGetLedgerFullMovements(
        db=db,
        user=user,
        ledger=ledger,
        query=query,
        pageSize=ledgerMovementPaginationPageSize,
        pageStart=pageIndex * ledgerMovementPaginationPageSize,
    ))
    firstShownPage = max(
        1,
        pageIndex - ledgerMovementPaginationShownPagesPerSide,
    )
    lastShownPage = min(
        pageIndex + ledgerMovementPaginationShownPagesPerSide,
        totalPages - 1,
    )
    pagesToShow = [0] + list(range(
        firstShownPage,
        lastShownPage,
    )) + [totalPages - 1]
    paginationInfo = {
        'page_index': pageIndex,
        'total_pages': totalPages,
        'row_count': recordCount,
        'row_first_shown': (ledgerMovementPaginationPageSize
                            * pageIndex),
        'row_last_shown': (ledgerMovementPaginationPageSize * pageIndex
                           + len(fullMovementObjects) - 1),
        'pages_shown': pagesToShow,
    }

    # we decide how to split to insert edit form (editing/nonediting)
    if movementId is not None:
        splitIndices = [
            movIndex
            for movIndex, movObj in enumerate(fullMovementObjects)
            if movObj['movement'].movement_id == movementId
        ]
        if len(splitIndices) > 0:
            splitIndex = splitIndices[0]
        else:
            splitIndex = None
    else:
        splitIndex = None
    #
    preMovementObjects = (
        []
        if splitIndex is None
        else fullMovementObjects[:splitIndex]
    )
    postMovementObjects = (
        fullMovementObjects
        if splitIndex is None
        else fullMovementObjects[splitIndex + 1:]
    )
    if splitIndex is None:
        editeeMovement = None
    else:
        editeeMovement = fullMovementObjects[splitIndex]
    #
    paidFormFieldMap = {
        actor.actor_id: getattr(addmovementform,
                                'actorpaid_%s' % actor.actor_id)
        for actor in actorsInLedger
    }
    propFormFieldMap = {
        actor.actor_id: getattr(addmovementform,
                                'actorprop_%s' % actor.actor_id)
        for actor in actorsInLedger
    }
    #
    if editeeMovement is None:
        # new-movement form: just current date as default
        addmovementform.date.data = datetime.datetime.now().strftime(
            ledgerDatetimeFormat,
        )
    else:
        # edit-movement form: express the full movement
        addmovementform.date.data = editeeMovement[
            'movement'].date.strftime(ledgerDatetimeFormat)
        addmovementform.description.data = editeeMovement[
            'movement'].description
        addmovementform.categoryId.data = editeeMovement[
            'movement'].category_id
        addmovementform.subcategoryId.data = ('%s.%s' % (
            editeeMovement['movement'].category_id,
            editeeMovement['movement'].subcategory_id,
        ))
        for actor in actorsInLedger:
            if actor.actor_id in editeeMovement['contributions']:
                tMov = editeeMovement['contributions'][actor.actor_id]
                if tMov.paid != 0:
                    thisPaid = tMov.paid
                else:
                    thisPaid = None
                if tMov.proportion != 0:
                    thisProp = tMov.proportion
                else:
                    thisProp = None
            else:
                thisPaid = None
                thisProp = None
            paidFormFieldMap[actor.actor_id].data = applyDefault(
                transformIfNotEmpty(
                    thisPaid,
                    lambda pd: '%.2f' % pd,
                ),
                '',
            )
            propFormFieldMap[actor.actor_id].data = applyDefault(
                transformIfNotEmpty(thisProp, int),
                '',
            )

    # we decide whether to show the form at all (this controls
    # both edit-form and new-item-form aka nonediting)
    if editeeMovement is not None:
        displayMovementForm = True
    else:
        displayMovementForm = len(query) == 0 and pageIndex == 0
    # for appearance's sake
    applyingQuery = len(query) > 0
    #
    usernameToName = recursivelyMergeDictionaries(
        {
            u.username: u.fullname
            for u in dbGetUsersForLedger(db, user, ledger)
        },
        defaultMap={
            '': dbGetUser(db, '').fullname,
        },
    )
    actorIdToName = {
        a.actor_id: a.name
        for a in actorsInLedger
    }
    # in-page-js injected variables
    categoryTreeJSON = json.dumps(
        {
            catObj['category'].category_id: [
                subcat.subcategory_id
                for subcat in catObj['subcategories']
            ]
            for catObj in categoryTree
        },
        ensure_ascii=True,
    )
    catFullIdToDescriptionJSON = json.dumps(
        {
            catObj['category'].category_id: catObj['category'].description
            for catObj in categoryTree
        },
        ensure_ascii=True,
    )
    subcatFullIdToDescriptionJSON = json.dumps(
        {
            (
                '%s.%s' % (
                    catObj['category'].category_id,
                    subcat.subcategory_id,
                )
            ): subcat.description
            for catObj in categoryTree
            for subcat in catObj['subcategories']
        },
        ensure_ascii=True,
    )
    # balance refreshing if needed
    duesMap = refreshLedgerDuesMap(db, user, ledger)
    #
    return render_template(
        'apps/accounting/ledger.html',
        user=user,
        ledger=ledger,
        actors=actorsInLedger,
        actorIdToName=actorIdToName,
        duesMap=duesMap,
        usernameToName=usernameToName,
        editeeMovement=editeeMovement,
        preMovementObjects=preMovementObjects,
        postMovementObjects=postMovementObjects,
        ledgerDatetimeFormat=ledgerDatetimeFormat,
        ledgerDatetimeFormatDesc=ledgerDatetimeFormatDesc,
        numActors=len(actorsInLedger),
        addmovementform=addmovementform,
        queryform=queryform,
        categoryTreeJSON=categoryTreeJSON,
        catFullIdToDescriptionJSON=catFullIdToDescriptionJSON,
        subcatFullIdToDescriptionJSON=subcatFullIdToDescriptionJSON,
        displayMovementForm=displayMovementForm,
        applyingQuery=applyingQuery,
        paidFormFieldMap=paidFormFieldMap,
        propFormFieldMap=propFormFieldMap,
        paginationInfo=paginationInfo,
        **pageFeatures,
    )
