# TODO for Ostracion

## Maintenance (internals)

### Use pathToFileStructure everywhere (fileaccess views etc)

### makeFileInParent should check for permissions (hence have more arguments)

### External links

MUCH DUPLICATION OF BOILERPLATE TO REDUCE
there seems to emerge a notion of 'file-like'
e.g. that can be moved, etc. See movelink two views VS move file
OR ALL the checks done before move-file VS move-link (permissions etc)

### Ansible, nginx restart target, why it seems nonexistent sometimes?
(then, after various reruns of the ansible, all is ok)

### Re-salting of password

Password and re-salting: it is wrong to have this in the model and
it is fragile to have it dependent on whether 'password' or 'password hash'
is passed to the model class. Move it somewhere better.

### CSS

Css-ification of all style elements in all templates for tidiness,
also moving the little javascript to scripts in static.

Also: css-ification of all background colors & co. with
a tag-prepended css file template built by a route?

Tree viev: make all of it into a css style sheet.

### Tables

Tables and small screens: currently a disaster.


## TODOs for the next major release

### A "paste text" ticket

### API / Command line tools to sync in either direction

### Zip handling

Users will be able to:

1. download box (+children)
2. upload zip (creates children, with all trouble of overwrites and
               intertype overnamings)

Formats:
1. zip
2. tar(/.gz)

Current status:
       zip                  targz
down   X, no emptydirs      -
uplo   -                    -

(size is approximated due to links being rendered as files)

With this one creates the zip ready to stream:
  https://github.com/BuzonIO/zipfly#zipfly
but zipping "links" (and other future file-like objects) would be a hassle.

### Messages

A system-messages table (login protection alerts, etc).

### "WELLS, wormholes on file system"

Boxes of type 'real fs'

### Biblio app

### Calendar app
(in general, with application in calendar) gather/present information on aspect ratio for images

### Accounting app - DOING -

Accumulated todos:
  - add removal of items from tables when erasing a user
  - getAllLedgers is for admins only: make getUserLedgers to handle ordinary view (which for admins covers all)
  - in dbRemoveActor, make it impossible to remove actors if they have movement contribs
  - tooltip in in-table "add" button, how to?
  - filter ledger-user-choice with: those with the accounting app only
    - how to deal with: user loses the 'accounting' app role, yet they are in some ledgers?
  - handle last_edit_date / last_edit_username at each movement operation on ledger
  - upon user deletion, what to do with the movements? and anonymize user contribs to ledger
  - Actual images (=default images for ledger, add-ledger and so on)
  - native sqlite joins for movement/movcontribs
  - pagination, limit (sqlite) in movements queries
  - edit movement (uses ledger.html in 'edit mode' or something)
  - Remove the 'apps' task if it's empty (e.g. for anon user), as it is not there in the menu
  - icons to "apps" in the menu

  - for pagination / filtering:
      https://www.sqlitetutorial.net/sqlite-count-function/
      https://stackoverflow.com/questions/3325515/sqlite-limit-offset-query


  + js to adapt subcats / show the description
