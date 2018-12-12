import pyobo

import inspect

with open("po.obo") as myobo:
    o = pyobo(myobo)
print(o.getID("PO:0025099").resolve())
print(o["PO:0025099"])
