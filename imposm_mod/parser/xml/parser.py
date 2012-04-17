# Copyright 2011 Omniscale GmbH & Co. KG
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import with_statement

from marshal import dumps

# modified for MoSP-GeoTool
#from imposm.parser.xml.util import log_file_on_exception, iterparse
from imposm_mod.parser.xml.util import log_file_on_exception, iterparse
# end of modification

class XMLParser(object):
    # modified for MoSP-GeoTool
    
    #def __init__(self, nodes_callback=None, ways_callback=None,
    #    relations_callback=None, coords_callback=None, nodes_tag_filter=None,
    #    ways_tag_filter=None, relations_tag_filter=None, marshal_elem_data=False):
    
    # the original library does not support the import of the bounding box
    # callback function for for bounding box added in the parameter list
    def __init__(self, nodes_callback=None, ways_callback=None,
        relations_callback=None, coords_callback=None, bounds_callback=None, nodes_tag_filter=None,
        ways_tag_filter=None, relations_tag_filter=None, marshal_elem_data=False):
    # end of modification
        self.nodes_callback = nodes_callback
        self.ways_callback = ways_callback
        self.relations_callback = relations_callback
        self.coords_callback = coords_callback
        # modified for MoSP-GeoTool
        # the original library does not support the import of the bounding box
        self.bounds_callback = bounds_callback
        # end of modification
        self.nodes_tag_filter = nodes_tag_filter
        self.ways_tag_filter = ways_tag_filter
        self.relations_tag_filter = relations_tag_filter
        self.marshal_elem_data = marshal_elem_data
    
    def parse(self, xml):
        with log_file_on_exception(xml):
            coords = []
            nodes = []
            ways = []
            relations = []
            tags = {}
            refs = []
            members = []
            root, context = iterparse(xml)
            # modified for MoSP-GeoTool
            bounds = []
            # end of modification


# modified for MoSP-GeoTool
# original code follows           
#            for event, elem in context:
#                if event == 'start': continue
#                if elem.tag == 'tag':
#                    tags[elem.attrib['k']] = elem.attrib['v']
#                elif elem.tag == 'node':
#                    osmid = int(elem.attrib['id'])
#                    x, y = float(elem.attrib['lon']), float(elem.attrib['lat'])
#                    if self.coords_callback:
#                        coords.append((osmid, x, y))
#                    if self.nodes_tag_filter:
#                        self.nodes_tag_filter(tags)
#                    if tags and self.nodes_callback:
#                        if self.marshal_elem_data:
#                            nodes.append((osmid, dumps((tags, (x, y)), 2)))
#                        else:
#                            nodes.append((osmid, tags, (x, y)))
#                    tags = {}
#                elif elem.tag == 'nd':
#                    refs.append(int(elem.attrib['ref']))
#                elif elem.tag == 'member':
#                    members.append((int(elem.attrib['ref']), elem.attrib['type'], elem.attrib['role']))
#                elif elem.tag == 'way':
#                    osm_id = int(elem.attrib['id'])
#                    if self.ways_tag_filter:
#                        self.ways_tag_filter(tags)
#                    if self.ways_callback:
#                        if self.marshal_elem_data:
#                            ways.append((osm_id, dumps((tags, refs), 2)))
#                        else:
#                            ways.append((osm_id, tags, refs))
#                    refs = []
#                    tags = {}
#                elif elem.tag == 'relation':
#                    osm_id = int(elem.attrib['id'])
#                    if self.relations_tag_filter:
#                        self.relations_tag_filter(tags)
#                    if tags and self.relations_callback:
#                        if self.marshal_elem_data:
#                            relations.append((osm_id, dumps((tags, members), 2)))
#                        else:
#                            relations.append((osm_id, tags, members))
#                    members = []
#                    tags = {}
# end of original code follows
#
# modified code follows
            
            for event, elem in context:
                if event == 'start': continue
                
                # new code: bound/bounds added
                if elem.tag == 'bounds':
                    minlon, minlat = float(elem.attrib['minlon']), float(elem.attrib['minlat'])
                    maxlon, maxlat = float(elem.attrib['maxlon']), float(elem.attrib['maxlat'])
                    if self.bounds_callback:
                        bounds.extend([minlon, minlat, maxlon, maxlat])
                elif elem.tag == 'bound':
                    box = elem.attrib['box'].split(',')
                    box = [float(i) for i in box]
                    minlat, minlon, maxlat, maxlon = box
                    if self.bounds_callback:
                        bounds.extend([minlon, minlat, maxlon, maxlat])

                elif elem.tag == 'tag':
                    tags[elem.attrib['k']] = elem.attrib['v']
                elif elem.tag == 'node':
                    osmid = int(elem.attrib['id'])
                    x, y = float(elem.attrib['lon']), float(elem.attrib['lat'])


# the original library makes a difference
# between "coordinates" (nodes without tags)
# and "nodes" (nodes with tags)
# we don't make this diffrence
#                    if self.coords_callback:
#                        coords.append((osmid, x, y))

                    # new code:
                    # remove id, lon, lat from the attribute list
                    # otherwise we will have them twice
                    del elem.attrib['id']
                    del elem.attrib['lon']
                    del elem.attrib['lat']

                    if self.nodes_tag_filter:
                        self.nodes_tag_filter(tags)
#                    if tags and self.nodes_callback:
                    if self.nodes_callback:     # new code
                        if self.marshal_elem_data:
                            nodes.append((osmid, dumps((tags, (x, y)), 2)))
                        else:
#                            nodes.append((osmid, tags, (x, y)))
                            nodes.append((osmid, tags, (x, y), elem.attrib))    # new code: attributes are also added
                    tags = {}
                elif elem.tag == 'nd':
                    refs.append(int(elem.attrib['ref']))
                elif elem.tag == 'member':
                    members.append((int(elem.attrib['ref']), elem.attrib['type'], elem.attrib['role']))
                elif elem.tag == 'way':
                    osm_id = int(elem.attrib['id'])
                    del elem.attrib['id']   # new code: remove id from the attribute list
                    if self.ways_tag_filter:
                        self.ways_tag_filter(tags)
                    if self.ways_callback:
                        if self.marshal_elem_data:
                            ways.append((osm_id, dumps((tags, refs), 2)))
                        else:
#                            ways.append((osm_id, tags, refs))
                            ways.append((osm_id, tags, refs, elem.attrib))  # new code: attributes are also added
                    refs = []
                    tags = {}
                elif elem.tag == 'relation':
                    osm_id = int(elem.attrib['id'])
                    del elem.attrib['id']   # new code: remove id from the attribute list
                    if self.relations_tag_filter:
                        self.relations_tag_filter(tags)
#                    if tags and self.relations_callback:
                    if self.relations_callback:     # new code
                        if self.marshal_elem_data:
                            relations.append((osm_id, dumps((tags, members), 2)))
                        else:
#                            relations.append((osm_id, tags, members))
                            relations.append((osm_id, tags, members, elem.attrib))  # new code: attributes are also added
                    members = []
                    tags = {}
#####################
# end of modification
#####################



                # modified for MoSP-GeoTool
                if len(bounds) >= 1:
                    self.bounds_callback(bounds)
                    bounds = []
                # end of modification
            
                if len(coords) >= 512:
                    self.coords_callback(coords)
                    coords = []
                if len(nodes) >= 128:
                    self.nodes_callback(nodes)
                    nodes = []
                if len(relations) >= 128:
                    self.relations_callback(relations)
                    relations = []
                if len(ways) >= 128:
                    self.ways_callback(ways)
                    ways = []

                root.clear()
        
            if self.coords_callback:
                self.coords_callback(coords)
            if self.nodes_callback:
                self.nodes_callback(nodes)
            if self.ways_callback:
                self.ways_callback(ways)
            if self.relations_callback:
                self.relations_callback(relations)

