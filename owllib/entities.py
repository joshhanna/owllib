import rdflib
from rdflib import RDF, RDFS, OWL, Literal


class Entity:
    """
    base class for all owllib entities, e.g. classes, individuals, object properties
    """
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
        """
        makes the entity match the representation in the ontology
        :return:
        """
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
        """
        makes the ontology representation match the entity
        :return:
        """
        self.ontology.sync_entity_to_graph(self)

    def _get_parents(self):
        raise NotImplementedError

    def _get_children(self):
        raise NotImplementedError

    def is_named(self):
        """
        returns true of the uri of the entity is not a bnode
        :return:
        """
        return isinstance(self.uri, rdflib.URIRef)


class Class(Entity):
    """
    Represents an OWL2 Class
    """
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(Class, self).__init__(uri, ontology, labels, comments)

    def _get_parents(self):
        """
        raises an error if there is no ontology associated; otherwise, returns all classes that this is a
        'rdfs:subClassOf'
        :return:
        """
        if not self.ontology:
            raise ValueError("No associated ontology.")

        return self.ontology.get_super_classes(self)

    def _get_children(self):
        """
        raises an error if there is no ontology associated; otherwise, returns all classes that are a 'rdfs:subClassOf'
        this class
        :return:
        """
        if not self.ontology:
            raise ValueError("No associated ontology.")

        return self.ontology.get_sub_classes(self)


class Individual(Entity):
    """
    represents an OWL2 individual
    """
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(Individual, self).__init__(uri, ontology, labels, comments)

    def _get_parents(self):
        """
        raises an error if there is no ontology associated; otherwise, returns all classes that this is a 'rdf:type' of
        :return:
        """
        if not self.ontology:
            raise ValueError("No associated ontology.")

        return self.ontology.get_individual_type(self)

    def _get_children(self):
        """
        individuals cannot have children, so this returns an empty set
        :return:
        """
        return set()


class Property(Entity):
    """
    base class for the three property types in OWL
    """
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(Property, self).__init__(uri, ontology, labels, comments)

    def _get_parents(self):
        """
        raises an error if there is no ontology associated; otherwise, returns all properties that this is a
        'rdfs:subPropertyOf'
        :return:
        """
        if not self.ontology:
            raise ValueError("No associated ontology.")

        return self.ontology.get_super_properties(self)

    def _get_children(self):
        """
      raises an error if there is no ontology associated; otherwise, returns all properties that are a
      'rdfs:subPropertyOf' this property
      :return:
      """
        if not self.ontology:
            raise ValueError("No associated ontology.")

        return self.ontology.get_sub_properties(self)


class ObjectProperty(Property):
    """
    represents a OWL ObjectProperty
    """
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(ObjectProperty, self).__init__(uri, ontology, labels, comments)


class DataProperty(Property):
    """
    represents a OWL DataProperty
    """
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(DataProperty, self).__init__(uri, ontology, labels, comments)


class AnnotationProperty(Property):
    """
    represents a OWL AnnotationProperty
    """
    def __init__(self, uri=None, ontology=None, labels=None, comments=None):
        super(AnnotationProperty, self).__init__(uri, ontology, labels, comments)

