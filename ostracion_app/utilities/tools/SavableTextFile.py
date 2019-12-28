""" SavableTextFile.py
    A simple class offering the same interface as an uploaded file,
    used interally to handle editing of text files through web forms.
"""


class SavableTextFile():

    def __init__(self, contents):
        """Initialize with the contents that will be 'saved'."""
        self.contents = contents

    def save(self, path):
        """Save the contents to a given path."""
        open(path, 'w').write('%s' % self.contents)
