import json
import re

class Qualifier(object):
    __slots__ =  ['key','value']
    def __init__(self, key, value):
        self.key = key
        self.value = value
    def __getitem__(self,key):
        if key in self.__slots__:
            return getattr(self,key)
        else:
            raise KeyError()
    def __repr__(self):
        return "Qualifier({})".format(str(self))
    def __str__(self):
        return "{}={}".format(self.key,json.dumps(self.value))

class TagValue(object):
    __slots__ =  ['_stanza','tag','value','qualifiers','comment']
    def __init__(self, stanza, tag, value, qualifiers=[], comment=None):
        if isinstance(qualifiers,str) and comment==None and not (qualifiers[0]=="{" and qualifiers[-1]=="}"):
            comment = qualifiers
            qualifiers = []
        self._stanza = stanza
        self.tag = tag
        self.value = stanza.parser(tag)(value)
        self.qualifiers = self.parseQualifiers(qualifiers)
        self.comment = comment        
    def parseQualifiers(self, qualifiers):
        if isinstance(qualifiers,str):
            # parse qualifiers
            l = []
            for match in re.finditer(r"([^\{\s]*?)=(?<!\\)\"(.*?)(?<!\\)\"\s*,?\s*",qualifiers): 
                l.append(Qualifier(match.group(1),match.group(2)))
            return l
        elif isinstance(qualifiers,dict):
            return [Qualifier(k,qualifiers[k]) for k in qualifiers]
        elif isinstance(qualifiers,list):
            return [Qualifier(k['key'],k['value']) for k in qualifiers]
        else:
            raise ValueError("unknown qualifier list type")
    def __repr__(self):
        return "TagValue{ "+", ".join(
            "{}={}".format(slot, repr(getattr(self,slot))) 
                for slot in self.__slots__ if not slot.startswith("_")
        )+" }"
    def __str__(self):
        s = "{name!s}: {value!s}".format(
            name   = self.tag, 
            value  = self._stanza.formatter(self.tag)(self.value)
        )
        if len(self.qualifiers)>0:
            s += " {{ {} }}".format(
                ", ".join(str(q) for q in self.qualifiers)
            )
        if self.comment!=None:
            s += " ! {!s}".format(
                self.comment
            )
        return s
        
class TagValueGroup(object):
    __slots__ =  ['stanza','tag','list']
    def __init__(self, stanza, tag):
        self.stanza = stanza
        self.tag = tag
        self.list = []
    def __getitem__(self,index):
        return self.list[index]
    def __setitem__(self, index, *args):
        self.list[index] = TagValue(self.stanza, self.tag, *args)
    def __delitem__(self, index):
        del self.list[index]
    def add(self, *args):
        tgv = TagValue(self.stanza, self.tag, *args)
        self.list.append(tgv)
        return tgv
    def remove(self, val):
        self.list.remove(val)
    def __iter__(self):
        return (v for v in self.list)
    def __len__(self):
        return len(self.list)
    def __repr__(self):
        return repr(self.list)
