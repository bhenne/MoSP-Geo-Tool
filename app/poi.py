""" The module C{app.poi} provides methods to connect points of interest with the street network 
@author: C. Protsch
"""

# -*- coding: utf-8 -*-
from geo.geo_utils import get_building_entrance, is_building, \
    distance_point_line, create_node_box, \
    is_inside_polygon, have_same_coords, get_nearest_street, connect_by_node,\
    connect_by_projection, get_nearest_street_node
from globals import DEBUG
#from pyproj import Geod

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

POI_SELECTED = 1	#: used to mark a node as selected
POI_CONNECTED = 2	#: used to mark a node as connected with the street network
POI_NOT_CONNECTED = 4	#: used to mark a node that couldn't be connected with the street network

class Poi(object):
    """ This class provides methods to select points of interest,
    stores the selected nodes and provides methods to
    connect the selected POI with the street network 
    """
    
    def __init__(self, osm_object):
        """
        
    	@type osm_object: L{geo.osm_import.OSM_objects}
    	@param osm_object: The OSM data representation        
        """
        self.__osm_object = osm_object	#: Stores the reference to the OSM data representation
        #self.__geod = Geod(ellps='WGS84')
        #self.__nodes = osm_object.node_tree.region_query(osm_object.box)
        self.__nodes = osm_object.node_objects #: Stores a list of all L{geo.osm_import.Node} objects
        self.__poi_nodes = set() #: Stores a set of the L{geo.osm_import.Node} objects that have been selected as point of interest

    def get_poi(self, items):
        """
        Returns the nodes that have been selected as points of interest
        
        Selected nodes that aren't already part of the street network are marked as POI_selected
        
        @param items: dictionary of key/value pairs that are used to select a poi
        @returns: a set of the selected L{geo.osm_import.Node} objects
        @rtype: C{set} of L{geo.osm_import.Node}
        """
        for (key, value) in items:
            if value == '*':
                self.get_poi_by_key(key)
            else:
                for node in self.__nodes:
                    if node.getTags().get(key) == value:
                        self.__poi_nodes.add(node)
                        if node.get_poi() != POI_CONNECTED:
                            node.set_poi(POI_SELECTED)
        return self.__poi_nodes
                

    def get_poi_by_key(self, key):
        """
        Marks all nodes with a given tag key as points of interest
        
        @param key: the name of a tag key
        """
        for node in self.__nodes:
            if key in node.getTags():
                self.__poi_nodes.add(node)
                if node.get_poi() != POI_CONNECTED:
                    node.set_poi(POI_SELECTED)

    def is_street_node(self, node):
        """
        Checks if a given node is part of a street.
        @type node: L{geo.osm_import.Node}
        @param node: The OSM Node object that is checked
        @return: True, if the node is aprt of a street
        @rtype: C{bool}
        """
        # a node is a street node if it has neighbours
        return node.getNeighbours() != []

    # TODO: nicht benoetigt
    #def get_poi_street_name(self, poi_node):
    #    return poi_node.getTags().get('addr:street')

    def get_street_by_name(self, name, streets):
        """ Looks in a list of streets for streets with the given name
        
        @param name: the street name
        @param streets: a list of streets in which is looked for streets with the given name
        @returns: a list of found streets with the given street name
        @rtype: C{list} of L{geo.osm_import.Way}
        """
        if not name:
            return None
        street_by_name = []
        for street in streets:
            if street.getTags().get('name') == name:
                street_by_name.append(street)
        return street_by_name

    def get_adjacent_buildings(self, node, threshold):
        """ Finds the buildngs that are within a search area around a given L{geo.osm_import.Node} object
        
        @type node: L{geo.osm_import.Node}
        @param node: OSM Node object
        @param threshold: search distance in meters
        @returns: a list of the found buildings
        @rtype: C{list} of L{geo.osm_import.Way}
        """
        box = create_node_box(node, threshold)
        buildings = [self.__osm_object.getWayByID(index) for index in self.__osm_object.building_tree.intersection(box, "raw")]
        return buildings

    def get_nearest_building(self, node, buildings):
        """ Looks in a list of buildings for the building that is closest to a given L{geo.osm_import.Node} object
        
        @type node: L{geo.osm_import.Node}
        @param node: the OSM Node object for which the nearest building is searched
        @param buildings: list of L{geo.osm_import.Way} objects that represent buildings
        @returns: a tuple containing the L{geo.osm_import.Way} object of the nearest building and the distance in meters (building, distance), returns None if no building is found
        @rtype: C{L{geo.osm_import.Way}, float)}
        """
        min_dist = 1e400
        nearest_building = None
        for building in buildings:
            distance = self.distance_poi_building(node, building)
            if distance < min_dist:
                min_dist = distance
                nearest_building = building
        return (nearest_building, min_dist)
    
    def connect_by_building(self, poi_node, building, streets, projection_threshold, address_threshold):
        """ Tries to connect a selected point of interest via a building with the street network
        
        The method checks if the given node lies within a building. It extracts several properties of the building like entrances or the address and tries to connect the node with these parameters to the street network
        
        @type poi_node: L{geo.osm_import.Node}
        @param poi_node: the OSM Node object that shall be connected with the street network
        @type building: L{geo.osm_import.Way}
        @param building: OSM Way object that is a building
        @param streets: list of L{geo.osm_import.Way} objects that are streets
        @param projection_threshold: distance in meters that a connection to the next node may be longer than a direct connection by projection
        @param address_threshold: distance in meters that a connection to a street with a given name may be longer than a direct connection to the next street
        @returns: True if the connection was successful, False otherwise (i. e. the node doesn't lie within the building at all)
        @rtype: C{bool}
        """

        connected = False

        # do nothing if the 'building' isn't a building at all
        # or if the POI isn't inside the building
        if not (is_building(building) and is_inside_polygon(poi_node, building)):
            return False
        
        building_address = building.getTags().get('addr:street')
        building_entrance = get_building_entrance(building)
        poi_address = poi_node.getTags().get('addr:street')
       
        # connect the POI with the entrance if the building has an entrance
        if building_entrance:
            for entrance in building_entrance:
                connect_by_node(self.__osm_object, poi_node, entrance)
                entrance_address = entrance.getTags().get('addr:street')
                # choose the possible connection:
                #connect by entrance address or poi address or building address or directly with the next street 
                if entrance_address:
                    connected = self.connect_by_address(entrance, entrance_address, streets, projection_threshold, address_threshold)
                elif poi_address:
                    connected = self.connect_by_address(entrance, poi_address, streets, projection_threshold, address_threshold)
                elif building_address:
                    connected = self.connect_by_address(entrance, building_address, streets, projection_threshold, address_threshold)
                else:
                    connected = self.connect_with_nearest_street(entrance, streets, projection_threshold)
        
        # if no entrance was found choose the possible connection:
        # connect by poi address or building address or directly with the next street 
        elif poi_address:
            connected = self.connect_by_address(poi_node, poi_address, streets, projection_threshold, address_threshold)
        elif building_address:
            connected = self.connect_by_address(poi_node, building_address, streets, projection_threshold, address_threshold)
        else:
            connected = self.connect_with_nearest_street(poi_node, streets, projection_threshold)
        return connected

    def connect_by_address(self, poi_node, address, streets, projection_threshold, address_threshold):
        """
        Tries to connect a selected point of interest to a street with a given name
        
        @type poi_node: L{geo.osm_import.Node}
        @param poi_node: the OSM Node object that shall be connected with the street network
        @param address: The street name
        @param streets: list of L{geo.osm_import.Way} objects that are streets
        @param projection_threshold: distance in meters that a connection to the next node may be longer than a direct connection by projection
        @param address_threshold: distance in meters that a connection to a street with a given name may be longer than a direct connection to the next street
        @returns: True if the connection was successful, False otherwise
        @rtype: C{bool}
        """
        connected = False
        named_streets = self.get_street_by_name(address, streets)
        if named_streets:
            address_street, address_distance, address_mode = get_nearest_street(poi_node, named_streets)
            nearest_street, nearest_distance, nearest_mode = get_nearest_street(poi_node, streets)
            
            # decide based on the address_threshold whether the poi is connected to the named street or the next street
            if address_distance - nearest_distance < address_threshold:
                connected = self.connect_with_nearest_street(poi_node, named_streets, projection_threshold)
            else:
                connected = self.connect_with_nearest_street(poi_node, streets, projection_threshold)
        
        # if no street with the given address is found connect to the nearest street 
        else:
            connected = self.connect_with_nearest_street(poi_node, streets, projection_threshold)
        return connected

    def distance_poi_building(self, poi_node, building):
        """ Returns the distance between a point of interest and a building 
        
        @type poi_node: L{geo.osm_import.Node}
        @param poi_node: OSM Node object
        @type building: L{geo.osm_import.Way}
        @param building: OSM Way object that is a building
        @returns: the distance in meters
        @rtype: C{float}
        """
        min_dist = 1e400
        bnodes = building.nodes
        for i in range(len(bnodes) - 1):
            distance = distance_point_line(bnodes[i], bnodes[i + 1], poi_node)
            if distance < min_dist:
                min_dist = distance
        return min_dist

    def connect_with_nearest_street(self, poi_node, streets, projection_threshold):
        """ Tries to connect a selected point of interest with the nearest streets
        
        The method looks in a list of streets for the neareast street and connects the poi and this street.
        
        @type poi_node: L{geo.osm_import.Node}
        @param poi_node: the OSM Node object that shall be connected with the street network
        @param streets: list of L{geo.osm_import.Way} objects that are streets
        @param projection_threshold: distance in meters that a connection to the next node may be longer than a direct connection by projection
        @returns: True if the connection was successful, False otherwise
        @rtype: C{bool}
        """
        connected = False
        
        # connection fails if the street list is empty or None
        if not streets:
            return False
        
        nearest_street, street_distance, nearest_mode = get_nearest_street(poi_node, streets)
        
        
        # for explanation of the distance_mode see geo.geo_utils.__distance_point_to_line
        # connect to nearest node if no projection is possible
        if len(nearest_mode) == 1:
            connected = connect_by_node(self.__osm_object, poi_node, nearest_mode[0])
        else:
            nearest_node, node_distance = get_nearest_street_node(poi_node, [nearest_street])
            if node_distance - street_distance < projection_threshold:
                connected = connect_by_node(self.__osm_object, poi_node, nearest_node)
            else:
                connected = connect_by_projection(self.__osm_object, poi_node, nearest_street, nearest_mode)
        return connected        
       
    def connect_poi(self, poi_thresholds):
        """ Initializes the connection of the points of interests with the street network
        
        @param poi_thresholds: a dictionary containing search distance, projection threshold and address threshold { 'search':svalue, 'projection':pvalue, 'address':avalue }
        """
        search_threshold = int(poi_thresholds.get('search'))
        projection_threshold = int(poi_thresholds.get('projection'))
        address_threshold = int(poi_thresholds.get('address'))
        for poi_node in self.__poi_nodes:
            

            # do nothing if the poi is already part of the street network
            if self.is_street_node(poi_node):
                poi_node.set_poi(POI_CONNECTED)
                continue
            
            connected = False
            
            # extract the streets within the search distance
            streets = self.__osm_object.get_adjacent_streets(poi_node, search_threshold)
            
            if streets:
            
                # get the poi address
                poi_address = poi_node.getTags().get('addr:street')
                
                # extract the buildings within the search distance
                buildings = self.get_adjacent_buildings(poi_node, search_threshold)
                
                nearest_building, building_distance = self.get_nearest_building(poi_node, buildings)
                nearest_node, node_distance = get_nearest_street_node(poi_node, streets)
                
                # connect to the nearest node if there is already a street node with the same coordinates
                if have_same_coords(poi_node, nearest_node):
                    connected = connect_by_node(self.__osm_object, poi_node, nearest_node)
                
                # try to conenct in the following order:
                # by building, by street name, with the nearest street
                if not connected:
                    connected = self.connect_by_building(poi_node, nearest_building, streets, projection_threshold, address_threshold)
                if not connected and poi_address:
                    connected = self.connect_by_address(poi_node, poi_address, streets, projection_threshold, address_threshold)
                if not connected:
                    connected = self.connect_with_nearest_street(poi_node, streets, projection_threshold)
            
            # mark a successfully connected poi as connected
            if connected:
                poi_node.set_poi(POI_CONNECTED)
            if not connected:
                print 'nothing found'
                poi_node.set_poi(POI_NOT_CONNECTED)
        # TODO: remove debug message
        if DEBUG:
            print 'ende'
                

if __name__ == '__main__':
    pass
