__author__ = 'joshhanna'

from owllib.ontology import Ontology
from rdflib import URIRef

ont = Ontology("https://bfo.googlecode.com/svn/releases/2014-05-03/owl-group/bfo.owl")

for cls in ont.classes:
    if isinstance(cls.uri, URIRef):
        for comment in cls.definitions:
            print(comment.value)
