""" admin.py
    Views related to the admin panel and other
    admin-only parts of the app.
"""

from operator import itemgetter
import datetime

from flask import (
    g,
    abort,
    render_template,
    url_for,
    redirect,
    request,
)

from ostracion_app.utilities.fileIO.physical import (
    mkDirP,
    isWritableDirectory,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

from ostracion_app.app_main import app

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.models.Role import Role
from ostracion_app.utilities.models.User import User
from ostracion_app.utilities.models.BoxRolePermission import BoxRolePermission

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)
from ostracion_app.utilities.database.userTools import (
    dbGetUser,
    dbUpdateUser,
    dbCreateUser,
    dbDeleteUser,
    dbGetAllUsers,
    getUserFullName,
)
from ostracion_app.utilities.database.permissions import (
    dbGetAllRoles,
    dbGetUsersByRole,
    dbDeleteRole,
    dbGetRole,
    dbUpdateRole,
    dbCreateRole,
    dbGetUserRoles,
    dbGrantRoleToUser,
    dbRevokeRoleFromUser,
    userIsAdmin,
    dbDeleteBoxRolePermission,
    dbInsertBoxRolePermission,
    dbToggleBoxRolePermissionBit,
    reformatBoxPermissionAlgebraIntoLists,
)
from ostracion_app.utilities.database.usernameChecks import (
    isUsername,
    isProspectedUsername,
)

from ostracion_app.utilities.database.tickets import (
    dbGetAllUserInvitationTickets,
    dbMakeUserInvitationTicket,
    dbGetAllUserChangePasswordTickets,
    dbMakeUserChangePasswordTicket,
    dbGetAllFileTickets,
    dbGetAllUploadTickets,
    dbGetAllGalleryTickets,
    enrichTicket,
    richTicketSorter,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingSubmapIntoListForConfigViews,
    makeSettingImageUrl,
    dbUpdateStandardSettingDict,
    getFormValueFromSetting,
)

from ostracion_app.utilities.tools.formatting import (
    applyDefault,
    transformIfNotEmpty,
)

from ostracion_app.utilities.tools.setNaming import (
    colloquialJoinClauses,
)

from ostracion_app.utilities.viewTools.pathTools import (
    makeBreadCrumbs,
    splitPathString,
    prepareTaskPageFeatures,
    describeBoxTitle,
)

from ostracion_app.utilities.database.fileSystem import (
    getBoxFromPath,
)

from ostracion_app.utilities.database.permissions import (
    userHasPermission,
    calculateBoxPermissionAlgebra,
    userRoleRequired,
)

from ostracion_app.utilities.fileIO.physical import (
    flushFsDeleteQueue,
)

from ostracion_app.utilities.forms.forms import (
    EditRoleForm,
    UserDataForm,
    generateNewUserForm,
    generateChangePasswordForm,
    generateColorForm,
    generateGenericSettingsForm,
    generateUserInvitationTicketForm,
    generateChangePasswordTicketForm,
)

from ostracion_app.utilities.tools.markdownTools import (
    loadMarkdownReplacements,
)

from ostracion_app.views.viewTools.adminPageTreeDescriptor import (
    genericSettingsPageDesc,
    adminPageDescriptor,
)


@app.route('/adminhome')
@userRoleRequired({('system', 'admin')})
def adminHomeView():
    """Main-page route for admin area."""
    user = g.user
    db = dbGetDatabase()
    #
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root'],
        g,
    )
    #
    return render_template(
        'tasks.html',
        user=user,
        bgcolor=g.settings['color']['task_colors']['admin_task']['value'],
        **pageFeatures,
    )


@app.route('/adminsettings')
@userRoleRequired({('system', 'admin')})
def adminHomeSettingsView():
    """Admin/Settings generic route."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('adminHomeView')
    #
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root', 'settings'],
        g,
    )
    #
    return render_template(
        'tasks.html',
        user=user,
        bgcolor=g.settings['color']['task_colors']['admin_task']['value'],
        **pageFeatures,
    )


@app.route('/adminsettings_generic/<settingType>', methods=['GET', 'POST'])
@userRoleRequired({('system', 'admin')})
def adminHomeSettingsGenericView(settingType):
    """Admin/Settings/<standard_settings> route, with one parameter."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('adminHomeSettingsView')
    #
    groupedSettings = makeSettingSubmapIntoListForConfigViews(
        g.settings[genericSettingsPageDesc[settingType]['settingKlass']],
    )
    form = generateGenericSettingsForm(groupedSettings)
    wideIdToFormProperties = {
        '%s___%s' % (gSet['setting'].group_id, gSet['setting'].id): {
            'group_caption': (gSet['setting'].group_title
                              if gSetIndex == 0
                              else None),
            'richSetting': gSet,
        }
        for _, gSets in groupedSettings
        for gSetIndex, gSet in enumerate(gSets)
    }

    if form.validate_on_submit():
        # we gather the results and directly invoke a loop of saves
        for genSetting in (s for _, gSets in groupedSettings for s in gSets):
            dbUpdateStandardSettingDict(
                db,
                genSetting,
                getattr(
                    form,
                    '%s___%s' % (
                        genSetting['setting'].group_id,
                        genSetting['setting'].id,
                    )
                ).data,
                user,
                skipCommit=True
            )
        #
        if settingType == 'system_settings':
            fsDir = form.system_directories___fs_directory.data
            tmpDir = form.system_directories___temp_directory.data
            okTmp = isWritableDirectory(tmpDir)
            okFs = isWritableDirectory(fsDir)
            if not okTmp or not okFs:
                # flash a message
                if not okTmp:
                    flashMessage(
                        'Error',
                        'Error',
                        ('Temp directory FAILED the read/write access '
                         'test. Platform cannot be currently used'),
                    )
                if not okFs:
                    flashMessage(
                        'Error',
                        'Error',
                        ('Filesystem physical directory FAILED the read/write '
                         'access test. Platform cannot be currently used'),
                    )
            else:
                # message
                flashMessage(
                    'Info',
                    'Info',
                    ('Provided directories have passed the read/write '
                     'access test. The application is now set up')
                )
            # setting about fs usability
            dbUpdateStandardSettingDict(
                db,
                g.settings['managed']['post_install_finalisations'][
                    'directories_set_up'],
                okTmp and okFs,
                user,
                skipCommit=True,
            )
        elif settingType == 'behaviour':
            if not g.settings['managed']['post_install_finalisations'][
                    'settings_reviewed']['value']:
                # we issue a 'post-install finished' message and that's it
                flashMessage(
                    'Info',
                    'Post-install completed',
                    ('The application is now fully functioning. A good '
                     'place to start is creating users, making more admins '
                     'and/or changing the current admin password; '
                     'moreover, the contact emails (DPO and Website info, '
                     'in the Privacy policy and About page settings '
                     'respectively) should be set as soon as possible.'),
                )
            # we just duly note that the settings page has been reviewed
            dbUpdateStandardSettingDict(
                db,
                g.settings['managed']['post_install_finalisations'][
                    'settings_reviewed'],
                True,
                user,
                skipCommit=True,
            )
        #
        db.commit()
        return redirect(url_for('adminHomeSettingsView'))
    else:
        # valorizing form
        for genSetting in (s for _, gSets in groupedSettings for s in gSets):
            thisFormComponent = getattr(
                form,
                '%s___%s' % (
                    genSetting['setting'].group_id,
                    genSetting['setting'].id,
                )
            )
            # reasons for the hacks below:
            # 1. for Boolean, the form .data is always either T or F
            # 2. for option, the default value of .data is the
            #    string 'None' (!)
            thisFormComponent.data = applyDefault(
                (thisFormComponent.data
                 if genSetting['setting'].type not in {'boolean'}
                 else None),
                getFormValueFromSetting(genSetting['setting']),
                additionalNulls=(['None']
                                 if genSetting['setting'].type == 'option'
                                 else [])
            )
        #
        pageFeatures = prepareTaskPageFeatures(
            adminPageDescriptor,
            ['root', 'settings', settingType],
            g,
        )
        if genericSettingsPageDesc[settingType]['markdownHelp']:
            pageFeatures['pageSubtitle'] = '%s. %s' % (
                pageFeatures['pageSubtitle'],
                'Special macros available in the markdown: %s' % (
                    ', '.join(
                        '"%s"' % repName
                        for repName, _ in sorted(
                            loadMarkdownReplacements(g.settings),
                            key=itemgetter(0),
                        )
                    )
                ),
            )
        #
        return render_template(
            'adminsettings_generic.html',
            user=user,
            form=form,
            groupedSettings=groupedSettings,
            wideIdToFormProperties=wideIdToFormProperties,
            **pageFeatures,
        )


@app.route('/adminsettings_images')
@userRoleRequired({('system', 'admin')})
def adminHomeSettingsImagesView():
    """Admin/Settings/Images route."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('adminHomeSettingsView')
    imageGroupedSettings = makeSettingSubmapIntoListForConfigViews(
        g.settings['image'],
    )
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root', 'settings', 'images'],
        g,
    )
    #
    return render_template(
        'adminsettings_images.html',
        user=user,
        groupedSettings=imageGroupedSettings,
        **pageFeatures,
    )


@app.route('/adminsettings_colors', methods=['GET', 'POST'])
@userRoleRequired({('system', 'admin')})
def adminHomeSettingsColorsView():
    """Admin/Settings/Colors route."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('adminHomeSettingsView')
    colorGroupedSettings = makeSettingSubmapIntoListForConfigViews(
        g.settings['color'],
    )
    wideIdToFormProperties = {
        '%s___%s' % (gSet['setting'].group_id, gSet['setting'].id): {
            'group_caption': (gSet['setting'].group_title
                              if gSetIndex == 0
                              else None),
            'richSetting': gSet,
        }
        for _, gSets in colorGroupedSettings
        for gSetIndex, gSet in enumerate(gSets)
    }
    form = generateColorForm(colorGroupedSettings)
    #
    if form.validate_on_submit():
        # we gather the results and directly invoke a loop of saves
        for cSetting in (
                s
                for _, gSets in colorGroupedSettings
                for s in gSets):
            dbUpdateStandardSettingDict(
                db,
                cSetting,
                getattr(
                    form,
                    '%s___%s' % (
                        cSetting['setting'].group_id,
                        cSetting['setting'].id,
                    )
                ).data,
                user,
                skipCommit=True,
            )
        db.commit()
        return redirect(url_for('adminHomeSettingsView'))
    else:
        # we valorize the in-values
        for cSetting in (
                s
                for _, gSets in colorGroupedSettings
                for s in gSets):
            thisFormComponent = getattr(
                form,
                '%s___%s' % (
                    cSetting['setting'].group_id,
                    cSetting['setting'].id
                )
            )
            thisFormComponent.data = applyDefault(
                thisFormComponent.data,
                getFormValueFromSetting(cSetting['setting']),
            )
        #
        pageFeatures = prepareTaskPageFeatures(
            adminPageDescriptor,
            ['root', 'settings', 'colors'],
            g,
        )
        pageFeatures['pageSubtitle'] = '%s. %s' % (
            pageFeatures['pageSubtitle'],
            'Insert colors as e.g. "#80b0ff" (pound symbol optional)',
        )
        #
        return render_template(
            'adminsettings_colors.html',
            user=user,
            form=form,
            wideIdToFormProperties=wideIdToFormProperties,
            groupedSettings=colorGroupedSettings,
            **pageFeatures,
        )


@app.route('/adminusers')
@userRoleRequired({('system', 'admin')})
def adminHomeUsersView():
    """Admin/users route."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('adminHomeView')

    def equipUser(d, u, usr):
        u.setRoles([
            r
            for r in dbGetUserRoles(d, u)
            if r.roleKey() != ('system', 'anonymous')
        ])
        return {
            'user': u,
            'profilepicture': url_for(
                'userThumbnailView',
                dummyId='%s_' % u.icon_file_id,
                username=u.username,
            ),
            'canDelete': not userIsAdmin(db, u),
            'bannable': u.username != usr.username,
            'is_current_user': u.username == usr.username,
        }
    #
    users = [
        equipUser(db, u, user)
        for u in sorted(
            dbGetAllUsers(db, user),
            key=lambda u: (
                0.0 if u.username == user.username else 1.0,
                0.0 if userIsAdmin(db, u) else 1.0,
                u.username.lower(),
            ),
        )
    ]
    #
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root', 'users'],
        g,
    )
    return render_template(
        'adminusers.html',
        user=user,
        users=users,
        **pageFeatures,
    )


@app.route('/adminuserroles/<username>')
@app.route('/adminuserroles/<username>/<op>/<roleClass>/<roleId>')
@userRoleRequired({('system', 'admin')})
def adminUserRolesView(username, op=None, roleClass=None, roleId=None):
    """Admin/Users/role-for-a-user route."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('adminHomeView')
    #
    targetUser = dbGetUser(db, username)
    targetUser.setRoles([
        r
        for r in dbGetUserRoles(db, targetUser)
        if r.roleKey() != ('system', 'anonymous')
    ])
    grantedRoleKeys = {r.roleKey() for r in targetUser.roles}
    # reaction to requested operations add/remove
    if op == 'add':
        # does the role exist? is it not anonymous?
        # is it not yet among the user roles?
        roleToAdd = dbGetRole(db, roleClass, roleId, user)
        if roleToAdd is None:
            request._onErrorUrl = url_for(
                'adminUserRolesView',
                username=username,
            )
            raise OstracionError('Role does not exist')
        else:
            dbGrantRoleToUser(db, roleToAdd, targetUser, user)
            return redirect(url_for('adminUserRolesView', username=username))
    elif op == 'del':
        roleToRevoke = dbGetRole(db, roleClass, roleId, user)
        if roleToRevoke is None:
            request._onErrorUrl = url_for(
                'adminUserRolesView',
                username=username,
            )
            raise OstracionError('Role does not exist')
        else:
            dbRevokeRoleFromUser(db, roleToRevoke, targetUser, user)
            return redirect(url_for(
                'adminUserRolesView',
                username=username,
            ))

    def equipRole(db, r, grantedKeys, user):
        return {
            'role': r,
            'granted': r.roleKey() in grantedKeys,
        }

    allRoles = [
        equipRole(db, r, grantedRoleKeys, user)
        for r in sorted(
            (
                ro
                for ro in dbGetAllRoles(db, user)
                if ro.can_user != 0
            ),
            key=lambda _r: (
                _r.can_delete,
                _r.can_box,
                _r.can_user,
                _r.description.lower(),
                _r.description
            ),
        )
    ]
    #
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root', 'users'],
        g,
        appendedItems=[
            {
                'kind': 'link',
                'link': False,
                'target': url_for('adminUserRolesView', username=username),
                'name': 'Roles for user',
            }
        ],
    )
    #
    return render_template(
        'adminuserroles.html',
        user=user,
        targetUser=targetUser,
        roleItems=allRoles,
        **pageFeatures,
    )


@app.route('/adminroles')
@userRoleRequired({('system', 'admin')})
def adminHomeRolesView():
    """Admin/Roles route."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('adminHomeView')

    def equipRole(d, rl, ur):
        users = [
            {
                'username': u.username,
                'fullname': getUserFullName(db, u.username),
            }
            for u in sorted(
                (
                    u
                    for u in dbGetUsersByRole(
                        d,
                        rl.role_class,
                        rl.role_id,
                        ur,
                    )
                ),
                key=lambda u: u.username,
            )
        ]
        canDelete = rl.can_delete != 0 and len(users) == 0
        return {
            'role': rl,
            'role_users': users,
            'canDelete': canDelete,
        }
    #
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root', 'roles'],
        g,
    )
    roles = [
        equipRole(db, role, user)
        for role in sorted(
            dbGetAllRoles(db, user),
            key=lambda r: r.sortableTuple(),
        )
    ]
    return render_template(
        'adminroles.html',
        user=user,
        roles=roles,
        **pageFeatures,
    )


@app.route('/admindeleterole/<roleClass>/<roleId>')
@userRoleRequired({('system', 'admin')})
def adminDeleteRoleView(roleClass, roleId):
    """Route to delete a role."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('adminHomeRolesView')
    dbDeleteRole(db, roleClass, roleId, user)
    return redirect(url_for('adminHomeRolesView'))


@app.route('/adminnewrole', methods=['GET', 'POST'])
@app.route('/admineditrole/<roleClass>/<roleId>', methods=['GET', 'POST'])
@userRoleRequired({('system', 'admin')})
def adminEditRole(roleClass='manual', roleId=None):
    """Route to edit a role."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for('adminHomeRolesView')
    #
    form = EditRoleForm()
    if form.validate_on_submit():
        # either overwrite or insert new, depending on roleId
        # (plus checks)
        role = Role(
            role_class=roleClass,
            role_id=form.roleid.data,
            description=form.roledescription.data,
            can_delete=1,
            can_user=1,
            can_box=1,
        )
        if roleId is None:
            dbCreateRole(db, role, user)
        else:
            # updating
            if role.roleKey() == (roleClass, roleId):
                dbUpdateRole(db, role, user)
            else:
                raise RuntimeError('Malformed request')
        return redirect(url_for('adminHomeRolesView'))
    else:
        #
        if roleId is not None:
            role = dbGetRole(db, roleClass, roleId, user)
            if role is None:
                raise OstracionWarning('Could not retrieve role')
        else:
            role = None
        #
        if role is not None:
            form.roleid.data = applyDefault(
                form.roleid.data,
                role.role_id,
            )
            form.roledescription.data = applyDefault(
                form.roledescription.data,
                role.description,
            )
            _roleClass = role.role_class
            _roleCanDelete = role.can_delete
            _roleCanBox = role.can_box
            _roleCanUser = role.can_user
        else:
            _roleClass = 'manual'
            _roleCanDelete = 1
            _roleCanBox = 1
            _roleCanUser = 1
        #
        pageTitle = 'New role' if roleId is None else 'Edit role'
        roleCans = colloquialJoinClauses([
            sent
            for sent in (
                ('be associated to boxes with specific permissions'
                 if _roleCanBox
                 else None),
                ('be attached to users to grant them permissions'
                 if _roleCanUser
                 else None),
                'be deleted' if _roleCanDelete else None,
            )
            if sent is not None
        ])
        pageSubtitle = 'This "%s" role can %s.' % (
            _roleClass,
            roleCans,
        )
        # here the subtitle depending on what role this is
        pageFeatures = prepareTaskPageFeatures(
            adminPageDescriptor,
            ['root', 'roles'],
            g,
            appendedItems=[
                {
                    'kind': 'link',
                    'link': False,
                    'target': url_for(
                        'adminEditRole',
                        **{
                            k: v
                            for k, v in {
                                'roleId': roleId,
                                'roleClass': roleClass,
                            }.items()
                            if v is not None
                        }
                    ),
                    'name': pageTitle,
                }
            ],
            overrides={
                'pageTitle': pageTitle,
                'pageSubtitle': pageSubtitle,
            },
        )
        #
        return render_template(
            'admineditrole.html',
            user=user,
            form=form,
            editableId=roleId is None,
            **pageFeatures,
            backToUrl=url_for('adminHomeRolesView'),
        )


@app.route('/adminedituser/<username>', methods=['POST', 'GET'])
@userRoleRequired({('system', 'admin')})
def adminEditUser(username):
    """Route to (admin-is-god) edit a user."""
    request._onErrorUrl = url_for('adminHomeUsersView')
    adminIsGod = g.settings['behaviour']['behaviour_admin_powers'][
        'admin_is_god']['value']
    if not adminIsGod:
        raise OstracionError(
            'This feature is turned off in the configuration'
        )
    else:
        user = g.user
        db = dbGetDatabase()
        editeeUser = dbGetUser(db, username)
        form = UserDataForm()
        #
        if form.validate_on_submit():
            #
            newUser = User(**editeeUser.asDict())
            newUser.email = form.email.data
            newUser.fullname = form.fullname.data
            #
            dbUpdateUser(db, newUser, user)
            #
            return redirect(url_for('adminHomeUsersView'))
        else:
            form.email.data = applyDefault(
                form.email.data,
                editeeUser.email,
            )
            form.fullname.data = applyDefault(
                form.fullname.data,
                editeeUser.fullname,
            )
            #
            pageFeatures = prepareTaskPageFeatures(
                adminPageDescriptor,
                ['root', 'users'],
                g,
                appendedItems=[
                    {
                        'kind': 'link',
                        'link': False,
                        'target': url_for(
                            'adminEditUser',
                            username=username,
                        ),
                        'name': 'Edit user',
                    }
                ],
                overrides={
                    'pageTitle': 'Edit user profile',
                    'pageSubtitle': 'Edit email and full name',
                    'iconUrl': makeSettingImageUrl(
                        g,
                        'user_images',
                        'user_data',
                    ),
                },
            )
            #
            return render_template(
                'userdataedit.html',
                user=user,
                form=form,
                backToUrl=url_for('adminHomeUsersView'),
                **pageFeatures,
            )


@app.route('/adminnewuser', methods=['GET', 'POST'])
@userRoleRequired({('system', 'admin')})
def adminNewUserView():
    """Route to (admin-is-god) create a new user explicitly."""
    request._onErrorUrl = url_for('adminHomeUsersView')
    adminIsGod = g.settings['behaviour']['behaviour_admin_powers'][
        'admin_is_god']['value']
    if not adminIsGod:
        raise OstracionError(
            'This feature is turned off in the configuration'
        )
    else:
        #
        user = g.user
        db = dbGetDatabase()
        form = generateNewUserForm(g.settings)
        pageFeatures = prepareTaskPageFeatures(
            adminPageDescriptor,
            ['root', 'users'],
            g,
            appendedItems=[
                {
                    'kind': 'link',
                    'link': False,
                    'target': url_for('adminNewUserView'),
                    'name': 'New user',
                }
            ],
            overrides={
                'pageTitle': 'New user',
                'pageSubtitle': ('Remember to safely provide username/'
                                 'password to the account holder '
                                 'after creation'),
                'iconUrl': makeSettingImageUrl(g, 'user_images', 'user_icon'),
            },
        )
        if form.validate_on_submit():
            #
            if isUsername(db, form.username.data, user):
                # for the convenience of keeping filled form fields,
                # this flashMessage is not made into a raised error
                flashMessage('Warning', 'Warning', 'Username exists already')
                return render_template(
                    'newuser.html',
                    user=user,
                    form=form,
                    lockUsernameField=False,
                    **pageFeatures,
                )
            else:
                #
                newUser = User(
                    username=form.username.data,
                    fullname=form.fullname.data,
                    email=form.email.data,
                    password=form.password.data,
                    icon_file_id='',
                    icon_file_id_username='',
                    banned=0,
                )
                dbCreateUser(db, newUser, user)
                return redirect(url_for('adminHomeUsersView'))
        else:
            return render_template(
                'newuser.html',
                user=user,
                form=form,
                lockUsernameField=False,
                **pageFeatures,
            )


@app.route('/adminuserchangepassword/<username>', methods=['GET', 'POST'])
@userRoleRequired({('system', 'admin')})
def adminUserChangePasswordView(username):
    """Route to (admin-is-god) explicitly change the password of a user."""
    request._onErrorUrl = url_for('adminHomeUsersView')
    adminIsGod = g.settings['behaviour']['behaviour_admin_powers'][
        'admin_is_god']['value']
    if not adminIsGod:
        raise OstracionError(
            'This feature is turned off in the configuration'
        )
    else:
        user = g.user
        db = dbGetDatabase()
        form = generateChangePasswordForm(g.settings)
        changeeUser = dbGetUser(db, username)
        #
        if form.validate_on_submit():
            # check that the old password matches
            if not user.checkPassword(form.oldpassword.data):
                request._onErrorUrl = url_for(
                    'adminUserChangePasswordView',
                    username=username,
                )
                raise OstracionWarning(
                    'Please retry: old password does not match'
                )
            else:
                minPasswordLength = g.settings['behaviour'][
                    'behaviour_security']['password_min_length']['value']
                if len(form.newpassword.data) < minPasswordLength:
                    request._onErrorUrl = url_for(
                        'adminUserChangePasswordView',
                        username=username,
                    )
                    raise OstracionWarning(
                        ('Please retry: password too short '
                         '(min. %i characters)') % minPasswordLength
                    )
                else:
                    # store the new one
                    newUser = User(**({
                        (k
                         if k != 'passwordhash'
                         else 'password'): (v
                                            if k != 'passwordhash'
                                            else form.newpassword.data)
                        for k, v in changeeUser.asDict().items()
                    }))
                    dbUpdateUser(db, newUser, user)
                    # flash a message
                    flashMessage(
                        'Success',
                        'Success',
                        ('Password changed. Please provide the new '
                         'password to user %s ("%s")') % (
                            newUser.username,
                            newUser.fullname,
                        )
                    )
                    # go to user profile
                    return redirect(url_for('adminHomeUsersView'))
        else:
            pageFeatures = prepareTaskPageFeatures(
                adminPageDescriptor,
                ['root', 'users'],
                g,
                appendedItems=[
                    {
                        'kind': 'link',
                        'link': False,
                        'target': url_for(
                            'adminUserChangePasswordView',
                            username=username,
                        ),
                        'name': 'Change password',
                    }
                ],
                overrides={
                    'iconUrl': makeSettingImageUrl(
                        g,
                        'user_images',
                        'change_password',
                    ),
                    'pageTitle': 'Change password',
                    'pageSubtitle': ('Enter your admin password and (twice) '
                                     'the user\'s new one'),
                }
            )
            return render_template(
                'userchangepassword.html',
                user=user,
                form=form,
                showOldPasswordField=True,
                mode='admin',
                backToUrl=url_for('adminHomeUsersView'),
                **pageFeatures,
            )


@app.route('/adminbanuser/<username>/<int:state>')
@userRoleRequired({('system', 'admin')})
def adminBanUserView(username, state):
    """Route to ban/unban a user."""
    request._onErrorUrl = url_for('adminHomeUsersView')
    user = g.user
    db = dbGetDatabase()
    banneeUser = dbGetUser(db, username)
    if user.username != banneeUser.username or state == 0:
        newUser = User(**banneeUser.asDict())
        newUser.banned = state
        dbUpdateUser(db, newUser, user)
    else:
        raise OstracionWarning('Cannot apply ban to self')
    return redirect(url_for('adminHomeUsersView'))


@app.route('/admindeleteuser/<username>')
@app.route('/admindeleteuser/<username>/<int:confirm>')
@userRoleRequired({('system', 'admin')})
def adminDeleteUserView(username, confirm=0):
    """ Route to delete a user.
        The need for a confirmation prompt is handled with
        the parameter 'confirm', which is set to 1 only in the request
        to this endpoint coming from going through
        the ok in the conf. prompt.
    """
    request._onErrorUrl = url_for('adminHomeUsersView')
    user = g.user
    db = dbGetDatabase()
    deleteeUser = dbGetUser(db, username)
    if deleteeUser is not None:
        fileStorageDirectory = g.settings['system']['system_directories'][
            'fs_directory']['value']
        if confirm == 0:
            pageFeatures = prepareTaskPageFeatures(
                adminPageDescriptor,
                ['root', 'users'],
                g,
                appendedItems=[
                    {
                        'kind': 'link',
                        'link': False,
                        'target': url_for(
                            'adminDeleteUserView',
                            username=username,
                        ),
                        'name': 'Delete account',
                    }
                ],
                overrides={
                    'iconUrl': makeSettingImageUrl(
                        g,
                        'user_images',
                        'delete_account',
                    ),
                    'pageTitle': None,
                    'pageSubtitle': None,
                }
            )
            return render_template(
                'confirmoperation.html',
                contents={},
                user=user,
                confirmation={
                    'heading': ('Warning: this will irreversibly delete '
                                'the user, all its uploaded contents, all'
                                ' icons set by and all metadata edited by'
                                ' the user. There is no way back'),
                    'forwardToUrl': url_for(
                        'adminDeleteUserView',
                        username=username,
                        confirm=1,
                    ),
                    'backToUrl': url_for('adminHomeUsersView'),
                },
                **pageFeatures,
            )
        else:
            fsDeleteQueue = dbDeleteUser(
                db,
                username,
                user,
                fileStorageDirectory=fileStorageDirectory,
            )
            flushFsDeleteQueue(fsDeleteQueue)
            #
            flashMessage(
                'Success',
                'Success',
                'User %s ("%s") irreversibly removed from existence' % (
                    username,
                    deleteeUser.fullname,
                ),
            )
            return redirect(url_for('adminHomeUsersView'))
    else:
        raise OstracionError('User not found')


@app.route('/adminlspermissions')
@app.route('/adminlspermissions/')
@app.route('/adminlspermissions/<path:lsPathString>')
@userRoleRequired({('system', 'admin')})
def adminLsPermissionsView(lsPathString=''):
    """Route to view a box's permission as admin."""
    user = g.user
    boxPath = splitPathString(lsPathString)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    #
    db = dbGetDatabase()
    # colorMap=makeSettingColorValueMap(db)
    thisBox = getBoxFromPath(db, boxPath, user)
    if thisBox is not None:
        #
        thisBoxPermissionAlgebra = calculateBoxPermissionAlgebra(
            thisBox.permissionHistory,
            thisBox.permissions,
        )
        boxNiceName = describeBoxTitle(thisBox)
        pathBCrumbs = makeBreadCrumbs(
            boxPath,
            g,
            appendedItems=[{
                'kind': 'link',
                'target': None,
                'name': 'Permissions',
            }],
        )
        mentionedRoleKeys = {r.roleKey() for r in thisBox.permissions}
        roleKeyToRoleMap = {
            r.roleKey(): r
            for r in dbGetAllRoles(db, user)
            if r.can_box != 0
        }
        unmentionedRoleKeys = [
            rk_r[0]
            for rk_r in sorted(
                (
                    (rK, r)
                    for rK, r in roleKeyToRoleMap.items()
                    if rK not in mentionedRoleKeys
                ),
                key=lambda rk_r: rk_r[1].sortableTuple(),
            )
        ]
        #
        structuredPermissionInfo = reformatBoxPermissionAlgebraIntoLists(
            thisBoxPermissionAlgebra,
            roleKeyToRoleMap,
        )
        permissionInfo = {
            'powers': structuredPermissionInfo,
        }
        #
        boxNativePermissions = sorted(
            thisBox.listPermissions('native'),
            key=lambda brp: roleKeyToRoleMap[brp.roleKey()].sortableTuple(),
        )
        boxInheritedPermissions = sorted(
            thisBox.listPermissions('inherited'),
            key=lambda brp: roleKeyToRoleMap[brp.roleKey()].sortableTuple(),
        )
        #
        return render_template(
            'adminboxpermissions.html',
            user=user,
            thisBox=thisBox,
            boxNativePermissions=boxNativePermissions,
            boxInheritedPermissions=boxInheritedPermissions,
            permissionInfo=permissionInfo,
            unmentionedRoleKeys=unmentionedRoleKeys,
            roleKeyToRoleMap=roleKeyToRoleMap,
            boxNiceName=boxNiceName,
            boxPath=boxPath[1:],
            breadCrumbs=pathBCrumbs,
        )
    else:
        raise OstracionError('Could not find box for permission editing')


@app.route('/adminrmpermission/<roleClass>/<roleId>/')
@app.route('/adminrmpermission/<roleClass>/<roleId>')
@app.route('/adminrmpermission/<roleClass>/<roleId>/<path:lsPathString>')
@userRoleRequired({('system', 'admin')})
def adminRmPermissionView(roleClass, roleId, lsPathString=''):
    """Route to delete an explicit permission set from a box."""
    user = g.user
    boxPath = splitPathString(lsPathString)
    request._onErrorUrl = url_for(
        'adminLsPermissionsView',
        lsPathString=lsPathString,
    )
    #
    db = dbGetDatabase()
    thisBox = getBoxFromPath(db, boxPath, user)
    if thisBox is not None:
        dbDeleteBoxRolePermission(db, thisBox.box_id, roleClass, roleId, user)
        return redirect(url_for(
            'adminLsPermissionsView',
            lsPathString=lsPathString,
        ))
    else:
        raise OstracionError('Could not find box for permission removal')


@app.route('/adminmkpermission/<roleClass>/<roleId>/')
@app.route('/adminmkpermission/<roleClass>/<roleId>')
@app.route('/adminmkpermission/<roleClass>/<roleId>/<path:lsPathString>')
@userRoleRequired({('system', 'admin')})
def adminMkPermissionView(roleClass, roleId, lsPathString=''):
    """Route to create an explicit permission set from a box."""
    user = g.user
    boxPath = splitPathString(lsPathString)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    #
    db = dbGetDatabase()
    thisBox = getBoxFromPath(db, boxPath, user)
    if thisBox is not None:
        # there may or may not be a permission with the requested role_id
        requiredBRPermissions = [
            p
            for p in thisBox.permissions
            if p.roleKey() == (roleClass, roleId)
        ]
        if len(requiredBRPermissions) > 0:
            newPermission = BoxRolePermission(**(
                recursivelyMergeDictionaries(
                    {'box_id': thisBox.box_id},
                    defaultMap=requiredBRPermissions[0].asDict(),
                )
            ))
        else:
            newPermission = BoxRolePermission(
                role_class=roleClass,
                role_id=roleId,
                box_id=thisBox.box_id,
                r=0,
                w=0,
                c=0,
            )
        #
        dbInsertBoxRolePermission(db, newPermission, user)
        #
        return redirect(url_for(
            'adminLsPermissionsView',
            lsPathString=lsPathString
        ))
    else:
        g._onErrorUrl = url_for('lsView', lsPathString=lsPathString)
        raise OstracionError('Could not find box for permission making')


@app.route('/admintogglepermissionbit/<roleClass>/<roleId>/<bit>/')
@app.route('/admintogglepermissionbit/<roleClass>/<roleId>/<bit>')
@app.route('/admintogglepermissionbit/<roleClass>/'
           '<roleId>/<bit>/<path:lsPathString>')
@userRoleRequired({('system', 'admin')})
def adminTogglePermissionBitView(roleClass, roleId, bit, lsPathString=''):
    """Route to alter single powers of a permission set of a box."""
    user = g.user
    boxPath = splitPathString(lsPathString)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    #
    db = dbGetDatabase()
    thisBox = getBoxFromPath(db, boxPath, user)
    #
    if thisBox is not None:
        # we call a specific 'toggle' db util
        dbToggleBoxRolePermissionBit(db, thisBox, roleClass, roleId, bit, user)
    else:
        raise OstracionError('Could not find box for permission editing')
    return redirect(url_for(
        'adminLsPermissionsView',
        lsPathString=lsPathString,
    ))


@app.route('/admintickets/')
@userRoleRequired({('system', 'admin')})
def adminHomeTicketsView():
    """Route for per-ticket-type specific admin pages."""
    request._onErrorUrl = url_for('adminHomeView')
    user = g.user
    db = dbGetDatabase()
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root', 'tickets'],
        g,
    )
    return render_template(
        'tasks.html',
        user=user,
        bgcolor=g.settings['color']['task_colors']['admin_task']['value'],
        **pageFeatures,
    )


@app.route('/adminuserinvitations/')
@userRoleRequired({('system', 'admin')})
def adminUserInvitationsView():
    """Route to list user-invitation tickets."""
    request._onErrorUrl = url_for('adminHomeTicketsView')
    user = g.user
    db = dbGetDatabase()
    #
    ticketDicts = sorted(
        (
            enrichTicket(db, t, urlRoot=request.url_root)
            for t in dbGetAllUserInvitationTickets(db, user)
        ),
        key=richTicketSorter,
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root', 'tickets', 'user_invitations'],
        g,
    )
    return render_template(
        'viewtickets.html',
        user=user,
        tickets=ticketDicts,
        mode='u',
        asAdmin=True,
        targetName='User',
        newItemMenu={
            'title': 'Invite user ...',
            'endpointName': 'adminNewUserInvitationView',
        },
        **pageFeatures,
    )


@app.route(
    '/adminuserissuechangepasswordticket/<username>',
    methods=['GET', 'POST'],
)
@userRoleRequired({('system', 'admin')})
def adminUserIssueChangePasswordTicket(username):
    """Route to generate a change-password ticket."""
    request._onErrorUrl = url_for('adminHomeUsersView')
    user = g.user
    db = dbGetDatabase()
    # is username valid?
    if isUsername(db, username, user):
        form = generateChangePasswordTicketForm(g.settings)
        if form.validate_on_submit():
            ticketName = form.name.data
            ticketMessage = transformIfNotEmpty(
                form.ticketmessage.data
            ),
            validityHours = form.ticketmessage.data(
                form.validityhours.data,
                int,
            ),
            magicLink = dbMakeUserChangePasswordTicket(
                db,
                ticketName=ticketName,
                validityHours=validityHours,
                userName=username,
                ticketMessage=ticketMessage,
                user=user,
                urlRoot=request.url_root,
                settings=g.settings,
            )
            flashMessage(
                'Info',
                'Done',
                ('Change-password ticket generated. Give the recipient '
                 'the following magic link:'),
                pillText=magicLink,
            )
        else:
            #
            pageFeatures = prepareTaskPageFeatures(
                adminPageDescriptor,
                ['root', 'users'],
                g,
                appendedItems=[
                    {
                        'kind': 'link',
                        'link': False,
                        'target': url_for(
                            'adminUserIssueChangePasswordTicket',
                            username=username,
                        ),
                        'name': 'Password ticket',
                    }
                ],
                overrides={
                    'pageTitle': 'Change-password ticket',
                    'pageSubtitle': ('A ticket will be issued, with optional '
                                     'expiry time, that will be redeemed to '
                                     'change the password'),
                    'iconUrl': makeSettingImageUrl(
                        g,
                        'admin_images',
                        'change_password_ticket',
                    ),
                },
            )
            #
            ticketName = 'Password-%s-%s' % (
                username,
                datetime.datetime.now().strftime('%Y_%m_%d'),
            )
            form.name.data = applyDefault(
                form.name.data,
                ticketName,
            )
            maxValidityHours = g.settings['behaviour']['behaviour_tickets'][
                'max_ticket_validityhours']['value']
            form.validityhours.data = applyDefault(
                form.validityhours.data,
                str(maxValidityHours) if maxValidityHours is not None else '',
            )
            return render_template(
                'changepasswordticket.html',
                user=user,
                form=form,
                **pageFeatures,
            )
    else:
        raise OstracionError('User "%s" not found' % username)
    return redirect(url_for('adminUserChangePasswordTicketsView'))


@app.route('/adminchangepasswordtickets')
@userRoleRequired({('system', 'admin')})
def adminUserChangePasswordTicketsView():
    """Route to list password-change tickets."""
    request._onErrorUrl = url_for('adminHomeTicketsView')
    user = g.user
    db = dbGetDatabase()
    #
    ticketDicts = sorted(
        (
            enrichTicket(db, t, urlRoot=request.url_root)
            for t in dbGetAllUserChangePasswordTickets(db, user)
        ),
        key=richTicketSorter,
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root', 'tickets', 'change_password'],
        g,
    )
    return render_template(
        'viewtickets.html',
        user=user,
        tickets=ticketDicts,
        mode='p',
        asAdmin=True,
        targetName='User',
        newItemMenu=None,
        **pageFeatures,
    )


@app.route('/adminnewuserinvitation', methods=['GET', 'POST'])
@userRoleRequired({('system', 'admin')})
def adminNewUserInvitationView():
    """Route to generate a user-invitation ticket."""
    request._onErrorUrl = url_for('adminHomeTicketsView')
    user = g.user
    db = dbGetDatabase()
    #
    form = generateUserInvitationTicketForm(g.settings)
    #
    if form.validate_on_submit():
        validityHours = (None
                         if form.validityhours.data == ''
                         else int(form.validityhours.data))
        if form.username.data != '':
            if isProspectedUsername(
                    db,
                    form.username.data,
                    user,
                    urlRoot=request.url_root):
                request._onErrorUrl = url_for('adminNewUserInvitationView')
                raise OstracionWarning(
                    ('Username "%s" exists already either as user or '
                     'valid user invitation ticket') % form.username.data
                )
        #
        magicLink = dbMakeUserInvitationTicket(
            db,
            ticketName=form.name.data,
            validityHours=validityHours,
            userName=transformIfNotEmpty(
                form.username.data,
            ),
            userFullName=transformIfNotEmpty(
                form.fullname.data,
            ),
            userEmail=transformIfNotEmpty(
                form.email.data,
            ),
            ticketMessage=transformIfNotEmpty(
                form.ticketmessage.data,
            ),
            user=user,
            urlRoot=request.url_root,
            settings=g.settings,
        )
        flashMessage(
            'Success',
            'Done',
            ('User invitation ticket generated. Give the recipient the '
             'following magic link:'),
            pillText=magicLink,
        )
        return redirect(url_for('adminUserInvitationsView'))
    else:
        #
        pageFeatures = prepareTaskPageFeatures(
            adminPageDescriptor,
            ['root', 'tickets', 'user_invitations'],
            g,
            appendedItems=[
                {
                    'kind': 'link',
                    'link': False,
                    'target': url_for('adminNewUserInvitationView'),
                    'name': 'Invite user',
                }
            ],
            overrides={
                'pageTitle': 'New user invitation',
                'pageSubtitle': ('The invitation is a ticket, with optional '
                                 'expiry time, that will be redeemed to '
                                 'create the account'),
            },
        )
        #
        form.ticketmessage.data = applyDefault(
            form.ticketmessage.data,
            'Please create your account on "%s"' % g.settings['behaviour'][
                'behaviour_appearance']['application_long_name']['value'],
        )
        form.name.data = applyDefault(
            form.name.data,
            'User-Invitation',
        )
        maxValidityHours = g.settings['behaviour']['behaviour_tickets'][
            'max_ticket_validityhours']['value']
        form.validityhours.data = applyDefault(
            form.validityhours.data,
            str(maxValidityHours) if maxValidityHours is not None else '',
        )
        return render_template(
            'adminnewuserinvitation.html',
            user=user,
            form=form,
            **pageFeatures,
        )


@app.route('/adminuploadtickets/')
@userRoleRequired({('system', 'admin')})
def adminUploadTicketsView():
    """Route to list upload-in-box tickets."""
    request._onErrorUrl = url_for('adminHomeTicketsView')
    user = g.user
    db = dbGetDatabase()
    #
    ticketDicts = sorted(
        (
            enrichTicket(db, t, urlRoot=request.url_root)
            for t in dbGetAllUploadTickets(db, user)
        ),
        key=richTicketSorter,
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root', 'tickets', 'upload'],
        g,
    )
    return render_template(
        'viewtickets.html',
        user=user,
        tickets=ticketDicts,
        mode='c',
        asAdmin=True,
        targetName='Box',
        newItemMenu=None,
        **pageFeatures,
    )


@app.route('/admingallerytickets/')
@userRoleRequired({('system', 'admin')})
def adminGalleryTicketsView():
    """Route to list gallery tickets."""
    request._onErrorUrl = url_for('adminHomeTicketsView')
    user = g.user
    db = dbGetDatabase()
    #
    ticketDicts = sorted(
        (
            enrichTicket(db, t, urlRoot=request.url_root)
            for t in dbGetAllGalleryTickets(db, user)
        ),
        key=richTicketSorter,
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root', 'tickets', 'gallery'],
        g,
    )
    return render_template(
        'viewtickets.html',
        user=user,
        tickets=ticketDicts,
        mode='g',
        asAdmin=True,
        targetName='Gallery',
        newItemMenu=None,
        **pageFeatures,
    )


@app.route('/adminfiletickets/')
@userRoleRequired({('system', 'admin')})
def adminFileTicketsView():
    """Route to list file tickets."""
    request._onErrorUrl = url_for('adminHomeTicketsView')
    user = g.user
    db = dbGetDatabase()
    #
    ticketDicts = sorted(
        (
            enrichTicket(db, t, urlRoot=request.url_root)
            for t in dbGetAllFileTickets(db, user)
        ),
        key=richTicketSorter,
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        adminPageDescriptor,
        ['root', 'tickets', 'file'],
        g,
    )
    return render_template(
        'viewtickets.html',
        user=user,
        tickets=ticketDicts,
        mode='f',
        asAdmin=True,
        targetName='File',
        newItemMenu=None,
        **pageFeatures,
    )
