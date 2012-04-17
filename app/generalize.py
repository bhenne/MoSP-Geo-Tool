""" The module app.generalize provides a method to prepare
OSM street objects for line generalization
@author: C. Protsch
"""

from douglas_peucker import douglas_peucker

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

def generalize(osm_object, tolerance):
    """ Initializes the line generalization

    This method prepares the OSM street object for the line generalization
    by the Douglas Peucker algorithm. It splits the streets at road junctions
    or Points of Interests into segments and passes the segments to the
    Douglas Peucker algorithm. Afterwards it reconnects the generalized segments
    to a complete street again. 
    
    @type osm_object: L{geo.osm_import.OSM_objects}
    @param osm_object: The OSM data representation
    @param tolerance: The tolerance value for the generlization in meters
    """

    # add the tolerance value to the set of already performed generalizations 
    osm_object.generalized.add(tolerance)
    
    # get all streets of the OSM data representation
    ways = [osm_object.getWayByID(index) for index in osm_object.street_tree.intersection(osm_object.box, "raw")]
    
    # initialize sets for node counting
    node_count_old = set()
    node_count_new = set()
    
    for way in ways:
        
        new_way = []
        segment = [way.nodes[0]]
        
        # add the node objects of the current way to the counting set
        # of the nodes before the generalization
        node_count_old |= set(way.nodes)
        
        
        for i in range(1, len(way.nodes)):
        
            # build up the way segment that will be generalized
            segment.append(way.nodes[i])
            
            # start the line generalization if the current node
            # is a road junction, if it is the last node of the current street
            # or if the node is a Point of Interest
            # otherwise build up the segment furthermore
            if len(way.nodes[i].neighbours) != 2 or i == len(way.nodes) - 1 or way.nodes[i].get_poi() > 0:
                dp = douglas_peucker(segment, tolerance)
                
                # connect the generalized segments to the new representation of the street
                if new_way:
                    # the last node of the last segment is the first node
                    # of the current segment
                    # don't add it twice ...
                    new_way.pop()
                    new_way.extend(dp)
                else:
                    new_way.extend(dp)
                
                # the current node is the start of the next segment
                segment = [way.nodes[i]]
        
        # add the new list of street nodes to the dictionary of already performed generalizations
        # later the user can choose one of the generalizations to be the new representation of the street
        way.generalized.setdefault(tolerance, new_way)
        
        # add the node objects of the new street to the counting set
        # of the nodes after the generalization
        node_count_new |= set(new_way)
    
    print 'street nodes before generalization: %i' % len(node_count_old)    
    print 'street nodes after generalization: %i' % len(node_count_new)
        


if __name__ == '__main__':
    pass
