# Ostracion admin guide

## Ostracion configuration

Most of the managing of Ostracion by administrators occurs
through the "Admin area" section (for instance, the application configuration
detailed in the following); a notable exception concerns
the permissions granted to individual boxes, which are handled
in a special page reachable from the box-view itself.

Administrators have quite some freedom when it comes
to application appearance and behaviour.
Besides configuring colors and images to be used
throughout the navigation, there are the following
important sections:

- _About page_: contact email and body of the contents shown in the
"About" page.
The text body is in Markdown. The contact email is stored internally as text,
but is always rendered as image to make the life of crawler bots a bit more
difficult.
- _Privacy policy_: similar to the previous case. Again, the DPO contact email
is always rendered as image to visitors.
- _System settngs_: this is where the mapping to the actual machine filesystem
is done. One must be **extremely cautious** when re-configuring this. A
change in the "filesystem physical location" will make all files currently
hosted in Ostracion become suddenly unavailable.
- The _Behaviour settings_ are explained below.

### "Behaviour Settings"

Most of the options listed in this section change the actual behaviour of
the application in various ways:

- _Logged-in users only_, if switched on, blocks the navigation completely
to anybody who is not authenticated as a Ostracion user (the login
page, though, is still accessible). Used to make Ostracion a
"invite-only" place.
- _Localnet mode setting_: when a new box is created in the root box,
its default permissions for the "anonymous" role (hence, non-logged-in users)
are set here. It is suggested to have a no-permission default
("Locked for Web")
when Ostracion is used on the Internet, and adjust the setting as desired on
a local-only network.
- _Invasive user management_ means that administrators can directly create
users and change their (metadata and) password, as opposed to releasing tickets
to let the users themselves do it (so that only the final holders of
the account know their password).
- _Brute-force protection_ is the number of seconds that have to pass before
a second authentication can be attempted from the same client IP. This is a
measure to mitigate the risk of brute-force account cracking. To make the
storage of the IP anonymous, an admin
should also insert some random characters in the field _IP hashing salt_.
- _File tickets for everyone_ means that all new users will automatically
be assigned to the "ticketer" role, thus making them able to issue tickets.
Role assignments can always be reviewed and changed user by user at a
later time.
- _Protect user-issued tickets_ temporarily locks the availability of tickets
when the issuer user is banned. Turning this off means that a ticket stays
valid when the issuer is banned.
- _Protect user/password tickets_ means that a ticket for user creation or
password change, issued by an admin, stops being valid if the issuer is no
more an admin; otherwise, the ticket maintains validity no matter what
the current admin status of the issuer is.
- _Maximum ticket validity / Maximum grants per ticket_: administrators can
put an upper limit to the validity parameters chosen for every individual
ticket that will be issued.
- _Access to Tree view_, _Files visible in tree view_ and _Access to search_
can limit the availability of these special pages to certain sets of users;
moreover, the _Show match scores..._ option controls the visibility of the
internal "match score" used in sorting and selecting the results of a search.

## The many powers of admins

Administrators always have full access, with all permissions, to all of the
contents stored on Ostracion. That is, they can upload files, create boxes,
change metadata and icons, move files and boxes around, and delete items
without any limit.

The most important actions an admin can do on a user are:
they can temporarily ban/unban users, completely delete their account (keeping
in mind the _no-parachute principle_), change their role assignment
(see below), issue them a password-change ticket, invite/create new users.
These actions are accessible in the "User" section of the admin area of
the application.

As mentioned above, administrators can also directly operate on user
passwords (and, likewise, on profile icons and metadata), but this is a
discouraged practice: an etiquette-conscious administrator always acts by
means of tickets for password-related matters.

Admins can also review and revoke (i.e. erase) any ticket, regardless of the
issuer. This is done in the "Tickets" section of the admin area.

### Roles

Usually, Ostracion administrators create some "roles" (such as "friend",
"student" or "schoolmate") which are then associated to users (a user can
have any number of roles).

Generally speaking, the box permissions granted to a user are the union of
the permissions coming from the roles attached to that user (including,
automatically, `anonymous`): for instance, if `User` belongs to roles `family`
and `friends`, and box `B` is read-only (**R--**) for `family` and
write-only (**-W-**) for `friends`, as a result `User` is given **RW-**
permission on `B`.

(_NOTE_: The logic of box permission attribution in its full complexity
is outlined below.)

There are, in Ostracion, a number of **system roles** with a special
significance:

- "admin": users with this role are administrators. Any administrator can
give and remove this role attribution to/from other users, but cannot remove
it from themselves: in this way, it is impossible to simultaneously
"lock all administrators out".
- "ticketer": this role is necessary to make a user able to issue tickets.
Administrators need not have this role to issue all kinds of ticket.
Whether a user gets this role by default upon creation is controlled in the
application settings.
- "anonymous": this role cannot be assigned to any user and identifies the
non-logged-in visitor of the pages. Setting box permissions for this role
is how the administrators control what anonymous
users of Ostracion can and cannot do. _Note: for the permission algebra
outlined below, every user is treated as belonging to this role._

### How box permissions and roles combine for a user

In general, administrators can set permissions for all roles on all boxes,
with the exception of the root box, whose sole admitted roles are "admin"
and "anonymous", which cannot be altered.

To edit the permissions of a box, when viewing the box, administrators have
the option of expanding the box heading and open the "Edit permissions" page:
there, the inherited permissions are shown along with the explicit ones.
Explicit permissions can be removed and inherited permissions can be made
explicit to override the inherited behaviour (note that, to reduce the
permissions for a given role with respect to the parent box, it is necessary
to first make the item explicit and then turn off parts of the permissions).

There is a system of "permission inheritance", according to which the
permissions for a role `R` are inherited by all contained boxes,
_unless they are given explicit permissions for role `R`_.

Admins should remember that when creating boxes directly contained in the
root box, default permissions for the "anonymous" role are added to the box
according to how Ostracion is configured (see "_Localnet mode setting_").

**Example**.
There is a chain of boxes contained into each other:

        Root > B1 > B2

and there exist roles `admin`, `anonymous`, `friends`, `colleagues`,
`schoolmates` and `family`, with assignments as in:

                        +--------------------------+
                        |  Root  |    B1   |   B2  |
        +---------------+--------+---------+-------|
        | admin         | RWC    |         |       |
        | anonymous     | R--    |   ---   |       |
        | friends       |        |   R--   |  RW-  |
        | family        |        |         |  RWC  |
        | colleagues    |        |   R--   |  ---  |
        | schoolmates   |        |   R--   |       |
        +------------------------------------------+

(only explicit permissions are given in the schema above), then what happens
is that:

- `admin` will have all permissions on all boxes (an unchangeable fact);
- `anonymous` would have read access to all boxes, but the blocking "- - -"
setting for `B1` means that neither `B1` nor `B2` (the latter by inheritance)
would be visible to non-logged-in users;
- `B1`, has the "R - -" permission for `friends`, `colleagues` and
`schoolmates` alike;
- `B2`, counting inheritance and explicit settings, has the following: 
"- - -" for `colleagues`, "R W C" for `family`, "R W -" for `friends`
and "R - -" for `schoolmates`.

Now, for a user to be able to access a box `B`, they _must have read
permission all the way from the root box to `B`_, even by "jumping" between
their associated roles in doing so. Thus,

- to have read-access to `B1`, users can have either of the following roles
(or any superset thereof): `admin`, `colleagues`, `friends`, `schoolmates`;
- to have read-access to `B2`, users can have either of the following roles
(or any superset thereof): `admin`, `friends`, `schoolmates`,
`colleagues+family` (note that the last one is a _double requirement_: only
users with both roles end up having the access).

As far as the **W**(rite) and the **C**(hange) permissions are concerned,
things work in a slightly different way: for `User` to actually be able to
upload/delete/update/edit files in `Box`, it must be that 

1. `User` has **R** access to `Box` (i.e. all the way down from root);
and, at the same time,
2. `User` has **W** permission on `Box` itself (and _not necessarily on
the ancestor boxes_).

Likewise, for the power to create sub-boxes in `Box`, the user must be able
to see the contents of the box and be granted **C** permission on it.

So, suppose there is a box `B3` inside the aforementioned `B2` as follows:

                        +----------------------------------+
                        |  Root  |    B1   |   B2  |   B3  |
        +---------------+--------+---------+-------|-------|
        | admin         | RWC    |         |       |       |
        | anonymous     | R--    |   ---   |       |       |
        | friends       |        |   R--   |  RW-  |       |
        | family        |        |         |  RWC  |       |
        | colleagues    |        |   R--   |  ---  |       |
        | schoolmates   |        |   R--   |       |  R-C  |
        +--------------------------------------------------+

then, for box `B3`, the requirements are as follows:

- to read, one must have `admin`, `friends`, `schoolmates` or
`friends+family` roles;
- to write, one must have `admin`, `friends`, `colleagues+family` or
`family+schoolmates` roles;
- to create (and remove) sub-boxes, one must have `admin`, `schoolmates`,
`colleagues+family` or `family+friends` roles.

All this information is readily summarized when an admin (or a regular user
if so configured in the application settings) inspects the permission of each
box by expanding the "Permission" section of the box header; moreover, when
updating the role-permission assignments for a box, the results of the above
permission algebra are constantly updated.

### Tickets issuable by admins

There are types of tickets which can be issued only by an administrator.

The **user creation ticket** (or "user invitation"), when redeemed, allows
the creation of a new account on Ostracion. When creating this ticket
(from the Admin/Users page) it is possible to specify the username or leave
the freedom to choose it.

The **change password ticket** is intended for users who somehow forgot
their password and are then able, by redeeming the ticket, to reset their
password and log in again.

Tickets of these types, regardless of who created them, can be seen and
revoked from within the "Admin/Tickets" pages.
