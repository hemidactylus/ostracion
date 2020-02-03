# TODO for Ostracion

## Maintenance (internals)

### makeFileInParent should check for permissions (hence have more arguments)

### External links

MUCH DUPLICATION OF BOILERPLATE TO REDUCE
there seems to emerge a notion of 'file-like'
e.g. that can be moved, etc. See movelink two views VS move file
OR ALL the checks done before move-file VS move-link (permissions etc)

### A convention for 'system roles' (ASAP)

to handle in the future roles such as calendar/(ticketer)/accounting ...
with a convention and that the admins cannot delete/create them.
Such roles cannot be given to boxes, only users.

More: roles should have several attributes:
  (app+ means: accounting + ticketer and other sysconfigurations)
                      adm   sys/app regular   anon
  givable to boxes  |   Y     N           Y      Y
  deletable         |   N     N           Y      N
  givable to users  |   Y     Y           Y      N

Check transpose:
                      boxes |  deletable | users
  [S]admin          |     Y            N       Y
  
  ticketer+...      |     N            N       Y
  [app]accounting+..|
  
  [manual]          |     Y            Y       Y
  [x]anonymous      |     Y            N       N  

Features are then:
  - givable to boxes
  - deletable
  - givable to users

This should be done with a drastic change in primary keys,
namely a double-field key (roleclass, roleid):
    admin  (sys, 'admin')
    anon   (sys, 'anonymous')
    ticketer... (sys, 'ticketer')
    ...

EITHER THAT OR A STRICT UNIQUE-ID with a prefix system (bleah)
AND NEVER USE THE ID IN DISPLAY + VISUAL CUES (e.g. colors)
    

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

### The markdown-with-images riddle

When viewing a rendered markdown, if it embeds an image it is a mess
since a rel path 'image.png' would inherint the fsv ("V") full url.
Find an elegant solution.



## TODOs for the next major release

### "Terms and conditions" with compulsory acceptance before using the account?
(as per new setting: "must new users accept before browsing?")

### API / Command line tools to sync in either direction

### Zip handling

Users will be able to:

1. download box (+children)
2. upload zip (creates children)

### Messages

A system-messages table (login protection alerts, etc).

### "WELLS, wormholes on file system"

Boxes of type 'real fs'

### Apps

Boxes of type 'app'.

1. As an exercise: PDF calendar maker.
2. Accounting app in particular and its special config.
