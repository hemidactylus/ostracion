""" appsPageTreeDescriptor.py
    Descriptor of the tree for the special-page part 'apps'
"""

appsPageDescriptor = {
    'tasks': {
        'root': {
            'title': 'Apps',
            'subtitle': 'Available applications',
            'image_id': ('custom_apps_images', 'general_apps'),
            'endpoint_name': ('appsView', {}),
            'task_order': ['calendar_maker', 'accounting'],
            'tasks': {
                'calendar_maker': {
                    'title': 'Calendar maker',
                    'subtitle': 'Create your own custom calendar',
                    'image_id': ('custom_apps_images', 'calendar_maker'),
                    'endpoint_name': ('calendarMakerIndexView', {}),
                    'task_order': ['settings', 'images'],
                    'tasks': {
                        'settings': {
                            'title': 'Settings',
                            'subtitle': ('Configure calendar properties. '
                                         'Click "Set" to save.'),
                            'image_id': (
                                'custom_apps_images',
                                'calendar_maker',
                            ),
                            'endpoint_name': ('calendarMakerSettingsView', {}),
                        },
                        'images': {
                            'title': 'Images',
                            'subtitle': ('Select images for calendar. Navigate'
                                         ' to a box with the bottom block: to '
                                         'select images click on "C" (set as c'
                                         'over) or "+" (add to image list). Re'
                                         'arrange/delete chosen images with th'
                                         'e controls above. Hit "Done with ima'
                                         'ges" when finished. For otpimal resu'
                                         'lts, choose a cover in Portrait form'
                                         'at and month images in Landscape for'
                                         'mat.'),
                            'image_id': (
                                'custom_apps_images',
                                'calendar_maker',
                            ),
                            'endpoint_name': ('calendarMakerImagesView', {}),
                        },
                    }
                },
                'accounting': {
                    'title': 'Accounting',
                    'subtitle': 'Manage accounting',
                    'image_id': ('custom_apps_images', 'accounting'),
                    'endpoint_name': ('accountingIndexView', {}),
                }
            },
        },
    },
}
