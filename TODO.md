# TODO for Ostracion

## Maintenance (internals)

### Root box naming

'Root', '(root)' etc, are slapped in various places as literals.
Fix this. Cf. e.g. `fileaccess.py:581`.

### Nonifystring

The repeated logic of "None if empty string" in
`fileAccess.py/fsMakeTicketView:467`
can be written better.

### determineThumbnailFormatByModeAndTarget

The function 'determineThumbnailFormatByModeAndTarget' should not be in
the thumbnails.py **view** code, rather in a tiny library file.

### Text file view modes

Very ugly how it is now slapped in `uploads.py/editTextFileView`.
Prepare proper settings place and as a test enable
(later via settings) HTML view mode.

### Setting for thumbnailing

A settings to enable taking thumbnails of thumbnailables.

### Re-salting of password

Password and re-salting: it is wrong to have this in the model and
it is fragile to have it dependent on whether 'password' or 'password hash'
is passed to the model class. Move it somewhere better.

### Anonymous mixin

Create and use a proper mixin for non-logged-in users - check it is
going to be used everywhere.

### CSS

Css-ification of all style elements in all templates for tidiness,
also moving the little javascript to scripts in static.

Also: css-ification of all background colors & co. with
a tag-prepended css file template built by a route?

Tree viev: make all of it into a css style sheet.

### Tables

Tables and small screens: currently a disaster.




## TODOs for the next major release

### External links

in ls view, items of type 'bookmark' or so, with icon, title, subtitle
which are just links to external urls

### Zip handling

Users will be able to:

1. download box (+children)
2. upload zip (creates children)

### Messages

A system-messages table (login protection alerts, etc).

### "Windows on file system"

Boxes of type 'real fs'

### Apps

Boxes of type 'app'.

1. As an exercise: PDF calendar maker.
2. Accounting app in particular and its special config.
