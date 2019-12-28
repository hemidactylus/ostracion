""" infoPageTreeDescriptor.py
    Descriptor of the tree for the special-page part 'info'
"""

infoPageDescriptor = {
    'tasks': {
        'root': {
            'title': 'Info',
            'subtitle': 'Manuals, privacy policy, about ...',
            'image_id': ('ostracion_images', 'info'),
            'endpoint_name': ('infoHomeView', {}),
            'task_order': ['user_guide', 'admin_guide', 'privacy', 'about'],
            'tasks': {
                'user_guide': {
                    'title': 'User Guide',
                    'subtitle': 'A short guide to using Ostracion',
                    'image_id': ('ostracion_images', 'user_guide'),
                    'endpoint_name': ('userGuideView', {}),
                },
                'admin_guide': {
                    'title': 'Admin Guide',
                    'subtitle': 'A short guide to administering Ostracion',
                    'image_id': ('ostracion_images', 'admin_guide'),
                    'endpoint_name': ('adminGuideView', {}),
                },
                'privacy': {
                    'title': 'Privacy policy',
                    'subtitle': '',
                    'image_id': ('ostracion_images', 'privacy_policy_logo'),
                    'endpoint_name': ('privacyPolicyView', {}),
                },
                'about': {
                    'title': 'About',
                    'subtitle': '',
                    'image_id': ('ostracion_images', 'application_logo'),
                    'endpoint_name': ('aboutView', {}),
                },
            },
        },
    },
}
