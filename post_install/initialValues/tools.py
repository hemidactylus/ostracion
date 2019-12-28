"""
    tools.py
        tools for dynamic parts of the on-DB setting structure.
"""

from pathlib import Path
import os

from config import resourceDirectory

defaultMarkdownDirectory = os.path.join(
    resourceDirectory,
    'default_markdown',
)


# dynamic parts
def loadDefaultPrivacyPolicyBody():
    """Load the default markdown for privacy policy."""
    return open(
        os.path.join(
            defaultMarkdownDirectory,
            'default_privacy_policy.md',
        )
    ).read()


def loadDefaultAboutInstanceBody():
    """Load the default markdown for about/instance."""
    return open(
        os.path.join(
            defaultMarkdownDirectory,
            'default_about_instance.md',
        )
    ).read()


def loadDefaultAboutBody():
    """Load the default markdown for about/ostracion."""
    return open(
        os.path.join(
            defaultMarkdownDirectory,
            'default_about.md',
        )
    ).read()


def getDefaultTempDirectory():
    """Give the default temp dir path as string."""
    return '/tmp/ostracion'


def getDefaultFilesystemDirectory():
    """Give the default FS dir as string."""
    return os.path.join(
        str(Path.home()),
        'ostracion_filesystem',
    )
