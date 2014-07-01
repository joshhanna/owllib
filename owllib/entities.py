import rdflib
from rdflib import RDF, RDFS, OWL, Literal


class Entity:
    def __init__(self, uri=None, ontology=None, labels=None, comments=None, definitions=None):
        if not uri:
            uri = rdflib.BNode

        self.uri = uri
        self.ontology = ontology
        if ontology:
            self.annotations = self.ontology.get_annotations(self)
            self.labels = self.ontology.get_labels(self)
            self.comments = self.ontology.get_comments(self)
            self.definitions = self.ontology.get_definitions(self)
        else:
            self.annotations = set()
            if labels:
                self.labels = labels
            else:
                self.labels = set()

            if comments:
                self.comments = comments
            else:
                self.comments = set()

            if definitions:
                self.definitions = definitions
            else:
                self.definitions = set()

            self.triples = set()


class Class(Entity):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(Class, self).__init__(uri, ontology, labels, comments)

class Individual(Entity):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(Individual, self).__init__(uri, ontology, labels, comments)

class Property(Entity):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(Property, self).__init__(uri, ontology, labels, comments)

class ObjectProperty(Property):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(ObjectProperty, self).__init__(uri, ontology, labels, comments)

class DataProperty(Property):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(DataProperty, self).__init__(uri, ontology, labels, comments)

class AnnotationProperty(Property):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(AnnotationProperty, self).__init__(uri, ontology, labels, comments)
