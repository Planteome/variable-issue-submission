from collections import defaultdict
import re
import inspect

from .tagvalue import *

class Stanza(object):
    """
    The base class for all classes which contain collections of `TagValue`s.
    The _tags dictionary keeps track of parsing and formatting for every subclass
    of this class, and settings can be inherited between parent classes.
    """
    def __init__(self, obo):
        self.obo = obo
        self.label = None
        self.tags = {}
        
    def __getitem__(self, key):
        if self.defined(key):
            if key in self.tags:
                return self.tags[key]
            elif self.isPlural(key):
                self.tags[key] = TagValueGroup(self,key)
                return self.tags[key]
            else:
                raise KeyError(key)
        else:
            raise KeyError(key)
    
    def __contains__(self, key):
        return key in self.tags
    
    def __setitem__(self, key, values):
        values = values if isinstance(values,tuple) else (values,)
        if self.defined(key):
            if self.isPlural(key):
                raise KeyError("Can't Assign to Plural Tag")
            else:
                self.tags[key] = TagValue(self, key, *values)
        else:
            raise KeyError()
            
    def __delitem__(self, key):
        if self.defined(key):
            if self.isPlural(key):
                raise KeyError("Can't Delete Plural Tag")
            else:
                del self.tags[key]
        else:
            raise KeyError()
    
    def __str__(self):
        lines = [] if self.label==None else ["[{}]".format(self.label)]
        for tag in self.tags:
            if self.isPlural(tag):
                for val in self.tags[tag]:
                    lines.append(str(val))
            else:
                lines.append(str(self.tags[tag]))
        return "\n".join(lines)
            
    
    def loadLine(self,line):
        try:
            # split off the tag
            tag, remaining = map(lambda s: s.strip(), line.split(":", 1))
            # split off the comment
            comment = None
            quoted = False
            for i in range(len(remaining)):
                if (i==0 or remaining[i-1]!="\\"):
                    if remaining[i]=="!" and not quoted:
                        remaining, comment = remaining[:i], remaining[i+1:]
                        break
                    elif remaining[i] in ("'",'"'):
                        if not quoted:
                            quoted = remaining[i]
                        elif quoted==remaining[i]:
                            quoted = False
            # split off the qualifier string
            qualifiers = []
            match = re.search(r"^(.*?)((?<!\\)\{([^\{\}]*?|'.*?'|\".*?\")*(?<!\\)\})$", remaining)
            if match:
                remaining, qualifiers = match.group(1).strip(), match.group(2).strip()
            value = remaining
            if self.isPlural(tag):
                self[tag].add(value, qualifiers, comment)
            else:
                self[tag] = value, qualifiers, comment
            
        except ValueError as e:
            raise ValueError("tag/value line improperly formatted: "+line)
        
        
    _tags = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda:False)))
    
    @classmethod
    def define(cls, tag):
        cls._tags[cls][tag] = cls._tags[cls][tag]
        
    @classmethod
    def plural(cls, tag, plu=True):
        cls._tags[cls][tag]['plural'] = plu
    
    @classmethod
    def require(cls, tag, req=True):
        cls._tags[cls][tag]['required'] = req
    
    @classmethod
    def parse(cls, tag):
        def decorator(parser):
            cls._tags[cls][tag]['parse'] = parser
            return parser
        return decorator
    
    @classmethod
    def format(cls, tag):
        def decorator(parse):
            cls._tags[cls][tag]['format'] = parse
            return parse
        return decorator
    
    @classmethod
    def defined(cls, tag):
        for anc in filter(lambda c:c!=object, inspect.getmro(cls)):
            if tag in cls._tags[anc]:
                return True
        return False
    
    @classmethod
    def isPlural(cls, tag):
        for anc in filter(lambda c:c!=object, inspect.getmro(cls)):
            if 'plural' in cls._tags[anc][tag]:
                return cls._tags[anc][tag]['plural']
        return False
    
    @classmethod
    def required(cls, tag):
        for anc in filter(lambda c:c!=object, inspect.getmro(cls)):
            if 'required' in cls._tags[anc][tag]:
                return cls._tags[anc][tag]['required']
        return False
        
    def parser(self, tag):
        cls = type(self)
        for anc in filter(lambda c:c!=object, inspect.getmro(cls)):
            if 'parse' in cls._tags[anc][tag]:
                return lambda x: cls._tags[anc][tag]['parse'](self,x)
        return lambda x: str(x)
    
    def formatter(self, tag):
        cls = type(self)
        for anc in filter(lambda c:c!=object, inspect.getmro(cls)):
            if 'format' in cls._tags[anc][tag]:
                return lambda x: cls._tags[anc][tag]['format'](self,x)
        return lambda x: str(x)




class IDStanza(Stanza):
    """docstring for IDStanza"""
    load_callbacks = defaultdict(list)
    def __init__(self, obo):
        super(IDStanza, self).__init__(obo)
                
IDStanza.require("id")
@IDStanza.parse("id")
def parseID(self, value):
    if 'id' in self:
        return self.obo.getID(self['id']).rename(value)
    else:
        return self.obo.setID(value, self)
@IDStanza.format("id")
def formatID(self, value):
    return value.id
