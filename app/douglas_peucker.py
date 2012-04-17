""" The module provides methods to perform the Douglas Peucker line generalization algorith """

from geo.geo_utils import distance_point_line

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

def douglas_peucker(way_segment, tolerance):
    """
    Performes the Douglas Peucker line generalization algorithm for a given way segment
    
    @param way_segment: List of L{geo.osm_import.Node} objects that represent the way segment
    @param tolerance: The tolerance value for the generlization in meters
    @return: A list of L{geo.osm_import.Node} objects that represents the generalized way segment
    @rtype: C{list} of L{geo.osm_import.Node}
    @see: the algorithm is adapted from the following public domain sources:
    	- U{http://www.cse.hut.fi/en/research/SVG/TRAKLA2/exercises/DouglasPeucker-212.html}
    	- U{http://www.mappinghacks.com/code/PolyLineReduction/}
    	- U{http://mappinghacks.com/code/dp.py.txt}
    """

    # the algorithm is adapted from:
    # http://www.cse.hut.fi/en/research/SVG/TRAKLA2/exercises/DouglasPeucker-212.html
    # http://www.mappinghacks.com/code/PolyLineReduction/
    # http://mappinghacks.com/code/dp.py.txt

    new_way = []
    stack = []
    anchor = 0
    floater = len(way_segment)-1
    new_way.append(way_segment[anchor])
    stack.append(floater)
    
    while stack:
        max_distance = 0.0
        farthest = floater
        for i in range(anchor + 1, floater):
            distance = distance_point_line(way_segment[anchor], way_segment[floater], way_segment[i])
            if distance > max_distance:
                max_distance = distance
                farthest = i
            
        if max_distance < tolerance:
            new_way.append(way_segment[stack.pop()])
            anchor = floater
            if stack:
                floater = stack[-1]
        else:
            floater = farthest
            stack.append(floater)
            
    return new_way

if __name__ == '__main__':
    pass
