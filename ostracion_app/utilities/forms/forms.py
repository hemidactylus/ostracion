""" forms.py
    All forms by the Ostracion web app are defined here.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    BooleanField,
    SubmitField,
    RadioField,
    HiddenField,
    SelectField,
    PasswordField,
    TextAreaField,
    FormField,
    FieldList,
    Form,
)
from wtforms.validators import (
    InputRequired,
    DataRequired,
    Required,
    EqualTo,
    Length,
)

from flask_wtf.file import (
    FileField,
    FileRequired,
)

from config import (
    maxIdentifierLength,
    maxStoredTextLength,
    lowercaseAlphabet,
)

from ostracion_app.utilities.forms.validators.validators import (
    CharacterSelector,
    MinimumLength,
    ColorString,
    ConstrainedOptionalInt,
    PositiveInteger,
    OptionalInteger,
    NonnegativeInteger,
)


class LoginForm(FlaskForm):
    """Login form (class)."""
    username = StringField('UserName', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    login = SubmitField('Log In')


def makeMakeBoxForm(confirmTitle):
    """ Generate a make-box form (class) with a
        given caption on submit button.
    """
    class MakeBoxForm(FlaskForm):
        boxname = StringField(
            'BoxName',
            validators=[
                InputRequired(),
                CharacterSelector(),
                Length(max=maxIdentifierLength)
            ]
        )
        boxtitle = StringField(
            'BoxTitle',
            validators=[
                InputRequired(),
                Length(max=maxIdentifierLength)
            ]
        )
        boxdescription = StringField(
            'BoxDescription',
            validators=[
                Length(max=maxIdentifierLength)
            ]
        )
        confirm = SubmitField(confirmTitle)
    return MakeBoxForm


class FileDataForm(FlaskForm):
    """File metadata form class)."""
    filename = StringField(
        'FileName',
        validators=[
            InputRequired(),
            CharacterSelector(),
            Length(max=maxIdentifierLength)
        ]
    )
    filedescription = StringField(
        'FileDescription',
        validators=[Length(max=maxIdentifierLength)]
    )
    confirm = SubmitField('Save')


class UploadSingleFileForm(FlaskForm):
    """Single-file upload form (class)."""
    file = FileField('File', validators=[FileRequired()])
    filename = StringField(
        'FileName',
        validators=[CharacterSelector(), Length(max=maxIdentifierLength)]
    )
    filedescription = StringField(
        'FileDescription',
        validators=[Length(max=maxIdentifierLength)]
    )
    confirm = SubmitField('Upload')


class MakeTextFileForm(FlaskForm):
    """Make-text-file form (class)."""
    filename = StringField(
        'FileName',
        validators=[
            InputRequired(),
            CharacterSelector(),
            Length(max=maxIdentifierLength)
        ]
    )
    filedescription = StringField(
        'FileDescription',
        validators=[Length(max=maxIdentifierLength)]
    )
    confirm = SubmitField('Create')


class EditTextFileForm(FlaskForm):
    """Edit-text-file form (class)."""
    textformat = RadioField('Textfile format: ')
    filecontents = TextAreaField('Text')
    save = SubmitField('Save')


class UploadMultipleFilesForm(FlaskForm):
    """Multiple-file upload form (class)."""
    files = FileField('Files', validators=[FileRequired()])
    filesdescription = StringField(
        'FilesDescription',
        validators=[Length(max=maxIdentifierLength)]
    )
    confirm = SubmitField('Upload')


class UploadIconForm(FlaskForm):
    """Thumbnail upload form (class)."""
    file = FileField('Icon', validators=[FileRequired()])
    confirm = SubmitField('Set')


class EditRoleForm(FlaskForm):
    """Role information edit form (class)."""
    roleid = StringField(
        'Role ID',
        validators=[InputRequired(), CharacterSelector(lowercaseAlphabet)]
    )
    roledescription = StringField(
        'Description',
        validators=[Length(max=maxIdentifierLength)]
    )
    confirm = SubmitField('Save')


class UserDataForm(FlaskForm):
    """User information edit form (class)."""
    fullname = StringField(
        'Full name',
        validators=[InputRequired(), Length(max=maxIdentifierLength)]
    )
    email = StringField(
        'Email',
        validators=[Length(max=maxIdentifierLength)]
    )
    confirm = SubmitField('Save')


def generateNewUserForm(settings):
    """Generate a <new user> form (instance) according to settings."""
    minPasswordLength = settings['behaviour']['behaviour_security'][
        'password_min_length']['value']

    class _NewUserForm(FlaskForm):
        username = StringField(
            'Username',
            validators=[
                InputRequired(),
                CharacterSelector(),
                Length(max=maxIdentifierLength)
            ]
        )
        fullname = StringField(
            'Full name',
            validators=[
                InputRequired(),
                Length(max=maxIdentifierLength)
            ]
        )
        password = PasswordField(
            'Password',
            validators=[
                Required(),
                MinimumLength(minPasswordLength),
                EqualTo('confirmpassword', message='Password mismatch'),
                Length(max=maxIdentifierLength)
            ]
        )
        confirmpassword = PasswordField('confirmpassword')
        email = StringField('Email')
        confirm = SubmitField('Save')
    return _NewUserForm()


def generateUserInvitationTicketForm(settings):
    """ Generate a <user invitation> ticket form (instance)
        according to the settings for limits, etc.
    """
    maxValidityHours = settings['behaviour']['behaviour_tickets'][
        'max_ticket_validityhours']['value']

    class _UserInvitationTicketForm(FlaskForm):
        username = StringField(
            'Username',
            validators=[
                CharacterSelector(),
                Length(max=maxIdentifierLength)
            ]
        )
        fullname = StringField(
            'Full name',
            validators=[Length(max=maxIdentifierLength)]
        )
        email = StringField(
            'Email',
            validators=[Length(max=maxIdentifierLength)]
        )
        name = StringField(
            'Internal ticket name',
            validators=[Length(max=maxIdentifierLength)]
        )
        ticketmessage = StringField(
            'Message on ticket',
            validators=[Length(max=maxIdentifierLength)]
        )
        validityhours = StringField(
            'Validity (hours)',
            validators=[ConstrainedOptionalInt(maxValidityHours)]
        )
        confirm = SubmitField('Save')
    return _UserInvitationTicketForm()


def generateChangePasswordTicketForm(settings):
    """ Generate a change-password ticket form (instance)
        according to settings for limitations, etc.
    """
    maxValidityHours = settings['behaviour']['behaviour_tickets'][
        'max_ticket_validityhours']['value']

    class _ChangePasswordTicketForm(FlaskForm):
        submit = SubmitField('Save')
        ticketmessage = StringField(
            'Message on ticket',
            validators=[Length(max=maxIdentifierLength)]
        )
        name = StringField(
            'Internal ticket name',
            validators=[Length(max=maxIdentifierLength)]
        )
        validityhours = StringField(
            'Validity (hours)',
            validators=[ConstrainedOptionalInt(maxValidityHours)]
        )
    return _ChangePasswordTicketForm()


def generateChangePasswordForm(settings):
    """Generate a change-password form (instance) according to settings."""
    minPasswordLength = settings['behaviour']['behaviour_security'][
        'password_min_length']['value']

    class _ChangePasswordForm(FlaskForm):
        submit = SubmitField('Save')
        oldpassword = PasswordField(
            'oldpassword',
            validators=[DataRequired()]
        )
        newpassword = PasswordField(
            'newpassword',
            validators=[
                Required(),
                MinimumLength(minPasswordLength),
                EqualTo('confirmpassword', message='Password mismatch'),
                Length(max=maxIdentifierLength)
            ]
        )
        confirmpassword = PasswordField('confirmpassword')
    return _ChangePasswordForm()


def generateTicketChangePasswordForm(settings):
    """ Generate a ticket-driven change-password form (instance)
        according to settings.
    """
    minPasswordLength = settings['behaviour']['behaviour_security'][
        'password_min_length']['value']

    class _TicketChangePasswordForm(FlaskForm):
        submit = SubmitField('Save')
        username = StringField('Username', validators=[Required()])
        newpassword = PasswordField(
            'newpassword',
            validators=[
                Required(),
                MinimumLength(minPasswordLength),
                EqualTo('confirmpassword', message='Password mismatch'),
                Length(max=maxIdentifierLength)
            ]
        )
        confirmpassword = PasswordField('confirmpassword')
    return _TicketChangePasswordForm()


def generateFsTicketForm(fileModePresent, settings):
    """ Generate a filesystem-related (up/download...) ticket
        form (instance) according to settings and whether the file-mode
        choice is required on the form.
    """
    maxMultiplicity = settings['behaviour']['behaviour_tickets'][
        'max_ticket_multiplicity']['value']
    maxValidityHours = settings['behaviour']['behaviour_tickets'][
        'max_ticket_validityhours']['value']

    class _fsTicketForm(FlaskForm):
        ticketmessage = StringField(
            'Message on ticket',
            validators=[Length(max=maxIdentifierLength)]
        )
        submit = SubmitField('Create')
        name = StringField(
            'Internal ticket name',
            validators=[Length(max=maxIdentifierLength)]
        )
        validityhours = StringField(
            'Validity (hours)',
            validators=[ConstrainedOptionalInt(maxValidityHours)]
        )
        multiplicity = StringField(
            'Times redeemable',
            validators=[ConstrainedOptionalInt(maxMultiplicity)]
        )
        filemode = RadioField(
            'Access mode',
            choices=[
                ('direct', 'Direct download'),
                ('view', 'View-file page'),
            ]
        )
    if not fileModePresent:
        del _fsTicketForm.filemode
    return _fsTicketForm()


def generateColorForm(colorGroupedSettings):
    """ Generate a color-settings form (instance) according
        to the color settings (in their wholeness) passed."""

    class _cForm(FlaskForm):
        confirm = SubmitField('Save')
    for cg, gSettings in colorGroupedSettings:
        for gSetting in gSettings:
            gSettingFullId = '%s___%s' % (
                gSetting['setting'].group_id,
                gSetting['setting'].id
            )
            qField = StringField(
                gSetting['setting'].title,
                validators=[
                    ColorString(),
                    Length(max=maxIdentifierLength)
                ]
            )
            setattr(_cForm, gSettingFullId, qField)

    return _cForm()


def generateGenericSettingsForm(behaviourGroupedSettings):
    """ Generate a generic settings form (instance) according
        to the settings (and their grouping) passed.
    """

    class _cForm(FlaskForm):
        confirm = SubmitField('Save')
    for cg, gSettings in behaviourGroupedSettings:
        for gSetting in gSettings:
            gSettingFullId = '%s___%s' % (
                gSetting['setting'].group_id,
                gSetting['setting'].id
            )
            if gSetting['setting'].type in {'string'}:
                qField = StringField(
                    gSetting['setting'].title,
                    validators=[Length(max=maxIdentifierLength)]
                )
            elif gSetting['setting'].type in {'nonempty_string'}:
                qField = StringField(
                    gSetting['setting'].title,
                    validators=[Required(), Length(max=maxIdentifierLength)]
                )
            elif gSetting['setting'].type in {'optional_integer'}:
                qField = StringField(
                    gSetting['setting'].title,
                    validators=[
                        OptionalInteger(),
                        Length(max=maxIdentifierLength)
                    ]
                )
            elif gSetting['setting'].type in {'positive_integer'}:
                qField = StringField(
                    gSetting['setting'].title,
                    validators=[
                        PositiveInteger(),
                        Length(max=maxIdentifierLength)
                    ]
                )
            elif gSetting['setting'].type in {'nonnegative_integer'}:
                qField = StringField(
                    gSetting['setting'].title,
                    validators=[
                        NonnegativeInteger(),
                        Length(max=maxIdentifierLength)
                    ]
                )
            elif gSetting['setting'].type in {'text'}:
                qField = TextAreaField(
                    gSetting['setting'].title,
                    validators=[Length(max=maxStoredTextLength)]
                )
            elif gSetting['setting'].type in {'boolean'}:
                qField = BooleanField(
                    gSetting['setting'].title
                )
            elif gSetting['setting'].type in {'option'}:
                qField = RadioField(
                    gSetting['setting'].title,
                    choices=[
                        (vItem['id'], vItem['n'])
                        for vItem in gSetting['metadata']['choices']
                    ],
                )
            else:
                raise NotImplementedError(
                    ('unknown setting type "%s" in '
                     'generateGenericSettingsForm') % gSetting['setting'].type
                )
            setattr(_cForm, gSettingFullId, qField)

    return _cForm()


class FindForm(FlaskForm):
    """Search form (class), complete version."""
    text = StringField('Search term', validators=[Required()])
    #
    searchTypeBoxes = BooleanField('Boxes')
    searchTypeFiles = BooleanField('Files')
    #
    searchFieldDescription = BooleanField('Search in descriptions')
    #
    searchMode = RadioField(
        'Search mode',
        choices=[
            ('sim_ci', 'Similar items'),
            ('sub_ci', 'Substring, case-insensitive'),
            ('sub_cs', 'Substring, case-sensitive'),
        ],
    )
    #
    submit = SubmitField('Search')


class QuickFindForm(FlaskForm):
    """Search form abridged for navbar quick search."""
    quicktext = StringField('Quick search...', validators=[Required()])
    submit = SubmitField('Go')
