""" The module L{geo.osm_import} provides the OSM data representation of the MoSP-GeoTool.
It is responsible for the import and storage of the different OSM objects.
@author: C. Protsch
"""

from app.partition import PartitionFinder
from bintrees.avltree import AVLTree
#from data_structures.pr_quadtree import PRQuadtree
from geo.geo_utils import is_area, create_node_box
from imposm_mod.parser import OSMParser
from math import floor
from pyproj import Proj
from rtree import index
import datetime

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

def long_to_zone(lon):
    """Calculates the current UTM-zone for a given longitude."""
    return floor((lon + 180.0) / 6) + 1


class Node(object):
    """ The class Node is the data representation of an OSM node within the MoSP-GeoTool.
    
    The class provides methods to read and write the properties of the Node objects.
    """
    def __init__(self, osm_id=None, lon=None, lat=None, tags=None, attr=None, osm_object=None):
        """
	        
        @param osm_id: the OSM ID of the OSM node
        @param lon: geographic longitude of the OSM node
        @param lat: geographic latitude of the OSM node
        @param tags: dictionary of OSM tag key/value pairs
        @param attr: dictionary of OSM attribute key/value pairs
        @param osm_object: instance of the OSM data representation
        """
        self.__id = osm_id	#: OSM ID of the Node object
        self.__lon = lon #: geographic longitude of the Node object
        self.__lat = lat #: geographic latitude of the Node object
        if tags:
            self.__tags = tags #: dictionary of OSM tags as key/value pairs
        else:
            self.__tags = {}
        if attr:
            self.__attr = attr #: dictionary of OSM attributes as key/value pairs
        else:
            self.__attr = {}
        self.__osm_object = osm_object #: stores a reference to the OSM data representation
        
        self.__neighbours = []	#: C{list} of Node objects which are connected with the node by a street
        
        self.__partition_id = 0 #: partition id of the Node object
        # 0: no partition
        # -1: part of a filtered street
        # >= 1: 'normal' partition
        
        self.__filtered = False #: stores if the node belongs to a filtered street
        
        self.__poi = 0	#: stores if the node has been selected as poi or if it was successfully connected with the street network
    
    def getID(self):
        """ Returns the OSM ID of Node object
        
        @returns: the OSM ID of Node object
        @rtype: C{int}
        """
        return self.__id
    node_id = property(getID, None, None, 'read-only property for the OSM ID of Node object')
    
    def setTag(self, tags):
        """ Sets the OSM tag key/value pairs of the Node object
        
        @type tags: dictionary
        @param tags: dictionary of OSM attributes as key/value pairs
        """
        self.__tags = tags

    def getLon(self):
        """ Returns the geographic longitude of the Node object
        
        @returns: the geographic longitude of the Node object
        @rtype: C{float}
        """
        return self.__lon
    lon = property(getLon, None, None, 'read-only property for the geographic longitude of the Node object')

    def getLat(self):
        """ Returns the geographic latitude of the Node object
        
        @returns: the geographic latitude of the Node object
        @rtype: C{float}
        """
        return self.__lat    
    lat = property(getLat, None, None, 'read-only property for the geographic latitude of the Node object')
    
    def get_x_utm(self):
        """ Returns the geodetic x coordinate in UTM projection
        
        @returns: the geodetic x coordinate in UTM projection
        @rtype: C{float}
        """
        return self.get_xy_utm()[0]

    def get_y_utm(self):
        """ Returns the geodetic y coordinate in UTM projection
        
        @returns: the geodetic y coordinate in UTM projection
        @rtype: C{float}
        """
        return self.get_xy_utm()[1]
    
    def getX(self):
        """ Returns the geodetic x coordinate in epsg:3857-projection
        
        @returns: the geodetic x coordinate in epsg:3857-projection
        @rtype: C{float}
        """
        return self.get_xy()[0]
    x = property(getX, None, None, 'read-only property for the geodetic x coordinate in epsg:3857-projection')

    def getY(self):
        """ Returns the geodetic y coordinate in epsg:3857-projection
        
        @returns: the geodetic y coordinate in epsg:3857-projection
        @rtype: C{float}
        """
        return self.get_xy()[1]
    y = property(getY, None, None, 'read-only property for the geodetic y coordinate in epsg:3857-projection')

    def get_xy(self):
        """ Returns the geodetic x and y coordinates in epsg:3857-projection as a tuple
        
        @returns: the geodetic x and y coordinates in epsg:3857-projection as a tuple
        @rtype: (C{float}, C{float})
        """
        return self.__osm_object.get_osm_projection()(self.__lon, self.__lat)
    
    def get_xy_utm(self):
        """ Returns the geodetic x and y coordinates in UTM projection as a tuple
        
        @returns: the geodetic x and y coordinates in UTM projection as a tuple
        @rtype: (C{float}, C{float})
        """
        return self.__osm_object.get_utm_projection()(self.__lon, self.__lat)
    
    def getTags(self):
        """ Returns the OSM tag key/value pairs of the Node object
        
        @returns: the OSM tag key/value pairs of the Node object as a dictionary
        @rtype: C{dict}
        """
        return self.__tags
    
    def getNeighbours(self):
        """ Returns the neighbours of the Node object 
        
        @returns: the neighbours of the Node object as a list
        @rtype: C{list} of Node obejcts
        """
        return self.__neighbours
    neighbours = property(getNeighbours, None, None, 'read-only property for the neighbours of the Node object')

    def delete_neighbours(self):
        """ Clears the list of neighboured Node objects        
        """
        self.__neighbours = []
        
        # A node without neighbours is a single node and is not part of a street.
        # Therefore, it is not part of a partition.
        self.__partition_id = 0
    
    def getAttributes(self):
        """ Returns the OSM attribute key/value pairs of the Node object
        
        @returns: the OSM attribute key/value pairs of the Node object as a dictionary
        @rtype: C{dict}
        """
        return self.__attr
    attributes = property(getAttributes, None, None, 'read-only property for the OSM attribute key/value pairs of the Node object')
    
    def get_poi(self):
        """ Returns the poi state of the Node object 
        
        POI_SELECETED = 1, POI_CONNECTED = 2, POI_NOT_CONNECTED = 4
        
        @returns: the poi state of the Node object 
        @rtype: C{int}
        """
        return self.__poi
    
    def set_poi(self, state):
        """ Sets the poi state of the Node object
        
        POI_SELECETED = 1, POI_CONNECTED = 2, POI_NOT_CONNECTED = 4
        
        @type state: C{int}
        @param state: the poi state of the Node object
        """
        self.__poi = state
        
        # also add the information 'node is a poi' to the OSM data representation
        self.__osm_object.add_poi(self)
    
    def get_partition_id(self):
        """ Returns the partition ID of the Node object
        
        @returns: the partition ID of the Node object
        @rtype: C{int}
        """
        return self.__partition_id
    def set_partition_id(self, partition_id):
        """ Sets the partition ID of the Node object
        
        @type partition_id: C{int}
        @param partition_id: partition ID of the Node object
        """
        self.__partition_id = partition_id
    partition_id = property(get_partition_id, set_partition_id, None, 'read/write-property for the partition ID of the Node object')
    
    def get_filtered(self):
        """ Returns the information if the Node is part of a filtered street
        
        @returns: C{True} if the Node is part of a filtered street
        @rtype: C{bool}
        """
        return self.__filtered
    def set_filtered(self, state):
        """ Sets the information if the Node is part of a filtered street
        
        @type state: C{bool}
        @param state: C{True} if the Node is part of a filtered street
        """
        self.__filtered = state
    filtered = property(get_filtered, set_filtered, None, 'read/write-property for the information if the Node is part of a filtered street')
    
    def __str__(self):
        return '%i %s %f %f %s' % (self.__id, self.__tags,
                                   self.__lon, self.__lat,
                                   self.__attr)


class Way(object):
    """ The class Way is the data representation of an OSM way within the MoSP-GeoTool.
    
    The class provides methods to read and write the properties of the Way objects.
    """    
    def __init__(self, osm_id, nodes=None, tags=None, attr=None, node_avl=None):
        """
 
        @param osm_id: the OSM ID of the OSM way
        @param nodes: C{list} of OSM IDs of the referencing nodes
        @param tags: dictionary of OSM tag key/value pairs
        @param attr: dictionary of OSM attribute key/value pairs
        @param node_avl: instance of the AVL tree that stores the node objects
        """
        self.__id = osm_id
        if nodes:
            self.__nodes = nodes #: C{list} of OSM IDs of the referencing nodes
        else:
            self.__nodes = []
        if tags:
            self.__tags = tags #: dictionary of OSM tag key/value pairs
        else:
            self.__tags = {}
        if attr:
            self.__attr = attr #: dictionary of OSM attribute key/value pairs
        else:
            self.__attr = {}
        self.__node_objects = [] #: C{list} of the referencing L{Node} objects
        
        self.__partition_id = 0 #: partition ID of the Way object
        # 0: no partition
        # -1: filtered street
        # >= 1: 'normal' partition
        
        self.__filtered = False #: stores if the street has been filtered

        self.__generalized = {} #: C{dict} with tolerance values as keys and the generalized node lists as values. When a line generalization of a street is performed, the tolerance value and the resulting node list is added to the dictionary.
        
        # emulate infinite
        self.__min_lon = self.__min_lat = 1e400
        self.__max_lon = self.__max_lat = -1e400
        
        last_node = None
        for node_id in nodes:
            osm_node = node_avl.get(node_id)
            
            # find the bounding box of the way
            if osm_node.lon < self.__min_lon:
                self.__min_lon = osm_node.lon
            if osm_node.lon > self.__max_lon:
                self.__max_lon = osm_node.lon
            if osm_node.lat < self.__min_lat:
                self.__min_lat = osm_node.lat
            if osm_node.lat > self.__max_lat:
                self.__max_lat = osm_node.lat
            
            # build the list of referencing Node objects
            self.__node_objects.append(osm_node)
            
            # we don't need neighbour information if the way isn't a street
            # find the neighbours for streets only
            if 'highway' in tags and last_node:
                osm_node.neighbours.append(last_node)
                last_node.neighbours.append(osm_node)
            last_node = osm_node
        
        self.__box = [self.__min_lon, self.__min_lat, self.__max_lon, self.__max_lat] #: bounding box of the Way object
                
    def getID(self):
        """ Returns the OSM ID of Way object
        
        @returns: the OSM ID of Way object
        @rtype: C{int}
        """
        return self.__id
    
    def getNodeIDs(self):
        """ Returns a list of the OSM IDs of the referencing OSM nodes
        
        @returns: a list of the OSM IDs of the referencing OSM nodes
        @rtype: C{list} of C{int}
        """
        return self.__nodes
    nodeIDs = property(getNodeIDs, None, None, 'read-only property for a list of the OSM IDs of the referencing OSM nodes')
    
    def getNodes(self):
        """ Returns a list of the referencing L{Node} objects
        
        @returns: a list of the referencing L{Node} objects
        @rtype: C{list} of L{Node}
        """
        return self.__node_objects
    nodes = property(getNodes, None, None, 'read-only property for a list of the referencing L{Node} objects')
    
    def setNodes(self, nodes):
        """ Sets a list of the OSM IDs of the referencing OSM nodes
        
        @param nodes: a list of the OSM IDs of the referencing OSM nodes
        """
        self.__nodes = nodes
        
    def getTags(self):
        """ Returns the OSM tag key/value pairs of the Way object
        
        @returns: the OSM tag key/value pairs of the Way object as a dictionary
        @rtype: C{dict}
        """
        return self.__tags
    
    def getBox(self):
        """ Returns the bounding box of the Way object
        
        [min_lon, min_lat, max_lon, max_lat]
        
        @returns: the bounding box of the Way object
	@rtype: [min_lon, min_lat, max_lon, max_lat]
        """
        return self.__box
    box = property(getBox, None, None, 'read-only property for the bounding box of the Way object')
    
    def getAttributes(self):
        """ Returns the OSM attribute key/value pairs of the Way object
        
        @returns: the OSM attribute key/value pairs of the Way object as a dictionary
        @rtype: C{dict}
        """
        return self.__attr
    attributes = property(getAttributes, None, None, 'read-only property for the OSM attribute key/value pairs of the Way object')
    
    def getGeneralized(self):
        """ Returns a dictionary with tolerance values as keys and the generalized node lists as values
        
        @returns: a dictionary with tolerance values as keys and the generalized node lists as values
        @rtype: C{dict}
        """
        return self.__generalized
    generalized = property(getGeneralized, None, None, 'read-only property for a dictionary with tolerance values as keys and the generalized node lists as values')

    def get_partition_id(self):
        """ Returns the partition ID of the Way object
        
        @returns: the partition ID of the Way object
        @rtype: C{int}
        """
        return self.__partition_id
    def set_partition_id(self, partition_id):
        """ Sets the partition ID of the Way object
        
        @type partition_id: C{int}
        @param partition_id: partition ID of the Way object
        """
        self.__partition_id = partition_id
    partition_id = property(get_partition_id, set_partition_id, None, 'read/write-property for the partition ID of the Way object')

    def get_filtered(self):
        """ Returns the information if the street has been filtered
        
        @returns: C{True} if the street has been filtered
        @rtype: C{bool}
        """
        return self.__filtered
    def set_filtered(self, state):
        """ Sets the information if the street has been filtered
        
        @type state: C{bool}
        @param state: C{True} if the street has been filtered
        """
        self.__filtered = state
    filtered = property(get_filtered, set_filtered, None, 'read/write-property for the information if the street has been filtered')
    
    def apply_generalization(self, tolerance):
        """ Applies the line generalization with the given tolerance value.
        
        All streets are replaced by their generalized version. All other previously performed generalizations are deleted.

        @param tolerance: tolerance value of a generalization in meters
        """
        if tolerance in self.__generalized:
            
            # recalculate the neighbours
            original_set = set(self.__node_objects)
            generalized_set = set(self.__generalized[tolerance])
            # original - generalized
            # = nodes that aren't part of the street anymore 
            original_set.difference_update(generalized_set)
            for node in original_set:
                assert(len(node.neighbours) == 2)
                # the neighbours of the generalized node
                # are now neighbours of each other
                node.neighbours[0].neighbours.append(node.neighbours[1])
                node.neighbours[1].neighbours.append(node.neighbours[0])
                # the generalized node is not a neighbour anymore
                node.neighbours[0].neighbours.remove(node)
                node.neighbours[1].neighbours.remove(node)
                # remove the neighbour information from the generalized node
                node.delete_neighbours()
            
            # build the node lists of the generalized street
            self.__node_objects = []
            self.__nodes = []
            for node in self.__generalized[tolerance]:
                self.__node_objects.append(node)
                self.__nodes.append(node.node_id)
                
            # delete all generalizations
            self.__generalized = {}
    
    def insert_node(self, segment_start, segment_end, node):
        """ Inserts a new node between two exisiting nodes of a street
        
        @type segment_start: L{Node} 
        @param segment_start: the new node is inserted after this node
        @type segment_end: L{Node}
        @param segment_end: the new node is inserted before this node
        @type node: L{Node}
        @param node: OSM Node object that is inserted
        """
        index_start = self.__nodes.index(segment_start.node_id)
        index_end = self.__nodes.index(segment_end.node_id,1)
        
        # the method tests if the street nodes are neighbours
        # (you cannot insert a node between two nodes if they aren't neighbours)
        # the calling method has to choose the correct nodes for its own!
        assert(index_start == self.__node_objects.index(segment_start) and
               index_end == self.__node_objects.index(segment_end,1) and
               index_start == index_end - 1)
        
        # update the node id list
        self.__nodes.insert(index_end, node.node_id)
        # update the node object list
        self.__node_objects.insert(index_end, node)
        
        # recalculate the neighbours
        segment_start.neighbours.remove(segment_end)
        segment_start.neighbours.append(node)
        segment_end.neighbours.remove(segment_start)
        segment_end.neighbours.append(node)
        node.neighbours.extend([segment_start, segment_end])
        

    def connected(self, other):
        """ Checks if two Way objects are connected with each other
        
        @type other: L{Way}
        @param other: OSM Way object
        @returns: C{True} if the streets are connected
        @rtype: C{bool}
        """
        # check if at least one node_id of one way
        # is in the node-list of another way
        for node_id in self.__nodes:
            if node_id in other.nodes:
                return True
        return False
    
    def __str__(self):
        return '%s %s %s %s' % (self.__id, self.__tags, self.__nodes, self.__attr)
    
class OSM_objects(object):
    """ The class OSM_objects is the OSM data representation of the MoSP-GeoTool.
    
    The class provides methods and data structures to create, delete and store OSM objects.
    """
    def __init__(self, infile):
        """
        
        @param infile: path to the OSM-file
        """
        
        self.__infile = infile	#: path to the OSM-file
        
        # raw data received from the callback functions
        self.__imported_bounds = [] #: stores the bounding box as given in the OSM file as a list [min_lon, min_lat, max_lon, max_lat]
        self.__nodes = []
        self.__ways = []
        self.__relations = {}
        

        self.__parser_object = OSMParser(bounds_callback=self.__receive_bounds,
                                         nodes_callback=self.__receive_nodes,
                                         ways_callback=self.__receive_ways,
                                         relations_callback=self.__receive_relations) #: stores the instance of an OSMParser-object

        self.__min_lon = self.__min_lat = 1e400
        self.__max_lon = self.__max_lat = -1e400
        self.__calculated_bounds = [] #: stores the bounding box as it is calculated during the creation of the L{geo.osm_import.Way} objects as a list [min_lon, min_lat, max_lon, max_lat]
        
        #self.__node_tree = None
        self.__node_avl = AVLTree() #: instance of AVL-tree-object that stores L{Node} objects
        
        self.__street_tree = index.Index(properties=index.Property()) #: instance of R-tree-object that stores L{geo.osm_import.Way} objects that are tagged as streets
        self.__building_tree = index.Index(properties=index.Property()) #: instance of R-tree-object that stores L{geo.osm_import.Way} objects that are tagged as buildings
        self.__way_delete = [] # way objects that are tagged as deleted, only needed for a complete export
        self.__other_ways = [] # all other way objects that aren't streets, buildings or deleted, only needed for a complete export
        self.__way_avl = AVLTree() #: instance of AVL-tree-object that stores L{Way} objects
        
        self.__poi = set() #: stores a set of L{Node} objects that are selected as POI
        self.__generalized = set() #: stores the tolerance values of previously performed generalizations as a set 
        self.__partitions = None #: stores an instance of an L{app.partition.PartitionFinder} object
        

    #def getNodeTree(self):
    #    return self.__node_tree
    #node_tree = property(getNodeTree)

    def get_node_objects(self):
        """ Returns a list of all L{Node} objects
        
        @returns: a list of all L{Node} objects
        @rtype: C{list} of L{Node}
        """
        return [node for node in self.__node_avl.values()]
    node_objects = property(get_node_objects, None, None, 'read-only property for a list of all L{Node} objects')

    def getStreetTree(self):
        """ Returns the R-tree-object that stores the streets
        
        @returns: the R-tree-object that stores the streets
        @rtype: C{rtree.index.Index}
         """
        return self.__street_tree
    street_tree = property(getStreetTree, None, None, 'read-only property for the R-tree-object that stores the streets')

    def getBuildingTree(self):
        """ Returns the R-tree-object that stores the buildings
        
        @returns: the R-tree-object that stores the buildings
        @rtype: C{rtree.index.Index}
        """
        return self.__building_tree
    building_tree = property(getBuildingTree, None, None, 'read-only property for the R-tree-object that stores the buildings')
    
    def get_other_ways(self):
        """ Returns a list of L{Way} objects that are neither streets nor buildings
        
        @returns: a list of L{Way} objects that are neither streets nor buildings
        @rtype: C{list} of L{Way}
        """
        return self.__other_ways
    
    def get_relations(self):
        """ Returns a dictionary with osm_id as key and raw representation of a relation as it was imported as value
        
        @returns: {osm_id1:relation1, osm_id2:relation2, ...}
        @rtype: C{dictionary}
        """
        return self.__relations
    
    def getWayByID(self, index):
        """ Gets for an given OSM id the corresponding L{Way} object
        
        @type index: C{int}
        @param index: OSM id
        @returns: corresponding L{Way} object, C{None} if there is no such object
        @rtype: L{Way}
        """
        return self.__way_avl.get(index)
    
    def getWayDelete(self):
        """ Gets the OSM ways that are marked as 'deleted' in the original OSM file
        
        @returns: a list of OSM ids that belong to deleted ways
        @rtype: C{list} of C{int}
        """
        return self.__way_delete
    way_delete = property(getWayDelete, None, None, 'read-only property for the OSM ways that are marked as "deleted" in the original OSM file')
    
    def getBox(self):
        """ Returns the calculated bounding box of the OSM data representation
        
        @returns: the calculated bounding box of the OSM data representation
        @rtype: C{[min_lon, min_lat, max_lon, max_lat]}
        """
        return self.__calculated_bounds
    box = property(getBox, None, None, 'read-only property for the calculated bounding box of the OSM data representation')
    
    def getBounds(self):
        """ Returns the imported bounding box of the OSM data representation
        
        @returns: the imported bounding box of the OSM data representation
        @rtype: C{[min_lon, min_lat, max_lon, max_lat]}
        """
        return self.__imported_bounds
    bounds = property(getBounds, None, None, 'read-only property for the imported bounding box of the OSM data representation')

    def add_poi(self, poi_node):
        """ Adds a L{Node} object to the set of points of interest
        
        @type poi_node: L{Node}
        @param poi_node: L{Node}
        """
        self.__poi.add(poi_node)
    def get_poi(self):
        """ Returns the set of points of interests
        
        @returns: the set of points of interests
        @rtype: C{set} of L{Node}
        """
        return self.__poi

    def get_generalized(self):
        """ Returns the tolerance values of previously performed generalizations as a set
        
        @returns: the tolerance values of previously performed generalizations as a set
        @rtype: C{set} of C{int}
        """
        return self.__generalized
    generalized = property(get_generalized, None, None, 'read-only property for the tolerance values of previously performed generalizations')
    
    def reset_generalized(self):
        """
        Clears the set of previously performed generalizations
        """
        self.__generalized = set()
        
    def get_utm_projection(self):
        """ Returns an instance of a pyproj.Proj object which uses the UTM projection
        
        @returns: an instance of a pyproj.Proj object which uses the UTM projection
        @rtype: C{pyproj.Proj}
        """
        return self.__utm_projection
    
    def get_osm_projection(self):
        """ Returns an instance of a C{pyproj.Proj} object which uses epsg:3857-projection (the projection of OSM tiles)
        
        @returns: an instance of a C{pyproj.Proj} object which uses epsg:3857-projection
        @rtype: C{pyproj.Proj}
        """
        return self.__osm_projection
    
    def get_adjacent_streets(self, node, threshold):
        """ Returns a list of street objects within the threshold distance to the given node.
        
        A rectangular box with the node as the center is created. The threshold in meters is the distance from the center to the top/left/bottom/right. All street object that lie within this box are returned.
        
        @type node: L{Node}
        @param node: OSM Node object
        @type threshold: C{int}
        @param threshold: distatance in meters
        @returns: a list of street objects
        @rtype: C{list} of L{Way}
        
        """
        box = create_node_box(node, threshold)
        streets = [self.getWayByID(index) for index in self.street_tree.intersection(box, "raw")]
        return streets
        
    def get_partitions(self):
        """ Returns the instance of an L{app.partition.PartitionFinder} object that stores the partitions of the OSM data representation.
        
        @returns: an instance of an L{app.partition.PartitionFinder} object        
        @rtype: L{app.partition.PartitionFinder}
        """
        if not self.__partitions:
            self.__partitions = PartitionFinder(self)
        return self.__partitions

    def recalculate_partitions(self):
        """ Initialized the recalculation of the partitions of the OSM data representation.
        
        Resets all partition information and starts a new partition finding process.
        """
        if not self.__partitions:
            self.__partitions = PartitionFinder(self)
        else:
            self.__partitions.reset_partitions()
            self.__partitions.find_partitions()



    ########################################
    # callback functions of the OSM parser #
    ########################################

    def __receive_bounds(self, bounds):
        """ Callback function of the OSM parser for the bounding box

	Imports the bounding box of the parsed OSM file. 

        @type bounds: [min_lon, min_lat, max_lon, max_lat]
        @param bounds: Bounding box of the OSM file
        """
        self.__imported_bounds = bounds

    def __receive_nodes(self, nodes):
        """ Callback function of the OSM parser for the OSM nodes
        
        Imports the nodes of the parsed OSM file. 'nodes' is a list of node parameters.
        	- node parameter: (osm_id, tags, (lon, lat), attr)
        	- tags: {tag_key1:tag_value1, tag_key2:tag_value2, ...}
        	- attr: {attr_name1:attr_val1, attr_name2:attr_val2, ...}
        
        The method also determines the min/max coordinates of the calculated bounding box. 
        
        @param nodes: list of node parameters
        """
        for node in nodes:
            self.__nodes.append(node)
            osm_id, tags, (lon, lat), attr = node
            
            # find the min/max coordinates to calculate the bounding box
            if lon < self.__min_lon: self.__min_lon = lon
            if lon > self.__max_lon: self.__max_lon = lon
            if lat < self.__min_lat: self.__min_lat = lat
            if lat > self.__max_lat: self.__max_lat = lat  
                
    def __receive_ways(self, ways):
        """ Callback function of the OSM parser for the OSM ways
        
        Imports the ways of the parsed OSM file. 'ways' is a list of way parameters.
        	- way parameter: (osm_id, tags, refs, attr)
        	- tags: {tag_key1:tag_value1, tag_key2:tag_value2, ...}
        	- refs: [ref_id1, ref_id2, ...]
        	- attr: {attr_name1:attr_val1, attr_name2:attr_val2, ...}
        
        @param ways: list of way parameters
        """
        self.__ways.extend(ways)

    def __receive_relations(self, relations):
        """ Callback function of the OSM parser for the OSM relations
 
        Imports the relations of the parsed OSM file. 'relations' is a list of relation parameters.
        	- relation parameter: (osm_id, tags, members, attr)
        	- tags: {tag_key1:tag_value1, tag_key2:tag_value2, ...}
        	- members = [(refID1, type1, role1), (refID2, type2, role2), ...]
        	- attr: {attr_name1:attr_val1, attr_name2:attr_val2, ...}
        
        @param relations: list of relation parameters
        """
        for relation in relations:
            osm_id = relation[0]
            self.__relations.setdefault(osm_id, relation)



    def __create_nodes(self):
        """ Creates the L{Node} objects from the imported node parameters        
        """
        for osm_id, tags, coord, attr in self.__nodes:
            nd = Node(osm_id=osm_id, lon=coord[0], lat=coord[1], tags=tags, attr=attr, osm_object=self)
        
            # insert the created node object into the avl tree
            # osm_id as tree node key and the node object as tree node item
            # used for look up of a node object by its osm_id
            self.__node_avl.insert(osm_id, nd)

    def __create_ways(self):
        """ Creates the L{Way} objects from the imported way parameters
        """
        for osm_id, tags, nodes, attr in self.__ways:
            way = Way(osm_id, nodes, tags, attr, self.__node_avl)
            
            # don't insert ways which are marked as 'deleted' into the r-tree
            # they don't have nodes/coordinates
            if not attr.get('action') == 'delete':
            
                # insert the streets into the R-tree
                if 'highway' in tags:
                    
                    # only the osm_id is inserted
                    # if we insert a way object a copy of the object would be inserted
                    # but we need references!
                    # --> the AVL tree __way_avl is used to look up the way object by its osm_id
                    self.__street_tree.insert(osm_id, way.box, osm_id)
            
                # insert the buildings into th R-tree
                elif tags.get('building') == 'yes':
                    self.__building_tree.insert(osm_id, way.box, osm_id)
            
                # store the ids of the other ways (needed for complete export)
                else:
                    self.__other_ways.append(osm_id)
            
            else:
                # keep the deleted ways for a complete export
                self.__way_delete.append(osm_id)
            
            # insert the created way object into the avl tree
            # osm_id as tree node key and the way object as tree node item
            # used for look up of a way object by its osm_id
            self.__way_avl.insert(osm_id, way)

    def __create_bounds(self):
        """ Creates the calculated bounding box and the C{pyproj.Proj} objects for UTM- and epsg:3857-projection
        """
        self.__calculated_bounds.extend([self.__min_lon, self.__min_lat,
                                         self.__max_lon, self.__max_lat])

        # if there is no bound/bounds element in the imported OSM file
        # use the calculated box as imported box
        if not self.__imported_bounds:
            self.__imported_bounds = self.__calculated_bounds
        
        # determine the utm zone by the left side of the bounding box 
        utm_zone = long_to_zone(self.__min_lon)
        self.__utm_projection = Proj(proj='utm', zone=utm_zone, ellps='WGS84') #: Stores an instance of a C{pyproj.Proj} object which uses UTM projection, the UTM zone is determined by the left side of the calculated bounding box.
        self.__osm_projection = Proj(init='epsg:3857') #: Stores an instance of a C{pyproj.Proj} object which uses epsg:3857-projection (the projection of OSM tiles).

    def insert_new_node(self, lat, lon, tags, attr):
        """ Inserts a new L{Node} object into the OSM data representation
        
        @param lat: Geographic latitude of the new node
        @param lon: Geographic longitude of the new node
        @param tags: dictionary of OSM tag key/value pairs
        @param attr: dictionary of OSM attribute key/value pairs
        """
        osm_id = self.find_new_key()
        attr.setdefault('version', '1')
        nd = Node(osm_id=osm_id, lon=lon, lat=lat, tags=tags, attr=attr, osm_object=self)
        self.__node_avl.insert(osm_id, nd)
        return nd

    def append_new_street(self, tags, nodes, attr):
        """ Inserts a new L{Way} object into the OSM data representation
        
        @param tags: dictionary of OSM tag key/value pairs
        @param nodes: list of osm_ids of the referencing nodes
        @param attr: dictionary of OSM attribute key/value pairs
        """
        osm_id = self.find_new_key()
        attr.setdefault('version', '1')
        way = Way(osm_id, nodes, tags, attr, self.__node_avl)
        bounding_box = way.box
        self.__street_tree.insert(osm_id, bounding_box, osm_id)
        self.__way_avl.insert(osm_id, way)
        return way

    def delete_way(self, way):
        """ Removes a L{Way} object from the OSM data representation
        
        @type way: L{Way}
        @param way: OSM Way object
        """
        self.__street_tree.delete(way.getID(), way.box)
        self.__way_avl.remove(way.getID())

    def remove_unused_nodes(self):
        """ Removes all L{Node} that are not referenced by any way or relation
        and that don't have tags from the OSM data representation 
        """
        all_nodes = set()
        referenced_nodes = set()
        tagged_nodes = set()
        
        for node in self.node_objects:
            all_nodes.add(node)
            if node.getTags():
                tagged_nodes.add(node)
        
        streets = [self.getWayByID(index) for index in self.street_tree.intersection(self.box, "raw")]
        buildings = [self.getWayByID(index) for index in self.building_tree.intersection(self.box, "raw")]
    
        # look in the streets for references
        for street in streets:
            for node in street.nodes:
                referenced_nodes.add(node)
    
        # look in the buildings for references
        for building in buildings:
            for node in building.nodes:
                referenced_nodes.add(node)
        
        # look in all other way objects for references
        for way_id in self.get_other_ways():
            for node in self.getWayByID(way_id).nodes:
                referenced_nodes.add(node)
        
        # look in the relations for references
        for relation in self.get_relations().itervalues():
            rel_id, rel_tags, rel_members, rel_attributes = relation
            for memb_ref, memb_type, memb_role in rel_members:
                if memb_type == 'node':
                    referenced_nodes.add(self.__node_avl.get(memb_ref))
                    
        print 'total nodes #: %i' % len(all_nodes)
        
        # use the difference of the sets to determine the unused nodes
        unused_nodes = (all_nodes - tagged_nodes) - referenced_nodes
        
        print '%i unused nodes are removed' % len(unused_nodes)
        
        # finally, remove the unused nodes
        for node in unused_nodes:
            self.__node_avl.remove(node.node_id)
    
    def find_new_key(self):
        """ Finds a new unused OSM ID
        
        If there are only positive OSM IDs the new ID will be '-1'.
        If there are already negative OSM IDs the new ID will be the smallest ID so far minus 1
        
        @returns: the new OSM id
        @rtype: C{int} 
        """
        if not self.__relations:
            keys = [self.__node_avl.min_key(),
                    self.__node_avl.max_key(),
                    self.__way_avl.min_key(),
                    self.__way_avl.max_key()]
        else:
            keys = [self.__node_avl.min_key(),
                    self.__node_avl.max_key(),
                    self.__way_avl.min_key(),
                    self.__way_avl.max_key(),
                    min(self.__relations.keys()),
                    max(self.__relations.keys())]
        if min(keys) >= 0:
            osm_id = -1
        else:
            osm_id = min(keys) - 1
        return osm_id



    def parse(self):
        """ Initializes the parsing of the OSM file.
        
        Starts the methods to parse the OSM file, to calculate the bounding box and to create the L{geo.osm_import.Node} and L{geo.osm_import.Way} objects
        """
        # TODO: remove profiling message
        
        self.__parser_object.parse(self.__infile)
        
        self.__create_bounds()
        
        #starttime = datetime.datetime.today()
        #print 'start: %s' % starttime
        self.__create_nodes()
        #finishedtime = datetime.datetime.today()
        #print 'finished: %s' % finishedtime
        #print finishedtime - starttime
        
        self.__create_ways()
        
    

if __name__ == '__main__':
    
    indir = '../data/'
    infile_name = 'hannover2'
    infile = '%s%s.osm' % (indir, infile_name)
    
    starttime = datetime.datetime.today()
    print 'start: %s' % starttime
    
    osm = OSM_objects(infile)
    osm.parse()
    
    finishedtime = datetime.datetime.today()
    print 'finished: %s' % finishedtime
    
    print finishedtime - starttime 
    #print osm.box
    #print osm.getStreetTree().get_bounds()
    buildings = [osm.getWayByID(index) for index in osm.building_tree.intersection(osm.building_tree.get_bounds(), "raw")]
    #print buildings
    for b in buildings:
        if not is_area(b):
            print b
