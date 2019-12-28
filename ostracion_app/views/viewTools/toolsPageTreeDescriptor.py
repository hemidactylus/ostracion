""" toolsPageTreeDescriptor.py
    Descriptor of the tree for the special-page part 'tools'
"""

toolsPageDescriptor = {
    'tasks': {
        'root': {
            'title': 'Tools',
            'subtitle': 'Navigation tools (search, ...)',
            'image_id': ('app_images', 'tools'),
            'endpoint_name': ('toolsHomeView', {}),
            'task_order': ['tree_view', 'search'],
            'tasks': {
                'tree_view': {
                    'title': 'Tree View',
                    'subtitle': 'Hierarchic view of the available box tree',
                    'image_id': ('app_images', 'tree_view'),
                    'endpoint_name': ('dirTreeView', {}),
                },
                'search': {
                    'title': 'Search',
                    'subtitle': '',
                    'image_id': ('app_images', 'search'),
                    'endpoint_name': ('findView', {}),
                },
            },
        },
    },
}
