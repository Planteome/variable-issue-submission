from .stanza import IDStanza

class Typedef(IDStanza):
    """docstring for Typedef"""
    def __init__(self, obo):
        super(Typedef, self).__init__(obo)
        self.label = "Typedef"
