""" General geometric methods """

from math import sqrt
from pyproj import Geod
from globals import DEBUG

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

GEOD = Geod(ellps='WGS84')
TOLERANCE = 1e-7

def distance_points(point1, point2):
    """ Calculates the azimuth angles and distance between two OSM nodes
        
    The method Geod.inv of the pyproj-library has a bug if the coordinates of
    two points are too close but not exactly equal
    (see U{http://code.google.com/p/pyproj/issues/detail?id=18}).
    This method provides an exception handling.
    @type point1: L{geo.osm_import.Node}
    @param point1: OSM Node object
    @type point2: L{geo.osm_import.Node}
    @param point2: OSM Node object
    @return: a tuple containing the azimuth angles in degrees and
    the distance in meters (azimuth_forward, azimuth_backward, distance)
    between point1 and point2
    @rtype: C{(float, float, float)}
    """
    try:
        az_f, az_b, distance = GEOD.inv(point1.lon, point1.lat, point2.lon, point2.lat)
    except ValueError:
        # TODO: remove debug message
        if DEBUG:
            print 'ValueError-Exception'
        # set all values to zero if the exception occurs
        az_f, az_b, distance = 0.0
    return (az_f, az_b, distance)

def create_node_box(node, distance):
    """ creates a rectangular box with the node as the center
    
    @type node: L{geo.osm_import.Node}
    @param node: OSM Node object
    @param distance: the distance in meters is the distance from the center to the top/left/bottom/right
    @return: a list with lon/lat coordinates of the box: [left_lon, bottom_lat, right_lon, top_lat]
    @rtype: C{[float, float, float, float]}
    """ 
    north_lon, north_lat, north_backaz = GEOD.fwd(node.lon, node.lat, 0, distance)
    east_lon, east_lat, east_backaz = GEOD.fwd(node.lon, node.lat, 90, distance)
    south_lon, south_lat, south_backaz = GEOD.fwd(node.lon, node.lat, 180, distance)
    west_lon, west_lat, west_backaz = GEOD.fwd(node.lon, node.lat, 270, distance)
    box = [west_lon, south_lat, east_lon, north_lat]
    return box

def have_same_coords(point1, point2, tolerance=TOLERANCE):
    """ Checks if two OSM Nodes have the same coordinates
    
    Longitudes and latitudes are floating point values.
    Because floating point math isn't exact you cannot
    check equality. Check if the difference of the values
    is below a certain level 
    
    @type point1: L{geo.osm_import.Node}
    @param point1: OSM Node object
    @type point2: L{geo.osm_import.Node}
    @param point2: OSM Node object
    @param tolerance: tolerance value for floating point comparison
    @return: True if the absolute difference of longitude and latitude
    values of the two nodes are below the tolerance value
    @rtype: C{bool}

    """ 
    return point1 != None and point2 != None \
        and abs(point1.lon - point2.lon) <= tolerance \
        and abs(point1.lat - point1.lat) <= tolerance
        
def get_building_entrance(building):
    """ Gets for a given building the node objects that are tagged as entrance
    
    @param building: OSM Way object that represents a building
    @return: a set of L{geo.osm_import.Node} objects that are tagged as entrance
    @rtype: C{sert} of L{geo.osm_import.Node}
    """
    
    if is_building(building):
        
        entrance = set() # it is possible that a building has more than one entrance
        for node in building.nodes:
            if node.getTags().get('building') == 'entrance':
                entrance.add(node)
        return entrance
    else:
        return None

def is_area(way):
    """ Checks if a given Way object is an area
    
    @type way: L{geo.osm_import.Way}
    @param way: OSM Way object
    @return: True if the first and the last OSM Nodes in the list of
    referencing Nodes have the same OSM-ID
    @rtype: C{bool}
    """
    
    return way.nodeIDs[0] == way.nodeIDs[-1]

def is_building(building):
    """ Checks if a given Way object is a building
    
    @type building: L{geo.osm_import.Way}
    @param building: OSM Way object
    @return: True if the given Way object is an area and if it is tagged 'building' : 'yes'
    @rtype: C{bool}
    """
    
    if building:
        return is_area(building) and building.getTags().get('building') == 'yes'
    else:
        return False

def is_inside_polygon(node, way):
    
    """ Checks if a Node object is surrounded by a given Way object
    
    Check is performed with the 'even-odd-rule',
    algorithm adapted from U{http://paulbourke.net/geometry/insidepoly/}
    
    @type node: L{geo.osm_import.Node}
    @param node: OSM Node object
    @type way: L{geo.osm_import.Way}
    @param way: OSM Way object
    @return: True if Node is surrounded by a closed Way
    @rtype: C{bool}
    """
    
    # if the way is not an area it isn't a polygon at all
    if not is_area(way):
        return False
    
    # TODO: Abstand == 0 fehlt noch
        
    polygon = way.nodes
    
    n = len(polygon)
    intersections = 0
    
    # even-odd-rule 
    p1_x, p1_y = polygon[0].get_xy_utm()
    for i in range(n + 1):
        p2_x, p2_y = polygon[i % n].get_xy_utm()
        if node.get_y_utm() > min(p1_y, p2_y):
            if node.get_y_utm() <= max(p1_y, p2_y):
                if node.get_x_utm() <= max(p1_x, p2_x):
                    if p1_y != p2_y:
                        xinters = (node.get_y_utm() - p1_y) * (p2_x - p1_x) / (p2_y - p1_y) + p1_x
                    if p1_x == p2_x or node.get_x_utm() <= xinters:
                        intersections += 1
        p1_x, p1_y = p2_x, p2_y

    return intersections % 2 != 0 # even --> outside --> False

def __distance_point_to_line(line_start, line_end, point):
    """ Calculates the distance between a line segment given by its starting point and ending point and a node
    
    There are three possible cases to calculate the distance:
      - The projection of the node to the line segment lies on the interpolation of the segment before its starting point. The calculated distance is the distance between the node and the starting point. The distance mode is a list with the OSM Node object of the starting point as the single element.
      - The projection of the node to the line segment lies on the line segment between starting point and ending point. The calculated distance is given by the distance between the node and the projection of the node to the line segment. The distance mode is a list with three elements: the OSM Node object of the starting point, the OSM Node object of the ending point and the distance between the starting point and the projection of the node to the segment.
      - The projection of the node to the line segment lies on the interpolation of the segment after its ending point. The calculated distance is the distance between the node and the ending point. The distance mode is a list with the OSM Node object of the ending point as the single element.
    
    @type line_start: L{geo.osm_import.Node}
    @param line_start: OSM Node object, that represents the starting point of a Way segment
    @type line_end: L{geo.osm_import.Node}
    @param line_end: OSM Node object, that represents the ending point of a Way segment
    @type point: L{geo.osm_import.Node}
    @param point: OSM Node object, for which the distance to the line segment shall be calculated
    @return: a tuple containing the distance between the node and the line segment in meters and the distance mode (distance, distance_mode)
    @rtype: C{(float, list)}
    @see: the algorithm is adapted from:
        - U{http://www.cse.hut.fi/en/research/SVG/TRAKLA2/exercises/DouglasPeucker-212.html}
        - U{http://www.mappinghacks.com/code/PolyLineReduction/}
        - U{http://mappinghacks.com/code/dp.py.txt}
    """
    
    # The algorithm is adapted from:
    # http://www.mappinghacks.com/code/PolyLineReduction/
    # http://mappinghacks.com/code/dp.py.txt
    # for further explanation of the algorithm see these sites
    
    distance = 0.0
    mode = None

    if not have_same_coords(line_start, line_end):
        line_segment_x = float(line_end.get_x_utm() - line_start.get_x_utm())
        line_segment_y = float(line_end.get_y_utm() - line_start.get_y_utm())

        # Bug in Geod.inv
        # if two points are too close but not exactly equal
        # it raises a ValueError
        try:
            az_f, az_b, segment_length = GEOD.inv(line_start.lon, line_start.lat, line_end.lon, line_end.lat)
            line_segment_x /= segment_length
            line_segment_y /= segment_length
        except ValueError:
            # TODO: remove debug message
            if DEBUG:
                print 'ValueError-Exception'
            line_segment_x = line_segment_y = segment_length = 0.0
    else:
        line_segment_x = line_segment_y = segment_length = 0.0
    # compare to start
    start_to_point_x = float(point.get_x_utm() - line_start.get_x_utm())
    start_to_point_y = float(point.get_y_utm() - line_start.get_y_utm())
    projection_scalar = start_to_point_x * line_segment_x + start_to_point_y * line_segment_y
    if projection_scalar < 0.0:
        #distance = sqrt(start_to_point_x ** 2 + start_to_point_y ** 2)
        try:
            az_f, az_b, distance = GEOD.inv(line_start.lon, line_start.lat, point.lon, point.lat)
        except ValueError:
            # TODO: remove debug message
            if DEBUG:
                print 'ValueError-Exception'
            distance = 0.0
        mode = [line_start]
        
    else:
        # compare to end
        end_to_point_x = float(point.get_x_utm() - line_end.get_x_utm())
        end_to_point_y = float(point.get_y_utm() - line_end.get_y_utm())
        #segment_length = sqrt(end_to_point_x ** 2 + end_to_point_y ** 2)
        try:
            az_f, az_b, segment_length = GEOD.inv(line_end.lon, line_end.lat, point.lon, point.lat)
        except ValueError:
            # TODO: remove debug message
            if DEBUG:
                print 'ValueError-Exception'
            segment_length = 0.0
        projection_scalar2 = end_to_point_x * (-line_segment_x) + end_to_point_y * (-line_segment_y)
        if projection_scalar2 < 0.0:
            distance = segment_length
            mode = [line_end]
        else:
            distance = sqrt(abs(segment_length ** 2 - projection_scalar2 ** 2))
            mode = [line_start, line_end, projection_scalar]
    return (distance, mode)

def distance_mode_point_line(line_start, line_end, point):
    """ Calculates the distance between a line segment given by its starting point and ending point and a node
    
    @type line_start: L{geo.osm_import.Node}
    @param line_start: OSM Node object, that represents the starting point of a Way segment
    @type line_end: L{geo.osm_import.Node}
    @param line_end: OSM Node object, that represents the ending point of a Way segment
    @type point: L{geo.osm_import.Node}
    @param point: OSM Node object, for which the distance to the line segment shall be calculated
    @return: a tuple contaning the distance between the node and the line segment in meters and the distance mode (distance, distance_mode)
    @rtype: C{(float, list)}
    """

    return __distance_point_to_line(line_start, line_end, point)

def distance_point_line(line_start, line_end, point):
    """ Calculates the distance between a line segment given by its starting point and ending point and a node
    
    @type line_start: L{geo.osm_import.Node}
    @param line_start: OSM Node object, that represents the starting point of a Way segment
    @type line_end: L{geo.osm_import.Node}
    @param line_end: OSM Node object, that represents the ending point of a Way segment
    @type point: L{geo.osm_import.Node}
    @param point: OSM Node object, for which the distance to the line segment shall be calculated
    @return: the distance between the node and the line segment in meters
    @rtype: C{float}
    """
    
    return __distance_point_to_line(line_start, line_end, point)[0]

def distance_node_street(node, street):
    """ Calculates the distance between a OSM Node object and a OSM Way object
    
    The distance between a node and a street is the shortest distance between the node and a line segment of the street    
    @type node: L{geo.osm_import.Node}
    @param node: OSM Node object
    @type street: L{geo.osm_import.Way}
    @param street: OSM Way object
    @return: a tuple contaning the distance between the node and the street in meters and the distance mode (distance, distance_mode)
    @rtype: C{(float, list)}
    """
    min_dist = 1e400
    min_mode = None
    snodes = street.nodes
    
    # find the line segment with the shortest distance to the node
    for i in range(len(snodes) - 1):
        distance, mode = distance_mode_point_line(snodes[i], snodes[i + 1], node)
        if distance < min_dist:
            min_dist = distance
            min_mode = mode
    return (min_dist, min_mode)

def get_nearest_street_node(node, streets):
    """ Given an OSM node and a list of streets the method calculates
    the street node with the shortest distance to the given OSM node 
    
    @type node: L{geo.osm_import.Node}
    @param node: OSM Node object
    @param streets: A list of L{geo.osm_import.Way} objects
    @return: A tuple containing the nearest OSM node and the distance in meters (L{geo.osm_import.Node}, distance)
    @rtype: C{(L{geo.osm_import.Node}, float)}
    """
    min_dist = 1e400
    nearest_node = None
    for street in streets:
        for street_node in street.nodes:
            az_f, az_b, distance = distance_points(node, street_node)
            #az_f, az_b, distance = GEOD.inv(node.lon, node.lat, street_node.lon, street_node.lat)
            if distance < min_dist:
                min_dist = distance
                nearest_node = street_node
    return (nearest_node, min_dist)

def get_nearest_street(node, streets):
    """ Given an OSM node and a list of streets the method calculates
    the street with the shortest distance to the given OSM node 
    
    @type node: L{geo.osm_import.Node}
    @param node: OSM Node object
    @param streets: A list of L{geo.osm_import.Way} objects
    @return: A tuple containing the nearest OSM way, the distance in meters and the distance mode (L{geo.osm_import.Way}, distance, distance_mode)
    @rtype: C{(L{geo.osm_import.Node}, float, list)}
    """
    min_dist = 1e400
    nearest_street = None
    nearest_mode = None
    for street in streets:
        distance, mode = distance_node_street(node, street)
        if distance < min_dist:
            min_dist = distance
            nearest_street = street
            nearest_mode = mode
    return (nearest_street, min_dist, nearest_mode)

def connect_by_projection(osm_object, node, street, mode):
    """ Connects an OSM Node to an OSM Way by projecting the Node to the nearest line segment of the street 
    
    The correct line segment is given by the distance mode which has to be calculated in advance
    
    @type osm_object: L{geo.osm_import.OSM_objects}
    @param osm_object: The OSM data representation
    @type node: L{geo.osm_import.Node}
    @param node: The OSM Node object that shall be connected to a street
    @type street: L{geo.osm_import.Way}
    @param street: The OSM Way object that represents the street with which the node shall be connected
    @param mode: the distance mode 
    @return: If the connection was successfull the method returns the L{geo.osm_import.Way} object that is created to connect the node and the street
    @rtype: L{geo.osm_import.Way}
    """

    connected = False
    
    if street == None or mode == None:
        # TODO: remove debug message
        print node, street, mode
        return False

    # fallback to single mode
    # if the distance mode has the length 1, it isn't possible to connect by projection
    # --> connecting is performed by connecting the node and the node given by the distance mode
    if len(mode) == 1:
        connected = connect_by_node(node, mode[0])

    else:
    	# calculate the position of the new node
        start_node, end_node, projection_length = mode
        azimuth_f, az_b, dist = GEOD.inv(start_node.lon, start_node.lat, end_node.lon, end_node.lat)
        new_lon, new_lat, az_b = GEOD.fwd(start_node.lon, start_node.lat, azimuth_f, projection_length)
        
        # 7 decimal places is the standard osm format --> use it
        new_lon = float('%.7f' % new_lon)
        new_lat = float('%.7f' % new_lat)
        
        # the new node doesn't have tags
        tags = {}
        # create the neccessary attributes
        attr = { 'visible':'true'}
        # add the new node to the OSM data representation
        new_node = osm_object.insert_new_node(new_lat, new_lon, tags, attr)
        # set the partition id of the new node
        new_node.partition_id = street.partition_id
        # insert the new node into the street
        street.insert_node(start_node, end_node, new_node)
        # connect the given node and the newly created node
        connected = connect_by_node(osm_object, node, new_node)
    return connected

def connect_by_node(osm_object, node, street_node):
    """ Connects two OSM Nodes by a newly created street
    
    If one of the nodes is already part of the street network it should be the second Node object in the parameter list.
    
    @type osm_object: L{geo.osm_import.OSM_objects}
    @param osm_object: The OSM data representation
    @type node: L{geo.osm_import.Node}
    @param node: OSM Node object
    @type street_node: L{geo.osm_import.Node}
    @param street_node: OSM Node object
    
    """
    # tag the newly created street as 'footway'
    tags = { 'highway':'footway'}
    # the newly created street is references by the two given OSM Node objects
    nodes = [node.node_id, street_node.node_id]
    # create the neccessary attributes
    attr = { 'visible':'true'}
    # add the new street to the OSM data representation
    new_street = osm_object.append_new_street(tags, nodes, attr)
    # update the partition id 
    if node.partition_id > 0:
        new_street.partition_id = node.partition_id
    else:
        new_street.partition_id = street_node.partition_id
        node.partition_id = street_node.partition_id
    return new_street

def merge_boxes(box1, box2):
    """ Calculates a new bounding box by the furthermost left, bottom, right, top sides of the given boxes
    
    Boxes are given as lists with this format: [left_lon, bottom_lat, right_lon, top_lat]
    @param box1: Bounding box defined by a list of geographic coordinates: [left_lon, bottom_lat, right_lon, top_lat]
    @param box2: Bounding box defined by a list of geographic coordinates: [left_lon, bottom_lat, right_lon, top_lat]
    @return: the coordinate list of the merged bounding box
    @rtype: C{[float, float, float, float]}
    """
    box1_min_x, box1_min_y, box1_max_x, box1_max_y = box1
    box2_min_x, box2_min_y, box2_max_x, box2_max_y = box2
    return [min(box1_min_x, box2_min_x),
            min(box1_min_y, box2_min_y),
            max(box1_max_x, box2_max_x),
            max(box1_max_y, box2_max_y)]

def intersects(rectangle1, rectangle2):
    """ Calculates if two rectangles intersects each other
    
    @param rectangle1: Rectangle defined by a list of geographic coordinates: [left_lon, bottom_lat, right_lon, top_lat]
    @param rectangle2: Rectangle defined by a list of geographic coordinates: [left_lon, bottom_lat, right_lon, top_lat]
    @return: True, if the rectangles intersects each other
    @rtype: C{bool}
    """
    rect_min_x1, rect_min_y1, rect_max_x1, rect_max_y1 = rectangle1
    rect_min_x2, rect_min_y2, rect_max_x2, rect_max_y2 = rectangle2
    return (rect_min_x1 <= rect_max_x2 and rect_max_x1 >= rect_min_x2 and 
            rect_min_y1 <= rect_max_y2 and rect_max_y1 >= rect_min_y2)
