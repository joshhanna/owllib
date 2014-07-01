import rdflib
from rdflib import RDF, RDFS, OWL, Literal


class Entity:
    def __init__(self, uri=None, ontology=None, labels=None, comments=None, definitions=None):
        if not uri:
            uri = rdflib.BNode

        self.uri = uri
        self.ontology = ontology

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
        self.parents = set()
        self.children = set()

    def sync_from_ontology(self):
        if not self.ontology:
            raise ValueError("No associated ontology.")

        self.annotations = self.ontology.get_annotations(self)
        self.labels = self.ontology.get_labels(self)
        self.comments = self.ontology.get_comments(self)
        self.definitions = self.ontology.get_definitions(self)
        self.triples = self.ontology.get_triples(self)
        self.parents = self._get_parents()
        self.children = self._get_children()

    def sync_to_ontology(self):
        self.ontology.sync_entity_to_graph(self)

    def _get_parents(self):
        raise NotImplementedError

    def _get_children(self):
        raise NotImplementedError

    def is_named(self):
        return isinstance(self.uri, rdflib.URIRef)


class Class(Entity):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(Class, self).__init__(uri, ontology, labels, comments)

    def _get_parents(self):
        if not self.ontology:
            raise ValueError("No associated ontology.")

        return self.ontology.get_super_classes(self)

    def _get_children(self):
        if not self.ontology:
            raise ValueError("No associated ontology.")

        return self.ontology.get_sub_classes(self)


class Individual(Entity):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(Individual, self).__init__(uri, ontology, labels, comments)

    def _get_parents(self):
        if not self.ontology:
            raise ValueError("No associated ontology.")

        return self.ontology.get_individual_type(self)

    def _get_children(self):
        return set()


class Property(Entity):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(Property, self).__init__(uri, ontology, labels, comments)

    def _get_parents(self):
        if not self.ontology:
            raise ValueError("No associated ontology.")

        return self.ontology.get_super_properties(self)

    def _get_children(self):
        if not self.ontology:
            raise ValueError("No associated ontology.")

        return self.ontology.get_sub_properties(self)


class ObjectProperty(Property):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(ObjectProperty, self).__init__(uri, ontology, labels, comments)


class DataProperty(Property):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(DataProperty, self).__init__(uri, ontology, labels, comments)


class AnnotationProperty(Property):
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(AnnotationProperty, self).__init__(uri, ontology, labels, comments)

