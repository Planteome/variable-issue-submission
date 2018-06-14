from .stanza import IDStanza

class Term(IDStanza):
    """docstring for Term"""
    def __init__(self, obo):
        super(Term, self).__init__(obo)
        self.label = "Term"

Term.define("builtin")
Term.define("comment")
Term.define("created_by")
Term.define("creation_date")
Term.define("def")
Term.define("equivalent_to")
Term.define("intersection_of")
Term.define("is_obsolete")
Term.define("name")
Term.define("namespace")
Term.define("property_value")
Term.plural("alt_id")
Term.plural("consider")
Term.plural("disjoint_from")
Term.plural("intersection_of")
Term.plural("is_a")
Term.plural("relationship")

class _Relationship(object):
    __slots__ = ["relation","target"]
    def __init__(self, relation, target):
        self.relation = relation
        self.target = target
    def __repr__(self):
        return str(self.relation)+" "+str(self.target)
        
@Term.parse("relationship")
def parseRelationship(self,value):
    relation, target = map(self.obo.getID, value.split())
    return _Relationship(relation, target)
    
Term.plural("replaced_by")
Term.plural("subset")
Term.plural("synonym")
Term.plural("union_of")
Term.plural("xref")
