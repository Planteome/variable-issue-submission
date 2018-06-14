from pyobo.header import Header
from pyobo.term import Term
from pyobo.typedef import Typedef
from pyobo.instance import Instance
import sys

class OBO_Identifier(object):
    """docstring for OBO_Identifier"""
    __slots__ = ["obo", "id", "content"]
    def __init__(self, obo, iD):
        self.obo = obo
        self.id = None
        self.rename(iD)
        self.content = None
    def setContent(self, content): 
        self.content = content
        return self
    def resolve(self): 
        if not self.content:
            raise Exception("ID not found")
        else:
            return self.content
    def rename(self, newID):
        if newID in self.obo.idmap:
            raise ValueError("ID already in use!")
        self.obo.idmap[newID] = self
        if self.id:
            del self.obo.idmap[self.id]
        self.id = newID
    def __repr__(self):
        return "OBO_ID{{{}}}".format(self.id)
    def __str__(self):
        return self.id
            
class OBO(object):
    def __init__(self, fh=None):
        self.idmap = {}
        self.stanzas = []
        self.header = Header(self)
        if fh:
            self.load(fh)
    stanzaDict = {
        '[Term]': Term,
        '[Typedef]': Typedef,
        '[Instance]': Instance 
    }
    def load(self, fh):
        # parse stanzas
        current = self.header
        for raw_line in fh:
            line = raw_line.strip() # more lenient than spec, allows left whitespace
            # print(line)
            if not line: # ignore empty lines
                continue 
            elif line in self.stanzaDict: # start new stanza
                current = self.stanzaDict[line](self)
                self.stanzas.append(current)
            else: # add line to stanza
                current.loadLine(line)
                
    def Term(self, iD):
        newTerm = self.stanzaDict["[Term]"](self)
        newTerm["id"] = iD
        return newTerm
    def Typedef(self, iD):
        newTypedef = self.stanzaDict["[Typedef]"](self)
        newTypedef["id"] = iD
        return newTypedef
    def Instance(self, iD):
        newInstance = self.stanzaDict["[Instance]"](self)
        newInstance["id"] = iD
        return newInstance
        
    def getTerms(self):
        for stanza in self.stanzas:
            if isinstance(stanza,self.stanzaDict["[Term]"]):
                yield stanza
                
    def getTypedefs(self):
        for stanza in self.stanzas:
            if isinstance(stanza,self.stanzaDict["[Typedef]"]):
                yield stanza
                
    def getInstances(self):
        for stanza in self.stanzas:
            if isinstance(stanza,self.stanzaDict["[Instance]"]):
                yield stanza
                
    
    def __str__(self):
        s = str(self.header)
        s = s+"\n\n"+"\n\n".join(str(st) for st in self.stanzas)
        return s
        
    def __getitem__(self, key):
        if isinstance(key,OBO_Identifier):
            key = key.id
        if not key in self.idmap:
            raise KeyError("ID not found")
        return self.idmap[key].resolve()
            
    def getID(self, key):
        if isinstance(key,OBO_Identifier):
            key = key.id
        if not key in self.idmap:
            self.idmap[key] = OBO_Identifier(self, key)
        return self.idmap[key]
        
    def setID(self, key, content):
        if not key in self.idmap:
            self.idmap[key] = OBO_Identifier(self, key)
        self.idmap[key].setContent(content)
        return self.idmap[key]

sys.modules[__name__] = OBO
