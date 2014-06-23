from rdflib import Graph, RDF, RDFS, OWL, BNode, URIRef
import urllib.request as url

from owllib.entities import *


class Ontology:
    """
    A class representing an Ontology
    """

    def __init__(self, location=None, uri=None, version_uri=None, imports=None):
        self._graph = Graph()

        if location:
            self._graph.parse(location, format=rdflib.util.guess_format(location))
            self.uri = [uri for uri in self._graph.subjects(RDF.type, OWL.Ontology)][0]

        if not uri and not location:
            self.uri = BNode()

        self._graph.add((self.uri, RDF.type, OWL.Ontology))

        if version_uri:
            self._graph.add((uri, OWL.versionIRI, version_uri))

        if imports:
            import_uris = [an_import.uri for an_import in imports]

            for uri in import_uris:
                self._graph.add((uri, OWL.imports, uri))

        self.classes = self._load_classes()
        self.individuals = self._load_individuals()
        self.object_properties = self._load_object_properties()
        self.annotation_properties = self._load_object_properties()
        self.data_properties = self._load_data_properties()
        self.individuals = self._load_individuals()

    def _load_classes(self):
        uris = [uri for uri in self._graph.subjects(RDF.type, OWL.Class)]

        entities = []

        for uri in uris:
            entities.append(Class(uri=uri, ontology=self))

        return entities

    def _load_individuals(self):
        #getting everything explicitly typed as a NamedIndividual
        uris = [uri for uri in self._graph.subjects(RDF.type, OWL.NamedIndividual)]

        entities = []

        for uri in uris:
            entities.append(Individual(uri=uri, ontology=self))

        return entities

    def _load_object_properties(self):
        uris = [uri for uri in self._graph.subjects(RDF.type, OWL.ObjectProperty)]

        entities = []

        for uri in uris:
            entities.append(ObjectProperty(uri=uri, ontology=self))

        return entities


    def _load_annotation_properties(self):
        uris = [uri for uri in self._graph.subjects(RDF.type, OWL.AnnotationProperty)]

        entities = []

        for uri in uris:
            entities.append(AnnotationProperty(uri=uri, ontology=self))

        return entities

    def _load_data_properties(self):
        uris = [uri for uri in self._graph.subjects(RDF.type, OWL.DatatypeProperty)]

        entities = []

        for uri in uris:
            entities.append(DataProperty(uri=uri, ontology=self))

        return entities

    def exists(self, uri):
        graph = self._graph

        uris = set(graph.subjects()).union(graph.predicates()).union(graph.objects())

        if uri in uris:
            return True
        else:
            return False

    def convert(self, entity):

        """
        Converts an rdflib item to an owllib item, if it exists in the ontology.  return owllib items unchanged (should be idempotent)
        :param entity:
        :param graph:
        :return:
        """

        #check if entity is already an owllib type
        if isinstance(entity, Class):
            return entity
        if isinstance(entity, Individual):
            return entity
        if isinstance(entity, ObjectProperty):
            return entity
        if isinstance(entity, AnnotationProperty):
            return entity
        if isinstance(entity, Literal):
            return entity
        if isinstance(entity, DataProperty):
            return entity

        #return rdflib Literal as-is
        if isinstance(entity, rdflib.Literal):
            return entity

        #convert URI or BNode to class, individual, or property
        if isinstance(entity, URIRef) or isinstance(entity, BNode):
            if not self.exists(entity):
                raise ValueError("URI not found in ontology.")

            for cls in self.classes:
                if entity == cls.uri:
                    return cls

            for prop in self.object_properties:
                if entity == prop.uri:
                    return prop

            for prop in self.annotation_properties:
                if entity == prop.uri:
                    return prop

            for prop in self.object_properties:
                if entity == prop.uri:
                    return prop

            for indiv in self.individuals:
                    if entity == indiv.uri:
                        return indiv

    def get_annotations(self, entity):

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        tuples = [(pred, obj) for (pred, obj) in self._graph.predicate_objects(entity.uri)]

        annotations = []

        for prop, obj in tuples:
            if prop in self._graph.subjects(RDF.type, OWL.AnnotationProperty):
                annotations.append(Annotation(source=self, prop=prop, target=obj))

        return annotations

    def get_labels(self, entity):

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        labels = [obj for obj in self._graph.objects(entity.uri, RDFS.label)]

        return labels

    def get_comments(self, entity):

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        comments = [obj for obj in self._graph.objects(entity.uri, RDFS.comment)]

        return comments

    def get_definitions(self, entity):

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        definitions = [obj for obj in self._graph.objects(entity.uri, URIRef("http://purl.obolibrary.org/obo/IAO_0000115"))]

        return definitions


