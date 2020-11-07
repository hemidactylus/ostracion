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

### Better navbar menu building

as for "g.availableApps.tasks.root.tasks" (see logins.py),
a unique menu construction shared by the menu and the in-page "tasks view"


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

### Apps

Boxes of type 'app'.

1. As an exercise: PDF calendar maker.
    TO DOC every function
    PEP8
    - no checkeds in search, fix
    - transparent GIfs in resizing, fix
    - make sure ansible has apd installs (latex & co)

2. Accounting app in particular and its special config.
3. Move biblio here?
