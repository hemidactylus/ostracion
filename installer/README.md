# Installation README

Below is assumed that:

1. there is a `host` machine with a public IP address;
2. `host` runs Ubuntu Xenial (16.04) or equivalent
    (in particular the service daemon must be `systemd`);
3. Python3 is available on the `host`;
4. you have `ssh` access to the `host` with RSA keys, i.e. no need
    to type password;
5. you have root privileges (through `sudo`) on the machine;
6. you have `nginx` or no Web server running on `host` and are willing
    to install `nginx`;

It is optional (although, except in a localhost setup, strongly
suggested) to have a domain name and to set up HTTPS.

These instructions will install and configure a Web server and Ostracion
served by the Web server through a reverse-proxy configuration.
The Let's Encrypt tools, if desired, will also be installed,
ready to generate a certificate to run the domain using the HTTPS protocol:
in this case, further security enhancements are available once HTTPS
is set up.

_NOTE_: if the target system runs a different OS, uses a system
daemon other than `systemd`, uses another Web server such as Apache,
or anything - despair not: you can probably set up Ostracion all the same,
but do not use this automated way. You are on your own: search the Web
on how to set up a WSGI Flask application in your system as a starting point.

## Steps

### One: Ostracion + Web server setup

Note that this step can be repeated each time a newer version
of the Ostracion repository needs to be deployed over the previous one.

On your local machine create a virtualenv `manage_ostracion` with
the contents of `installer_requirements.txt`, or just install Ansible v2.9+.
The following must be run in the project subdirectory `installer`.

Copy the file `hosts_template` to `hosts` and edit it so that it reflects
the public IP of the target machine.

Copy the file `ostracion/conf_template.yaml` to `ostracion/conf.yaml`
and edit it as suggested by the comments therein, to reflect your `ssh`
access details and some settings of the installation process.
_NOTE_: to be able to `sudo` commands on `host`, the sudo password
must be provided in `conf.yaml`. This file shall **never** be added to
the repo and, for added security, redacted except when being used.

Now you should be able to perform this step in a fully, Ansible-automated way
with:

    ansible-playbook -i hosts ostracion/ostracion_install.yaml

When it finished, Ostracion will be installed and configured for the first run
and `nginx` will be installed and configured to serve Ostracion.

You should be already able to access the application in a browser with either:

    http://IP_ADDRESS
    http://DOMAIN_NAME

depending on whether you have a domain name attached to the host
(please refer to your DNS provider for that).

### Two: first steps in the app

It is as good a time as any other to log in within Ostracion with the default
throwaway administrator account,

    admin / admin

and review a few settings as suggested by the messages. Please review the
choice of filesystem storage location (as changing it later would disrupt
stored files) and have a careful look at the "Behaviour" settings, to avoid
accidentally leaving settings too permissive. After that you should create
another account, promote it to admin status and, logging out and back in
with the new account's credentials, remove the default throwaway admin.

### Three: manual adjustments

As this point the application is up and ready to be used. However, there
are a few more steps that are strongly suggested and require some manual work.

You probably want to remove the `default` virtual server from the active
`nginx` servers: to do so, on the `host`, (sudo-)remove the symlink

    /etc/nginx/sites-enabled/default

(you will restart `nginx` with `sudo systemctl restart nginx` for this
to take full effect).

### Four: HTTPS

Assuming that there is a domain name for `host`,
and that HTTPS is desired (see `conf.yaml`), it is time to set up
HTTPS for Ostracion.

Step one already installed the Let's Encrypt tools suite: in order
to obtain a certificate for the domain, and have the tools handle
the `nginx` configuration for you, you should run:

    sudo certbot --nginx -d FULL_DOMAIN_NAME

(if there are other domains being served by this machine: make backups before
anything else, adjust the command accordingly and expect slightly different
outputs).

You will be asked a few questions and the certificate should be generated and
installed automatically; moreover, the `nginx` configuration should be updated
automatically by Certbot to make use of it. It is suggested to let Certbot
handle the automatic redirect of HTTP to HTTPS.

### Five: High-security HTTPS

TO-DO
