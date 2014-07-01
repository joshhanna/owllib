__author__ = 'joshhanna'

from owllib.ontology import Ontology
from rdflib import URIRef

ont = Ontology()
print("loading bfo")
ont.load(location="http://www.ifomis.org/bfo/owl")

for cls in ont.classes:
    if cls.is_named():
        print("cls:", cls.uri)
        for s, p, o in cls.triples:
            print(s, p, o)

        print("parents")
        for parent in cls.children:
            print(parent.uri)

print("loading iao")
ont.load(location="https://information-artifact-ontology.googlecode.com/svn/releases/2011-08-04/merged/iao.owl")

for cls in ont.classes:
    if cls.is_named():
        print("cls:", cls.uri)
        for s, p, o in cls.triples:
            print(s, p, o)

print("loading dron")
ont.load(location="http://purl.obolibrary.org/obo/dron.owl")
print("dron loaded")
