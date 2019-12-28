""" userProfilePageTreeDescriptor.py
    Descriptor of the tree for the special-page part 'user profile'
"""

from flask import (
    url_for,
)


def userProfileTitler(db, user):
    """Title for the section 'User Profile'"""
    return 'User "%s"' % user.fullname


def userProfileSubtitler(db, user):
    """Subtitle for the section 'User Profile'"""
    return user.username


def userProfileThumbnailer(db, user):
    """Icon for the section 'User Profile'"""
    return url_for(
        'userThumbnailView',
        dummyId='%s_' % user.icon_file_id,
        username=user.username,
    )


userProfilePageDescriptor = {
    'tasks': {
        'root': {
            'title': 'User profile',
            'subtitle': '',
            'image_id': ('user_images', 'user_icon'),
            'endpoint_name': ('userProfileView', {}),
            'task_order': [
                'user_data',
                'icon',
                'file_tickets',
                'upload_tickets',
                'gallery_tickets',
                'change_password',
                'delete_account',
            ],
            'tasks': {
                'user_data': {
                    'title': 'User data',
                    'subtitle': 'Edit user profile',
                    'image_id': ('user_images', 'user_data'),
                    'endpoint_name': ('editUserDataView', {}),
                },
                'icon': {
                    'title': 'Icon',
                    'subtitle': 'Change or remove profile picture',
                    'image_id': ('user_images', 'profile_thumbnail'),
                    'endpoint_name': (
                        'setIconView',
                        {'mode': 'u', 'itemPathString': 'self'},
                    ),
                },
                'file_tickets': {
                    'title': 'File tickets',
                    'subtitle': 'Manage issued file tickets',
                    'image_id': ('app_images', 'file_ticket'),
                    'endpoint_name': ('userFileTicketsView', {}),
                },
                'upload_tickets': {
                    'title': 'Upload tickets',
                    'subtitle': 'Manage issued upload tickets',
                    'image_id': ('app_images', 'upload_ticket'),
                    'endpoint_name': ('userUploadTicketsView', {}),
                },
                'gallery_tickets': {
                    'title': 'Gallery tickets',
                    'subtitle': 'Manage issued gallery tickets',
                    'image_id': ('app_images', 'gallery_ticket'),
                    'endpoint_name': ('userGalleryTicketsView', {}),
                },
                'change_password': {
                    'title': 'Password',
                    'subtitle': 'Change your password',
                    'image_id': ('user_images', 'change_password'),
                    'endpoint_name': ('userChangePasswordView', {}),
                },
                'delete_account': {
                    'title': 'Delete account',
                    'subtitle': 'Permanently and completely delete account',
                    'image_id': ('user_images', 'delete_account'),
                    'endpoint_name': ('deleteUserView', {}),
                },
            },
        },
    },
}
