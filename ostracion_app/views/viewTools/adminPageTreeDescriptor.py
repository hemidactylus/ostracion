""" adminPageTreeDescriptor.py
    Descriptor of the tree for the special-page part 'admin area'
"""

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

# special additional information for the various
# 'generic-settings' pages (i.e. no colors, no images)
genericSettingsPageDesc = {
    'behaviour': {
        'pageTitle': 'Behaviour settings',
        'pageSubtitle': ('Configure Ostracion behaviour. '
                         'Leave empty for default values'),
        'menuSubtitle': 'Configure Ostracion behaviour',
        'settingKlass': 'behaviour',
        'image_id': 'admin_settings_behaviour',
        'markdownHelp': False,
        'index': 0,
    },
    'about': {
        'pageTitle': 'About page',
        'pageSubtitle': 'Configure the appearance of Ostracion "About" page',
        'menuSubtitle': 'Configure the "About" page',
        'settingKlass': 'about',
        'image_id': 'admin_settings_about',
        'markdownHelp': True,
        'index': 1,
    },
    'privacy_policy': {
        'pageTitle': 'Privacy policy settings',
        'pageSubtitle': 'Configure Ostracion privacy policy document',
        'menuSubtitle': 'Configure the Privacy Policy',
        'settingKlass': 'privacy_policy',
        'image_id': 'admin_settings_privacy_policy',
        'markdownHelp': True,
        'index': 2,
    },
    'terms': {
        'pageTitle': 'Terms and conditions settings',
        'pageSubtitle': 'Configure Ostracion terms and conditions document',
        'menuSubtitle': 'Configure the Terms and Conditions',
        'settingKlass': 'terms',
        'image_id': 'admin_settings_terms',
        'markdownHelp': True,
        'index': 3,
    },
    'system_settings': {
        'pageTitle': 'System settings',
        'pageSubtitle': 'Configure post-install system settings',
        'menuSubtitle': 'Configure system settings',
        'settingKlass': 'system',
        'image_id': 'admin_settings_system',
        'markdownHelp': False,
        'index': 4,
    },
}

# admin pages tree for use by breadcrumbs and tasks
adminPageDescriptor = {
    'tasks': {
        'root': {
            'title': 'Admin area',
            'subtitle': 'Choose a task',
            'image_id': ('admin_images', 'admin_profile'),
            'endpoint_name': ('adminHomeView', {}),
            'task_order': ['roles', 'users', 'settings', 'tickets'],
            'tasks': {
                'roles': {
                    'title': 'Roles',
                    'subtitle': 'View and edit user roles',
                    'image_id': ('admin_images', 'admin_roles'),
                    'endpoint_name': ('adminHomeRolesView', {}),
                },
                'users': {
                    'title': 'Users',
                    'subtitle': 'Manage users',
                    'image_id': ('admin_images', 'admin_users'),
                    'endpoint_name': ('adminHomeUsersView', {}),
                },
                'settings': {
                    'title': 'Ostracion settings',
                    'subtitle': (
                        'Configure appearance and behaviour of Ostracion'
                    ),
                    'image_id': ('admin_images', 'admin_settings'),
                    'endpoint_name': ('adminHomeSettingsView', {}),
                    'task_order': ['images', 'colors']+[
                        k
                        for k, v in sorted(
                            genericSettingsPageDesc.items(),
                            key=lambda kv: kv[1]['index'],
                        )
                    ],
                    'tasks': recursivelyMergeDictionaries(
                        {
                            'images': {
                                'title': 'Images',
                                'subtitle': ('Configure images '
                                             '(icons and so on)'),
                                'image_id': (
                                    'admin_images',
                                    'admin_settings_images'
                                ),
                                'endpoint_name': (
                                    'adminHomeSettingsImagesView',
                                    {},
                                ),
                            },
                            'colors': {
                                'title': 'Colors',
                                'subtitle': ('Configure colors (for box, '
                                             'file, task cards and so on)'),
                                'image_id': (
                                    'admin_images',
                                    'admin_settings_colors'
                                ),
                                'endpoint_name': (
                                    'adminHomeSettingsColorsView',
                                    {},
                                ),
                            },
                        },
                        defaultMap={
                            genericSettingKey: {
                                'title': genericSettingInfo['pageTitle'],
                                'subtitle': genericSettingInfo['pageSubtitle'],
                                'image_id': (
                                    'admin_images',
                                    genericSettingInfo['image_id'],
                                ),
                                'endpoint_name': (
                                    'adminHomeSettingsGenericView',
                                    {'settingType': genericSettingKey},
                                ),
                            }
                            for genericSettingKey, genericSettingInfo in (
                                genericSettingsPageDesc.items()
                            )
                        }
                    ),
                },
                'tickets': {
                    'title': 'Tickets',
                    'subtitle': (
                        'Manage tickets of all types issued by everybody'
                    ),
                    'image_id': ('admin_images', 'admin_ticket'),
                    'endpoint_name': ('adminHomeTicketsView', {}),
                    'task_order': [
                        'user_invitations',
                        'change_password',
                        'file',
                        'upload',
                        'gallery',
                    ],
                    'tasks': {
                        'user_invitations': {
                            'title': 'User invitations',
                            'subtitle': 'Manage user-invitation tickets',
                            'image_id': ('admin_images', 'user_invitation'),
                            'endpoint_name': ('adminUserInvitationsView', {}),
                        },
                        'change_password': {
                            'title': 'Change-password tickets',
                            'subtitle': 'Manage change-password tickets',
                            'image_id': (
                                'admin_images',
                                'change_password_ticket'
                            ),
                            'endpoint_name': (
                                'adminUserChangePasswordTicketsView',
                                {},
                            ),
                        },
                        'file': {
                            'title': 'All file tickets',
                            'subtitle': 'Manage file tickets issued by anyone',
                            'image_id': ('admin_images', 'admin_file_ticket'),
                            'endpoint_name': ('adminFileTicketsView', {}),
                        },
                        'upload': {
                            'title': 'All upload tickets',
                            'subtitle': (
                                'Manage upload tickets issued by anyone'
                            ),
                            'image_id': (
                                'admin_images',
                                'admin_upload_ticket'
                            ),
                            'endpoint_name': ('adminUploadTicketsView', {}),
                        },
                        'gallery': {
                            'title': 'All gallery tickets',
                            'subtitle': (
                                'Manage gallery tickets issued by anyone'
                            ),
                            'image_id': (
                                'admin_images',
                                'admin_gallery_ticket'
                            ),
                            'endpoint_name': ('adminGalleryTicketsView', {}),
                        },
                    },
                },
            },
        },
    },
}
