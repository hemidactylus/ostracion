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
            'task_order': ['calendar_maker'],
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
                            'subtitle': 'Configure calendar properties',
                            'image_id': ('custom_apps_images', 'calendar_maker'),
                            'endpoint_name': ('calendarMakerSettingsView', {}),
                        },
                        'images': {
                            'title': 'Images',
                            'subtitle': 'Select images for calendar',
                            'image_id': ('custom_apps_images', 'calendar_maker'),
                            'endpoint_name': ('calendarMakerImagesView', {}),
                        },
                    }
                },
            },
        },
    },
}
