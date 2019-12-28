""" pageTreeDescriptorTools.py
    tools to manipulate generic page tree descriptors.
"""

from flask import (
    url_for,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)


def extractTopLevelTaskFromTreeDescriptor(tDesc, bgColorKey, g, overrides={}):
    """ Pick the top-level task item from a tree-descriptor
        and format it in a way fit for ls-view tasks.
    """
    rootTask = tDesc['tasks']['root']
    return recursivelyMergeDictionaries(
        overrides,
        defaultMap={
            'name': rootTask['title'],
            'description': rootTask['subtitle'],
            'url': url_for(
                rootTask['endpoint_name'][0],
                **rootTask['endpoint_name'][1],
            ),
            'thumbnail': makeSettingImageUrl(
                g,
                rootTask['image_id'][0],
                rootTask['image_id'][1],
            ),
            'bgcolor': g.settings['color']['task_colors'][bgColorKey]['value'],
        }
    )


def _filterTask(taskContents, prescription):
    """
        Recursive step in pruning a tree-descriptor as requested.

        'prescription' can be:
            - None, whereupon we keep everything
            - True, the same
            - False, we return None and block the task
            - a map, thereupon we work on 'tasks' recursively
    """
    if prescription is None:
        return taskContents
    elif isinstance(prescription, bool):
        return taskContents if prescription else None
    elif isinstance(prescription, dict):
        return {
            tk: tv if tk != 'tasks' else _filterTasks(tv, prescription)
            for tk, tv in taskContents.items()
        }
    else:
        raise NotImplementedError


def _filterTasks(taskMap, accessibilities):
    """ List form of _filterTask, where
        'accessibilities' is a map of prescriptions.
    """
    filteredTasks = {
        ftKey: ftVal
        for ftKey, ftVal in {
            tKey: _filterTask(tContents, accessibilities.get(tKey))
            for tKey, tContents in taskMap.items()
        }.items()
        if ftVal is not None
    }
    return filteredTasks


def filterToolsPageDescriptor(pDesc, subTasksAccessibility):
    '''
        Prune parts of a page tree descriptor according to a prescriptions.

        Given a (possibly nested) dictionary subTasksAccessibility
            {
                'root': True
            }
        or
            {
                'root': {
                    'task_in_root_1': True,
                    'task_in_root_2': False,
                }
            }
        (or more nesting), a partial view
        on a page tree descriptor is returned.

        Absent keys are treated as TRUEs,
        a whole True lets the whole subtree (if any) pass.
    '''
    return {
        'tasks': _filterTasks(
            pDesc['tasks'],
            subTasksAccessibility,
        )
    }
