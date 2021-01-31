""" userprofile.py
    Views of the 'my profile' section.
"""

from flask import (
    g,
    render_template,
    url_for,
    redirect,
    request,
)

from flask_login import (
    login_required,
    logout_user,
)

from ostracion_app.app_main import app

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.forms.forms import (
    generateChangePasswordForm,
    UserDataForm,
)

from ostracion_app.utilities.models.User import User

from ostracion_app.utilities.fileIO.physical import (
    flushFsDeleteQueue,
)

from ostracion_app.utilities.tools.formatting import (
    applyDefault,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)
from ostracion_app.utilities.database.userDeletion import (
    dbDeleteUser,
)
from ostracion_app.utilities.database.userTools import (
    dbUpdateUser,
    getUserFullName,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.database.tickets import (
    dbGetAllFileTicketsByUser,
    dbGetAllUploadTicketsByUser,
    dbGetAllGalleryTicketsByUser,
    enrichTicket,
    richTicketSorter,
)

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

from ostracion_app.views.viewTools.userProfilePageTreeDescriptor import (
    userProfilePageDescriptor,
    userProfileTitler,
    userProfileSubtitler,
    userProfileThumbnailer,
)


@app.route('/userprofile')
@login_required
def userProfileView():
    """Main user profile route."""
    user = g.user
    db = dbGetDatabase()
    infoLines = [
        {
            'heading': 'Email',
            'value': user.email,
        },
        {
            'heading': 'Icon set by',
            'value': getUserFullName(db, user.icon_file_id_username),
        },
    ]
    roleList = [
        r
        for r in sorted(user.roles)
        if r.roleKey() != ('system', 'anonymous')
    ]
    pageFeatures = prepareTaskPageFeatures(
        userProfilePageDescriptor,
        ['root'],
        g,
        overrides={
            'pageSubtitle': userProfileTitler(db, user),
            'pageSubtitleit': userProfileSubtitler(db, user),
            'iconUrl': userProfileThumbnailer(db, user),
        },
    )
    return render_template(
        'tasks.html',
        user=user,
        infoLines=infoLines,
        roleList=roleList,
        bgcolor=g.settings['color']['task_colors']['user_task']['value'],
        **pageFeatures,
    )


@app.route('/userchangepassword', methods=['GET', 'POST'])
@login_required
def userChangePasswordView():
    """Change-password (as user) route."""
    user = g.user
    db = dbGetDatabase()
    form = generateChangePasswordForm(g.settings)
    request._onErrorUrl = url_for('userProfileView')
    #
    if form.validate_on_submit():
        # check that the old password matches
        if not user.checkPassword(form.oldpassword.data):
            flashMessage('Info', 'Please retry', 'Old password does not match')
            return redirect(url_for('userChangePasswordView'))
        else:
            minPasswordLength = g.settings['behaviour']['behaviour_security'][
                'password_min_length']['value']
            if len(form.newpassword.data) < minPasswordLength:
                flashMessage(
                    'Info',
                    'Please retry',
                    'Password too short (min. %i characters)' % (
                        minPasswordLength
                    ),
                )
                return redirect(url_for('userChangePasswordView'))
            else:
                # store the new one
                newUser = User(**({
                    (k
                     if k != 'passwordhash'
                     else 'password'): (v
                                        if k != 'passwordhash'
                                        else form.newpassword.data)
                    for k, v in user.asDict().items()
                }))
                dbUpdateUser(db, newUser, user)
                # flash a message
                flashMessage(
                    'Success',
                    'Success',
                    'Password changed. Please log out and log in again',
                )
                # go to user profile
                return redirect(url_for('userProfileView'))
    else:
        pageFeatures = prepareTaskPageFeatures(
            userProfilePageDescriptor,
            ['root', 'change_password'],
            g,
            overrides={
                'pageSubtitle': ('Enter the old password and '
                                 '(twice) the new one'),
            },
        )
        return render_template(
            'userchangepassword.html',
            user=user,
            form=form,
            showOldPasswordField=True,
            mode='self',
            backToUrl=url_for('userProfileView'),
            **pageFeatures,
        )


@app.route('/usergallerytickets')
@login_required
def userGalleryTicketsView():
    """Issued gallery-tickets (as user) route."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('userProfileView')
    #
    ticketDicts = sorted(
        (
            enrichTicket(db, t, urlRoot=request.url_root)
            for t in dbGetAllGalleryTicketsByUser(db, user)
        ),
        key=richTicketSorter,
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        userProfilePageDescriptor,
        ['root', 'gallery_tickets'],
        g,
    )
    return render_template(
        'viewtickets.html',
        user=user,
        tickets=ticketDicts,
        mode='g',
        targetName='Gallery',
        newItemMenu=None,
        **pageFeatures,
    )


@app.route('/useruploadtickets')
@login_required
def userUploadTicketsView():
    """Issued upload-tickets (as user) route."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('userProfileView')
    #
    ticketDicts = sorted(
        (
            enrichTicket(db, t, urlRoot=request.url_root)
            for t in dbGetAllUploadTicketsByUser(db, user)
        ),
        key=richTicketSorter,
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        userProfilePageDescriptor,
        ['root', 'upload_tickets'],
        g,
    )
    return render_template(
        'viewtickets.html',
        user=user,
        tickets=ticketDicts,
        mode='c',
        targetName='Box',
        newItemMenu=None,
        **pageFeatures,
    )


@app.route('/userfiletickets')
@login_required
def userFileTicketsView():
    """Issued file-tickets (as user) route."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('userProfileView')
    #
    ticketDicts = sorted(
        (
            enrichTicket(db, t, urlRoot=request.url_root)
            for t in dbGetAllFileTicketsByUser(db, user)
        ),
        key=richTicketSorter,
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        userProfilePageDescriptor,
        ['root', 'file_tickets'],
        g,
    )
    return render_template(
        'viewtickets.html',
        user=user,
        tickets=ticketDicts,
        mode='f',
        targetName='File',
        newItemMenu=None,
        **pageFeatures,
    )


@app.route('/userdata', methods=['GET', 'POST'])
@login_required
def editUserDataView():
    """Edit-user-data route."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('userProfileView')
    form = UserDataForm()
    #
    if form.validate_on_submit():
        #
        newUser = User(**user.asDict())
        newUser.email = form.email.data
        newUser.fullname = form.fullname.data
        #
        dbUpdateUser(db, newUser, user)
        #
        return redirect(url_for('userProfileView'))
    else:
        form.email.data = applyDefault(
            form.email.data,
            user.email,
        )
        form.fullname.data = applyDefault(
            form.fullname.data,
            user.fullname,
        )
        pageFeatures = prepareTaskPageFeatures(
            userProfilePageDescriptor,
            ['root', 'user_data'],
            g,
        )
        return render_template(
            'userdataedit.html',
            user=user,
            form=form,
            backToUrl=url_for('userProfileView'),
            **pageFeatures,
        )


@app.route('/deleteuser')
@app.route('/deleteuser/<int:confirm>')
@login_required
def deleteUserView(confirm=0):
    """ Delete user route.
        Uses 'confirm' to distinguish between before-
        and after- having asked 'are you sure?'.
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('userProfileView')
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    if confirm == 0:
        pageFeatures = prepareTaskPageFeatures(
            userProfilePageDescriptor,
            ['root', 'delete_account'],
            g,
            overrides={
                'pageTitle': None,
                'pageSubtitle': None,
            },
        )
        return render_template(
            'confirmoperation.html',
            user=user,
            confirmation={
                'heading': ('Warning: this will irreversibly delete your '
                            'account, all uploaded contents, all icons set '
                            'by and all metadata edited by your user. There '
                            'is no way back.'),
                'forwardToUrl': url_for('deleteUserView', confirm=1),
                'backToUrl': url_for('userProfileView'),
            },
            **pageFeatures,
        )
    else:
        fsDeleteQueue = dbDeleteUser(
            db,
            user.username,
            user,
            fileStorageDirectory=fileStorageDirectory,
        )
        flushFsDeleteQueue(fsDeleteQueue)
        flashMessage(
            'Success',
            'Success',
            ('User %s ("%s") irreversibly removed from existence. '
             'Logging out now') % (
                user.username,
                user.fullname,
            ),
        )
        logout_user()
        return redirect(url_for('indexView'))
