""" The module geo.zoom provides methods to calculate and store the dimensions of a map
displayed in the MoSP GeoTool
@author: C. Protsch
"""

from tilenames import tileXY, tileEdges

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

TILE_SIZE = 256 #: pixel size of the OSM tiles

class ZoomObject(object):
    """ An instance of the ZoomObject class calculates and stores the dimensions of the displayed map
    
    On initialization the best zoom level is calculated so that the map is
    fully displayed within the viewport of the MoSP GeoTool.
    Everytime a map is moved or zoomed the dimensions of the map (pixel and geographic coordinates)
    are recalculated by calling the method L{find_zoom_level}
    """
    
    
    def __init__(self, size):
        """
        
        @type size: (int, int)
        @param size: window size in pixels as a tuple C{(width, height)}
        """
        width, height = size
        self.__window_width = width #: window width in pixels
        self.__window_height = height #: window height in pixels
        self.__zoom_level = 18	#: stores the OSM zoom level of the ZoomObject
   
    def find_zoom_level(self, box):
        """ Finds for a given bounding box the best zoom level so that the box fits into the screen. 
        
        @type box: C{[min_lat, min_lon, max_lat, max_lon]}
        @param box: OSM bounding box
        """
        self.__selection_box = box #: initial bounding box
        
        d_x, d_y = self.box_size_in_pixels(box)
        
        # decrease the zoom level until the box fits into the screen
        while d_x > self.__window_width or d_y > self.__window_height:
            self.__zoom_level -= 1
            d_x, d_y = self.box_size_in_pixels(box)
            
        self.__tiles_zoom_level = self.get_box_tiles(box) #: stores the U{slippy map tilenames<http://wiki.openstreetmap.org/index.php/Slippy_map_tilenames>} of the tiles that will be displayed in the windows of the MoSP-GeoTool
        self.__d_tiles_x, self.__d_tiles_y = [(self.__tiles_zoom_level[1][i] - self.__tiles_zoom_level[0][i] + 1) for i in range(2)]

    def box_size_in_pixels(self, box):
        """ Calculates for a given bounding box the pixel size of the box at the zoom level of the ZoomObject.
        
        @type box: C{[min_lat, min_lon, max_lat, max_lon]}
        @param box: OSM bounding box
        @returns: the width and height of the bounding box in pixels as a tuple (width, height)
        @rtype: C{(int, int)}
        """
        # find the tiles of the box edges at a given zoom level
        # NW, SE
        tiles_zoom_level = self.get_box_tiles(box)
        
        # calculate the number of intersected tiles
        d_tiles_x, d_tiles_y = [(tiles_zoom_level[1][i] - tiles_zoom_level[0][i] + 1) for i in range(2)]
        
        # calculate the distance in pixels of the box edges
        x1, y1 = self.get_position_in_tile(box[3], box[0])
        x2, y2 = self.get_position_in_tile(box[1], box[2])
        d_x = d_tiles_x * TILE_SIZE - x1 - (TILE_SIZE - x2)
        d_y = d_tiles_y * TILE_SIZE - y1 - (TILE_SIZE - y2)
        return (d_x, d_y)

    def get_box_tiles(self, box):
        """ Calculates for a given bounding box the
        U{slippy map tilenames<http://wiki.openstreetmap.org/index.php/Slippy_map_tilenames>}
        of the tiles that are intersected by the bounding box.
        
        The calculated tiles are given by the U{slippy map tilenames<http://wiki.openstreetmap.org/index.php/Slippy_map_tilenames>}
        of the top/left edge tile and the bottom/right edge tile.
        
        @type box: C{[min_lat, min_lon, max_lat, max_lon]}
        @param box: OSM bounding box
        @returns: slippy map tile names of the top/left tile and right/bottom tile of a rectangular box in the format C{[(topleft_x, topleft_y), (bottomright_x, bottomright_y)]}
        @rtype: C{[(int, int), (int, int)]}
        """
        return [tileXY(box[3], box[0], self.__zoom_level),
                tileXY(box[1], box[2], self.__zoom_level)]

    def tile_box(self):
        """ Expands the bounding box to the next even tile box.
        
        If the previously calculated box of tiles is smaller than the window size
        tiles are added until the box is larger than the window size
        
        @returns: the geographic coordinates of the bounding box of the displayed tiles
        @rtype: [min_lon, min_lat, max_lon, max_lat]
        """ 
        (min_x, max_y), (max_x, min_y) = self.__tiles_zoom_level
        while self.__d_tiles_x * TILE_SIZE < self.__window_width:
            self.__d_tiles_x += 1 #: stores the number of displayed tiles in x-direction
            max_x += 1
        while self.__d_tiles_y * TILE_SIZE < self.__window_height:
            self.__d_tiles_y += 1 #: stores the number of displayed tiles in y-direction
            min_y += 1
        
        # recalculate the tiles that will be displayed
        self.__tiles_zoom_level = [(min_x, max_y), (max_x, min_y)]
        # calculate the geographic coordinates of the edges
        s1, w1, n1, e1 = tileEdges(min_x, max_y, self.__zoom_level)
        s2, w2, n2, e2 = tileEdges(max_x, min_y, self.__zoom_level)
        
        # calculate the expansion of the displayed tiles in pixels
        self.__box_pixel = (self.__d_tiles_x * TILE_SIZE, self.__d_tiles_y * TILE_SIZE) #: pixel size of the box spanned by the displayed tiles (width, height)
        return [w1, s2, e2, n1]
    
    def get_tile_coordinates(self, lat, lon):
        """ Gets for a point given by its geographic coordinates the geographic coordinates of the edges
        of the tile this point lies in.
        
        @param lat: Geographic latitude of a point
        @param lon: Geographic longitude of a point
        @returns: Geographic coordinates of the edges of the corresponding tile
        @rtype: (min_lat, min_lon, max_lat, max_lon)
        """
        x, y = tileXY(lat, lon, self.__zoom_level)
        return tileEdges(x, y, self.__zoom_level) # S, W, N, E
    
    def get_position_in_tile(self, lat, lon):
        """ Calculates the position of a point within its tile.
        
        @param lat: Geographic latitude of a point
        @param lon: Geographic longitude of a point
        @returns: the distance in pixels from the left and the top as a tuple (x, y)
        @rtype: C{(int, int)}
        """
        s, w, n, e = self.get_tile_coordinates(lat, lon)
        x = int(TILE_SIZE * (lon - w) / (e - w))
        y = int(TILE_SIZE * (lat - n) / (s - n))
        return (x, y)
    
    def get_coord_by_position_in_tile(self, tile_x, tile_y, x, y):
        """ Calculates for the pixel coordinates of a point within a tile the corresponding geographic cordinates
        
        @type tile_x: C{int}
        @param tile_x: slippy map tilename in x direction
        @type tile_y: C{int}
        @param tile_y: slippy map tilename in y direction
        @type x: C{int}
        @param x: x coordinate within the tile
        @type y: C{int}
        @param y: y coordinate within the tile
        @returns: Geographic coordinates of the point as a tuple (lat, lon)
        @rtype: C{lat, lon)}
        """
        s, w, n, e = tileEdges(tile_x, tile_y, self.__zoom_level)
        lat = y * (s - n) / TILE_SIZE + n
        lon = x * (e - w) / TILE_SIZE + w
        return (lat, lon)
        
    def viewport_coordinates(self):
        """ Calculates the geographic coordinates of the edges of the MoSP-GeoTool viewport
        
        @returns: the geographic coordinates of the viewport
        @rtype: C{[min_lon, min_lat, max_lon, max_lat]}         
        """
        position_nw = self.get_position_in_tile(self.__selection_box[3], self.__selection_box[0])
        (tile_w, tile_n) = tileXY(self.__selection_box[3], self.__selection_box[0], self.__zoom_level)
        tiles_x = (position_nw[0] + self.__window_width) / TILE_SIZE
        tiles_y = (position_nw[1] + self.__window_height) / TILE_SIZE
        x = TILE_SIZE - ((tiles_x + 1) * TILE_SIZE - (position_nw[0] + self.__window_width))
        y = TILE_SIZE - ((tiles_y + 1) * TILE_SIZE - (position_nw[1] + self.__window_width))
        tile_e = tile_w + tiles_x
        tile_s = tile_n + tiles_y
        coord_se = self.get_coord_by_position_in_tile(tile_e, tile_s, x, y)
        return [self.__selection_box[0], coord_se[0], coord_se[1], self.__selection_box[3]]
    
    def tile_box_pixel(self):
        """ Gets the pixel size of the box spanned by the displayed tiles
        
        @returns: the pixel size of the box spanned by the displayed tiles as a tuple (width, height)
        @rtype: C{(int, int)}
        """
        return self.__box_pixel
     
    def get_tiles(self):
        """ Gets the slippy map tilenames of the displayed tiles
        
        @returns: slippy map tile names of the top/left tile and right/bottom tile of the displayed tiles in the format C{[(topleft_x, topleft_y), (bottomright_x, bottomright_y)]}
        @rtype: C{[(int, int), (int, int)]}
        """
        return self.__tiles_zoom_level
    
    def get_zoom_level(self):
        """ Gets the zoom level of the ZoomObject
        
        @returns: the zoom level of the ZoomObject
        @rtype: C{int}
        """
        return self.__zoom_level
    zoom_level = property(get_zoom_level, None, None, 'read-only property for the zoom level of the ZoomObject')

    def zoom_in(self):
        """ Increases the zoom_level instance variable by one """
        self.__zoom_level += 1        
    
    def zoom_out(self):
        pass

if __name__ == "__main__":
    pass
