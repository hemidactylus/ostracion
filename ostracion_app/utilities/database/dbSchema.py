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
            ('terms_accepted', 'TEXT'),
            ('terms_accepted_version', 'TEXT'),
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
            ('title', 'TEXT'),
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
            ('dvector_title', 'TEXT'),
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
            ('role_class', 'TEXT'),
            ('role_id', 'TEXT'),
        ],
        'columns': [
            ('description', 'TEXT'),
            ('can_box', 'INTEGER'),
            ('can_user', 'INTEGER'),
            ('can_delete', 'INTEGER'),
        ],
    },
    'box_role_permissions': {
        'primary_key': [
            ('box_id', 'TEXT'),
            ('role_class', 'TEXT'),
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
                [['role_class', 'role_id'], ['role_class', 'role_id']],
            ],
        },
    },
    'user_roles': {
        'primary_key': [
            ('username', 'TEXT'),
            ('role_class', 'TEXT'),
            ('role_id', 'TEXT'),
        ],
        'columns': [],
        'foreign_keys': {
            'users': [
                [['username'], ['username']],
            ],
            'roles': [
                [['role_class', 'role_id'], ['role_class', 'role_id']],
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
    },
    # accounting app, tables
    'accounting_ledgers': {
        'primary_key': [
            ('ledger_id', 'TEXT'),
        ],
        'columns': [
            ('name', 'TEXT'),
            ('description', 'TEXT'),
            ('creator_username', 'TEXT'),
            ('creation_date', 'TIMESTAMP'),
            ('configuration_date', 'TIMESTAMP'),
            ('last_edit_date', 'TIMESTAMP'),
            ('last_edit_username', 'TEXT'),
            ('icon_file_id', 'TEXT'),
            ('icon_file_id_username', 'TEXT'),
            ('icon_mime_type', 'TEXT'),
            ('summary', 'TEXT'),
            ('summary_date', 'TIMESTAMP'),
        ],
        'foreign_keys': {
            'users': [
                [['last_edit_username'], ['username']],
            ],
        },
    },
    'accounting_ledgers_users': {
        'primary_key': [
            ('username', 'TEXT'),
            ('ledger_id', 'TEXT'),
        ],
        'columns': [],
        'foreign_keys': {
            'users': [
                [['username'], ['username']],
            ],
            'accounting_ledgers': [
                [['ledger_id'], ['ledger_id']],
            ],
        },
    },
    'accounting_actors': {
        'primary_key': [
            ('ledger_id', 'TEXT'),
            ('actor_id', 'TEXT'),
        ],
        'columns': [
            ('name', 'TEXT'),
        ],
        'foreign_keys': {
            'accounting_ledgers': [
                [['ledger_id'], ['ledger_id']],
            ],
        },
    },
    'accounting_movement_categories': {
        'primary_key': [
            ('ledger_id', 'TEXT'),
            ('category_id', 'TEXT'),
        ],
        'columns': [
            ('description', 'TEXT'),
            ('sort_index', 'INTEGER')
        ],
        'foreign_keys': {
            'accounting_ledgers': [
                [['ledger_id'], ['ledger_id']],
            ],
        },
    },
    'accounting_movement_subcategories': {
        'primary_key': [
            ('ledger_id', 'TEXT'),
            ('category_id', 'TEXT'),
            ('subcategory_id', 'TEXT'),
        ],
        'columns': [
            ('description', 'TEXT'),
            ('sort_index', 'INTEGER')
        ],
        'foreign_keys': {
            'accounting_ledgers': [
                [['ledger_id'], ['ledger_id']],
            ],
            'accounting_movement_categories': [
                [['ledger_id', 'category_id'], ['ledger_id', 'category_id']],
            ],
        },
    },
    'accounting_ledger_movements': {
        'primary_key': [
            ('ledger_id', 'TEXT'),
            ('movement_id', 'TEXT'),
        ],
        'columns': [
            ('category_id', 'TEXT'),
            ('subcategory_id', 'TEXT'),
            ('date', 'TIMESTAMP'),
            ('description', 'TEXT'),
            ('last_edit_date', 'TIMESTAMP'),
            ('last_edit_username', 'TEXT'),
        ],
        'indices': {
            'accounting_ledger_movements_date_index': [
                ('date', 'DESC'),
                ('last_edit_date', 'DESC'),
            ],
        },
        'foreign_keys': {
            'users': [
                [['last_edit_username'], ['username']],
            ],
            'accounting_ledgers': [
                [['ledger_id'], ['ledger_id']],
            ],
            'accounting_movement_subcategories': [
                [
                    ['ledger_id', 'category_id', 'subcategory_id'],
                    ['ledger_id', 'category_id', 'subcategory_id']
                ],
            ],
        },
    },
    'accounting_movement_contributions': {
        'primary_key': [
            ('ledger_id', 'TEXT'),
            ('movement_id', 'TEXT'),
            ('actor_id', 'TEXT'),
        ],
        'columns': [
            ('paid', 'REAL'),
            ('due', 'REAL'),
            ('proportion', 'REAL'),
        ],
        'foreign_keys': {
            'accounting_ledger_movements': [
                [['ledger_id', 'movement_id'], ['ledger_id', 'movement_id']],
            ],
            'accounting_actors': [
                [['ledger_id', 'actor_id'], ['ledger_id', 'actor_id']],
            ],
        },
    },
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
    # accounting app
    'accounting_ledgers',
    'accounting_ledgers_users',
    'accounting_actors',
    'accounting_movement_categories',
    'accounting_movement_subcategories',
    'accounting_ledger_movements',
    'accounting_movement_contributions',
]

tableCreationOrder = {
    tN: tI
    for tI, tN in enumerate(tableCreationOrderSequence)
}
