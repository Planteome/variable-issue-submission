

# How I think I want the syntax to work
import pyobo as obo

o = obo("v1.2.1")       # New OBO with given format-version
o = obo(file)           # Load OBO

# Access Stanzas
o.header             # Access the header
o["PO:0001"]         # Access Stanza with given ID 
o.getTerms()         # Returns an iterator of all Terms (with a __len__)
o.getTypdefs()       # Returns an iterator of all Typdefs (with a __len__)
o.getInstances()     # Returns an iterator of all Instances (with a __len__)

# Create Stanzas
o.Term("PO:0001")           # Create new Term with given ID (returns ref to created obj)
o.Typdef("PO:0001")         # Create new Typedef with given ID (returns ref to created obj)
o.Instance("PO:0001")       # Create new Instance with given ID (returns ref to created obj)
o.add(Stanza, "PO:0001")    # Create copy of Stanza with given ID
o["PO:0001"] = Stanza       # Create copy of Stanza with given ID

# Delete Stanzas
del o["PO:0001"]
o.remove(Stanza)

# Access tag/value pairs (Cardinality 0|1)
o.header["format-version"]
o["PO:0001"]["name"]
for term in o.getTerms():
    print(term["id"])

# Access tag/value pairs (Cardinality n)
o.header["subsetdef"][0]
for value in o.header["subsetdef"]:
    print(value)
    
o["PO:0001"]["synonym"][0]
for value in o["PO:0001"]["synonym"]:
    print(value)
    
for term in o.getTerms():
    for value in term["xref"]:
        print(value)

# Delete tag/value pairs (Cardinality 0|1), required IDs cannot be deleted
del o.header["saved-by"]
del o["PO:0001"]["name"]
for term in o.getTerms():
    del term["namespace"]

# Delete tag/value pairs (Cardinality n)
del o.header["subsetdef"][0]
for i in range(len(o.header["subsetdef"])):
    del o.header["subsetdef"][i]
    
del o["PO:0001"]["synonym"][0]
for i in range(len(o["PO:0001"]["synonym"])):
    del o["PO:0001"]["synonym"][i]
    
for term in o.getTerms():
    for i in range(len(term["xref"])):
        del term["xref"][i]
