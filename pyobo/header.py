from .stanza import Stanza
from datetime import datetime

class Header(Stanza):
    """docstring for Header"""
    def __init__(self, obo):
        super(Header, self).__init__(obo)
                
Header.require("format-version")
Header.define("data-version")
Header.define("version")
Header.define("ontology")

@Header.parse("date")
def parseDate(self, value):
    return datetime.strptime(str(value).strip(), "%d:%m:%Y %H:%M")
@Header.format("date")
def formatDate(self, value):
    return value.strftime("%d:%m:%Y %H:%M")
    
Header.define("default-namespace")
Header.define("saved-by")
Header.define("namespace-id-rule")
Header.define("auto-generated-by")

Header.plural("subsetdef")
Header.plural("import")
Header.plural("synonymtypedef")
Header.plural("idspace")

Header.define("default-relationship-id-prefix")
Header.define("id-mapping")
Header.define("remark")
Header.define("treat-xrefs-as-equivalent")
Header.define("treat-xrefs-as-genus-differentia")
Header.define("treat-xrefs-as-relationship")
Header.define("treat-xrefs-as-is_a")
Header.define("relax-unique-identifier-assumption-for-namespace")
Header.define("relax-unique-label-assumption-for-namespace")
