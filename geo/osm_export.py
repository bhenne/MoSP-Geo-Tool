""" The module C{geo.osm_export} provides a method to generate an OSM XML file from the OSM data set.
@author: C. Protsch
"""

from xml.sax.saxutils import quoteattr, escape

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

def OSM_export(outfile, osm):
    """ Method to generate an OSM XML file for a given OSM data set
    
    @param outfile: path to the OSM XML file that will be written
    @type osm: L{geo.osm_import.OSM_objects}
    @param osm: the OSM data representation
    """
    outobj = open(outfile, "w")
    outobj.write('<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n')
    outobj.write('<osm version=\"0.6\" generator=\"MoSP-GeoTool\">\n')
    
    nodes = osm.node_objects
    streets = [osm.getWayByID(index) for index in osm.street_tree.intersection(osm.box, "raw")]
    buildings = [osm.getWayByID(index) for index in osm.building_tree.intersection(osm.box, "raw")]
    minlon, minlat, maxlon, maxlat = osm.bounds
    
    outobj.write('  <bounds minlat=\"%f\" minlon=\"%f\" maxlat=\"%f\" maxlon=\"%f\" />\n' % (minlat, minlon, maxlat, maxlon))

    # write the nodes    
    for node in nodes:
        outobj.write('  <node id=\"%i\" lat=\"%f\" lon=\"%f\"' % (node.getID(), node.getLat(), node.getLon()))
        for key in node.attributes:
            outobj.write(' %s=%s' % (key, quoteattr(escape(node.attributes[key]))))
        if node.getTags() == {}:
            outobj.write(' />\n')
        else:
            outobj.write('>\n')
            for key in node.getTags():
                outobj.write('    <tag k=\"%s\" v=%s />\n' % (key, quoteattr(escape(node.getTags()[key]))))
            outobj.write('  </node>\n')
    
    
    # write the ways
    def __way_output(way):
        outobj.write('  <way id=\"%i\"' % way.getID())
        for key in way.attributes:
            outobj.write(' %s=%s' % (key, quoteattr(escape(way.attributes[key]))))
        outobj.write('>\n')
        for node_id in way.nodeIDs:
            outobj.write('    <nd ref=\"%i\" />\n' % node_id)
        for key in way.getTags():
            outobj.write('    <tag k=\"%s\" v=%s />\n' % (key, quoteattr(escape(way.getTags()[key]))))
        outobj.write('  </way>\n')
            
    for street in streets:
        __way_output(street)

    for building in buildings:
        __way_output(building)
    
    for way_id in osm.get_other_ways():
        __way_output(osm.getWayByID(way_id))
    
    for way_id in osm.way_delete:
        __way_output(osm.getWayByID(way_id))

    # write the relations
    for relation in osm.get_relations().itervalues():
        rel_id, rel_tags, rel_members, rel_attributes = relation
        outobj.write('  <relation id=\"%s\"' % rel_id)
        
        for key, value in rel_attributes.iteritems():
            outobj.write(' %s=%s' % (key, quoteattr(escape(value))))
        outobj.write('>\n')
        
        for memb_ref, memb_type, memb_role in rel_members:
            outobj.write('    <member type=\"%s\" ref=\"%i\" role=\"%s\"/>\n' % (memb_type, memb_ref, memb_role))
        
        for key, value in rel_tags.iteritems():
            outobj.write('    <tag k=\"%s\" v=%s />\n' % (key, quoteattr(escape(value))))
        outobj.write('  </relation>\n')
        

    outobj.write('</osm>\n')
    outobj.close()
