__author__ = 'joshhanna'

from owllib.ontology import Ontology
from rdflib import URIRef

ont = Ontology()
print("loading bfo")
ont.load(location="http://www.ifomis.org/bfo/owl")

for cls in ont.classes:
    if isinstance(cls.uri, URIRef):
        print(cls.uri)

print("loading iao")
ont.load(location="https://information-artifact-ontology.googlecode.com/svn/releases/2011-08-04/merged/iao.owl")

for cls in ont.classes:
    if isinstance(cls.uri, URIRef):
        print(cls.uri)

print("all imports")

for imp in ont.direct_imports.union(ont.indirect_imports):
    print(imp, imp.uri)

