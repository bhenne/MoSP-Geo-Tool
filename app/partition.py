""" The module C{app.partititon} provides methods to identify, store and connect partitions.
@author: C. Protsch
"""
from geo.geo_utils import distance_node_street, get_nearest_street,\
    connect_by_node, connect_by_projection, get_nearest_street_node, merge_boxes,\
    distance_points
#from geo.osm_import import OSM_objects
from globals import DEBUG
import datetime

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

class PartitionFinder(object):
    """ This class provides methods to identify partitions, it stores the partitions and provides methods to connect the partitions to the street network.
    """

    def __init__(self, osm_object):
        """
        
        @type osm_object: L{geo.osm_import.OSM_objects}
    	@param osm_object: The OSM data representation
        """
        self.__osm_object = osm_object	#: stores the reference to the OSM data representation
        self.__recalculate = False	#: stores if the partitions will be recalculated when they are needed for the next time
        self.__filtered_streets = []	#: stores street objects that will be removed as a list
        self.__street_box = self.__osm_object.street_tree.get_bounds() #: stores the bounding box of the street network
        self.__streets = [self.__osm_object.getWayByID(index) for index in self.__osm_object.street_tree.intersection(self.__street_box, "raw")] #: stores all street objects of the data representation as a list
        self.find_partitions()

    def find_partitions(self):
        """
        Initializes the partition finding
        """
        self.__partitions = {} #: dictionary with partition_id as key and L{app.partition.Partition} objects as value
        self.__partition_id = 0 #: stores the highest partition id found so far
        self.__largest_partition = 0 #: stores the partition id of the largest partition (= main street network)
        self.breadth_first_search(self.__streets)
        self.__largest_partition = self.find_largest_partition()
        self.__recalculate = False

    def get_partition_id(self):
        """
        Returns the highest partition id

	@returns: the highest partition id
	@rtype: C{int}
        """
        return self.__partition_id

    def reset_partitions(self):
        """
        Removes all partition information
        
        Resets the partition ids of streets and nodes, deletes all L{Partition} objects
        """
        self.__street_box = self.__osm_object.street_tree.get_bounds()
        self.__streets = [self.__osm_object.getWayByID(index) for index in self.__osm_object.street_tree.intersection(self.__street_box, "raw")]
        
        # reset the filtered streets
        self.__filtered_streets = []
        
        # reset all partition ids and filter information
        for street in self.__streets:
            street.partition_id = 0
            street.filtered = False
            for node in street.nodes:
                node.partition_id = 0
                node.filtered = False
                
        # delete all partition objects
        for partition in self.__partitions.itervalues():
            del partition
    
    def filter_streets(self, street_filter):
        """
        Marks streets as 'filtered' if their highway type is listed in the street_filter parameter
                
        @param street_filter: a list containing the OSM highway types that will be filtered
        @returns: True if there are streets that have been filtered
        @rtype: C{bool}
        """
        filtered = False
        
        # the partitions have to be recalculated if streets are removed
        self.reset_partitions()
        
        self.__street_box = self.__osm_object.street_tree.get_bounds()
        streets = [self.__osm_object.getWayByID(index) for index in self.__osm_object.street_tree.intersection(self.__street_box, "raw")]
        
        for street in streets:
            if street.getTags().get('highway') in street_filter:
                filtered = True
                
                # mark all filtered objects as filtered
                street.partition_id = -1 # all filtered objects belong to "Partition -1"
                street.filtered = True
                for node in street.nodes:
                    node.partition_id = -1
                    node.filtered = True
                self.__filtered_streets.append(street)
        self.find_partitions()
        return filtered

    def remove_filtered_streets(self):
        """
        Removes all filtered streets from the OSM data representation
        """
        for street in self.__filtered_streets:
            self.__osm_object.delete_way(street)

    def connect_partitions(self, partition_thresholds):
        """ Initializes the connection of all partitions with each other
        
        @param partition_thresholds: a dictionary containing search distance, projection threshold, size threshold, connection threshold and distance threshold { 'search':svalue, 'projection':pvalue, 'size':sivalue, 'connection':cvalue, 'distance':dvalue }
        """
        
        # do a recalculation of the partitions if neccessary
        if self.__recalculate:
            self.reset_partitions()
            self.find_partitions()
        
        # 'partition counter'
        # everytime a partition could not be connected, 'parts' is incremented by 1
        parts = 1

        print 'partitions before connection: %i' % len(self.__partitions)
        
        # Everytime a partition is successfully connected with the street network
        # 'len(self.__partitions)' is reduced by 1.
        # If 'len(self.__partitions)' and 'parts' are equal the loop has finished.
        while len(self.__partitions) > parts:
        
            # TODO: remove debug message
            if DEBUG:
                print 'laenge, parts: ', len(self.__partitions), parts
            connected = False
            partition_ids = self.__partitions.keys()
            partition_id = partition_ids[0]
            if partition_id == self.__largest_partition:
                partition_id = partition_ids[1]
            connected = self.connect_partition(partition_id, partition_thresholds)
            if not connected:
                parts += 1
        
        print 'remaining partitions: %i' % parts
                
        return parts

    def get_recalculation(self):
        """
        Returns the recalculation state
        
        @returns: the recalculation state
        @rtype: C{bool}
        """
        return self.__recalculate
    def set_recalculation(self, state):
        """
        Sets the recalculation state
        
        @type state: C{bool}
        @param state: the recalculation state
        """
        self.__recalculate = state
    recalculate = property(get_recalculation, set_recalculation, None, 'read/write property of the recalculation state')

    def get_largest_partition(self):
        """
        Returns the partition id of the largest partition
        
        @returns: the partition id of the largest partition
       	@rtype: C{int}
        """
        return self.__largest_partition

    def breadth_first_search(self, streets):
        """
        Breath first search over the map graph to find partitions
        
        @param streets: A list of streets representing the street network
        """
        for street in streets:
        
            # ignore filtered streets
            if street.filtered:
                # TODO: remove debug message
                if DEBUG:
                    print 'filtered'
                continue
                
            nodes = street.nodes
            
            # if the nodes of the current street are already assigned to a partition
            # the street gets the same partition id
            # and the street is added to the street set of the corresponding partition
            # then go on with the next street
            if nodes[0].partition_id > 0:
                street.partition_id = nodes[0].partition_id
                self.__partitions.get(nodes[0].partition_id).add_street(street)
                continue
            
            # if the nodes of the current street are not already assigned to a partition
            # a new partition is found
            else:
                self.__partition_id += 1
                new_partition = Partition(self.__partition_id)
                
                # TODO: remove debug message
                if DEBUG:
                    print 'part_id: ', self.__partition_id
                
                # assign the new partition id, add the partition object to the dictionary of partitions
                # and add the current street to the partition
                street.partition_id = self.__partition_id
                self.__partitions.setdefault(self.__partition_id, new_partition)
                self.__partitions.get(self.__partition_id).add_street(street)
                
                # create a FIFO queue of nodes, starting with the nodes of the current street
                node_queue = nodes[:]	# it's important to create a copy and not just a reference
            
            while node_queue:
                node = node_queue.pop(0)
                
                # do nothing if the node is already assigned to a partition
                if node.partition_id > 0:
                    continue
                
                # filtered streets are producing partitions
                # the algorithm must not walk along filtered streets
                elif node.partition_id == -1 and node.filtered:
                    node.partition_id = self.__partition_id 
                    for neighbour in node.neighbours:
                        # only add not filtered neighbours to the queue
                        if not neighbour.filtered:
                            node_queue.append(neighbour)
                # filtered node with an partition id > 0 means we have already looked at it
                elif node.filtered:
                    continue
                
                # node.partition_id = 0 --> nodes that haven't looked at so far ...
                else:
                    node.partition_id = self.__partition_id			# get an partition id
                    self.__partitions.get(self.__partition_id).add_node(node)	# add the node to the partition
                    node_queue.extend(node.neighbours)				# add all neighbours to the queue 

    def find_largest_partition(self):
        """
        Returns the partition id of the largest partition
        
        The partition with the most nodes is recognized as largest partition. If two partitions have the same node count the partition with the most streets is recognized as largest partition.        
        @returns: the partition id of the largest partition
        @rtype: C{int}
        """
        max_partition = 0
        max_size = 0
        for partition_id, partition in self.__partitions.iteritems():
            partition_size = partition.partition_size_by_nodes() 
            if partition_size > max_size:
                max_partition = partition_id
                max_size = partition_size
            elif partition_size == max_size:
                if partition.partition_size_by_streets() > self.__partitions.get(max_partition).partition_size_by_streets():
                    max_partition = partition_id
                    max_size = partition_size
        # TODO: remove debug message
        if DEBUG:
            print 'max_part: ', max_partition
        return max_partition
                
#    def get_nearest_partition(self, partition_id, threshold):
#        """
#        
#        @param partition_id:
#        @param threshold:
#        """
#        min_distance = 1e400
#        nearest_partition = 0
#        nearest_mode = None
#        for node in self.__partitions.get(partition_id).nodes:
#            streets = self.__osm_object.get_adjacent_streets(node, threshold)
#            if streets:
#                for street in streets:
#                    if street.partition_id == partition_id:
#                        continue
#                    else:
#                        distance, mode = distance_node_street(node, street)
#                        if distance < min_distance:
#                            min_distance = distance
#                            nearest_partition = street.partition_id
#                            nearest_mode = mode
#        return (nearest_partition, min_distance)
        
    def filter_streets_by_partition(self, streets, partition_id):
        """
        Returns the streets that are part of a partition given by a partition id
        
        @param streets: list of streets
        @type partition_id: C{int}
        @param partition_id: partition id
        @returns: list of streets that have the given partition id
        """
        filtered = []
        for street in streets:
            if street.partition_id != partition_id:
                filtered.append(street)
        return filtered

    def remove_partition(self, partition):
        """
        Deletes all streets of a given L{Partition} object.
        
        Removes all streets of the partition from the OSM data representation and deletes the partition object itself.
        
        @type partition: L{Partition}
        @param partition: the L{Partition} object representing the partition that shall be removed
        """
        streets = partition.streets
        for street in streets:
            self.__osm_object.delete_way(street)
        del self.__partitions[partition.partition_id]
        del partition
        
    def connect_partition(self, partition_id, thresholds):
        """ Initializes the connection of a single partition given by its partition id with the street network
        
        @type partition_id: C{int}
        @param partition_id: partition id
        @param thresholds: a dictionary containing search distance, projection threshold, size threshold, connection threshold and distance threshold { 'search':svalue, 'projection':pvalue, 'size':sivalue, 'connection':cvalue, 'distance':dvalue }
        @returns: True if the partition was successfully connected with the street network
        @rtype: C{bool}
        """
        search_threshold = int(thresholds.get('search'))
        projection_threshold = int(thresholds.get('projection'))
        size_threshold = int(thresholds.get('size'))
        connection_threshold = int(thresholds.get('connection'))
        distance_threshold = int(thresholds.get('distance'))
        
        partition = self.__partitions.get(partition_id)
        
        if partition.partition_size_by_nodes() < size_threshold:
            self.remove_partition(partition)
            return True
        
        #nearest_street = None
        min_distance = 1e400
        #min_mode = None
        nearest_part_node = None
        
        nodes_and_distances = []
        
        new_partition_id = 0

        # saves the nodes that have already been connected to another partition
        connected_nodes = []
        
        for node in partition.nodes:
            streets = self.__osm_object.get_adjacent_streets(node, search_threshold)
            streets = self.filter_streets_by_partition(streets, partition_id)
            
            # TODO: remove debug message
            #if DEBUG:
            #    print node, get_nearest_street(node, streets)
            street, distance, mode = get_nearest_street(node, streets)
            
            if street:
                nodes_and_distances.append((distance, node, street))
                
        sorted_nodes_by_distances = sorted(nodes_and_distances)

        partition_connected = False

        connection_count = 0
        index = 0
        while connection_count < connection_threshold:
            
            if index >= len(sorted_nodes_by_distances):
                break
            
            connected = False
            min_distance, nearest_part_node, nearest_street = sorted_nodes_by_distances[index]
            index += 1
            
            ignore = False
            for connected_node in connected_nodes:
                az_f, az_b, distance = distance_points(nearest_part_node, connected_node)
                if distance < distance_threshold:
                    ignore = True
  
            if not ignore:
                
                nearest_street, dist, min_mode = get_nearest_street(nearest_part_node, [nearest_street])
                
                if len(min_mode) == 1:
                    connected = connect_by_node(self.__osm_object, nearest_part_node, min_mode[0])
                    if connected:
                        new_partition_id = min_mode[0].partition_id
                        partition.add_street(connected)
                else:
                    nearest_street_node, node_distance = get_nearest_street_node(nearest_part_node, [nearest_street])
                    if node_distance - min_distance < projection_threshold:
                        connected = connect_by_node(self.__osm_object, nearest_part_node, nearest_street_node)
                        if connected:
                            new_partition_id = nearest_street_node.partition_id
                            partition.add_street(connected)
                    else:
                        connected = connect_by_projection(self.__osm_object, nearest_part_node, nearest_street, min_mode)
                        if connected:
                            new_partition_id = nearest_street.partition_id
                            partition.add_street(connected)
                
                if connected:
                    connected_nodes.append(nearest_part_node)
                    connection_count += 1
                
                partition_connected = partition_connected or connected
            
        # merge the joined partitions to one partition
        if partition_connected:
            new_partition = self.__partitions.get(new_partition_id)
            # TODO: remove debug message
            if DEBUG:
                if new_partition == None:
                    print new_partition_id
                    print thresholds
            new_partition.append_partition(partition)
            del self.__partitions[partition_id]
            del partition
        return partition_connected


class Partition(object):
    """ Representation of one partition
    
    The class stores the node and street objects of the partition.
    It provides methods to expand the partition.
    """

    def __init__(self, partition_id):
        """
        
        @type partition_id: C{int}
        @param partition_id: unique id as identificator of the partition
        """
        self.__partition_id = partition_id	#: partition id of the partition object
        self.__nodes = set()			#: set of the nodes of the partition 
        self.__streets = set()			#: set of the streets of the partition
        self.__box = None			#: bounding box of the partition
        
    def add_street(self, street):
        """ Adds a street to the partition object
        
        The bounding box of the partition is calculated by the bounding boxes of the added streets.
        @type street: L{geo.osm_import.Way}
        @param street: OSM way object representing a street
        """
        if self.__box:
            self.__box = merge_boxes(self.__box, street.box)
        else:
            self.__box = street.box
        self.__streets.add(street)
    
    def get_nodes(self):
        """
        Returns a list of the L{geo.osm_import.Node} objects of the partition
        
        @returns: a list of the L{geo.osm_import.Node} objects of the partition
        """
        return self.__nodes
    nodes = property(get_nodes, None, None, 'read-only property for the L{geo.osm_import.Node} objects of the partition')

    def get_streets(self):
        """ Returns a list of the L{geo.osm_import.Way} objects representing the streets of the partition
        
        @returns: a list of the L{geo.osm_import.Node} objects representing the streets of the partition
        """
        return self.__streets
    streets = property(get_streets, None, None, 'read-only property for the L{geo.osm_import.Way} objects of the partition')

    def get_box(self):
        """
        Returns the bounding box of the partition
        
        @returns: the bounding box of the partition
        """
        return self.__box
    box = property(get_box, None, None, 'read-only property for the bounding box of the partition')

    def add_node(self, node):
        """
        Adds a Node object to the Partition object
        
        @type node: L{geo.osm_import.Node}
        @param node: OSM Node object
        """
        self.__nodes.add(node)

    def append_partition(self, other_partition):
        """
        Merges two partition objects to one single object
        
        @type other_partition: L{Partition}
        @param other_partition: Partition object of the second partition
        """
        streets = other_partition.streets
        nodes = other_partition.nodes
        
        # copy the partition ids
        for node in nodes:
            node.partition_id = self.__partition_id
        for street in streets:
            street.partition_id = self.__partition_id

        # merge streets, nodes and boxes
        self.__streets.update(streets)
        self.__nodes.update(nodes)
        self.__box = merge_boxes(self.__box, other_partition.box)
        

    def get_partition_id(self):
        """
        Returns the partition ID of the partition
        
        @returns: the partition ID of the partition
        @rtype: C{int}
        """
        return self.__partition_id
    partition_id = property(get_partition_id, None, None, 'read-only property for the partition ID of the partition')
    
    def partition_size_by_nodes(self):
        """
        Returns the size of the partition by nodes
        
        @returns: the size of the partition by nodes
        @rtype: C{int}
        """
        return len(self.__nodes)
    
    def partition_size_by_streets(self):
        """
        Returns the size of the partition by streets
        
        @returns: the size of the partition by streets
        @rtype: C{int}
        """
        return len(self.__streets)

if __name__ == '__main__':
    pass
            

