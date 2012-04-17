""" The module C{geo.osm_map_rendering} provides methods to display the map in the window of the MoSP GeoTool
@author: C. Protsch
"""
from geo.tile_image import background_from_tiles, pil_image_to_pixbuf
from geo.zoom import ZoomObject
import gtk
from app.poi import POI_SELECTED, POI_CONNECTED, POI_NOT_CONNECTED

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

POI_SIZE = 8
FOREGROUND_COLOR = '#666'

class OSMMapRendering(object):
    """ Objects of the class C{OSMMapRendering} stores the display parameters of the map.
    
    The instance methods of the class are used to set the display parameters,
    to draw the map and move/zoom the map.
    """

    def __init__(self, osm_object, size):
        """
        
        @type osm_object: L{geo.osm_import.OSM_objects}
        @param osm_object: The OSM data representation
        @type size: (int, int)
        @param size: window size in pixels as a tuple C{(width, height)}
        """
        width, height = size
        self.__window_width = width     #: window width in pixels
        self.__window_height = height   #: window height in pixels
        self.__show_tiles = False       #: stores if the background tiles are shown
        self.__show_poi = False         #: stores if the points of interest are shown
        self.__show_partitions = False  #: stores if the partitions are shown
        
        self.__osm_object = osm_object  #: OSM data representation
        self.__osm_box = osm_object.street_tree.get_bounds() #: bounding box of all street objects
        self.__zoom_object = ZoomObject(size) #: stores a reference to the L{geo.zoom.ZoomObject} 
        self.__zoom_object.find_zoom_level(self.__osm_box)
        
        self.__viewport_coordinates = self.__zoom_object.viewport_coordinates() #: Geographic coordinates of the edges of the visible area
                
        self.__draw_map()

        self.__show_generalized = 0     #: stores the tolerance value of the generalization currently shown

    def __draw_map(self):
        """ The method initialized the drawing of the map
        """
        
        # calculate the pixel dimensions
        tile_box = self.__zoom_object.tile_box()
        self.__min_lon, self.__min_lat, self.__max_lon, self.__max_lat = tile_box
        self.__projection = self.__osm_object.get_osm_projection()
        self.__min_x, self.__min_y = self.__projection(self.__min_lon, self.__min_lat)
        self.__max_x, self.__max_y = self.__projection(self.__max_lon, self.__max_lat)
        self.__width = self.__max_x - self.__min_x
        self.__height = self.__max_y - self.__min_y
        self.__pixel_width, self.__pixel_height = self.__zoom_object.tile_box_pixel()

        # calculate the adjustment of the map
        position = self.__zoom_object.get_position_in_tile(self.__osm_box[3], self.__osm_box[0])
        self.__vadj = gtk.Adjustment(position[1], lower=0,
                                     upper=self.__pixel_height,
                                     step_incr=10,
                                     page_incr=100,
                                     page_size=self.__window_height)    #: U{GTK Adjustment object<http://developer.gnome.org/pygtk/stable/class-gtkadjustment.html>} for the vertical alignment of the viewport
        self.__hadj = gtk.Adjustment(position[0],
                                     lower=0,
                                     upper=self.__pixel_width,
                                     step_incr=10,
                                     page_incr=100,
                                     page_size=self.__window_width)     #: U{GTK Adjustment object<http://developer.gnome.org/pygtk/stable/class-gtkadjustment.html>} for the horizontal alignment of the viewport
        
        # create the drawing area
        self.__area = gtk.DrawingArea() #: U{GTK drawing area<http://developer.gnome.org/pygtk/stable/class-gtkdrawingarea.html>}
        self.__area.set_size_request(self.__pixel_width, self.__pixel_height)
        
        self.__viewport_coordinates = self.__zoom_object.viewport_coordinates()
        self.__street_box = self.increase_box(self.__viewport_coordinates)
        
        # start the drawing itself
        self.__area.connect("expose-event", self.__draw_ways)
        
        # needed for display within the gui
        # add the drawing area to a viewport
        # the viewport will later on be added to the main window
        self.__vp = gtk.Viewport() #: U{GTK viewport object<http://developer.gnome.org/pygtk/stable/class-gtkviewport.html>}
        #self.__vp = gtk.ScrolledWindow()
        self.__vp.set_size_request(self.__window_width, self.__window_height)
        self.__vp.add(self.__area)
        #self.__vp.add_with_viewport(self.__area)
        
    
    
    def getArea(self):
        """
        Returns the U{GTK viewport object<http://developer.gnome.org/pygtk/stable/class-gtkviewport.html>} that contains the drawing area

        @returns: the U{GTK viewport object<http://developer.gnome.org/pygtk/stable/class-gtkviewport.html>} that contains the drawing area
        @rtype: C{U{gtk.Viewport<http://developer.gnome.org/pygtk/stable/class-gtkviewport.html>}}
        """
        return self.__vp

    def get_vadjustment(self):
        """ Returns the U{GTK Adjustment object<http://developer.gnome.org/pygtk/stable/class-gtkadjustment.html>} for the vertical alignment of the viewport.
        
        @returns: the U{GTK Adjustment object<http://developer.gnome.org/pygtk/stable/class-gtkadjustment.html>} for the vertical alignment of the viewport.
        @rtype: C{U{gtk.Adjustment<http://developer.gnome.org/pygtk/stable/class-gtkadjustment.html>}}
        """
        return self.__vadj
    vadj = property(get_vadjustment, None, None, 'read-only property for the U{GTK Adjustment object<http://developer.gnome.org/pygtk/stable/class-gtkadjustment.html>} for the vertical alignment of the viewport.')

    def get_hadjustment(self):
        """ Returns the U{GTK Adjustment object<http://developer.gnome.org/pygtk/stable/class-gtkadjustment.html>} for the horizontal alignment of the viewport.
        
        @returns: the U{GTK Adjustment object<http://developer.gnome.org/pygtk/stable/class-gtkadjustment.html>} for the horizontal alignment of the viewport.
        @rtype: C{U{gtk.Adjustment<http://developer.gnome.org/pygtk/stable/class-gtkadjustment.html>}}
        """
        return self.__hadj
    hadj = property(get_hadjustment, None, None, 'read-only property for the U{GTK Adjustment object<http://developer.gnome.org/pygtk/stable/class-gtkadjustment.html>} for the horizontal alignment of the viewport.')
    
    def __draw_ways(self, area, event):
        """ Callback function for the "expose-event signal"
        
        The method is executed everytime the drawing area receives a redraw signal.
        
        @param area: the GTK widget that received the signal
        @param event: the event that triggered the signal
        """
        self.style = self.__area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]


        # TODO: remove debug code
#        colors = ['#f00', '#0f0', '#00f', '#f0f', '#0ff', '#f0f']
#        color_index = 0
#        boxes_to_draw = [self.__osm_box, self.__street_box, self.__viewport_coordinates]
#        for box_to_draw in boxes_to_draw:
#            self.gc.set_rgb_fg_color(gtk.gdk.Color(colors[color_index]))
#            color_index += 1
#            w, s, e, n = box_to_draw
#            sw_x, sw_y = self.__projection(w, s)
#            nw_x, nw_y = self.__projection(w, n)
#            ne_x, ne_y = self.__projection(e, n)
#            se_x, se_y = self.__projection(e, s)
#            self.__area.window.draw_line(self.gc,
#                                         self.__pixel_x(sw_x), self.__pixel_y(sw_y),
#                                         self.__pixel_x(nw_x), self.__pixel_y(nw_y))
#            self.__area.window.draw_line(self.gc,
#                                         self.__pixel_x(sw_x), self.__pixel_y(sw_y),
#                                         self.__pixel_x(ne_x), self.__pixel_y(ne_y))
#            self.__area.window.draw_line(self.gc,
#                                         self.__pixel_x(sw_x), self.__pixel_y(sw_y),
#                                         self.__pixel_x(se_x), self.__pixel_y(se_y))
#            self.__area.window.draw_line(self.gc,
#                                         self.__pixel_x(ne_x), self.__pixel_y(ne_y),
#                                         self.__pixel_x(nw_x), self.__pixel_y(nw_y))
#            self.__area.window.draw_line(self.gc,
#                                         self.__pixel_x(se_x), self.__pixel_y(se_y),
#                                         self.__pixel_x(nw_x), self.__pixel_y(nw_y))
#            self.__area.window.draw_line(self.gc,
#                                         self.__pixel_x(se_x), self.__pixel_y(se_y),
#                                         self.__pixel_x(ne_x), self.__pixel_y(ne_y))
#            print self.__pixel_x(sw_x), self.__pixel_y(sw_y)
#            print self.__pixel_x(nw_x), self.__pixel_y(nw_y)
#            print self.__pixel_x(ne_x), self.__pixel_y(ne_y)
#            print self.__pixel_x(se_x), self.__pixel_y(se_y)
#        self.gc.set_rgb_fg_color(gtk.gdk.Color(FOREGROUND_COLOR))



        # create the background image if tiles are activated 
        if self.__show_tiles:
            background_image = background_from_tiles(self.__zoom_object.get_tiles(), self.__zoom_object.zoom_level)
            pixbuf = pil_image_to_pixbuf(background_image)
            self.__area.window.draw_pixbuf(self.gc, pixbuf, 0, 0, 0, 0)

        #ways = [self.__osm_object.getWayByID(index) for index in self.__osm_object.way_tree.intersection(self.__osm_object.box, "raw")]
        #way_colors = ['#f00','#0f0', '#00f', '#f0f', '#0ff', '#f0f']
        way_colors = ['#f00','#0f0', '#00f']
        
        # draw the streets
        ways = [self.__osm_object.getWayByID(index) for index in self.__osm_object.street_tree.intersection(self.__street_box, "raw")]
        for way in ways:
            
            # calculate color and thickness of the streets,
            # depending on what is displayed
            self.gc.line_width = 1
            if self.__show_tiles:
                self.gc.line_width += 1
            if self.__show_partitions:
                self.__osm_object.get_partitions()
                if self.__osm_object.get_partitions().recalculate:
                    self.__osm_object.recalculate_partitions()
                partition = way.partition_id
                if self.__osm_object.get_partitions().get_largest_partition() == partition:
                    self.gc.set_rgb_fg_color(gtk.gdk.Color(FOREGROUND_COLOR))
                elif partition == -1:
                    self.gc.line_width += 3
                    self.gc.set_rgb_fg_color(gtk.gdk.Color('#f00'))
                else:
                    self.gc.line_width += 2
                    self.gc.set_rgb_fg_color(gtk.gdk.Color(way_colors[partition % len(way_colors)]))
            
            # find the nodes for drawing the lines
            if 'highway' in way.getTags():
                points = []
                if self.__show_generalized == 0:
                    nodes = way.nodes
                else:
                    # if necessary use the generalized way
                    nodes = way.generalized.get(self.__show_generalized)
                for node in nodes:
                    node_x, node_y = node.get_xy()
                    points.append((self.__pixel_x(node_x), self.__pixel_y(node_y)))
                self.__area.window.draw_lines(self.gc, points)
        
        if self.__show_partitions:
            self.gc.set_rgb_fg_color(gtk.gdk.Color(FOREGROUND_COLOR))
        
        # draw the POI
        if self.__show_poi:
            for node in self.__osm_object.get_poi():
                poi_state = node.get_poi()

                # different colors for the different states of a POI
                if poi_state == POI_CONNECTED:
                    self.gc.set_rgb_fg_color(gtk.gdk.Color('#0f0'))
                elif poi_state == POI_SELECTED:  
                    self.gc.set_rgb_fg_color(gtk.gdk.Color('#00f'))
                elif poi_state == POI_NOT_CONNECTED:  
                    self.gc.set_rgb_fg_color(gtk.gdk.Color('#f00'))
                node_x, node_y = node.get_xy()
                self.__area.window.draw_arc(self.gc, True,
                                            self.__pixel_x(node_x)-POI_SIZE/2,
                                            self.__pixel_y(node_y)-POI_SIZE/2,
                                            POI_SIZE, POI_SIZE, 0, 360*64)
            self.gc.set_rgb_fg_color(gtk.gdk.Color(FOREGROUND_COLOR))
        
    def __pixel_x(self, x):
        """ Calculates for a given geodetic x coordinate the pixel coordinate based on the dimensions of the map
        
        @type x: C{float}
        @param x: geodetic x coordinate
        @returns: pixel coordinate in x direction
        @rtype: C{int}
        """
        return int((x - self.__min_x) * self.__pixel_width / self.__width) + 1

    def __pixel_y(self, y):
        """ Calculates for a given geodetic y coordinate the pixel coordinate based on the dimensions of the map
        
        @type y: C{float}
        @param y: geodetic y coordinate
        @returns: pixel coordinate in y direction
        @rtype: C{int}
        """
        return int((self.__max_y - y) * self.__pixel_height / self.__height) + 1

    def zoom_in(self):
        """ Increases the OSM zoom level by 1 and initializes the recalculation of the map dimensions     
        """
        if self.__zoom_object.zoom_level < 18:
            #self.__street_box = self.__osm_box[:]
            self.__osm_box = self.decrease_box(self.__osm_box)
            self.__zoom_object.zoom_in()
            self.__zoom_object.find_zoom_level(self.__osm_box)
            self.__draw_map()
    
    def zoom_out(self):
        """ Decreases the OSM zoom level by 1 and initializes the recalculation of the map dimensions     
        """
        if self.__zoom_object.zoom_level > 10:
            #self.__osm_box = self.__street_box[:]
            #self.__street_box = self.increase_box(self.__street_box)
            self.__osm_box = self.increase_box(self.__osm_box)
            self.__zoom_object.find_zoom_level(self.__osm_box)
            self.__draw_map()

    def move(self, keyname):
        """ Moves the map and initializes the recalculation of the map dimensions
        
        @param keyname: one of 'Left', 'Right', 'Up' or 'Down'
        """
        d_x = self.__osm_box[2] - self.__osm_box[0]
        d_y = self.__osm_box[3] - self.__osm_box[1]
        if keyname == 'Left':
            self.__osm_box[0] += d_x/2
            self.__osm_box[2] += d_x/2
            #self.__street_box[0] += d_x/2
            #self.__street_box[2] += d_x/2
        if keyname == 'Right':
            self.__osm_box[0] -= d_x/2
            self.__osm_box[2] -= d_x/2
            #self.__street_box[0] -= d_x/2
            #self.__street_box[2] -= d_x/2
        if keyname == 'Up':
            self.__osm_box[1] -= d_y/2
            self.__osm_box[3] -= d_y/2
            #self.__street_box[1] -= d_y/2
            #self.__street_box[3] -= d_y/2
        if keyname == 'Down':
            self.__osm_box[1] += d_y/2
            self.__osm_box[3] += d_y/2
            #self.__street_box[1] += d_y/2
            #self.__street_box[3] += d_y/2
        self.__zoom_object.find_zoom_level(self.__osm_box)
        self.__draw_map()
        
    def increase_box(self, box):
        """ Doubles the size of an OSM bounding box
        
        @type box: C{[min_lon, min_lat, max_lon, max_lat]}
        @param box: OSM bounding box
        @returns: the increased bounding box
        @rtype: C{[min_lon, min_lat, max_lon, max_lat]}
        """
        d_x = box[2] - box[0]
        d_y = box[3] - box[1]
        increased_box = [box[0] - d_x/2,
                         box[1] - d_y/2,
                         box[2] + d_x/2,
                         box[3] + d_y/2]
        return increased_box
 
    def decrease_box(self, box):
        """ Halves the size of an OSM bounding box
        
        @type box: C{[min_lon, min_lat, max_lon, max_lat]}
        @param box: OSM bounding box
        @returns: the decreased bounding box
        @rtype: C{[min_lon, min_lat, max_lon, max_lat]}
        """
        d_x = box[2] - box[0]
        d_y = box[3] - box[1]
        decreased_box = [box[0] + d_x/4,
                         box[1] + d_y/4,
                         box[2] - d_x/4,
                         box[3] - d_y/4]
        return decreased_box   

    def set_show_tiles(self, state):
        """ Sets the state if the OSM tiles are shown
        
        @type state: C{bool}
        @param state: True if the tiles are shown
        """
        self.__show_tiles = state
    show_tiles = property(None, set_show_tiles, None, 'write-only property for the "show tile" state')

    def set_show_poi(self, state):
        """ Sets the state if the points of interest are shown
        
        @type state: C{bool}
        @param state: True if the POI are shown
        """
        self.__show_poi = state
    show_poi = property(None, set_show_poi, None, 'write-only property for the "show POI" state')        

    def set_show_partitions(self, state):
        """ Sets the state if the partitions are shown
        
        @type state: C{bool}
        @param state: True if the partitions are shown
        """
        self.__show_partitions = state
    show_partitions = property(None, set_show_partitions, None, 'write-only property for the "show partitions" state') 

    def set_show_generalized(self, tolerance):
        """ Sets the tolerance value of the generalization that will be used for the map display
        
        @param tolerance: tolerance value of the generalization that will be used for the map display
        """
        self.__show_generalized = tolerance
    show_generalized = property(None, set_show_generalized, None, 'write-only property for the generalization that will be displayed')

#def main():
#    gtk.main()
#    return 0

if __name__ == "__main__":
    pass
