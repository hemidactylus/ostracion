"""
    defaultDb.py
        used only by postInstall, contains data
        to re/generate database entries (default user, settings...).
"""

from datetime import datetime

from ostracion_app.utilities.models.User import User
from ostracion_app.utilities.models.File import File
from ostracion_app.utilities.models.Role import Role
from ostracion_app.utilities.models.UserRole import UserRole
from ostracion_app.utilities.models.Box import Box
from ostracion_app.utilities.models.BoxRolePermission import BoxRolePermission
from ostracion_app.utilities.models.Setting import Setting

from ostracion_app.utilities.tools.securityCodes import makeSecurityCode

from post_install.initialValues.tools import (
    loadDefaultPrivacyPolicyBody,
    loadDefaultAboutInstanceBody,
    loadDefaultTermsBody,
    loadDefaultAboutBody,
    getDefaultTempDirectory,
    getDefaultFilesystemDirectory,
)

from ostracion_app.utilities.userTools.anonymousRole import (
    anonymousRoleDict,
)

initialDbValues = {
    'users': {
        'model': User,
        'values': [
            {
                'username':         '',
                'fullname':         '(nobody)',
                'email':            '',
                'password':         '',
                'icon_file_id':     '',
                'icon_file_id_username':         '',
                'banned':           1,
            },
            #
            {
                'username':         'admin',
                'fullname':         'Default Admin',
                'email':            'n/a',
                'password':         'admin',
                'icon_file_id':     '',
                'icon_file_id_username':         'admin',
                'banned':           0,
            },
        ],
    },
    'boxes': {
        'model': Box,
        'values': [
            {
                'box_id':           '',
                'box_name':         '',
                'parent_id':        '',
                'title':             'Root',
                'description':      'Top-level box',
                'icon_file_id':     '',
                'date':             datetime(2018, 12, 27, 18, 47, 5),
                'nature':           'system',
                'creator_username': '',
                'icon_file_id_username': '',
                'metadata_username': '',
            },
        ],
    },
    'files': {
        'model': File,
        'values': [
        ],
    },
    'roles': {
        'model': Role,
        'values': [
            anonymousRoleDict,
            {
                'role_class': 'system',
                'role_id':          'admin',
                'description':      'Admin',
                'can_box': 1,
                'can_user': 1,
                'can_delete': 0,
            },
            {
                'role_class': 'system',
                'role_id':          'ticketer',
                'description':      'Ticketer',
                'can_box': 0,
                'can_user': 1,
                'can_delete': 0,
            },
            {
                'role_class': 'system',
                'role_id':          'archiver',
                'description':      'Archiver',
                'can_box': 0,
                'can_user': 1,
                'can_delete': 0,
            },
            {
                'role_class': 'app',
                'role_id':          'accounting',
                'description':      'Accounting',
                'can_box': 0,
                'can_user': 1,
                'can_delete': 0,
            },
        ],
    },
    'user_roles': {
        'model': UserRole,
        'values': [
            {
                'username': 'admin',
                'role_class': 'system',
                'role_id': 'admin',
            },
        ],
    },
    'box_role_permissions': {
        'model': BoxRolePermission,
        'values': [
            {
                'box_id': '',
                'role_class': 'system',
                'role_id': 'admin',
                'r': 1,
                'w': 1,
                'c': 1,
            },
            {
                'box_id': '',
                'role_class': 'system',
                'role_id': 'anonymous',
                'r': 1,
                'w': 0,
                'c': 0,
            },
        ],
    },
    'settings': {
        'model': Setting,
        'values': [
            {
                'id':               'login',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Login',
                'description':      'Icon for Login',
                'default_value':    'login.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'user_images',
                'group_title':      'User image settings',
                'group_ordering':   10,
                'ordering':         5,
            },
            {
                'id':               'logout',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Logout',
                'description':      'Icon for Logout',
                'default_value':    'logout.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'user_images',
                'group_title':      'User image settings',
                'group_ordering':   10,
                'ordering':         10,
            },
            {
                'id':               'user_icon',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'User icon',
                'description':      'Default user icon',
                'default_value':    'user_icon.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'user_images',
                'group_title':      'User image settings',
                'group_ordering':   10,
                'ordering':         15,
            },
            {
                'id':               'user_data',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'User-data image',
                'description':      'Icon for "User data"',
                'default_value':    'user_data.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'user_images',
                'group_title':      'User image settings',
                'group_ordering':   10,
                'ordering':         20,
            },
            {
                'id':               'profile_thumbnail',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Change-user-icon',
                'description':      'Icon for "Change user icon"',
                'default_value':    'profile_thumbnail.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'user_images',
                'group_title':      'User image settings',
                'group_ordering':   10,
                'ordering':         25,
            },
            {
                'id':               'change_password',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'icon_mime_type':   'image/png',
                'title':            'Change-password image',
                'description':      'Icon for "Change password"',
                'default_value':    'change_password.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'user_images',
                'group_title':      'User image settings',
                'group_ordering':   10,
                'ordering':         30,
            },
            {
                'id':               'delete_account',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Delete-account image',
                'description':      'Icon for "Delete account"',
                'default_value':    'delete_account.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'user_images',
                'group_title':      'User image settings',
                'group_ordering':   10,
                'ordering':         35,
            },
            #
            {
                'id':               'admin_profile',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Admin-area image',
                'description':      'Icon for "Admin Area"',
                'default_value':    'admin_profile.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         5,
            },
            {
                'id':               'admin_roles',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Roles image',
                'description':      'Icon for "Roles"',
                'default_value':    'admin_roles.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         10,
            },
            {
                'id':               'admin_users',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Users image',
                'description':      'Icon for "Users"',
                'default_value':    'admin_users.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         15,
            },
            {
                'id':               'admin_settings',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Settings image',
                'description':      'Icon for "Settings"',
                'default_value':    'admin_settings.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         20,
            },
            {
                'id':               'admin_settings_images',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Settings/images image',
                'description':      'Icon for "Settings/images"',
                'default_value':    'admin_settings_images.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         25,
            },
            {
                'id':               'admin_settings_colors',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Settings/colors image',
                'description':      'Icon for "Settings/colors"',
                'default_value':    'admin_settings_colors.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         30,
            },
            {
                'id':               'admin_settings_behaviour',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Settings/behaviour image',
                'description':      'Icon for "Settings/behaviour"',
                'default_value':    'admin_settings_behaviour.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         35,
            },
            {
                'id':               'admin_settings_privacy_policy',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Settings/privacy policy image',
                'description':      'Icon for "Settings/privacy policy"',
                'default_value':    'admin_settings_privacy_policy.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         40,
            },
            {
                'id':               'admin_settings_terms',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Settings/terms and conditions image',
                'description':      'Icon for "Settings/terms and conditions"',
                'default_value':    'admin_settings_terms.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         45,
            },
            {
                'id':               'admin_settings_about',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Settings/about-page image',
                'description':      'Icon for "Settings/about page"',
                'default_value':    'admin_settings_about.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         50,
            },
            {
                'id':               'admin_settings_system',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Settings/system settings image',
                'description':      'Icon for "Settings/system"',
                'default_value':    'admin_settings_system.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         55,
            },
            {
                'id':               'admin_ticket',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Tickets image',
                'description':      'Icon for admin Ticket section',
                'default_value':    'admin_ticket.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         60,
            },
            {
                'id':               'user_invitation',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'User invitation image',
                'description':      'Icon for User invitation',
                'default_value':    'user_invitation.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         65,
            },
            {
                'id':               'change_password_ticket',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Change-password ticket image',
                'description':      'Icon for "Change-password" ticket pages',
                'default_value':    'change_password_ticket.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         70,
            },
            {
                'id':               'admin_file_ticket',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Admin file ticket',
                'description':      'Icon for file tickets as admin',
                'default_value':    'admin_file_ticket.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         75,
            },
            {
                'id':               'admin_upload_ticket',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Admin upload ticket',
                'description':      'Icon for upload tickets as admin',
                'default_value':    'admin_upload_ticket.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         80,
            },
            {
                'id':               'admin_gallery_ticket',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Admin gallery ticket',
                'description':      'Icon for gallery tickets as admin',
                'default_value':    'admin_gallery_ticket.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'admin_images',
                'group_title':      'Admin image settings',
                'group_ordering':   20,
                'ordering':         85,
            },
            #
            {
                'id':               'root_box',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Root box',
                'description':      'Root box icon',
                'default_value':    'root_box.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         5,
            },
            {
                'id':               'standard_box',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Standard box',
                'description':      'Box default icon',
                'default_value':    'standard_box.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         10,
            },
            {
                'id':               'file_ticket',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'File ticket',
                'description':      'Icon for file tickets',
                'default_value':    'file_ticket.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         15,
            },
            {
                'id':               'gallery_ticket',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Gallery ticket',
                'description':      'Icon for "Gallery ticket"',
                'default_value':    'gallery_ticket.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         20,
            },
            {
                'id':               'upload_ticket',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Upload ticket',
                'description':      'Icon for upload tickets',
                'default_value':    'upload_ticket.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         25,
            },
            {
                'id':               'move',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Move',
                'description':      'Icon for "move file/box"',
                'default_value':    'move.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         30,
            },
            {
                'id':               'single_upload',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Single upload',
                'description':      'Icon for single upload',
                'default_value':    'single_upload.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         35,
            },
            {
                'id':               'multiple_upload',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Multiple upload',
                'description':      'Icon for multiple upload',
                'default_value':    'multiple_upload.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         40,
            },
            {
                'id':               'tools',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Tool area',
                'description':      (
                                        'Icon for tool area '
                                        '(search, tree view ...)'
                                    ),
                'default_value':    'tools.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         45,
            },
            {
                'id':               'tree_view',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Tree dump',
                'description':      'Tree view icon',
                'default_value':    'tree_view.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         50,
            },
            {
                'id':               'search',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Search',
                'description':      'Icon for search',
                'default_value':    'search.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         55,
            },
            {
                'id':               'external_link',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'External link',
                'description':      'Icon for external link',
                'default_value':    'external_link.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'app_images',
                'group_title':      'Application image settings',
                'group_ordering':   30,
                'ordering':         60,
            },
            #
            {
                'id':               'navbar_logo',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Navbar logo',
                'description':      'Application logo for use in navbar',
                'default_value':    'navbar_logo.svg',
                'default_icon_mime_type':   'image/svg+xml',
                'metadata':         '{"thumbnailFormat":"logo_small"}',
                'group_id':         'ostracion_images',
                'group_title':      'Ostracion image settings',
                'group_ordering':   40,
                'ordering':         5,
            },
            {
                'id':               'application_logo',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Application logo',
                'description':      'Application logo for in-page use',
                'default_value':    'application_logo.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'ostracion_images',
                'group_title':      'Ostracion image settings',
                'group_ordering':   40,
                'ordering':         10,
            },
            {
                'id':               'application_about_image_2',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Application second image',
                'description':      (
                                        'Second Application image for '
                                        '"About" page'
                                    ),
                'default_value':    'application_about_image_2.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"landscape"}',
                'group_id':         'ostracion_images',
                'group_title':      'Ostracion image settings',
                'group_ordering':   40,
                'ordering':         15,
            },
            {
                'id':               'user_guide',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'User guide',
                'description':      'Icon for user guide',
                'default_value':    'user_guide.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'ostracion_images',
                'group_title':      'Ostracion image settings',
                'group_ordering':   40,
                'ordering':         20,
            },
            {
                'id':               'info',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Info area',
                'description':      'Icon for info area (guides, about ...)',
                'default_value':    'info.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'ostracion_images',
                'group_title':      'Ostracion image settings',
                'group_ordering':   40,
                'ordering':         25,
            },
            {
                'id':               'admin_guide',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Admin guide',
                'description':      'Icon for guide for admins',
                'default_value':    'admin_guide.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'ostracion_images',
                'group_title':      'Ostracion image settings',
                'group_ordering':   40,
                'ordering':         30,
            },
            {
                'id':               'privacy_policy_logo',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Privacy Policy logo',
                'description':      'Privacy policy page image',
                'default_value':    'privacy_policy_logo.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'ostracion_images',
                'group_title':      'Ostracion image settings',
                'group_ordering':   40,
                'ordering':         35,
            },
            {
                'id':               'terms_logo',
                'klass':            'image',
                'type':             'image',
                'value':            '',
                'title':            'Terms and conditions logo',
                'description':      'Terms and conditions page image',
                'default_value':    'terms_logo.png',
                'default_icon_mime_type':   'image/png',
                'metadata':         '{"thumbnailFormat":"thumbnail"}',
                'group_id':         'ostracion_images',
                'group_title':      'Ostracion image settings',
                'group_ordering':   40,
                'ordering':         40,
            },
            #
            #
            {
                'id':               'box',
                'klass':            'color',
                'type':             'color',
                'value':            '',
                'title':            'Box Color',
                'description':      'Color of box cards',
                'default_value':    '#85a7b4',
                'metadata':         '',
                'group_id':         'navigation_colors',
                'group_title':      'Navigation colors',
                'group_ordering':   5,
                'ordering':         5,
            },
            {
                'id':               'file',
                'klass':            'color',
                'type':             'color',
                'value':            '',
                'title':            'File Color',
                'description':      'Color of file cards',
                'default_value':    '#c8ffd4',
                'metadata':         '',
                'group_id':         'navigation_colors',
                'group_title':      'Navigation colors',
                'group_ordering':   5,
                'ordering':         10,
            },
            {
                'id':               'link',
                'klass':            'color',
                'type':             'color',
                'value':            '',
                'title':            'Link Color',
                'description':      'Color of link cards',
                'default_value':    '#f0a0a0',
                'metadata':         '',
                'group_id':         'navigation_colors',
                'group_title':      'Navigation colors',
                'group_ordering':   5,
                'ordering':         15,
            },
            #
            {
                'id':               'shade_treeview_boxes',
                'klass':            'color',
                'type':             'color',
                'value':            '',
                'title':            'Tree view, boxes',
                'description':      (
                                        'Gradient color for tree view '
                                        '(boxes only)'
                                    ),
                'default_value':    '#babaff',
                'metadata':         '',
                'group_id':         'tree_shade_colors',
                'group_title':      'Tree-views shade colors',
                'group_ordering':   10,
                'ordering':         5,
            },
            {
                'id':               'shade_treeview_files',
                'klass':            'color',
                'type':             'color',
                'value':            '',
                'title':            'Tree view, files',
                'description':      (
                                        'Gradient color for tree view '
                                        '(with files)'
                                    ),
                'default_value':    '#baa0ba',
                'metadata':         '',
                'group_id':         'tree_shade_colors',
                'group_title':      'Tree-views shade colors',
                'group_ordering':   10,
                'ordering':         10,
            },
            {
                'id':               'shade_treeview_pickbox',
                'klass':            'color',
                'type':             'color',
                'value':            '',
                'title':            'Choose destination box',
                'description':      (
                                        'Gradient color for "choose destina'
                                        'tion box" tree view (for moving)'
                                    ),
                'default_value':    '#d0d0a9',
                'metadata':         '',
                'group_id':         'tree_shade_colors',
                'group_title':      'Tree-views shade colors',
                'group_ordering':   10,
                'ordering':         15,
            },
            #
            {
                'id':               'admin_task',
                'klass':            'color',
                'type':             'color',
                'value':            '',
                'title':            'Admin task',
                'description':      'Color of admin tasks',
                'default_value':    '#f0bb60',
                'metadata':         '',
                'group_id':         'task_colors',
                'group_title':      'Task colors',
                'group_ordering':   15,
                'ordering':         5,
            },
            {
                'id':               'user_task',
                'klass':            'color',
                'type':             'color',
                'value':            '',
                'title':            'User task',
                'description':      'Color of user tasks',
                'default_value':    '#e590d0',
                'metadata':         '',
                'group_id':         'task_colors',
                'group_title':      'Task colors',
                'group_ordering':   15,
                'ordering':         10,
            },
            {
                'id':               'tool_task',
                'klass':            'color',
                'type':             'color',
                'value':            '',
                'title':            'Tool',
                'description':      'Color of special tools',
                'default_value':    '#9fabee',
                'metadata':         '',
                'group_id':         'task_colors',
                'group_title':      'Task colors',
                'group_ordering':   15,
                'ordering':         15,
            },
            {
                'id':               'info_task',
                'klass':            'color',
                'type':             'color',
                'value':            '',
                'title':            'Info page',
                'description':      'Color of info pages',
                'default_value':    '#93ba86',
                'metadata':         '',
                'group_id':         'task_colors',
                'group_title':      'Task colors',
                'group_ordering':   15,
                'ordering':         20,
            },
            {
                'id':               'table',
                'klass':            'color',
                'type':             'color',
                'value':            '',
                'title':            'Tables',
                'description':      'Color of tables',
                'default_value':    '#90e0df',
                'metadata':         '',
                'group_id':         'task_colors',
                'group_title':      'Task colors',
                'group_ordering':   15,
                'ordering':         25,
            },
            #
            #
            {
                'id':               'application_long_name',
                'klass':            'behaviour',
                'type':             'string',
                'value':            '',
                'title':            'Application name',
                'description':      (
                                        'Name of this instance of the '
                                        'Ostracion app'
                                    ),
                'default_value':    'Ostracion Application',
                'metadata':         '',
                'group_id':         'behaviour_appearance',
                'group_title':      'Appearance',
                'group_ordering':   5,
                'ordering':         5,
            },
            {
                'id':               'application_short_name',
                'klass':            'behaviour',
                'type':             'string',
                'value':            '',
                'title':            'Application short name',
                'description':      (
                                        'Short name of this instance of the '
                                        'Ostracion app'
                                    ),
                'default_value':    'Ostracion',
                'metadata':         '',
                'group_id':         'behaviour_appearance',
                'group_title':      'Appearance',
                'group_ordering':   5,
                'ordering':         10,
            },
            {
                'id':               'hide_navbar',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '0',
                'title':            'Hide navigation bar',
                'description':      'Navigation through breadcrumbs only',
                'default_value':    '0',
                'metadata':         '',
                'group_id':         'behaviour_appearance',
                'group_title':      'Appearance',
                'group_ordering':   5,
                'ordering':         15,
            },
            {
                'id':               'extract_thumbnails',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '1',
                'title':            'Extract file icons',
                'description':      (
                                        'Try to extract icons from uploaded '
                                        'files (may make uploads slower)'
                                    ),
                'default_value':    '1',
                'metadata':         '',
                'group_id':         'behaviour_appearance',
                'group_title':      'Appearance',
                'group_ordering':   5,
                'ordering':         20,
            },
            #
            {
                'id':               'logged_in_users_only',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '0',
                'title':            'Logged-in users only',
                'description':      (
                                        'Forbid any kind of navigation to '
                                        'non-logged-in visitors altogether'
                                    ),
                'default_value':    '0',
                'metadata':         '',
                'group_id':         'behaviour_permissions',
                'group_title':      'Permissions',
                'group_ordering':   10,
                'ordering':         5,
            },
            {
                'id':               'rootchild_box_anonymous_permissions',
                'klass':            'behaviour',
                'type':             'option',
                'value':            '___',
                'title':            'Localnet mode setting',
                'description':      (
                                        'Permissions for "anonymous" on '
                                        'newly-created boxes under root'
                                    ),
                'default_value':    '',
                'metadata':         (
                                        '{"choices":[{"n":"\\"RWC\\" (localne'
                                        't)","id":"rwc"},{"n":"\\"R--\\" (read'
                                        '-only)","id":"r__"},{"n":"\\"---\\" '
                                        '(locked for Web)","id":"___"}]}'
                                    ),
                'group_id':         'behaviour_permissions',
                'group_title':      'Permissions',
                'group_ordering':   10,
                'ordering':         10,
            },
            {
                'id':               'show_permission',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '0',
                'title':            'Show permissions',
                'description':      (
                                        'Show box permission info also to any '
                                        'non-admin visitor'
                                    ),
                'default_value':    '0',
                'metadata':         '',
                'group_id':         'behaviour_permissions',
                'group_title':      'Permissions',
                'group_ordering':   10,
                'ordering':         15,
            },
            #
            {
                'id':               'admin_is_god',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '0',
                'title':            'Invasive user management',
                'description':      (
                                        'Admin can directly create users and '
                                        'set their password and other data, '
                                        'bypassing ticketing'
                                    ),
                'default_value':    '0',
                'metadata':         '',
                'group_id':         'behaviour_admin_powers',
                'group_title':      'Admin powers',
                'group_ordering':   15,
                'ordering':         5,
            },
            #
            {
                'id':               'password_min_length',
                'klass':            'behaviour',
                'type':             'positive_integer',
                'value':            '',
                'title':            'Minimum password length',
                'description':      (
                                        'Minimum number of characters to '
                                        'accept for user passwords'
                                    ),
                'default_value':    '6',
                'metadata':         '',
                'group_id':         'behaviour_security',
                'group_title':      'Security',
                'group_ordering':   20,
                'ordering':         5,
            },
            {
                'id':               'login_protection_seconds',
                'klass':            'behaviour',
                'type':             'nonnegative_integer',
                'value':            '',
                'title':            'Brute-force protection',
                'description':      (
                                        'Seconds to wait between consecutive '
                                        'login attempts from a host to thwart '
                                        'brute-force account cracking. Zero '
                                        'disables the feature'
                                    ),
                'default_value':    '3',
                'metadata':         '',
                'group_id':         'behaviour_security',
                'group_title':      'Security',
                'group_ordering':   20,
                'ordering':         10,
            },
            {
                'id':               'ip_addr_hashing_salt',
                'klass':            'behaviour',
                'type':             'string',
                'value':            makeSecurityCode(nSyllables=3),
                'title':            'IP hashing salt',
                'description':      (
                                        'A random string to make IP anonymiza'
                                        'tion for the brute-force protection '
                                        'truly anonymous (insert gibberish!)'
                                    ),
                'default_value':    'xyz',
                'metadata':         '',
                'group_id':         'behaviour_security',
                'group_title':      'Security',
                'group_ordering':   20,
                'ordering':         15,
            },
            #
            {
                'id':               'new_users_are_ticketer',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '0',
                'title':            'File tickets for everyone',
                'description':      (
                                        'Newly-created users get the "ticketer'
                                        '" role by default'
                                    ),
                'default_value':    '0',
                'metadata':         '',
                'group_id':         'behaviour_tickets',
                'group_title':      'Tickets',
                'group_ordering':   25,
                'ordering':         5,
            },
            {
                'id':               'protect_banned_user_tickets',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '1',
                'title':            'Protect user-issued tickets',
                'description':      'Tickets by banned users are suspended',
                'default_value':    '1',
                'metadata':         '',
                'group_id':         'behaviour_tickets',
                'group_title':      'Tickets',
                'group_ordering':   25,
                'ordering':         10,
            },
            {
                'id':               'protect_nonadmin_user_password_tickets',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '1',
                'title':            'Protect user/password tickets',
                'description':      (
                                        'User-creation/change-password '
                                        'tickets by users who cease to be '
                                        'admin are suspended'
                                    ),
                'default_value':    '1',
                'metadata':         '',
                'group_id':         'behaviour_tickets',
                'group_title':      'Tickets',
                'group_ordering':   25,
                'ordering':         15,
            },
            {
                'id':               'max_ticket_validityhours',
                'klass':            'behaviour',
                'type':             'optional_integer',
                'value':            '',
                'title':            'Maximum ticket validity (hours)',
                'description':      (
                                        'Maximum validity in hours for file/'
                                        'upload tickets. Leave empty for '
                                        'unlimited'
                                    ),
                'default_value':    '',
                'metadata':         '',
                'group_id':         'behaviour_tickets',
                'group_title':      'Tickets',
                'group_ordering':   25,
                'ordering':         20,
            },
            {
                'id':               'max_ticket_multiplicity',
                'klass':            'behaviour',
                'type':             'optional_integer',
                'value':            '',
                'title':            'Maximum grants per ticket',
                'description':      (
                                        'Maximum number of granted accesses '
                                        'for issued tickets. Leave empty for '
                                        'unlimited'
                                    ),
                'default_value':    '',
                'metadata':         '',
                'group_id':         'behaviour_tickets',
                'group_title':      'Tickets',
                'group_ordering':   25,
                'ordering':         25,
            },
            #
            {
                'id':               'anonymous_is_archiver',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '0',
                'title':            'Archives for everyone',
                'description':      ('The "anonymous" user can upload/download'
                                     ' archives for entire box trees (makes '
                                     'the "archiver" role irrelevant)'),
                'default_value':    '0',
                'metadata':         '',
                'group_id':         'archives',
                'group_title':      'Archive settings',
                'group_ordering':   30,
                'ordering':          5,
            },
            {
                'id':               'archive_download_alert_size',
                'klass':            'behaviour',
                'type':             'optional_integer',
                'value':            '50',
                'title':            'Archive download alert',
                'description':      ('Size, in MiB, at which to issue an alert'
                                     ' before archive download of a box'),
                'default_value':    '',
                'metadata':         '',
                'group_id':         'archives',
                'group_title':      'Archive settings',
                'group_ordering':   30,
                'ordering':         10,
            },
            {
                'id':               'archive_download_blocking_size',
                'klass':            'behaviour',
                'type':             'optional_integer',
                'value':            '100',
                'title':            'Archive download max size',
                'description':      ('Maximum size, in MiB, of a downloadable'
                                     ' box archive'),
                'default_value':    '',
                'metadata':         '',
                'group_id':         'archives',
                'group_title':      'Archive settings',
                'group_ordering':   30,
                'ordering':         15,
            },
            #
            {
                'id':               'tree_view_access',
                'klass':            'behaviour',
                'type':             'option',
                'value':            'anybody',
                'title':            'Access to Tree view',
                'description':      (
                                        'Access to the "Tree view" page is '
                                        'restricted to:'
                                    ),
                'default_value':    '',
                'metadata':         (
                                        '{"choices": [{"n": "Nobody", "id": '
                                        '"nobody"}, {"n": "Admins", "id": '
                                        '"admins"}, {"n": "Anybody", "id": '
                                        '"anybody"}]}'
                                    ),
                'group_id':         'search',
                'group_title':      'Resource publicity',
                'group_ordering':   35,
                'ordering':         5,
            },
            {
                'id':               'tree_view_files_visible',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '1',
                'title':            'Files visible in Tree view',
                'description':      (
                                        'The "Tree view" page can go down to '
                                        'file detail (may be slow on heavy '
                                        'filesystems)'
                                    ),
                'default_value':    '1',
                'metadata':         '',
                'group_id':         'search',
                'group_title':      'Resource publicity',
                'group_ordering':   35,
                'ordering':         10,
            },
            {
                'id':               'search_access',
                'klass':            'behaviour',
                'type':             'option',
                'value':            'anybody',
                'title':            'Access to Search',
                'description':      (
                                        'Access to the "Search" page is '
                                        'restricted to:'
                                    ),
                'default_value':    '',
                'metadata':         (
                                        '{"choices": [{"n": "Nobody", "id": '
                                        '"nobody"}, {"n": "Admins", "id": '
                                        '"admins"}, {"n": "Anybody", "id": '
                                        '"anybody"}]}'
                                    ),
                'group_id':         'search',
                'group_title':      'Resource publicity',
                'group_ordering':   35,
                'ordering':         15,
            },
            {
                'id':               'show_search_results_scores',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '0',
                'title':            'Show match scores in search results',
                'description':      (
                                        'In the "Search results" page, a '
                                        'visible numeric match score next to '
                                        'each found item'
                                    ),
                'default_value':    '0',
                'metadata':         '',
                'group_id':         'search',
                'group_title':      'Resource publicity',
                'group_ordering':   35,
                'ordering':         20,
            },
            {
                'id':               'serve_robots_txt',
                'klass':            'behaviour',
                'type':             'boolean',
                'value':            '1',
                'title':            'Provide robots.txt info',
                'description':      (
                                        'Serve file "robots.txt" when asked,'
                                        ' i.e. respond to requests'
                                        ' for "robots.txt"'
                                    ),
                'default_value':    '1',
                'metadata':         '',
                'group_id':         'search',
                'group_title':      'Resource publicity',
                'group_ordering':   35,
                'ordering':         25,
            },
            {
                'id':               'robots_txt_body',
                'klass':            'behaviour',
                'type':             'short_text',
                'value':            '',
                'title':            'robots.txt',
                'description':      'Contents of file "robots.txt"',
                'default_value':    'User-agent: *\nDisallow: /',
                'metadata':         '',
                'group_id':         'search',
                'group_title':      'Resource publicity',
                'group_ordering':   35,
                'ordering':         30,
            },
            #
            {
                'id':               'privacy_policy_version',
                'klass':            'privacy_policy',
                'type':             'string',
                'value':            '',
                'title':            'Privacy policy version',
                'description':      (
                                        'Version of last revision of the '
                                        'privacy policy'
                                    ),
                'default_value':    '1.1.0',
                'metadata':         '',
                'group_id':         'privacy_policy',
                'group_title':      'Privacy Policy',
                'group_ordering':    5,
                'ordering':          5,
            },
            {
                'id':               'privacy_policy_date',
                'klass':            'privacy_policy',
                'type':             'string',
                'value':            '',
                'title':            'Privacy policy date',
                'description':      (
                                        'Date of last revision of the '
                                        'privacy policy'
                                    ),
                'default_value':    'Jun 1st, 2020',
                'metadata':         '',
                'group_id':         'privacy_policy',
                'group_title':      'Privacy Policy',
                'group_ordering':    5,
                'ordering':          10,
            },
            {
                'id':               'dpo_email',
                'klass':            'privacy_policy',
                'type':             'string',
                'value':            '',
                'title':            'DPO Email',
                'description':      'Email of the DPO to show - as image',
                'default_value':    'currently-not-set',
                'metadata':         '{"is_text_image":true}',
                'group_id':         'privacy_policy',
                'group_title':      'Privacy Policy',
                'group_ordering':   5,
                'ordering':         15,
            },
            {
                'id':               'privacy_policy_body',
                'klass':            'privacy_policy',
                'type':             'text',
                'value':            '',
                'title':            'Privacy policy text',
                'description':      (
                                        'Markdown for last revision of the '
                                        'privacy policy (empty for default)'
                                    ),
                'default_value':    loadDefaultPrivacyPolicyBody(),
                'metadata':         '',
                'group_id':         'privacy_policy',
                'group_title':      'Privacy Policy',
                'group_ordering':    5,
                'ordering':          20,
            },
            #
            {
                'id':               'terms_version',
                'klass':            'terms',
                'type':             'string',
                'value':            '',
                'title':            'Terms and conditions version',
                'description':      (
                                        'Version of last revision of the '
                                        'terms and conditions'
                                    ),
                'default_value':    '1.0.0',
                'metadata':         '',
                'group_id':         'terms',
                'group_title':      'Terms and conditions',
                'group_ordering':    5,
                'ordering':          5,
            },
            {
                'id':               'terms_date',
                'klass':            'terms',
                'type':             'string',
                'value':            '',
                'title':            'Terms and conditions date',
                'description':      (
                                        'Date of last revision of the '
                                        'terms and conditions'
                                    ),
                'default_value':    'Jun 1st, 2020',
                'metadata':         '',
                'group_id':         'terms',
                'group_title':      'Terms and conditions',
                'group_ordering':    5,
                'ordering':          10,
            },
            {
                'id':               'terms_must_agree',
                'klass':            'terms',
                'type':             'boolean',
                'value':            '1',
                'title':            'Users must agree to Terms and conditions',
                'description':      (
                                        'Agreement is compulsory to navigate ('
                                        'logged-in users)'
                                    ),
                'default_value':    '1',
                'metadata':         '',
                'group_id':         'terms',
                'group_title':      'Terms and conditions',
                'group_ordering':   5,
                'ordering':         15,
            },
            {
                'id':               'terms_must_agree_anonymous',
                'klass':            'terms',
                'type':             'boolean',
                'value':            '1',
                'title':            (
                                        'Visitors must agree to Terms '
                                        'and conditions'
                                    ),
                'description':      (
                                        'Agreement is compulsory to navigate ('
                                        'anonymous visitors). Warning: this '
                                        'also applies before when visitors '
                                        'redeem a ticket.'
                                    ),
                'default_value':    '1',
                'metadata':         '',
                'group_id':         'terms',
                'group_title':      'Terms and conditions',
                'group_ordering':   5,
                'ordering':         20,
            },
            {
                'id':               'terms_body',
                'klass':            'terms',
                'type':             'text',
                'value':            '',
                'title':            'Terms and conditions text',
                'description':      (
                                        'Markdown for last revision of the '
                                        'terms and conditions (empty for '
                                        'default)'
                                    ),
                'default_value':    loadDefaultTermsBody(),
                'metadata':         '',
                'group_id':         'terms',
                'group_title':      'Terms and conditions',
                'group_ordering':    5,
                'ordering':          25,
            },
            #
            {
                'id':               'about_contact_info',
                'klass':            'about',
                'type':             'string',
                'value':            '',
                'title':            'Contact info',
                'description':      (
                                        'Contact info to show - as image - '
                                        'in the About page'
                                    ),
                'default_value':    'no-contact-info',
                'metadata':         '{"is_text_image":true}',
                'group_id':         'about',
                'group_title':      'About Page',
                'group_ordering':   10,
                'ordering':         5,
            },
            {
                'id':               'about_instance_body',
                'klass':            'about',
                'type':             'text',
                'value':            '',
                'title':            'About, instance-specific body',
                'description':      (
                                        'Markdown for the instance-specific '
                                        'part of the About page (empty for '
                                        'default)'
                                    ),
                'default_value':    loadDefaultAboutInstanceBody(),
                'metadata':         '',
                'group_id':         'about',
                'group_title':      'About Page',
                'group_ordering':   10,
                'ordering':         10,
            },
            {
                'id':               'about_body',
                'klass':            'about',
                'type':             'text',
                'value':            '',
                'title':            'About, generic body',
                'description':      (
                                        'Markdown for the generic-'
                                        'application part of the About page '
                                        '(empty for default)'
                                    ),
                'default_value':    loadDefaultAboutBody(),
                'metadata':         '',
                'group_id':         'about',
                'group_title':      'About Page',
                'group_ordering':   10,
                'ordering':         15,
            },
            #
            {
                'id':               'directories_set_up',
                'klass':            'managed',
                'type':             'boolean',
                'value':            '0',
                'title':            'System directories setup',
                'description':      (
                                        'Post-install setup: have system '
                                        'directories been configured?'
                                    ),
                'default_value':    '0',
                'metadata':         '',
                'group_id':         'post_install_finalisations',
                'group_title':      'Post-install finalisations',
                'group_ordering':    15,
                'ordering':          5,
            },
            {
                'id':               'settings_reviewed',
                'klass':            'managed',
                'type':             'boolean',
                'value':            '0',
                'title':            'App settings review',
                'description':      (
                                        'Post-install setup: has the admin '
                                        'reviewed app behaviour settings?'
                                    ),
                'default_value':    '0',
                'metadata':         '',
                'group_id':         'post_install_finalisations',
                'group_title':      'Post-install finalisations',
                'group_ordering':    15,
                'ordering':          10,
            },
            #
            {
                'id':               'fs_directory',
                'klass':            'system',
                'type':             'nonempty_string',
                'value':            getDefaultFilesystemDirectory(),
                'title':            'Filesystem physical location',
                'description':      (
                                        'Full path of the directory hosting '
                                        'the app file system. Warning: '
                                        'changing this disrupts existing '
                                        'content! Ostracion needs read/write '
                                        'permission on it'
                                    ),
                'default_value':    '',
                'metadata':         '',
                'group_id':         'system_directories',
                'group_title':      'Directories',
                'group_ordering':    5,
                'ordering':          5,
            },
            {
                'id':               'temp_directory',
                'klass':            'system',
                'type':             'nonempty_string',
                'value':            getDefaultTempDirectory(),
                'title':            'Physical temp directory',
                'description':      (
                                        'Full path of the directory used for '
                                        'temporary file manipulations. '
                                        'Ostracion needs read/write permission'
                                        ' on it'
                                    ),
                'default_value':    '',
                'metadata':         '',
                'group_id':         'system_directories',
                'group_title':      'Directories',
                'group_ordering':    5,
                'ordering':          10,
            },
        ],
    },
}

if __name__ == '__main__':
    """An ugly check that the above is ordered as seen on pages."""
    lastGOrd = None
    lastGTitle = None
    prevOrd = None
    for val in initialDbValues['settings']['values']:
        if val['group_ordering'] == lastGOrd:
            goToPrint = None
        else:
            goToPrint = val['group_ordering']
        lastGOrd = val['group_ordering']
        if val['group_title'] == lastGTitle:
            gtToPrint = None
        else:
            gtToPrint = val['group_title']
        #
        lastGTitle = val['group_title']
        print('"%-16s/%-32s/%-48s" : %-48s >> %s . %3i%s' % (
            val['klass'],
            val['group_id'],
            val['id'],
            #
            '"%s"' % gtToPrint if gtToPrint is not None else '',
            '%3i' % goToPrint if goToPrint is not None else '   ',
            val['ordering'],
            '' if goToPrint is not None else '    (%i)' % (
                val['ordering'] - prevOrd
            ),
        ))
        prevOrd = val['ordering']
