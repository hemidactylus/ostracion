""" tickets.py
    Views to handle:
        - ticket deletion
        - redemption of all classes of ticket
"""

from flask import (
    g,
    url_for,
    request,
    redirect,
    render_template,
    send_from_directory,
    abort,
)

import datetime

from werkzeug.utils import secure_filename

from ostracion_app.app_main import app

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.models.User import User

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToSplitPath,
    fileIdToPath,
)

from ostracion_app.utilities.tools.comparisonTools import (
    optionNumberLeq,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)
from ostracion_app.utilities.database.userTools import (
    dbGetUser,
    dbUpdateUser,
    dbCreateUser,
)
from ostracion_app.utilities.database.usernameChecks import (
    isUsername,
)

from ostracion_app.utilities.tools.formatting import (
    applyDefault,
)

from ostracion_app.utilities.database.fileSystem import (
    getBoxFromPath,
    getFilesFromBox,
    getFileFromParent,
)

from ostracion_app.utilities.fileIO.fileStorage import (
    saveAndAnalyseFilesInBox,
)

from ostracion_app.utilities.database.permissions import (
    userIsAdmin,
    userHasPermission,
)

from ostracion_app.utilities.database.tickets import (
    dbGetEnrichAndCheckTicket,
    dbPunchRichTicket,
    dbDeleteTicket,
    enrichTicket,
)

from ostracion_app.utilities.forms.forms import (
    generateNewUserForm,
    generateTicketChangePasswordForm,
    #
    UploadMultipleFilesForm,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.fileIO.fileTypes import (
    fileViewingClass,
)

from ostracion_app.utilities.fileIO.fileTypes import (
    produceFileViewContents,
)

# to which page should user be redirected after
# they delete a ticket of a certain type while acting as admin/nonadmin?
deleteTicketRedirectMap = {
    ('u', '1'): 'adminUserInvitationsView',
    ('p', '1'): 'adminUserChangePasswordTicketsView',
    ('f', '0'): 'userFileTicketsView',
    ('f', '1'): 'adminFileTicketsView',
    ('c', '0'): 'userUploadTicketsView',
    ('c', '1'): 'adminUploadTicketsView',
    ('g', '0'): 'userGalleryTicketsView',
    ('g', '1'): 'adminGalleryTicketsView',
}


@app.route('/deleteticket/<mode>/<asAdmin>/<ticketId>')
def deleteTicketView(mode, asAdmin, ticketId):
    """ Delete-a-ticket route. Ticket of any kind,
        deleted as either admin or issuer.
    """
    user = g.user
    db = dbGetDatabase()
    dbDeleteTicket(db, ticketId, user, mode)
    return redirect(url_for(
        deleteTicketRedirectMap.get((mode, asAdmin), 'lsView')
    ))


@app.route(
    '/redeemticket/<mode>/<ticketId>/<securityCode>',
    methods=['GET', 'POST'],
)
def redeemTicketView(mode, ticketId, securityCode):
    """
        Redeem-a-ticket view. This is the route associated to the URL
        given in the 'ticket' as a magic link and internally performs
        one of several operations, depending on the ticket type.

        Depending on the type of ticket, different checks are in place.
        The actual handling of the ticket action (including upon POSTs) is in
        the hands of the subsequently-called function (not: endpoint), but:

            ** all checks except existing/redeemable are up
            to the individual functions. **
    """
    user = g.user
    db = dbGetDatabase()
    #
    richTicket = dbGetEnrichAndCheckTicket(
        db,
        mode,
        ticketId,
        securityCode,
        request.url_root,
    )
    if richTicket is None:
        raise OstracionError('Invalid ticket magic link')
    else:
        issuer = (dbGetUser(db, richTicket['ticket'].username)
                  if richTicket is not None
                  else None)
        if richTicket is not None and richTicket['redeemable']:
            if mode == 'u':
                # new user creation with ticket registering
                # upon actual creation
                return createUserUponTicket(
                    db=db,
                    user=user,
                    issuer=issuer,
                    richTicket=richTicket,
                    urlRoot=request.url_root,
                )
            elif mode == 'p':
                # change password: change password form with ticket
                # registering upon successful change
                return changePasswordUponTicket(
                    db=db,
                    user=user,
                    issuer=issuer,
                    richTicket=richTicket,
                    urlRoot=request.url_root,
                )
            elif mode == 'f':
                return retrieveFileUponTicket(
                    db=db,
                    user=user,
                    issuer=issuer,
                    richTicket=richTicket,
                    urlRoot=request.url_root,
                )
            elif mode == 'c':
                return uploadFilesUponTicket(
                    db=db,
                    user=user,
                    issuer=issuer,
                    richTicket=richTicket,
                    urlRoot=request.url_root,
                )
            elif mode == 'g':
                return galleryViewUponTicket(
                    db=db,
                    user=user,
                    issuer=issuer,
                    richTicket=richTicket,
                    urlRoot=request.url_root,
                )
            else:
                raise OstracionError('Invalid ticket magic link')
        else:
            raise OstracionError('Invalid ticket magic link')


def galleryViewUponTicket(db, user, issuer, richTicket, urlRoot):
    """ This is a tiny redirect to a separate view
        with a parameter "page" that is silently brought within [ 0 : (n-1) ]
        and handles the gallery display with hiding of the bcrumbs
        and everything.
        At each access we repeat the checking of the validity
        (and punch the ticket).

        Note: not a route.
    """
    return redirect(url_for(
        'ticketGalleryView',
        ticketId=richTicket['ticket'].ticket_id,
        securityCode=richTicket['ticket'].security_code,
        page=0,
    ))


@app.route('/ticketgallery/<ticketId>/<securityCode>/<int:page>')
def ticketGalleryView(ticketId, securityCode, page=0):
    """Actual route to view a gallery with a ticket."""
    user = g.user
    db = dbGetDatabase()
    #
    richTicket = dbGetEnrichAndCheckTicket(
        db,
        'g',
        ticketId,
        securityCode,
        request.url_root,
    )
    if richTicket is None:
        raise OstracionError('Invalid ticket magic link')
    else:
        issuer = dbGetUser(db, richTicket['ticket'].username)
        if richTicket['redeemable']:
            # valid ticket. Further checks are on the way.
            noBandUsrTickets = g.settings['behaviour'][
                'behaviour_tickets']['protect_banned_user_tickets']['value']
            if (not noBandUsrTickets or issuer.banned == 0):
                #
                boxPath = richTicket['metadata']['box_path']
                request._onErrorUrl = url_for(
                    'lsView',
                    lsPathString='/'.join(boxPath[1:]),
                )
                parentBox = getBoxFromPath(db, boxPath[1:], issuer)
                if parentBox is not None:
                    if parentBox.box_id == richTicket['metadata']['box_id']:
                        galleryMessage = richTicket['metadata'].get('message')
                        fileStorageDirectory = g.settings['system'][
                            'system_directories']['fs_directory']['value']
                        files = sorted(
                            getFilesFromBox(db, parentBox),
                            key=lambda f: (f.name.lower(), f.name),
                        )
                        numGalleryFiles = len(files)
                        if numGalleryFiles > 0:
                            thisFileIndex = page % numGalleryFiles
                            file = files[thisFileIndex]
                            # gallery navigation calculations
                            nextFileIndex = (
                                thisFileIndex + 1
                            ) % numGalleryFiles
                            prevFileIndex = (
                                thisFileIndex - 1 + numGalleryFiles
                            ) % numGalleryFiles
                            #
                            fileContents = produceFileViewContents(
                                db,
                                file,
                                mode='galleryview',
                                viewParameters={
                                    'boxPath': boxPath,
                                    'fileName': file.name,
                                    'ticketId': ticketId,
                                    'securityCode': securityCode,
                                },
                                fileStorageDirectory=fileStorageDirectory,
                                urlRoot=request.url_root,
                                protectBannedUserTickets=noBandUsrTickets,
                            )
                            fileActions = {
                                'gallery_prev': url_for(
                                    'ticketGalleryView',
                                    ticketId=ticketId,
                                    securityCode=securityCode,
                                    page=prevFileIndex,
                                ),
                                'gallery_next': url_for(
                                    'ticketGalleryView',
                                    ticketId=ticketId,
                                    securityCode=securityCode,
                                    page=nextFileIndex,
                                ),
                                'homepage': url_for(
                                    'lsView',
                                )
                            }
                            return render_template(
                                'fileview.html',
                                fileActions=fileActions,
                                fileInfo=None,
                                filecontents=fileContents,
                                breadCrumbs=None,
                                user=user,
                                pageTitle='Gallery view, file "%s" (%i/%i)' % (
                                    file.name,
                                    thisFileIndex + 1,
                                    numGalleryFiles,
                                ),
                                pageSubtitle=(None
                                              if galleryMessage is None
                                              else (
                                                'Message on ticket: "%s"' % (
                                                    galleryMessage,
                                                )
                                              )),
                                downloadUrl=None,
                                hideBreadCrumbs=True,
                                hideNavbar=True,
                            )
                            #
                            return fsView(fsPathString)
                        else:
                            flashMessage(
                                'Info',
                                'Empty box',
                                'Cannot view as gallery a box without files',
                            )
                            return redirect(url_for('lsView'))
                    else:
                        raise OstracionError('Ticket cannot be redeemed')
                else:
                    raise OstracionError('Invalid ticket magic link')
            else:
                raise OstracionError('Ticket cannot be redeemed')
        else:
            raise OstracionError('Invalid ticket magic link')


@app.route('/ticketgalleryfsv/<ticketId>/<securityCode>/<fileName>')
def ticketGalleryFsView(ticketId, securityCode, fileName):
    """
        View-file-within-a-ticket-generated-gallery-view route.

        Helper endpoint to return viewable (only viewables,
        there's no 'download') files in a ticket-gallery view.
        Must take care of punching the ticket.
    """
    user = g.user
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    #
    richTicket = dbGetEnrichAndCheckTicket(
        db,
        'g',
        ticketId,
        securityCode,
        request.url_root,
    )
    if richTicket is not None:
        issuer = dbGetUser(db, richTicket['ticket'].username)
        if richTicket['redeemable']:
            # valid ticket. Further checks are on the way.
            if (not g.settings['behaviour']['behaviour_tickets'][
                    'protect_banned_user_tickets']['value'] or
                    issuer.banned == 0):
                #
                boxPath = richTicket['metadata']['box_path']
                request._onErrorUrl = url_for(
                    'lsView',
                    lsPathString='/'.join(boxPath[1:]),
                )
                parentBox = getBoxFromPath(db, boxPath[1:], issuer)
                if parentBox is not None:
                    # we retrieve the file and serve it
                    file = getFileFromParent(db, parentBox, fileName, issuer)
                    if file is not None:
                        dbPunchRichTicket(db, richTicket)
                        filePhysicalPath, filePhysicalName = fileIdToSplitPath(
                            file.file_id,
                            fileStorageDirectory=fileStorageDirectory,
                        )
                        return send_from_directory(
                            filePhysicalPath,
                            filePhysicalName,
                            attachment_filename=file.name,
                            as_attachment=True,
                            mimetype=file.mime_type,
                        )
                    else:
                        return abort(404, 'Content unavailable')
                else:
                    return abort(404, 'Content unavailable')
            else:
                return abort(404, 'Content unavailable')
        else:
            return abort(404, 'Content unavailable')
    else:
        return abort(404, 'Content unavailable')


def retrieveFileUponTicket(db, user, issuer, richTicket, urlRoot):
    """ Retrieve a file using a file ticket.

        Retrieval fails if either:
            1. user banned;
            2. object not available to the issuer.
    """
    noBandUsrTickets = g.settings['behaviour'][
        'behaviour_tickets']['protect_banned_user_tickets']['value']
    if (not noBandUsrTickets or issuer.banned == 0):
        boxPath, fileName = (
            richTicket['metadata']['path'][:-1],
            richTicket['metadata']['path'][-1],
        )
        fileStorageDirectory = g.settings['system']['system_directories'][
            'fs_directory']['value']
        parentBox = getBoxFromPath(db, boxPath, issuer)
        #
        if parentBox is not None:
            file = getFileFromParent(db, parentBox, fileName, issuer)
            if file is not None:
                if richTicket['metadata'].get('file_mode') == 'view':
                    # either we offer a view-type page
                    # (with ticketMessage and optionally view)
                    # and decide whether to punch the ticket and how ...
                    fileRetrievalUrl = url_for(
                        'ticketFsDownloadView',
                        ticketId=richTicket['ticket'].ticket_id,
                        securityCode=richTicket['ticket'].security_code,
                    )
                    # for mode='ticketview'this will internally call
                    # the punching endpoint 'ticketFsDownloadView' below.
                    fileContents = produceFileViewContents(
                        db,
                        file,
                        mode='ticketview',
                        viewParameters={
                            'ticketId': richTicket['ticket'].ticket_id,
                            'securityCode': richTicket['ticket'].security_code,
                        },
                        fileStorageDirectory=fileStorageDirectory,
                        urlRoot=urlRoot,
                        protectBannedUserTickets=noBandUsrTickets,
                    )
                    return render_template(
                        'fileview.html',
                        fileActions=None,
                        fileInfo=None,
                        filecontents=fileContents,
                        breadCrumbs=[],
                        user=user,
                        pageTitle='File access',
                        pageSubtitle='View/download the file%s' % (
                            ''
                            if richTicket['metadata'].get('message') is None
                            else (
                                '. Message on ticket: "%s"' % (
                                    richTicket['metadata']['message']
                                )
                            )
                        ),
                        downloadUrl=fileRetrievalUrl,
                    )
                elif richTicket['metadata'].get('file_mode') == 'direct':
                    # ... or we offer a direct download and punch the ticket...
                    return ticketFsDownloadView(
                        richTicket['ticket'].ticket_id,
                        richTicket['ticket'].security_code,
                    )
                else:
                    raise NotImplementedError(
                        'Unknown file_mode "%s" in file ticket' % (
                            richTicket['metadata'].get('file_mode'),
                        )
                    )
            else:
                raise OstracionError('Ticket target unavailable')
        else:
            raise OstracionError('Ticket target unavailable')
    else:
        raise OstracionError('Ticket cannot be redeemed')


@app.route('/ticketfsd/<ticketId>/<securityCode>')
def ticketFsDownloadView(ticketId, securityCode):
    """ Give-the-file-contents-based-on-ticket route.

        Helper endpoint to load-and-return a file upon a ticket;
        access to files based on a ticket.

        Used by both the direct-file-download or the view-file
        file-ticket modes.

        Note: punching occurs here.
    """
    user = g.user
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    #
    richTicket = dbGetEnrichAndCheckTicket(
        db,
        'f',
        ticketId,
        securityCode,
        request.url_root,
    )
    issuer = (dbGetUser(db, richTicket['ticket'].username)
              if richTicket is not None
              else None)
    noBandUsrTickets = g.settings['behaviour']['behaviour_tickets'][
        'protect_banned_user_tickets']['value']
    if (issuer is not None and
            (not noBandUsrTickets or issuer.banned == 0)):
        boxPath, fileName = (
            richTicket['metadata']['path'][:-1],
            richTicket['metadata']['path'][-1],
        )
        parentBox = getBoxFromPath(db, boxPath, issuer)
        #
        if parentBox is not None:
            file = getFileFromParent(db, parentBox, fileName, issuer)
            if file is not None:
                # return it and contextually punch the ticket
                dbPunchRichTicket(db, richTicket)
                # then we return the file as a download
                # (this flow assumes download is desired as opposed to view)
                filePhysicalPath, filePhysicalName = fileIdToSplitPath(
                    file.file_id,
                    fileStorageDirectory=fileStorageDirectory,
                )
                return send_from_directory(
                    filePhysicalPath,
                    filePhysicalName,
                    attachment_filename=file.name,
                    as_attachment=True,
                    mimetype=file.mime_type,
                )
            else:
                return abort(404, 'Content unavailable')
        else:
            return abort(404, 'Content unavailable')
    else:
        return abort(404, 'Content unavailable')


def uploadFilesUponTicket(db, user, issuer, richTicket, urlRoot):
    """ Upload-file(s)-upon-ticket route.

        Upload fails if
            1. user banned;
            2. issuer has no upload permission
               (incl. access) on the target box.
    """
    noBandUsrTickets = g.settings['behaviour']['behaviour_tickets'][
        'protect_banned_user_tickets']['value']
    if not noBandUsrTickets or issuer.banned == 0:
        boxPath = richTicket['metadata']['box_path']
        request._onErrorUrl = url_for(
            'lsView',
            lsPathString='/'.join(boxPath[1:]),
        )
        box = getBoxFromPath(db, boxPath[1:], issuer)
        fileStorageDirectory = g.settings['system']['system_directories'][
            'fs_directory']['value']
        if userHasPermission(db, issuer, box.permissions, 'w'):
            # ticket is completely valid: here the form
            # handling (get/post) occurs
            uploadsLeft = (None
                           if richTicket['ticket'].multiplicity is None
                           else (
                                richTicket['ticket'].multiplicity
                                - richTicket['ticket'].times_redeemed
                           ))
            form = UploadMultipleFilesForm()
            if form.validate_on_submit():
                uploadedFiles = [
                    uf
                    for uf in request.files.getlist('files')
                    if uf.filename != ''
                ]
                filesdescription = form.filesdescription.data
                # are there too many files?
                if uploadsLeft is None or len(uploadedFiles) <= uploadsLeft:
                    filesToUpload = [
                        {
                            'box_id': box.box_id,
                            'name': secure_filename(uploadedFile.filename),
                            'description': form.filesdescription.data,
                            'date': datetime.datetime.now(),
                            'fileObject': uploadedFile,
                        }
                        for uploadedFile in uploadedFiles
                    ]
                    # we punch the ticket as many times as
                    # there were files provided
                    dbPunchRichTicket(
                        db,
                        richTicket,
                        numPunches=len(filesToUpload),
                    )
                    makeThumbnails = g.settings['behaviour'][
                        'behaviour_appearance']['extract_thumbnails']['value']
                    savingResult = saveAndAnalyseFilesInBox(
                        db=db,
                        files=filesToUpload,
                        parentBox=box,
                        user=issuer,
                        fileStorageDirectory=fileStorageDirectory,
                        thumbnailFormat=('thumbnail'
                                         if makeThumbnails
                                         else None),
                    )
                    flashMessage('Success', 'Info', savingResult)
                    return redirect(url_for(
                        'lsView',
                        lsPathString='',
                    ))
                else:
                    request._onErrorUrl = url_for(
                        'redeemTicketView',
                        mode='c',
                        ticketId=richTicket['ticket'].ticket_id,
                        securityCode=richTicket['ticket'].security_code,
                    )
                    raise OstracionError(
                        ('Cannot upload this many files '
                         '(maximum %i allowed)') % uploadsLeft
                    )
            else:
                return render_template(
                    'uploadmultiplefiles.html',
                    form=form,
                    user=user,
                    breadCrumbs=[],
                    pageTitle='Upload file(s)',
                    pageSubtitle='Upload%s files%s' % (
                        (''
                         if uploadsLeft is None
                         else ' up to %i' % uploadsLeft),
                        (''
                         if richTicket['metadata'].get('message') is None
                         else (
                            '. Message on ticket: "%s"' % (
                                richTicket['metadata']['message']
                            )
                         )),
                    ),
                    iconUrl=makeSettingImageUrl(
                        g,
                        'app_images',
                        ('single_upload'
                         if optionNumberLeq(1, uploadsLeft)
                         else 'multiple_upload'),
                    ),
                )
        else:
            # issuer has no write permission in box
            raise OstracionError('Ticket not acessible or expired')
    else:
        raise OstracionError('Ticket not acessible or expired')


def changePasswordUponTicket(db, user, issuer, richTicket, urlRoot):
    """Change-password-ticket route."""
    ticketsByformerAdminsAreProtected = g.settings['behaviour'][
        'behaviour_tickets'][
        'protect_nonadmin_user_password_tickets']['value']
    applicationLongName = g.settings['behaviour']['behaviour_appearance'][
        'application_long_name']['value']
    if not ticketsByformerAdminsAreProtected or userIsAdmin(db, issuer):
        form = generateTicketChangePasswordForm(g.settings)
        if form.validate_on_submit():
            changeeUser = dbGetUser(db, richTicket['metadata']['username'])
            if form.username.data == changeeUser.username:
                #
                newPassword = form.newpassword.data
                minPasswordLength = g.settings['behaviour'][
                    'behaviour_security']['password_min_length']['value']
                if len(form.newpassword.data) < minPasswordLength:
                    print('richTicket ', richTicket)
                    flashMessage(
                        'Info',
                        'Please retry',
                        'New password too short (min. %i characters)' % (
                            minPasswordLength,
                        ),
                    )
                    return redirect(url_for(
                        'redeemTicketView',
                        mode='p',
                        ticketId=richTicket['ticket'].ticket_id,
                        securityCode=richTicket['ticket'].security_code,
                    ))
                else:
                    newUser = User(**({
                        (k
                         if k != 'passwordhash'
                         else 'password'): (v
                                            if k != 'passwordhash'
                                            else form.newpassword.data)
                        for k, v in changeeUser.asDict().items()
                    }))
                    try:
                        dbPunchRichTicket(db, richTicket, skipCommit=True)
                        dbUpdateUser(db, newUser, user, skipCommit=True)
                        db.commit()
                        # flash a message
                        flashMessage(
                            'Success',
                            'Success',
                            'Password changed. You can now log in to %s' % (
                                applicationLongName,
                            ),
                        )
                        # go to login
                        return redirect(url_for('loginView'))
                    except Exception as e:
                        db.rollback()
                        raise e
            else:
                raise OstracionError('Wrong username provided')
        else:
            pageSubtitle = ('Complete the process by entering your '
                            'new password twice%s') % (
                                ''
                                if richTicket[
                                    'metadata'].get('message') is None
                                else '. Message on ticket: "%s"' % (
                                    richTicket['metadata'].get('message'),
                                )
                            )
            return render_template(
                'userchangepassword.html',
                user=user,
                form=form,
                showOldPasswordField=False,
                mode='ticket',
                breadCrumbs=None,
                pageTitle='Change password',
                pageSubtitle=pageSubtitle,
                iconUrl=makeSettingImageUrl(
                    g,
                    'admin_images',
                    'change_password_ticket'
                ),
                backToUrl=url_for('lsView'),
            )
    else:
        raise OstracionError('Ticket not acessible or expired')


def createUserUponTicket(db, user, issuer, richTicket, urlRoot):
    """User-creation-ticket route."""
    ticketsByformerAdminsAreProtected = g.settings['behaviour'][
        'behaviour_tickets'][
        'protect_nonadmin_user_password_tickets']['value']
    appLongName = g.settings['behaviour']['behaviour_appearance'][
        'application_long_name']['value']
    if not ticketsByformerAdminsAreProtected or userIsAdmin(db, issuer):
        form = generateNewUserForm(g.settings)
        if form.validate_on_submit():
            userDict = {
                'username': form.username.data,
                'fullname': form.fullname.data,
                'email': form.email.data,
                'password': form.password.data,
            }
            if ('username' in richTicket['metadata'] and
                    richTicket['metadata'][
                        'username'] != userDict['username']):
                raise RuntimeError(
                    'Detected attempt to escape username set by ticket issuer'
                )
            else:
                # the usename must not exist (relevant if left free in ticket)
                if isUsername(db, userDict['username'], user):
                    if 'username' in richTicket['metadata']:
                        request._onErrorUrl = url_for('lsView')
                    else:
                        request._onErrorUrl = url_for(
                            'redeemTicketView',
                            mode='u',
                            ticketId=ticketId,
                            securityCode=securityCode,
                        )
                    raise OstracionError(
                        'Username "%s" exists already' % userDict['username']
                    )
                else:
                    # we proceed with the user creation proper
                    newUser = User(
                        icon_file_id='',
                        icon_file_id_username=userDict['username'],
                        banned=0,
                        **userDict,
                    )
                    try:
                        dbPunchRichTicket(db, richTicket, skipCommit=True)
                        dbCreateUser(db, newUser, user)
                        #
                        flashMessage(
                            'Info',
                            'Success',
                            'User created. You can now log in to %s' % (
                                appLongName
                            ),
                        )
                        return redirect(url_for('loginView'))
                    except Exception as e:
                        db.rollback()
                        raise e
        else:
            form.username.data = applyDefault(
                form.username.data,
                richTicket['metadata'].get('username', ''),
            )
            form.fullname.data = applyDefault(
                form.fullname.data,
                richTicket['metadata'].get('fullname', ''),
            )
            form.email.data = applyDefault(
                form.email.data,
                richTicket['metadata'].get('email', ''),
            )
            return render_template(
                'newuser.html',
                form=form,
                user=user,
                pageTitle='Create user',
                pageSubtitle='Create your user account on %s%s' % (
                    appLongName,
                    (
                        ''
                        if richTicket['metadata'].get('message') is None
                        else '. Message on ticket: "%s"' % (
                            richTicket['metadata']['message']
                        )
                    ),
                ),
                iconUrl=makeSettingImageUrl(g, 'user_images', 'user_icon'),
                lockUsernameField='username' in richTicket['metadata'],
            )
    else:
        raise OstracionError('Ticket not acessible or expired')
        return redirect(url_for('lsView'))
