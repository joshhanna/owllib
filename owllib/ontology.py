from rdflib import Graph, RDF, RDFS, OWL, BNode, URIRef
import urllib.request as url

from owllib.entities import *


class Ontology:
    """
    A class representing an Ontology
    """

    def __init__(self, uri=None, version_uri=None, imports=None):
        """
        creates a new ontology; to load, use the Ontology.load method
        :param uri:
        :param version_uri:
        :param imports:
        :return:
        """

        self.graph = Graph()

        #if we have no uri, we create a bnode
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

    #read-only properties
    @property
    def entities(self):
        return self.classes | self.individuals | self.properties

    @property
    def properties(self):
        return self.object_properties | self.annotation_properties | self.data_properties

    def sync_entity_to_graph(self, entity):
        """
        removes all triples of the entity, then replaces them with the triples found in the entity instance
        :param entity:
        :return:
        """
        #removing all existing triples for this entity
        to_remove = self.get_triples(entity)

        for triple in to_remove:
            self.graph.remove(triple)

        #adding triples from entity to graph
        to_add = entity.triples

        for triple in to_add:
            self.graph.add(triple)

    def sync_to_graph(self):
        """
        syncs all entities to the graph
        :return:
        """
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
        """
        syncs all entities from the graph
        :return:
        """
        self.uri = self._load_uri()

        self.direct_imports = self._load_directs()
        self._consolidate_imports()

        self.indirect_imports = self._load_indirects()

        self.classes = self._load_classes()
        self.individuals = self._load_individuals()
        self.object_properties = self._load_object_properties()
        self.annotation_properties = self._load_object_properties()
        self.data_properties = self._load_data_properties()

        #TODO very slow for large ontologies; find more efficient way
        #was required because getting sub and super entities did not work without all of them already loaded
        for entity in self.entities:
            entity.sync_from_ontology()

    #inefficient, since it loads then discards ontologies
    def _consolidate_imports(self, imports=None):
        """
        recursively consolidates the imported ontologies such that there is only one of each ontology that shares a uri
        :param imports:
        :return:
        """
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

            #using a 'non-public' call, but it's in this file so I figure it's not too destructive
            imp._consolidate_imports(self.direct_imports | imports)
        else:
            for imp in self.direct_imports:
                imp._consolidate_imports(self.direct_imports)

    def load(self, source=None, publicID=None, format=None,
             location=None, file=None, data=None, **args):
        """
        loads the ontology into the graph.  params are identical to rdflib.Graph.parse
        :param source:
        :param publicID:
        :param format:
        :param location:
        :param file:
        :param data:
        :param args:
        :return:
        """

        self.graph = Graph()

        self._parse(source, publicID, format, location, file, data, **args)

        self.sync_from_graph()

    def _parse(self, source=None, publicID=None, format=None,
               location=None, file=None, data=None, **args):
        """
        parses the ontology using rdflib.Graph.parse().  First, uses rdflib's guess_format, then tries all of them
        :param source:
        :param publicID:
        :param format:
        :param location:
        :param file:
        :param data:
        :param args:
        :return:
        """

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
        """
        loads the ontology uri from the graph; chooses the one with the most triples if there are multiples
        :return:
        """
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
            return canon_uri

        elif len(uris) > 0:
            return uris[0]

    def _load_indirects(self):
        """
        recursively loads all of the imports of any of the direct imports
        :return:
        """
        indirects = set()

        for ont in self.direct_imports:
            indirects |= ont.indirect_imports | ont.direct_imports

        return indirects

    def _load_directs(self):
        """
        loads all of the direct imports, creating ontologies for each of them
        :return:
        """
        uris = [o for o in self.graph.objects(self.uri, OWL.imports)]

        entities = set()

        for uri in uris:
            ont = Ontology()
            ont.load(location=uri)
            entities.add(ont)

        return entities

    def _load_classes(self):
        """
        loads all of the classes in the graph into owllib entities
        :return:
        """
        uris = set(uri for uri in self.graph.subjects(RDF.type, OWL.Class)) \
               | set(uri for uri in self.graph.subjects(RDF.type, OWL.Restriction))

        entities = set()

        for uri in uris:
            entities.add(Class(uri=uri, ontology=self))

        return entities

    def _load_individuals(self):
        """
        loads all of the individuals in the graph into owllib entities
        :return:
        """
        uris = [uri for uri in self.graph.subjects(RDF.type, OWL.NamedIndividual)]

        entities = set()

        for uri in uris:
            entities.add(Individual(uri=uri, ontology=self))

        return entities

    def _load_object_properties(self):
        """
        loads all of the object properties in the graph into owllib entities
        :return:
        """
        uris = [uri for uri in self.graph.subjects(RDF.type, OWL.ObjectProperty)]

        entities = set()

        for uri in uris:
            entities.add(ObjectProperty(uri=uri, ontology=self))

        return entities

    def _load_annotation_properties(self):
        """
        loads all of the annotation properties in the graph into owllib entities
        :return:
        """
        uris = [uri for uri in self.graph.subjects(RDF.type, OWL.AnnotationProperty)]

        entities = set()

        for uri in uris:
            entities.add(AnnotationProperty(uri=uri, ontology=self))

        return entities

    def _load_data_properties(self):
        """
        loads all of the data properties int he graph into owllib entities
        :return:
        """
        uris = [uri for uri in self.graph.subjects(RDF.type, OWL.DatatypeProperty)]

        entities = set()

        for uri in uris:
            entities.add(DataProperty(uri=uri, ontology=self))

        return entities

    def exists(self, uri):
        """
        checks to see if the uri exists in the graph
        :param uri:
        :return:
        """
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
        """
        returns all annotations as tuples for the passed in entity
        :param entity:
        :return:
        """

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        tuples = [(pred, obj) for (pred, obj) in self.graph.predicate_objects(entity.uri)]

        annotations = set()

        for prop, obj in tuples:
            if prop in self.graph.subjects(RDF.type, OWL.AnnotationProperty):
                annotations.add((prop, obj))

        return annotations

    def get_labels(self, entity):
        """
        returns all rdfs:labels for the passed in entity
        :param entity:
        :return:
        """

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        labels = [obj for obj in self.graph.objects(entity.uri, RDFS.label)]

        return set(labels)

    def get_comments(self, entity):
        """
        returns all of the rdfs:comments for the passed in entity
        :param entity:
        :return:
        """

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        comments = [obj for obj in self.graph.objects(entity.uri, RDFS.comment)]

        return set(comments)

    def get_definitions(self, entity):
        """
        returns all of the IAO definitions of the passed in entity
        :param entity:
        :return:
        """

        #if it's a URIRef or similar, convert it to owllib representation
        entity = self.convert(entity)

        definitions = [obj for obj in self.graph.objects(entity.uri, URIRef("http://purl.obolibrary.org/obo/IAO_0000115"))]

        return set(definitions)

    def get_triples(self, entity):
        """
        returns all of the triples for the passed in entity where the entity was a subject, object, or predicate
        :param entity:
        :return:
        """
        entity = self.convert(entity)

        return set(self.graph.triples((entity.uri, None, None))) | set(self.graph.triples((None, entity.uri, None))) | set(self.graph.triples((None, None, entity.uri)))

    def get_super_classes(self, cls):
        """
        returns all of the super classes of :param cls
        :param cls:
        :return:
        """
        cls = self.convert(cls)
        parent_uris = set(self.graph.objects(cls.uri, RDFS.subClassOf))

        parents = [acls for acls in self.classes if acls.uri in parent_uris]

        return set(parents)

    def get_sub_classes(self, cls):
        """
        returns all fo the sub classes of :param cls
        :param cls:
        :return:
        """
        cls = self.convert(cls)
        children_uris = set(self.graph.subjects(RDFS.subClassOf, cls.uri))

        children = [acls for acls in self.classes if acls.uri in children_uris]

        return set(children)

    def get_individual_type(self, indiv):
        """
        returns the type of :param indiv
        :param indiv:
        :return:
        """
        indiv = self.convert(indiv)

        type_uris = set(self.graph.objects(indiv.uri, RDF.type))

        types = [cls for cls in self.classes if cls.uri in type_uris]

        return set(types)

    def get_super_properties(self, prop):
        """
        returns all of the super properties of :param prop
        :param prop:
        :return:
        """
        prop = self.convert(prop)
        parent_uris = set(self.graph.objects(prop.uri, RDFS.subPropertyOf))

        parents = [aprop for aprop in self.properties if aprop.uri in parent_uris]

        return set(parents)

    def get_sub_properties(self, prop):
        """
        returns all of the sub properties of :param prop
        :param prop:
        :return:
        """
        prop = self.convert(prop)
        children_uris = set(self.graph.objects(RDFS.subPropertyOf, prop.uri))

        children = [aprop for aprop in self.properties if aprop.uri in children_uris]

        return set(children)