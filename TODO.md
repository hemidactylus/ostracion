# TODO for Ostracion

## Maintenance (internals)

### makeFileInParent should check for permissions (hence have more arguments)

### External links

MUCH DUPLICATION OF BOILERPLATE TO REDUCE
there seems to emerge a notion of 'file-like'
e.g. that can be moved, etc. See movelink two views VS move file
OR ALL the checks done before move-file VS move-link (permissions etc)

### A convention for 'system roles' (ASAP)

TODO:
1. how to migrate from preexisting DB
  - creation of a user-role per each user
  - adding system roles in postInstall
  - keeping box/user role attributions
2:
   == remove the 'accounting' role and make roles addable per postInstall as with settings

ON MASTER
    'roles': {
        'primary_key': [
            ('role_id', 'TEXT'),
        ],
        'columns': [
            ('description', 'TEXT'),
            ('system', 'INTEGER'),
        ],
    },
    'box_role_permissions': {
        'primary_key': [
            ('box_id', 'TEXT'),
            ('role_id', 'TEXT'),
        ],
        'columns': [
            ('r', 'INTEGER'),
            ('w', 'INTEGER'),
            ('c', 'INTEGER'),
        ],
        'foreign_keys': {
            'boxes': [
                [['box_id'], ['box_id']],
            ],
            'roles': [
                [['role_id'], ['role_id']],
            ],
        },
    },
    'user_roles': {
        'primary_key': [
            ('username', 'TEXT'),
            ('role_id', 'TEXT'),
        ],
        'columns': [],
        'foreign_keys': {
            'users': [
                [['username'], ['username']],
            ],
            'roles': [
                [['role_id'], ['role_id']],
            ],
        },
    },

ON BRANCH
    'roles': {
        'primary_key': [
            ('role_class', 'TEXT'),
            ('role_id', 'TEXT'),
        ],
        'columns': [
            ('description', 'TEXT'),
            ('can_box', 'INTEGER'),
            ('can_user', 'INTEGER'),
            ('can_delete', 'INTEGER'),
        ],
    },
    'box_role_permissions': {
        'primary_key': [
            ('box_id', 'TEXT'),
            ('role_class', 'TEXT'),
            ('role_id', 'TEXT'),
        ],
        'columns': [
            ('r', 'INTEGER'),
            ('w', 'INTEGER'),
            ('c', 'INTEGER'),
        ],
        'foreign_keys': {
            'boxes': [
                [['box_id'], ['box_id']],
            ],
            'roles': [
                [['role_class', 'role_id'], ['role_class', 'role_id']],
            ],
        },
    },
    'user_roles': {
        'primary_key': [
            ('username', 'TEXT'),
            ('role_class', 'TEXT'),
            ('role_id', 'TEXT'),
        ],
        'columns': [],
        'foreign_keys': {
            'users': [
                [['username'], ['username']],
            ],
            'roles': [
                [['role_class', 'role_id'], ['role_class', 'role_id']],
            ],
        },
    },

Before anything else, in a separate module:
  - if 'roles' exists and has NO role_class => do the translation
  - The translation goes as:
    - use a special schema which combines legacy (by hand) + modern
    - create three tables XXX_transitional in order as given below
    - move item by item under some rules:
        roles:
          role_id <-- role_id
          role_class <-- 'system' if system else 'manual'
          system DIES
          description <-- description
          can_box     <-- 0 if system/ticketer else 1
          can_user    <-- 0 if system/anonymous else 1
          can_delete  <-- 0 if system else 1
        box_role_permissions:
          lookup the previous table to know how to add
          role_class when copying the records
        user_roles:
          same as previous table
    - drop the three original tables
    - rename the transitionals back to original names
      (with cur.execute("ALTER TABLE `foo` RENAME TO `bar`") ... see https://stackoverflow.com/questions/426495/how-do-you-rename-a-table-in-sqlite-3-0#426512)
  - proceed with everything else

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
