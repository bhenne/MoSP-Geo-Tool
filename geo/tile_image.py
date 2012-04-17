""" The module C{geo.tile_images} provides methods to convert OSM tiles to a background image
of a map displayed in the MoSP GeoTool.
@author: C. Protsch
"""

from PIL import Image
import StringIO
import gtk
import os
import urllib

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

TILE_SIZE = 256	#: pixel size of the OSM tiles
path = '../data/osm-tiles/' #: path to the directory where the tiles are saved

def background_from_tiles(tile_box, zoom_level):
    """ The method creates for an area given by a rectangular box of OSM tiles and an OSM zoom level a U{Python Imaging Library (PIL)<http://www.pythonware.com/products/pil/>} image.

    The rectangular box is given by the U{slippy map tilenames<http://wiki.openstreetmap.org/index.php/Slippy_map_tilenames>} of the OSM tiles of the top/left edge and the bottom/right edge.
    
    @type tile_box: C{[(int, int), (int, int)]}
    @param tile_box: slippy map tile names of the top/left tile and right/bottom tile of a rectangular box in the format C{[(topleft_x, topleft_y), (bottomright_x, bottomright_y)]}
    @type zoom_level: C{int}
    @param zoom_level: the OSM zoomlevel of the background image
    
    @returns: PIL image object
    @rtype: C{PIL.Image}
    """
    # tile_box: slippy map tile IDs [(left, top), (right, bottom)]
    
    d_tile_x, d_tile_y = [(tile_box[1][i] - tile_box[0][i] + 1) for i in range(2)]
    
    zoom_path = '%s%s/' % (path, zoom_level)
    
    # create an empty RGB PIL image object with the correct size
    background = Image.new("RGB", (d_tile_x * TILE_SIZE, d_tile_y * TILE_SIZE))
    
    pos_y = 0

    # calculate the remote and local paths
    for tile_y in range(tile_box[0][1], tile_box[1][1] + 1):
        pos_x = 0
        for tile_x in range(tile_box[0][0], tile_box[1][0] + 1):
            image_folder_path = '%s%s/' % (zoom_path,tile_x)
            image_path = '%s%s.png' % (image_folder_path, tile_y)
            
            # download the image only if it doesn't already exist
            if not os.access(image_path,os.F_OK):
                if not os.access(image_folder_path, os.F_OK):
                    # create the local folders if they don't exist
                    os.makedirs(image_folder_path)
                remote_path = 'http://a.tile.openstreetmap.org/%s/%s/%s.png' % (zoom_level, tile_x, tile_y)
                # download the image from remote_path and save it to image_path
                try:
                    urllib.urlretrieve (remote_path, image_path)
                # use an empty image if the download failed
                except IOError:
                    image_path = '%snot_available.png' % path
                    
            # open the single tile image ...
            tile = Image.open(image_path)
            # ... and put it at the correct position of the created image
            background.paste(tile, (pos_x * TILE_SIZE, pos_y* TILE_SIZE))
                
            pos_x += 1
        pos_y += 1
    return background

def pil_image_to_pixbuf(image):
    """ Converts a U{Python Imaging Library (PIL)<http://www.pythonware.com/products/pil/>} image to a U{GTK Pixbuf<http://developer.gnome.org/pygtk/stable/class-gdkpixbuf.html>}
    
    @see: taken from U{http://faq.pygtk.org/index.py?req=show&file=faq08.007.htp}
    @author: Sebastian Wilhelmi
    @type image: C{PIL.Image}
    @param image: PIL image object that shall be converted
    @returns: a gtk.gdk.Pixbuf object of the image
    @rtype: C{gtk.gdk.Pixbuf}
    """
    fd = StringIO.StringIO()
    image.save(fd, "ppm")
    contents = fd.getvalue()
    fd.close()
    loader = gtk.gdk.PixbufLoader("pnm")
    loader.write(contents, len(contents))
    pixbuf = loader.get_pixbuf()
    loader.close()
    return pixbuf
