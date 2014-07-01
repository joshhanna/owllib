from rdflib import Graph, RDF, RDFS, OWL, BNode, URIRef
import urllib.request as url

from owllib.entities import *


class Ontology:
    """
    A class representing an Ontology
    """

    def __init__(self, uri=None, version_uri=None, imports=None):
        self.graph = Graph()

        if not uri:
            self.uri = BNode()

        self.graph.add((self.uri, RDF.type, OWL.Ontology))

        if version_uri:
            self.graph.add((uri, OWL.versionIRI, version_uri))

        if imports:
            import_uris = [an_import.uri for an_import in imports]

            for uri in import_uris:
                self.graph.add((uri, OWL.imports, uri))
            self.direct_imports = imports
            self.indirect_imports = self._load_indirects()
        else:
            self.direct_imports = set()
            self.indirect_imports = set()

        self.classes = set()
        self.individuals = set()
        self.object_properties = set()
        self.annotation_properties = set()
        self.data_properties = set()

    def sync_entity_from_graph(self, entity):
        entity = self.convert(entity)

        if isinstance(entity, Class):
            return Class(uri=entity, ontology=self)
        if isinstance(entity, Individual):
            return Individual(uri=entity, ontology=self)
        if isinstance(entity, ObjectProperty):
            return ObjectProperty(uri=entity, ontology=self)
        if isinstance(entity, AnnotationProperty):
            return AnnotationProperty(uri=entity, ontology=self)
        if isinstance(entity, DataProperty):
            return DataProperty(uri=entity, ontology=self)

    def sync_entity_to_graph(self, entity):
        """
        TODO
        :param entity:
        :return:
        """
        pass

    def sync_to_graph(self):
        for cls in self.classes:
            self.sync_entity_to_graph(cls)
        for indiv in self.individuals:
            self.sync_entity_to_graph(indiv)
        for prop in self.object_properties:
            self.sync_entity_to_graph(prop)
        for prop in self.annotation_properties:
            self.sync_entity_to_graph(prop)
        for prop in self.data_properties:
            self.sync_entity_to_graph(prop)
        for imp in self.direct_imports:
            self.sync_entity_to_graph(imp)

    def sync_from_graph(self):

        self.uri = self._load_uri()

        self.direct_imports = self._load_directs()
        self._consolidate_imports()

        self.indirect_imports = self._load_indirects()

        self.classes = self._load_classes()
        self.individuals = self._load_individuals()
        self.object_properties = self._load_object_properties()
        self.annotation_properties = self._load_object_properties()
        self.data_properties = self._load_data_properties()

    #inefficient, since it loads then discards ontologies
    def _consolidate_imports(self, imports=None):

        if imports and len(self.direct_imports) > 0:
            new_imports = set()

            for imp in imports:
                for direct_import in self.direct_imports:
                    if direct_import.uri == imp.uri and direct_import != imp:
                        new_imports.add(imp)
                    elif direct_import.uri == imp.uri:
                        new_imports.add(direct_import)

            #adding back direct imports that had no analog
            uris = [ont.uri for ont in new_imports]

            for imp in self.direct_imports:
                if imp.uri not in uris:
                    new_imports.add(imp)

            self.direct_imports = new_imports

            imp._consolidate_imports(self.direct_imports | imports)
        else:
            for imp in self.direct_imports:
                imp._consolidate_imports(self.direct_imports)

    def load(self, source=None, publicID=None, format=None,
             location=None, file=None, data=None, **args):

        self.graph = Graph()

        self._parse(source, publicID, format, location, file, data, **args)

        self.sync_from_graph()

    def _parse(self, source=None, publicID=None, format=None,
               location=None, file=None, data=None, **args):

        #first, try rdflib's guess_format
        if location and not format:
            format = rdflib.util.guess_format(location)

        #hacky, hacky, hacky
        try:
            self.graph.parse(source, publicID, format, location, file, data, **args)
        except rdflib.plugin.PluginException:
            #if that failed, try each of them
            formats = ['xml',
                       'turtle',
                       'trix',
                       'rdfa1.1',
                       'rdfa1.0',
                       'rdfa',
                       'nt',
                       'nquads',
                       'n3',
                       'microdata',
                       'mdata',
                       'hturtle',
                       'html']

            for fmt in formats:
                try:
                    self.graph.parse(source, publicID, fmt, location, file, data, **args)
                    return
                except Exception:
                    pass

            #looks like none of them worked
            raise rdflib.plugin.PluginException("No parser plugin found for ontology.")

    def _load_uri(self):
        uris = [uri for uri in self.graph.subjects(RDF.type, OWL.Ontology)]

        #more than one ontology in the file; choosing one with most triples as canonical
        if len(uris) > 1:
            canon_uri = uris[0]
            canon_num = 0
            for uri in uris:
                tuples = [(pred, obj) for (pred, obj) in self.graph.predicate_objects(uri)]
                num = len(tuples)

                if num > canon_num:
                    canon_num = num
                    canon_uri = uri

        elif len(uris) > 0:
            return uris[0]

    def _load_indirects(self):
        indirects = set()

        for ont in self.direct_imports:
            indirects |= ont.indirect_imports | ont.direct_imports

        return indirects

    def _load_directs(self):
        uris = [o for o in self.graph.objects(self.uri, OWL.imports)]

        entities = set()

        for uri in uris:
            ont = Ontology()
            ont.load(location=uri)
            entities.add(ont)

        return entities

    def _load_classes(self):
        uris = [uri for uri in self.graph.subjects(RDF.type, OWL.Class)]

        entities = set()

        for uri in uris:
            entities.add(Class(uri=uri, ontology=self))

        return entities

    def _load_individuals(self):
        #getting everything explicitly typed as a NamedIndividual
        uris = [uri for uri in self.graph.subjects(RDF.type, OWL.NamedIndividual)]

        entities = set()

        for uri in uris:
            entities.add(Individual(uri=uri, ontology=self))

        return entities

    def _load_object_properties(self):
        uris = [uri for uri in self.graph.subjects(RDF.type, OWL.ObjectProperty)]

        entities = set()

        for uri in uris:
            entities.add(ObjectProperty(uri=uri, ontology=self))

        return entities

    def _load_annotation_properties(self):
        uris = [uri for uri in self.graph.subjects(RDF.type, OWL.AnnotationProperty)]

        entities = set()

        for uri in uris:
            entities.add(AnnotationProperty(uri=uri, ontology=self))

        return entities

    def _load_data_properties(self):
        uris = [uri for uri in self.graph.subjects(RDF.type, OWL.DatatypeProperty)]

        entities = set()

        for uri in uris:
            entities.add(DataProperty(uri=uri, ontology=self))

        return entities

    def exists(self, uri):
        graph = self.graph

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
        if isinstance(entity, Ontology):
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

        #looks like we couldn't find anything to convert to
        raise TypeError("Type could not be converted properly.  Found " + type(entity).__name__)

    def get_annotations(self, entity):

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        tuples = [(pred, obj) for (pred, obj) in self.graph.predicate_objects(entity.uri)]

        annotations = set()

        for prop, obj in tuples:
            if prop in self.graph.subjects(RDF.type, OWL.AnnotationProperty):
                annotations.add((prop, obj))

        return annotations

    def get_labels(self, entity):

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        labels = [obj for obj in self.graph.objects(entity.uri, RDFS.label)]

        return set(labels)

    def get_comments(self, entity):

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        comments = [obj for obj in self.graph.objects(entity.uri, RDFS.comment)]

        return set(comments)

    def get_definitions(self, entity):

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        definitions = [obj for obj in self.graph.objects(entity.uri, URIRef("http://purl.obolibrary.org/obo/IAO_0000115"))]

        return set(definitions)


