""" dbSchema.py:
    Description of the tables, their columns/indices/for.keys.
"""

dbSchema = {
    'users': {
        'primary_key': [
            ('username', 'TEXT'),
        ],
        'columns': [
            ('fullname', 'TEXT'),
            ('salt', 'TEXT'),
            ('passwordhash', 'TEXT'),
            ('email', 'TEXT'),
            ('icon_file_id', 'TEXT'),
            ('icon_file_id_username', 'TEXT'),
            ('icon_mime_type', 'TEXT'),
            ('banned', 'INTEGER'),
            ('last_login', 'TIMESTAMP'),
        ],
        'foreign_keys': {
            'users': [
                [['icon_file_id_username'], ['username']],
            ],
        },
    },
    'boxes': {
        'primary_key': [
            ('box_id', 'TEXT'),
        ],
        'columns': [
            ('box_name', 'TEXT'),
            ('parent_id', 'TEXT'),
            ('title', 'TEXT'),
            ('description', 'TEXT'),
            ('icon_file_id', 'TEXT'),
            ('date', 'TIMESTAMP'),
            ('nature', 'TEXT'),
            ('creator_username', 'TEXT'),
            ('metadata_username', 'TEXT'),
            ('icon_file_id_username', 'TEXT'),
            ('icon_mime_type', 'TEXT'),
            #
            ('dvector_box_name', 'TEXT'),
            ('dvector_title', 'TEXT'),
            ('dvector_description', 'TEXT'),
        ],
        'indices': {
            'boxes_parent_id_index': [
                ('parent_id', 'ASC'),
            ],
            'boxes_box_name_index': [
                ('box_name', 'ASC'),
            ],
        },
        'foreign_keys': {
            'users': [
                [['creator_username'], ['username']],
                [['metadata_username'], ['username']],
                [['icon_file_id_username'], ['username']],
            ],
        },
    },
    'files': {
        'primary_key': [
            ('file_id', 'TEXT'),
        ],
        'columns': [
            ('box_id', 'TEXT'),
            ('name', 'TEXT'),
            ('description', 'TEXT'),
            ('icon_file_id', 'TEXT'),
            ('date', 'TIMESTAMP'),
            ('mime_type', 'TEXT'),
            ('textual_mode', 'TEXT'),
            ('type', 'TEXT'),
            ('size', 'INTEGER'),
            ('creator_username', 'TEXT'),
            ('icon_file_id_username', 'TEXT'),
            ('icon_mime_type', 'TEXT'),
            ('metadata_username', 'TEXT'),
            ('editor_username', 'TEXT'),
            #
            ('dvector_name', 'TEXT'),
            ('dvector_description', 'TEXT'),
        ],
        'indices': {
            'files_box_id_index': [
                ('box_id', 'ASC'),
            ],
        },
        'foreign_keys': {
            'boxes': [
                [['box_id'], ['box_id']],
            ],
            'users': [
                [['creator_username'], ['username']],
                [['icon_file_id_username'], ['username']],
                [['metadata_username'], ['username']],
                [['editor_username'], ['username']],
            ],
        },
    },
    'links': {
        'primary_key': [
            ('link_id', 'TEXT'),
        ],
        'columns': [
            ('box_id', 'TEXT'),
            ('target', 'TEXT'),
            ('metadata', 'TEXT'),
            ('name', 'TEXT'),
            ('description', 'TEXT'),
            ('icon_file_id', 'TEXT'),
            ('date', 'TIMESTAMP'),
            ('creator_username', 'TEXT'),
            ('icon_file_id_username', 'TEXT'),
            ('icon_mime_type', 'TEXT'),
            ('metadata_username', 'TEXT'),
            #
            ('dvector_name', 'TEXT'),
            ('dvector_description', 'TEXT'),
        ],
        'indices': {
            'links_box_id_index': [
                ('box_id', 'ASC'),
            ],
        },
        'foreign_keys': {
            'boxes': [
                [['box_id'], ['box_id']],
            ],
            'users': [
                [['creator_username'], ['username']],
                [['icon_file_id_username'], ['username']],
                [['metadata_username'], ['username']],
            ],
        },
    },
    'roles': {
        'primary_key': [
            ('role_id', 'TEXT'),
        ],
        'columns': [
            ('description', 'TEXT'),
            ('system', 'INTEGER'),
        ],
    },
    'box_role_permissions': {
        'primary_key': [
            ('box_id', 'TEXT'),
            ('role_id', 'TEXT'),
        ],
        'columns': [
            ('r', 'INTEGER'),
            ('w', 'INTEGER'),
            ('c', 'INTEGER'),
        ],
        'foreign_keys': {
            'boxes': [
                [['box_id'], ['box_id']],
            ],
            'roles': [
                [['role_id'], ['role_id']],
            ],
        },
    },
    'user_roles': {
        'primary_key': [
            ('username', 'TEXT'),
            ('role_id', 'TEXT'),
        ],
        'columns': [],
        'foreign_keys': {
            'users': [
                [['username'], ['username']],
            ],
            'roles': [
                [['role_id'], ['role_id']],
            ],
        },
    },
    'settings': {
        'primary_key': [
            ('group_id', 'TEXT'),
            ('id', 'TEXT'),
        ],
        'columns': [
            ('klass', 'TEXT'),
            ('type', 'TEXT'),
            ('value', 'TEXT'),
            ('title', 'TEXT'),
            ('description', 'TEXT'),
            ('default_value', 'TEXT'),
            ('metadata', 'TEXT'),
            ('group_title', 'TEXT'),
            ('group_ordering', 'INTEGER'),
            ('ordering', 'INTEGER'),
            ('icon_mime_type', 'TEXT'),
            ('default_icon_mime_type', 'TEXT'),
        ],
    },
    'tickets': {
        'primary_key': [
            ('ticket_id', 'TEXT'),
        ],
        'columns': [
            ('name',            'TEXT'),
            ('security_code',   'TEXT'),
            ('username',        'TEXT'),
            ('issue_date',      'TIMESTAMP'),
            ('expiration_date', 'TIMESTAMP'),
            ('multiplicity',    'INTEGER'),
            ('target_type',     'TEXT'),
            ('metadata',        'TEXT'),
            ('last_redeemed',   'TIMESTAMP'),
            ('times_redeemed',  'INTEGER'),
        ],
        'indices': {
            'target_type_asc': [
                ('target_type', 'ASC'),
            ],
        },
        'foreign_keys': {
            'users': [
                [['username'], ['username']],
            ],
        },
    },
    'attempted_logins': {
        'primary_key': [
            ('sender_hash',     'TEXT'),
        ],
        'columns': [
            ('datetime',        'TIMESTAMP'),
        ],
    }
}

tableCreationOrderSequence = [
    'users',
    'boxes',
    'roles',
    'files',
    'links',
    'box_role_permissions',
    'user_roles',
    'settings',
    'tickets',
    'attempted_logins',
]

tableCreationOrder = {
    tN: tI
    for tI, tN in enumerate(tableCreationOrderSequence)
}
