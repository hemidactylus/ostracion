# Ostracion user guide

Ostracion is mainly a _filesystem with a Web interface_ which allows
user-specific remote access to a set of resources (viz. files), organized
in a hierarchical fashion.

The following guide outlines what can be done with the Ostracion
platform. It must be kept in mind that not all features may be
always available for a given item, according to how the
administrators set up the platform and what are the
permissions granted to the user for the item.

For instance, non-logged-in visitors can usually visit
only a subset of the existing resources, if any at all;
they may have no write permission on any box; the Search
capability may be limited to administrators only, and so forth.
In particular, what is not accessible even just in
read-only mode is simply not seen: hence,
different users will have different ideas of "all of Ostracion contents".

## Browsing boxes and files

The **files** are organised in **boxes**. Each box can contain files and/or
other boxes; the platform allows to inspect the contents of boxes and
to upload, view, download, and edit, the individual files
in boxes, depending on the nature of the files and the permissions
granted to the user.

Boxes form a single **tree**, a hierarchy that starts with the _root box_:
all boxes are ultimately contained in it. Boxes and files
are identified by a **path**, which specifies their relation to the root box
and, incidentally, forms the variable part of the associated URL.
A view on the contents of the root box is the homepage of Ostracion.

Besides their identifying name (and path), boxes as well as files
have editable associated metadata, such as a title and a description
and a thumbnail picture.

### Operations and permissions

A given `User`, for a given `Box`, can be assigned **permissions**
to with respect to the box and the files contained therein.
The available permissions are:

- **R**(ead): user has read-access to box contents: all files contained in
`Box`, plus those boxes contained in `Box` for which user `User` still has
read permission;
- **W**(rite): as for contained files, `User` can: upload, replace, edit,
delete, change metadata/thumbnail and move somewhere else. Furthermore,
`User` can edit metadata/icon of `Box` itself.
- **C**(reate): `User` can create, delete and move around boxes within
`Box`, provided they have also read permission on these boxes.

Ostracion administrators assign a number of **roles** to each user (such
as "family", "friends", "colleagues" and so on) and, for each 
box, specify permissions granted to roles: thus, a user inherit a certain
set of permission on each box. Moreover, unless explicit 
permissions are set on a box, those of the parent box are
automatically inherited. In particular, to each user
corresponds a _user-specific role_, a role that is automatically
and unchangeably given to the user and that the administrators
can use to set user-specific access permissions (which combine
with the other).

(Notes: 1. _The permissions on root box are special and cannot be 
altered._ 2. _Non-logged in visitors are automatically assigned
the special_ "anonymous" _role only._)

When visiting the contents of a box, the visibility of each individual
sub-box depends on specific settings of the sub-box itself;
conversely, for files it is an all-or-nothing case: if a user can see
within a box, all files contained therein are visible.

Being able to "see" a file in general implies, being able to _download_ it;
for some file formats (such as images or text), there
is also a view mode in the Web application itself.

One of the uses of a box is that of a _photo gallery_. A box which
contains pictures, or other viewable files, can be seen as a gallery:
it is possible to browse the contained files back and forth. Contained
boxes would be hidden from browsing until one switches back to the regular
box-contents-viewing mode.

### Deleting

As far as deleting is concerned, a general principle
 holds (_no-parachute_ principle):
**as soon as it is deleted, it is lost forever**.
That is, the moment one clicks the red button with the cross, the object
has disappeared from existence. It is time to be responsible for
one's actions.

As long as the **W** permission holds, a user can delete files.
As for boxes, not only must the **C** permission hold for the
parent box and the **W** for the deletee box, but also all
contained sub-items must be deletable by the user; otherwise,
an attempted deletion would fail with a warning message.

On a somewhat related note, uploading can result in overwriting
an already-existing file: according to the no-parachute
principle, the original file is lost in favour of the new one;
if a box exists with the same name, on the other hand, the upload fails.

### Text files and Markdown

Text files, besides being viewable in the application, can also be
created and edited directly in it, without the need for uploading
anything: further, when editing them, it is also possible to set
Markdown as preferred rendering mode.
In this way documents - from simple grocery lists all the way up
to multi-page projects such as a complex documentation - can be
hosted in Ostracion.

There are, however, limitations when it comes to navigating Markdown
pages accessed by ticket, see below.

## User profile

This section applies only to logged-in users and details the
available operations related to the user account.

### Change user information

The account menu gives options to change:

- user data (full name, email). This information is not compulsory
and is not used in any way, automated or otherwise;
- user profile picture;
- account password.

### Account deletion

Users can decide to delete their account. In violation of the no-parachute
principle, there is a confirmation screen
to go through (!), but once the deletion is done every trace of the user
activity is gone forever: uploaded files are deleted, created boxes are
deleted (unless they contain items the user has no right to delete,
in which case their relevant features are anonymized), contributions to
other items (metadata, thumbnails) are erased, and any open ticket
(see below) is immediately revoked and ceases to exist.

### Interaction with other users

_"Hell is other people" [J. P. Sartre]_

Only when looking at box or file metadata can a Ostracion user infer the
existence of other users.
There is no direct way to communicate with other users, track their
activities, look at their profile.
The only sharing that takes place is implicit through the possibility of
accessing the same boxes and files.

That is to say, a second important pillar of Ostracion is the following
principle ("NASN principle"): ** Ostracion is NOT a social network.**

## Tickets

There are cases in which a user wants to grant, perhaps temporarily, a
limited power to someone else, someone with no account on Ostracion.
For instance, `User` needs `Person` to view a file / a photo gallery hosted
on Ostracion; or, `User` would like `Person` to upload a file on a box.

To achieve these and similar goals, `User` can issue tickets of type "file",
"gallery" and "upload" respectively. A ticket is a coupon, in the form of a
"magic link", that can be redeemed while not being logged-in and allows to
perform some operations: a download/view of a particular file,
a gallery view of the contents of a specific box, an upload to a given box.

In order for `User` to be able to issue a ticket for performing operation `X`
(e.g. upload to a certain box), they have to be able to do `X` themselves;
a ticket, in general, can be limited in time and/or in number of operations
(downloads, views, uploads) it lets one do (_it is a good idea to always set
some limitations when issuing a ticket_).

A generated ticket is displayed on the application for `User` to copy the
magic link and give it (e.g. via email) to `Person`. Tickets have
an "internal" name, for quick identification by the issuer, and an optional
message, to be shown to the final person who redeems the
ticket and performs `X`.

Tickets can expire, when they reach their expiration time or when the number
of usages reaches the allowed total; all tickets issued by the user can be
inspected in the dedicated user profile pages and can be revoked
(that is, deleted) at any time.

#### Tickets and Markdown

When viewing a (rendered) Markdown page through a file-view ticket, other
pages linked there would result in broken links (that's because Ostracion
cannot assume the ticket holder has any right to see the link target);
for the same reason, embedded images would not be displayed. Similar
limitations apply to the case of a "gallery-view ticket" on a box that happens
to host Markdown material.

## Special pages

### Tree view

This page shows, at a glance, the whole of the hierarchy of boxes making
up the Ostracion filesystem (as far as the user is concerned), including
the files if so desired.

### Search

A search page to quickly locate files and/or boxes based on their name
and description.
One can also search for "similar-sounding" parts of the item name
(for instance, a search of type "Similar" will match "ioniZATion" even
if the search term is "ionisatin").
