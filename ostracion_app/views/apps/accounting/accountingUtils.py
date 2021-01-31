""" accountingUtils.py: utilities behind the accounting app. """

from flask import url_for
import datetime
import uuid
import json

from ostracion_app.utilities.tools.extraction import (
    safeNone,
    safeInt,
    safeFloat,
)

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
    convertIterableToDictOfLists,
)

from ostracion_app.views.apps.appsPageTreeDescriptor import appsPageDescriptor

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

from ostracion_app.utilities.database.userTools import (
    getUserFullName,
)

from ostracion_app.utilities.database.permissions import (
    userHasRole,
    userIsAdmin,
)

from ostracion_app.views.apps.accounting.db.accountingTools import (
    dbGetLedger,
    dbGetCategoriesForLedger,
    dbGetSubcategoriesForLedger,
    dbGetUsersForLedger,
    dbGetActorsForLedger,
    dbUpdateLedger,
    dbGetLedgerFullMovements,
    dbIsCategoryRepresentedInLedger,
    dbIsSubcategoryRepresentedInLedger,
)
from ostracion_app.views.apps.accounting.settings import ledgerDatetimeFormat
from ostracion_app.views.apps.accounting.models.Ledger import Ledger
from ostracion_app.views.apps.accounting.models.LedgerMovement import (
    LedgerMovement,
)
from ostracion_app.views.apps.accounting.models.\
    LedgerMovementContribution import LedgerMovementContribution


def makeItemUniqueId():
    return str(uuid.uuid4())


def isLedgerId(db, user, ledgerId):
    """
        Check if the ledgerId corresponds to a ledger
        and return True in that case.
    """
    return dbGetLedger(db, user, ledgerId) is not None


def extractLedgerCategoryTree(db, user, ledger):
    """
        Extract, for a given ledger, the tree
            categories -> subcategories
        and cast it as a tree suitable for rendering.
    """
    return sorted(
        [
            {
                'category': cat,
                'subcategories': sorted(
                    [
                        subcat
                        for subcat in dbGetSubcategoriesForLedger(
                            db,
                            user,
                            ledger,
                            cat,
                        )
                    ],
                    key=lambda subcat: subcat.sort_index,
                )
            }
            for cat in dbGetCategoriesForLedger(db, user, ledger)
        ],
        key=lambda cObj: cObj['category'].sort_index,
    )


def prepareAccountingCategoryViewFeatures(g, ledgerId, overrides={}):
    """
        Factored-away preparation of features for the "ledger categories"
        admin-only page.
    """
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'accounting'],
        g,
        overrides=recursivelyMergeDictionaries(
            overrides,
            defaultMap={
                'pageTitle': 'Categories for ledger "%s"' % ledgerId,
                'pageSubtitle': ('Configure categorisation of ledger '
                                 'movements. Use the "+" buttons to add '
                                 'new categories/subcategories, and the '
                                 'buttons on each row to delete/move the '
                                 'item.'),
            },
        ),
        appendedItems=[{
            'kind': 'link',
            'target': None,
            'name': 'Categories for ledger',
        }],
    )
    return pageFeatures


def prepareLedgerActions(db, user, ledger):
    """
        Prepare the ledger-specific actions for display in cards.
    """
    lActions = {}
    #
    if userHasRole(db, user, 'app', 'accounting') or userIsAdmin(db, user):
        if userIsAdmin(db, user):
            lActions['metadata'] = url_for(
                'accountingEditLedgerView',
                ledgerId=ledger.ledger_id,
            )
            lActions['app_accounting_users'] = url_for(
                'accountingLedgerUsersView',
                ledgerId=ledger.ledger_id,
            )
            lActions['app_accounting_actors'] = url_for(
                'accountingLedgerActorsView',
                ledgerId=ledger.ledger_id,
            )
            lActions['app_accounting_categories'] = url_for(
                'accountingLedgerCategoriesView',
                ledgerId=ledger.ledger_id,
            )
            lActions['delete'] = url_for(
                'accountingDeleteLedgerView',
                ledgerId=ledger.ledger_id,
            )
            lActions['icon'] = url_for(
                'setIconView',
                mode='accounting_ledger',
                itemPathString=ledger.ledger_id,
            )
    #
    return lActions


def prepareLedgerSummary(db, user, ledger):
    """Calculate a text summary of a ledger."""
    namedFields = ['ledger_id', 'name', 'description', 'creator_username',
                   'creation_date',  'configuration_date', 'last_edit_date',
                   'last_edit_username', 'icon_file_id',
                   'icon_file_id_username', 'icon_mime_type']
    numActors = len(list(dbGetActorsForLedger(db, user, ledger)))
    lastEditDate = ledger.last_edit_date
    return '%i actor%s. Last edited: %s' % (
        numActors,
        '' if numActors == 1 else 's',
        lastEditDate.strftime(' %b %d %H:%M'),
    )


def prepareLedgerInfo(db, user, ledger):
    """Calculate ledger information for display."""
    return [
        infoItem
        for infoItem in (
            {
                'action': 'Created',
                'actor': getUserFullName(db, ledger.creator_username),
            },
            {
                'action': 'Edited by',
                'actor': (getUserFullName(db, ledger.last_edit_username)
                          if (ledger.creator_username
                              != ledger.last_edit_username)
                          else None),
            },
            {
                'action': 'Icon',
                'actor': getUserFullName(db, ledger.icon_file_id_username),
            },
        )
        if infoItem['actor'] is not None
    ]


def parseNewMovementContributions(db, user, ledger, movementForm, actors,
                                  movement):
    """
        Parse and normalize the contributions part of a movement from a form.
        Use data from the 'movement' (in part. the movement_id)

        May return None upon unparseable inputs (which fails the whole parsing)
    """
    # string(/None) actor-to-input maps
    paidMap = {
        a.actor_id: safeFloat(
            getattr(
                movementForm,
                'actorpaid_%s' % a.actor_id,
            ).data,
            admitCommas=True,
        )
        for a in actors
    }
    propMap = {
        a.actor_id: safeInt(
            getattr(
                movementForm,
                'actorprop_%s' % a.actor_id,
            ).data
        )
        for a in actors
    }
    # proportions logic (with fallback)
    if all(v is None for v in propMap.values()):
        # default, equidistribution
        finalPropMap = {k: 1 for k in propMap.keys()}
    else:
        # normalisation of the input integers
        finalPropMap = {k: safeNone(v, 0) for k, v in propMap.items()}
    #
    finalPaidMap = {k: safeNone(v, 0) for k, v in paidMap.items()}
    totalPaid = sum(finalPaidMap.values())
    totalProp = sum(finalPropMap.values())
    if totalProp > 0:
        dueMap = {
            k: totalPaid * v / totalProp
            for k, v in finalPropMap.items()
        }
        # preparation of the contributions
        contributions = {
            actor.actor_id: LedgerMovementContribution(
                ledger_id=ledger.ledger_id,
                movement_id=movement.movement_id,
                actor_id=actor.actor_id,
                paid=finalPaidMap[actor.actor_id],
                due=dueMap[actor.actor_id],
                proportion=finalPropMap[actor.actor_id],
            )
            for actor in actors
        }
        #
        return contributions
    else:
        return None


def parseNewMovementForm(db, user, ledger, movementForm, categoryTree,
                         actors, preexistingId=None):
    """
        Parse the contents of a new-movement-form into (either None or)
        a structure describing the full movement information
    """
    # noncategory fields from form
    mvDate = datetime.datetime.strptime(
        movementForm.date.data,
        ledgerDatetimeFormat,
    )
    mvDescription = safeNone(movementForm.description.data)
    # sub/category normalisation
    categoryMap = {cObj['category'].category_id: cObj for cObj in categoryTree}
    mvCatId = movementForm.categoryId.data
    subcategoryMap = {
        sc.subcategory_id: sc
        for sc in categoryMap[mvCatId]['subcategories']
    }
    # in the form this is "cat_id.subcat_id" for unicity, so:
    splCatId, splSubcatId = movementForm.subcategoryId.data.split('.')
    if splCatId != mvCatId or splSubcatId not in subcategoryMap:
        return None
    else:
        mvSubcatId = subcategoryMap[splSubcatId].subcategory_id
        # movement generation
        movementId = (
            makeItemUniqueId()
            if preexistingId is None
            else preexistingId
        )
        movement = LedgerMovement(
            ledger_id=ledger.ledger_id,
            movement_id=movementId,
            category_id=mvCatId,
            subcategory_id=mvSubcatId,
            date=mvDate,
            description=mvDescription,
            last_edit_date=datetime.datetime.now(),
            last_edit_username=user.username,
        )
        # contributions logic
        contributions = parseNewMovementContributions(
            db,
            user,
            ledger,
            movementForm,
            actors,
            movement,
        )
        if contributions is None:
            return None
        else:
            return {
                'movement': movement,
                'contributions': contributions,
            }


def serializeLedgerQuery(query):
    """
        Prepare a cookie-savable string with a ledger-movement query stored
        in it.

        Default serdes is identity, with the exception of some fields.
    """
    serializable = {
        k: {
            'dateFrom': lambda w: datetime.datetime.strftime(
                w,
                '%Y-%m-%d %H:%M:%S',
            ),
            'dateTo': lambda w: datetime.datetime.strftime(
                w,
                '%Y-%m-%d %H:%M:%S',
            ),
        }.get(k, lambda w: w)(v)
        for k, v in query.items()
    }
    return json.dumps(serializable)


def deserializeLedgerQuery(sQuery):
    """Reverse the serialization of serializeLedgerQuery."""
    return {
        k: {
            'dateFrom': lambda w: datetime.datetime.strptime(
                w,
                '%Y-%m-%d %H:%M:%S',
            ),
            'dateTo': lambda w: datetime.datetime.strptime(
                w,
                '%Y-%m-%d %H:%M:%S',
            ),
        }.get(k, lambda w: w)(v)
        for k, v in json.loads(sQuery).items()
    }


def retrieveCookiedLedgerQuery(req, ledger):
    """Given a 'request' object, get its stored query."""
    sQuery = req.cookies.get('accounting_ledger_query_%s' % ledger.ledger_id)
    if sQuery is None:
        return {}
    else:
        return deserializeLedgerQuery(sQuery)


def setCookiedLedgerQuery(response, ledger, query):
    """
        Pile, on top of an already existing response, setting/deleting
        the cookie containing the ledger query for a ledger.
    """
    cookieName = 'accounting_ledger_query_%s' % ledger.ledger_id
    if query is not None and len(query) > 0:
        response.set_cookie(cookieName, serializeLedgerQuery(query))
    else:
        response.set_cookie(cookieName, '', expires=0)
    #
    return response


def refreshLedgerDuesMap(db, user, ledger):
    """
        Return the summary/summary_date info of a ledger packing it properly,
        updating the contents (on DB as well) if necessary.
    """
    if ledger.summary_date < ledger.last_edit_date:
        # perform updates: recalculates balance ...
        fullMovements = dbGetLedgerFullMovements(db, user, ledger)
        balance = convertIterableToDictOfLists(
            (
                (actorId, contribution)
                for movementObj in fullMovements
                for actorId, contribution in movementObj[
                    'contributions'].items()
            ),
            keyer=lambda conP: conP[0],
            valuer=lambda conP: (conP[1].paid, conP[1].due),
        )

        def _reducePairs(pairs):
            if len(pairs) > 0:
                paids, dues = zip(*pairs)
                return sum(paids) - sum(dues)
            else:
                return 0.0

        duesMap = [
            duePair
            for duePair in (
                (actorId, _reducePairs(actorPairs))
                for actorId, actorPairs in sorted(balance.items())
            )
            if duePair[1] != 0
        ]
        # then update ledger summary/summaruy_date
        newLedger = Ledger(**recursivelyMergeDictionaries(
            {
                'ledger_id': ledger.ledger_id,
                'summary': json.dumps(duesMap),
                'summary_date': datetime.datetime.now(),
            },
            defaultMap=ledger.asDict(),
        ))
        dbUpdateLedger(db, user, newLedger)
        #
        ledgerF = newLedger
    else:
        ledgerF = ledger
    #
    summary = json.loads(ledgerF.summary)
    summaryDate = ledgerF.summary_date
    return {
        'summary_date': summaryDate,
        'summary': summary,
    }


def extractUsedCategoryTreeForLedger(db, user, ledger, categoryTree):
    """
        Make a categoryTree into a mapping of the sub/categories that are
        actually used in some movements on DB.
        (this is used to disable the "delete" button for categories).
    """
    return {
        catObj['category'].category_id: {
            'represented': dbIsCategoryRepresentedInLedger(
                db,
                user,
                ledger,
                catObj['category'],
            ),
            'subcategories': {
                subcategory.subcategory_id: dbIsSubcategoryRepresentedInLedger(
                    db,
                    user,
                    ledger,
                    subcategory,
                )
                for subcategory in catObj['subcategories']
            }
        }
        for catObj in categoryTree
    }
