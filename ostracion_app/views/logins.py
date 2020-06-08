""" logins.py
    - Handling of login/logout (views and flask_login);
    - Triggers, checks, redirects and preloadings
      common to all requests;
    - also handling of special cases (user banned; app not-yet-ready, etc).
"""

import datetime
import urllib.parse

from flask import (
    g,
    redirect,
    url_for,
    render_template,
    request,
)

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    current_user,
    login_required,
)

from ostracion_app.app_main import app

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.forms.forms import (
    LoginForm,
    QuickFindForm,
)

from ostracion_app.utilities.models.User import User

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)
from ostracion_app.utilities.database.userTools import (
    dbGetUser,
    dbUpdateUser,
)

from ostracion_app.utilities.tools.formatting import (
    applyDefault,
)

from ostracion_app.utilities.tools.extraction import safeInt

from ostracion_app.utilities.database.permissions import (
    dbGetUserRoles,
    isUserWithinPermissionCircle,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
    dbLoadAllSettings,
)

from ostracion_app.utilities.database.loginProtection import (
    secondsToWaitBeforeLogin,
)

from ostracion_app.utilities.database.permissions import (
    userIsAdmin,
)

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.views.viewTools.loginTools import (
    loginTitle,
    loginSubtitle,
)

from ostracion_app.utilities.userTools.OstracionAnonymousUser import (
    OstracionAnonymousUser,
)

# initialisation of login manager is here
lm = LoginManager()
lm.anonymous_user = OstracionAnonymousUser
lm.init_app(app)

# endpoints for which we lift the rerouting due to just-installed,
# still-to-finalize-install Ostracion:
endpointsWithoutAppInitRerouting = {
    'loginView',
    'settingThumbnailView',
    'adminHomeSettingsGenericView',
    'userThumbnailView',
    'logoutView',
    'faviconView',
}

# endpoints for which we do not block anonymous access even if
# the app is configured to logged-in-users-only
endpointsWithoutInviteOnlyBlocking = {
    'loginView',
    'settingThumbnailView',
    'faviconView',
    'robotsTxtView',
    'termsView',
    'termsAcceptView',
    'infoHomeView',
    'userGuideView',
    'adminGuideView',
    'privacyPolicyView',
    'aboutView',
    'DPOEmailImageView',
    'contactInfoImageView',
}

# endpoints for which we do not redirect users (if so configured)
# to accept the terms of service
endpointsWithoutTermAcceptanceBlocking = {
    'loginView',
    'settingThumbnailView',
    'faviconView',
    'logoutView',
    'robotsTxtView',
    'termsView',
    'termsAcceptView',
    'infoHomeView',
    'userGuideView',
    'adminGuideView',
    'privacyPolicyView',
    'aboutView',
    'DPOEmailImageView',
    'contactInfoImageView',
}


@app.before_request
def before_request():
    """ Preparation of globally-accessible info for all views,
        handling of special post-install situations and of banned users
        and logged-in-only setups.
    """
    db = dbGetDatabase()
    g.user = current_user
    g.settings = dbLoadAllSettings(db, g.user)
    g.applicationLogoUrl = makeSettingImageUrl(
        g,
        'ostracion_images',
        'navbar_logo',
    )
    #
    g.canPerformSearch = isUserWithinPermissionCircle(
        db,
        g.user,
        g.settings['behaviour']['search']['search_access']['value'],
    )
    g.quickFindForm = QuickFindForm()
    g.canShowTreeView = isUserWithinPermissionCircle(
        db,
        g.user,
        g.settings['behaviour']['search']['tree_view_access']['value'],
    )
    #
    if g.user.is_authenticated:
        g.user.setRoles(list(dbGetUserRoles(db, g.user)))
        if g.user.banned:
            flashMessage(
                'Warning',
                'Warning',
                ('Your user is momentarily banned. '
                    'Please continue as anonymous'),
            )
            logout_user()
    # handling of first-time post-install forced steps
    dirsSetUp = g.settings['managed']['post_install_finalisations'][
        'directories_set_up']['value']
    if (not dirsSetUp
            and request.endpoint not in endpointsWithoutAppInitRerouting):
        if g.user.is_authenticated and userIsAdmin(db, g.user):
            flashMessage(
                'Warning',
                'Action required',
                ('Please review carefully the following directory settings '
                    'to make the application function. Changing them later, '
                    'when material is uploaded, is a disruptive operation.'),
            )
            return redirect(url_for(
                'adminHomeSettingsGenericView',
                settingType='system_settings'
            ))
        else:
            if g.user.is_authenticated:
                logout_user()
            flashMessage(
                'Warning',
                'Action required',
                ('To finalise installation/make the application function '
                    'properly, an administrator should log in and '
                    'complete the setup'),
            )
            return redirect(url_for('loginView'))
    else:
        # we care about reviewing the settings only if the dirs are OK
        if g.user.is_authenticated and userIsAdmin(db, g.user):
            if request.endpoint not in endpointsWithoutAppInitRerouting:
                settingsReviewed = g.settings['managed'][
                    'post_install_finalisations']['settings_reviewed']['value']
                if not settingsReviewed:
                    flashMessage(
                        'Warning',
                        'Action required',
                        ('Please carefully review the following application '
                            'behaviour settings before opening the service '
                            'to users (anyway, these settings can be '
                            'changed at any time).'),
                    )
                    return redirect(url_for(
                        'adminHomeSettingsGenericView',
                        settingType='behaviour'
                    ))
    # we take care of terms-and-conditions acceptance here
    if request.endpoint not in endpointsWithoutTermAcceptanceBlocking:
        usersMustAbideByTOS = g.settings['terms']['terms'][
            'terms_must_agree']['value']
        anonymousMustAbideByTOS = g.settings['terms']['terms'][
            'terms_must_agree_anonymous']['value']
        currentTermVersion = g.settings['terms']['terms'][
            'terms_version']['value']
        #
        if g.user.is_authenticated:
            mustAbideByTOS = usersMustAbideByTOS
            typeOfUsers = 'Users'
            storedTermsVersion = g.user.terms_accepted_version
            storedTermsAcceptance = safeInt(
                g.user.terms_accepted,
                default=None,
            )
        else:
            mustAbideByTOS = anonymousMustAbideByTOS
            typeOfUsers = 'Visitors'
            storedTermsVersion = request.cookies.get('termsAcceptedVersion')
            storedTermsAcceptance = safeInt(
                request.cookies.get('termsAccepted'),
                default=None,
            )
        #
        if storedTermsVersion == currentTermVersion:
            thisVersionAcceptance = storedTermsAcceptance
        else:
            thisVersionAcceptance = None
        #
        if thisVersionAcceptance is None:
            canContinueTermwise = not mustAbideByTOS
        elif thisVersionAcceptance == 0:
            # explicit not-acceptance
            canContinueTermwise = False
        else:
            # positive updated acceptance
            canContinueTermwise = True
        #
        if not canContinueTermwise:
            quotedTravelToPath = urllib.parse.quote_plus(request.full_path)
            flashMessage(
                'Info',
                'Action required',
                ('%s must review the Terms and Conditions'
                    ' before accessing the site.') % typeOfUsers,
            )
            return redirect(url_for(
                'termsView',
                showAgreementButtons='y',
                travelTo=quotedTravelToPath,
            ))

    # here the ordinary flow is resumed
    if g.settings['behaviour']['behaviour_permissions'][
            'logged_in_users_only']['value']:
        if (not g.user.is_authenticated and
                request.endpoint not in endpointsWithoutInviteOnlyBlocking):
            return redirect(url_for('loginView'))


@lm.user_loader
def load_user(uid):
    """Given an ID, fetch the DB and return the corresponding user, if any."""
    db = dbGetDatabase()
    return dbGetUser(db, uid)


@app.route('/logout')
@login_required
def logoutView():
    """Logout view."""
    if g.user is not None and g.user.is_authenticated:
        flashMessage(
            'Success',
            'Logged out',
            'farewell, %s.' % g.user.fullname,
        )
        logout_user()
    return redirect(url_for('indexView'))


@app.route('/login', methods=['GET', 'POST'])
def loginView():
    """Login view."""
    user = g.user
    db = dbGetDatabase()
    g._onErrorUrl = url_for('loginView')
    if user is not None and user.is_authenticated:
        return redirect(url_for('indexView'))
    form = LoginForm()
    loginProtectionSeconds = int(
        g.settings['behaviour']['behaviour_security'][
            'login_protection_seconds']['value']
    )
    if form.validate_on_submit():
        #
        loginWaitSeconds = secondsToWaitBeforeLogin(
            db,
            request.remote_addr,
            doWrite=True,
            loginProtectionSeconds=loginProtectionSeconds,
            hashSalt=g.settings['behaviour']['behaviour_security'][
                'ip_addr_hashing_salt']['value'],
        )
        if loginWaitSeconds <= 0:
            #
            qUser = dbGetUser(db, form.username.data)
            if qUser and qUser.checkPassword(form.password.data):
                #
                newUser = User(**qUser.asDict())
                newUser.last_login = datetime.datetime.now()
                dbUpdateUser(db, newUser, qUser)
                #
                login_user(qUser)
                #
                flashMessage(
                    'Success',
                    'Login successful',
                    'welcome, %s!' % (
                        qUser.fullname,
                    ),
                )
                #
                return redirect(url_for('indexView'))
            else:
                g._onErrorUrl = url_for(
                    'loginView',
                    username=form.username.data,
                )
                raise OstracionError('invalid username or password')
        else:
            raise OstracionWarning(
                ('Automated repeated login protection. '
                    'Please wait %i seconds ...') % int(loginWaitSeconds)
            )
    else:
        requestParams = request.args
        form.username.data = applyDefault(
            form.username.data,
            requestParams.get('username', ''),
        )
        appShortName = g.settings['behaviour']['behaviour_appearance'][
            'application_short_name']['value']
        iconUrl = makeSettingImageUrl(g, 'user_images', 'login')
        return render_template(
            'login.html',
            form=form,
            user=user,
            pageTitle=loginTitle(g),
            pageSubtitle=loginSubtitle(g),
            iconUrl=iconUrl,
        )
