from .stanza import IDStanza

class Instance(IDStanza):
    """docstring for Instance"""
    def __init__(self, obo):
        super(Instance, self).__init__(obo)
        self.label = "Instance"
