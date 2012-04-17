""" Main window of the MoSP GeoTool

Start this module to run the MoSP GeoTool.
@author: C. Protsch
"""

from geo.osm_export import OSM_export
from geo.osm_import import OSM_objects
from geo.osm_map_rendering import OSMMapRendering
from poi_window import PoiSelectionWindow, PoiConnectionWindow
import app.poi
import gtk
import pygtk
from gui.partition_window import PartitionConnectionWindow, FilterWindow
from gui.generalize_window import GeneralizeWindow
from gui.about_window import AboutWindow
from app.generalize import generalize
pygtk.require("2.0")

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

#w = gtk.gdk.get_default_root_window() 
#p = gtk.gdk.atom_intern('_NET_WORKAREA') 
#width, height = w.property_get(p)[2][2:4]
#WIDTH = int(width * .8)
#HEIGHT = int(height * .8)

MAIN_MONITOR = 0 #: 0 = primary monitor, 1 = secondary monitor, has to be 0 in single monitor mode
WIDTH = int(gtk.gdk.screen_get_default().get_monitor_geometry(MAIN_MONITOR).width * .8)
HEIGHT = int(gtk.gdk.screen_get_default().get_monitor_geometry(MAIN_MONITOR).height * .8)

#WIDTH = int(gtk.gdk.screen_width()*.8)
#HEIGHT = int(gtk.gdk.screen_height()*.8)

#WIDTH = 768
#HEIGHT = 512

MENU_HEIGHT = 50

class MainWindow(object):
    """ Main window of the MoSP GeoTool """
    def __init__(self):

        # set the initial path for the file open dialog
        # TODO: is there a simple method to get the project path?
        self.__path = '../data'
        self.__active_filename = ''
        self.__active_osm_object = None
        self.__map = None
        self.__poi_items = []
        self.__changed = False

        # configure the window, menu, etc.
        self.__main_window = gtk.Window()
        self.__main_window.connect("destroy", lambda w: gtk.main_quit())
        #self.__main_window.connect("destroy", self.__on_quit)
        self.__main_window.connect('key_press_event', self.__on_key_press_event)
        self.__main_window.set_title("MoSP-GeoTool")
        #self.__main_window.set_default_size(WIDTH, HEIGHT)
        self.__main_window.set_size_request(WIDTH, HEIGHT)
        self.__main_window.set_resizable(True)
        
        accel_group = gtk.AccelGroup()
        self.__main_window.add_accel_group(accel_group)
        
        menubar = gtk.MenuBar()
        menubar.set_size_request(WIDTH, MENU_HEIGHT)

        ###### Menu 'File' ######
        file_item = gtk.MenuItem("_File")
        file_item_sub = gtk.Menu()
        open = gtk.MenuItem("_Open...")
        self.__save = gtk.MenuItem("_Save")
        self.__save_as = gtk.MenuItem("Save _As...")
        self.__close = gtk.MenuItem("_Close")
        quit = gtk.MenuItem("_Exit")
        if self.__active_filename == '':
            self.__save.set_sensitive(False)
            self.__save_as.set_sensitive(False)
            self.__close.set_sensitive(False)
        file_item_sub.append(open)
        file_item_sub.append(self.__save)
        file_item_sub.append(self.__save_as)
        file_item_sub.append(self.__close)
        file_item_sub.append(quit)
        file_item.set_submenu(file_item_sub)

        open.connect("activate", self.__on_open)
        open.add_accelerator("activate", accel_group, ord("O"),
                             gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        self.__save.connect("activate", self.__on_save)
        self.__save.add_accelerator("activate", accel_group, ord("S"),
                                    gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        self.__save_as.connect("activate", self.__on_save_as)
        self.__close.connect("activate", self.__on_close)
        self.__close.add_accelerator("activate", accel_group, ord("W"),
                                     gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        quit.connect("activate", self.__on_quit)
        quit.add_accelerator("activate", accel_group, ord("Q"),
                             gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        menubar.append(file_item)


        ###### Menu 'Edit' ######
        self.__edit_item = gtk.MenuItem("_Edit")
        edit_item_sub = gtk.Menu()
        self.__select_poi = gtk.MenuItem("_Select POIs...")
        self.__connect_poi = gtk.MenuItem("_Connect POIs...")
        self.__connect_poi.set_sensitive(False)
        self.__connect_partitions = gtk.MenuItem("Connect _Partitions...")
        self.__filter_streets = gtk.MenuItem("_Filter Streets...")
        self.__apply_filter = gtk.MenuItem("Apply Street Filter")
        self.__apply_filter.set_sensitive(False)
        self.__remove_filter = gtk.MenuItem("Remove Street Filter")
        self.__remove_filter.set_sensitive(False)
        self.__generalize = gtk.MenuItem("_Generalize...")
        self.__apply_generalization = gtk.MenuItem("_Apply Generalization")
        self.__apply_generalization.set_sensitive(False)
        self.__remove_nodes = gtk.MenuItem("Remove Unused Nodes")
        edit_item_sub.append(self.__select_poi)
        edit_item_sub.append(self.__connect_poi)
        edit_item_sub.append(gtk.SeparatorMenuItem())
        edit_item_sub.append(self.__connect_partitions)
        edit_item_sub.append(self.__filter_streets)
        edit_item_sub.append(self.__apply_filter)
        edit_item_sub.append(self.__remove_filter)        
        edit_item_sub.append(gtk.SeparatorMenuItem())
        edit_item_sub.append(self.__generalize)
        edit_item_sub.append(self.__apply_generalization)
        edit_item_sub.append(gtk.SeparatorMenuItem())
        edit_item_sub.append(self.__remove_nodes)
        self.__edit_item.set_submenu(edit_item_sub)
        if self.__active_filename == '':
            self.__edit_item.set_sensitive(False)

        self.__select_poi.connect("activate", self.__on_select_poi)
        self.__connect_poi.connect("activate", self.__on_connect_poi)
        self.__connect_partitions.connect("activate", self.__on_connect_partitions)
        self.__filter_streets.connect("activate", self.__on_filter_streets)
        self.__apply_filter.connect("activate", self.__on_apply_filter)
        self.__remove_filter.connect("activate", self.__on_remove_filter)
        self.__generalize.connect("activate", self.__on_generalize)
        self.__apply_generalization.connect("activate", self.__on_apply_generalization)
        self.__remove_nodes.connect("activate", self.__on_remove_nodes)

        menubar.append(self.__edit_item)


        ###### Menu 'View' ######
        view_item = gtk.MenuItem("_View")
        view_item_sub = gtk.Menu()
        self.__show_tiles = gtk.CheckMenuItem("Show OSM-_Tiles")
        self.__show_partitions = gtk.CheckMenuItem("Show _Partitions")
        self.__zoom_in = gtk.MenuItem("Zoom _In")
        self.__zoom_out = gtk.MenuItem("Zoom _Out")
        
        self.__generalized = gtk.MenuItem('Show _Generalization')
        self.__generalized.set_sensitive(False)
        
        view_item_sub.append(self.__show_tiles)
        view_item_sub.append(self.__show_partitions)
        view_item_sub.append(gtk.SeparatorMenuItem())
        view_item_sub.append(self.__zoom_in)
        view_item_sub.append(self.__zoom_out)
        view_item_sub.append(gtk.SeparatorMenuItem())
        view_item_sub.append(self.__generalized)
        view_item.set_submenu(view_item_sub)
        if self.__active_filename == '':
            self.__zoom_in.set_sensitive(False)
            self.__zoom_out.set_sensitive(False)

        self.__show_tiles.connect("toggled", self.__on_show_tiles)
        self.__show_tiles.add_accelerator("activate", accel_group, ord("t"),
                                          0, gtk.ACCEL_VISIBLE)
        self.__show_partitions.connect("toggled", self.__on_show_partitions)
        self.__show_partitions.add_accelerator("activate", accel_group, ord("p"),
                                          0, gtk.ACCEL_VISIBLE)
        self.__zoom_in.connect("activate", self.__on_zoom_in)
        self.__zoom_in.add_accelerator("activate", accel_group, ord("+"),
                                       0, gtk.ACCEL_VISIBLE)
        self.__zoom_out.connect("activate", self.__on_zoom_out)
        self.__zoom_out.add_accelerator("activate", accel_group, ord("-"),
                                        0, gtk.ACCEL_VISIBLE)

        menubar.append(view_item)


        ###### Menu 'Help' ######        
        help_item = gtk.MenuItem("_Help")        
        help_item_sub = gtk.Menu()
        about = gtk.MenuItem("_About")
        help_item_sub.append(about)
        help_item.set_submenu(help_item_sub)

        about.connect("activate", self.__on_about)

        menubar.append(help_item)
        

        self.__vbox = gtk.VBox()
        self.__vbox.pack_start(menubar)
        
        self.__no_data = gtk.Label('no data loaded')
        self.__map_container = self.__no_data
        #self.__map_container.set_size_request(self.__main_window.get_size()[0], self.__main_window.get_size()[1]-MENU_HEIGHT)
        self.__map_container.set_size_request(WIDTH, HEIGHT)
        self.__vbox.pack_start(self.__map_container)

        self.__main_window.add(self.__vbox)
        self.__main_window.show_all()
    
        self.__last_key = None
    
    def __on_open(self, widget=None):
        
        if self.__changed:
                self.__save_message(widget)

        open_dialog = gtk.FileChooserDialog("Open an OSM file",
                                            action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                            buttons=(gtk.STOCK_CANCEL,
                                                     gtk.RESPONSE_CANCEL,
                                                     gtk.STOCK_OPEN,
                                                     gtk.RESPONSE_OK))
        open_dialog.set_default_response(gtk.RESPONSE_OK)
        
        open_dialog.set_current_folder(self.__path)
        
        # create a file filter to show only osm files
        filter = gtk.FileFilter()
        filter.set_name('OSM file')
        filter.add_mime_type('text/xml')
        filter.add_pattern('*.osm')
        open_dialog.add_filter(filter)
        
        # start the dialog
        open_dialog_response = open_dialog.run()
        
        # start file import and rendering
        # TODO: show something like a progress bar if a large map is opened
        if open_dialog_response == gtk.RESPONSE_OK:
            filename = open_dialog.get_filename()
            self.__path = open_dialog.get_current_folder()
            
            # remove a previously loaded map
            # TODO: check if the old map has been saved
            if self.__map_container:
                self.__vbox.remove(self.__map_container)
            
            self.__active_osm_object = OSM_objects(filename)
            self.__active_osm_object.parse()
            #self.__partitions = PartitionFinder(self.__active_osm_object)
            #self.__map = OSMMapRendering(self.__active_osm_object, (self.__main_window.get_size()[0],self.__main_window.get_size()[1]-MENU_HEIGHT))
            #self.__map = OSMMapRendering(self.__active_osm_object, self.__partitions, (WIDTH, HEIGHT))
            self.__map = OSMMapRendering(self.__active_osm_object, (WIDTH, HEIGHT))
            self.__show_tiles.set_active(False)
            self.__show_partitions.set_active(False)
            self.__map_container = self.__map.getArea()
            self.__vbox.pack_start(self.__map_container)
            self.__main_window.show_all()
            self.__map_container.set_vadjustment(self.__map.vadj)
            self.__map_container.set_hadjustment(self.__map.hadj)
            self.__active_filename = filename
            
            # activate the disabled menu items
            self.__save.set_sensitive(True)
            self.__save_as.set_sensitive(True)
            self.__close.set_sensitive(True)
            self.__edit_item.set_sensitive(True)
            self.__zoom_in.set_sensitive(True)
            self.__zoom_out.set_sensitive(True)
            
            self.__select_poi.set_sensitive(True)
            self.__connect_poi.set_sensitive(False)
            self.__connect_partitions.set_sensitive(True)
            self.__filter_streets.set_sensitive(True)
            self.__apply_filter.set_sensitive(False)
            self.__remove_filter.set_sensitive(False)
            self.__remove_nodes.set_sensitive(True)
            self.__generalize.set_sensitive(True)
            self.__generalized.set_sensitive(False)
            self.__apply_generalization.set_sensitive(False)
 
        # close the dialog
        open_dialog.destroy()
    
    def __on_save(self, widget=None):
        assert self.__active_filename != ''
        OSM_export(self.__active_filename, self.__active_osm_object)
        self.__changed = False
    
    def __on_save_as(self, widget=None):
        assert self.__active_filename != ''
        save_dialog = gtk.FileChooserDialog("Save an OSM file",
                                            action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                            buttons=(gtk.STOCK_CANCEL,
                                                     gtk.RESPONSE_CANCEL,
                                                     gtk.STOCK_SAVE,
                                                     gtk.RESPONSE_OK))
        save_dialog.set_default_response(gtk.RESPONSE_OK)
        save_dialog.set_do_overwrite_confirmation(True)
    
        #save_dialog.set_current_folder(self.__path)
        #save_dialog.set_current_name(self.__active_filename)
        save_dialog.set_filename(self.__active_filename)

        # start the dialog
        save_dialog_response = save_dialog.run()
        if save_dialog_response == gtk.RESPONSE_OK:
            filename = save_dialog.get_filename()
            OSM_export(filename, self.__active_osm_object)
            self.__changed = False

        # close the dialog
        save_dialog.destroy()
        
    def __on_close(self, widget=None):
        if self.__map_container:
            
            if self.__changed:
                self.__save_message(widget)
            
            self.__vbox.remove(self.__map_container)
            self.__map_container = self.__no_data
            self.__vbox.pack_start(self.__map_container)
            self.__main_window.show_all()
            self.__active_osm_object = None
            self.__map = None
            self.__partitions = None
            self.__changed = False
            
            # deactivate some menu items
            self.__save.set_sensitive(False)
            self.__save_as.set_sensitive(False)
            self.__close.set_sensitive(False)
            self.__edit_item.set_sensitive(False)
            self.__zoom_in.set_sensitive(False)
            self.__zoom_out.set_sensitive(False)
            self.__generalized.set_sensitive(False)
            self.__apply_generalization.set_sensitive(False)
            self.__show_tiles.set_active(False)
            self.__show_partitions.set_active(False)
    
    def __on_quit(self, widget=None):
        if self.__changed:
                self.__save_message(widget)
        
        else:        
            exit_message = gtk.MessageDialog(parent=None,
                                               buttons=gtk.BUTTONS_YES_NO,
                                               flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                               type=gtk.MESSAGE_WARNING,
                                               message_format="Do you really want to exit?")
            exit_message.set_title("Exit")
            delete_result = exit_message.run()
            exit_message.destroy()
            if delete_result == gtk.RESPONSE_YES:
                gtk.main_quit()

    def __on_select_poi(self, widget=None):
        if self.__map:
            poi_selec = PoiSelectionWindow(self.__main_window)
            selection = poi_selec.get_selection()
            if selection:
                self.__poi_items.append(selection)
                self.__poi = app.poi.Poi(self.__active_osm_object)
                if self.__poi.get_poi(self.__poi_items):
                    self.__map.show_poi = True
                    self.__map.getArea().queue_draw()
                    
                    self.__connect_poi.set_sensitive(True)
                    
                    self.__connect_partitions.set_sensitive(False)
                    self.__filter_streets.set_sensitive(False)
                    self.__apply_filter.set_sensitive(False)
                    self.__remove_filter.set_sensitive(False)
                    self.__generalize.set_sensitive(False)
                    self.__apply_generalization.set_sensitive(False)
                    self.__remove_nodes.set_sensitive(False)

    def __on_connect_poi(self, widget=None):
        if self.__map:
            poi_connect = PoiConnectionWindow(self.__main_window)
            poi_thresholds = poi_connect.get_connection_thresholds()
            if poi_thresholds:
                self.__poi.connect_poi(poi_thresholds)
                self.__changed = True
                self.__active_osm_object.get_partitions().recalculate = True
                self.__map.getArea().queue_draw()
                
                self.__connect_partitions.set_sensitive(True)
                self.__filter_streets.set_sensitive(True)
                self.__apply_filter.set_sensitive(False)
                self.__remove_filter.set_sensitive(False)
                self.__generalize.set_sensitive(True)
                self.__apply_generalization.set_sensitive(False)
                self.__remove_nodes.set_sensitive(True)

    def __on_connect_partitions(self, widget=None):
        if self.__map:
            partition_connect = PartitionConnectionWindow(self.__main_window)
            partition_thresholds = partition_connect.get_connection_thresholds()
            if partition_thresholds:
                self.__active_osm_object.get_partitions().connect_partitions(partition_thresholds)
                self.__map.getArea().queue_draw()
                self.__changed = True

    def __on_filter_streets(self, widget=None):
        if self.__map:
            filter_window = FilterWindow(self.__main_window)
            street_filter = filter_window.get_selection()
            if street_filter:
                filtered = self.__active_osm_object.get_partitions().filter_streets(street_filter)
                if filtered:
                    self.__show_partitions.set_active(True)
                    self.__toggle_partitions()
                    
                    self.__filter_streets.set_sensitive(False)
                    self.__apply_filter.set_sensitive(True)
                    self.__remove_filter.set_sensitive(True)
                    
                    self.__select_poi.set_sensitive(False)
                    self.__connect_poi.set_sensitive(False)
                    self.__connect_partitions.set_sensitive(False)
                    self.__generalize.set_sensitive(False)
                    self.__apply_generalization.set_sensitive(False)
                    self.__remove_nodes.set_sensitive(False)

    def __on_apply_filter(self, widget=None):
        if self.__map:
            self.__active_osm_object.get_partitions().remove_filtered_streets()
            self.__map.getArea().queue_draw()
            
            self.__changed = True

            self.__filter_streets.set_sensitive(True)
            self.__apply_filter.set_sensitive(False)
            self.__remove_filter.set_sensitive(False)
            
            self.__select_poi.set_sensitive(True)
            self.__connect_poi.set_sensitive(False)
            self.__connect_partitions.set_sensitive(True)
            self.__generalize.set_sensitive(True)
            self.__apply_generalization.set_sensitive(False)
            self.__remove_nodes.set_sensitive(True)
            
    def __on_remove_filter(self, widget=None):
        if self.__map:
            self.__active_osm_object.get_partitions().reset_partitions()
            self.__active_osm_object.get_partitions().find_partitions()
            self.__map.getArea().queue_draw()
            
            self.__filter_streets.set_sensitive(True)
            self.__apply_filter.set_sensitive(False)
            self.__remove_filter.set_sensitive(False)
            
            self.__select_poi.set_sensitive(True)
            self.__connect_poi.set_sensitive(False)
            self.__connect_partitions.set_sensitive(True)
            self.__generalize.set_sensitive(True)
            self.__apply_generalization.set_sensitive(False)
            self.__remove_nodes.set_sensitive(True)
                            
    def __on_generalize(self, widget=None):
        if self.__map:
            gw = GeneralizeWindow(self.__main_window)
            tolerance = gw.get_tolerance()
            if tolerance:
                print 'tolerance:', tolerance
                generalize(self.__active_osm_object, tolerance)
                
                self.__gen_list = gtk.Menu()
                default_item = gtk.RadioMenuItem(None,"None")
                default_item.connect("toggled", self.__on_show_generalized)
                self.__gen_list.append(default_item)
                for t in sorted(self.__active_osm_object.generalized):
                    list_item = gtk.RadioMenuItem(default_item,'%s'%t)
                    list_item.connect("toggled", self.__on_show_generalized, t)
                    self.__gen_list.append(list_item)
                    if t == tolerance:
                        list_item.set_active(True)
                self.__generalized.set_submenu(self.__gen_list)
                self.__generalized.set_sensitive(True)
                self.__apply_generalization.set_sensitive(True)
                
                self.__select_poi.set_sensitive(False)
                self.__connect_poi.set_sensitive(False)
                self.__connect_partitions.set_sensitive(False)
                self.__filter_streets.set_sensitive(False)
                self.__apply_filter.set_sensitive(False)
                self.__remove_filter.set_sensitive(False)
                self.__remove_nodes.set_sensitive(False)
                
                self.__main_window.show_all()

    def __on_apply_generalization(self, widget=None):
        if self.__active_osm_object:
            for item in self.__gen_list.get_children():
                if item.get_active():
                    tolerance = int(item.get_label())
            #TODO: remove debug code
            #for node in self.__active_osm_object.node_objects:
            #    print len(node.neighbours)
            ways = [self.__active_osm_object.getWayByID(index) for index in self.__active_osm_object.street_tree.intersection(self.__active_osm_object.box, "raw")]
            for way in ways:
                way.apply_generalization(tolerance)
            self.__active_osm_object.reset_generalized()
            self.__generalized.set_sensitive(False)
            self.__apply_generalization.set_sensitive(False)
            self.__map.show_generalized = 0
            self.__active_osm_object.get_partitions().recalculate = True

            self.__changed = True
            
            self.__select_poi.set_sensitive(True)
            self.__connect_poi.set_sensitive(False)
            self.__connect_partitions.set_sensitive(True)
            self.__filter_streets.set_sensitive(True)
            self.__apply_filter.set_sensitive(False)
            self.__remove_filter.set_sensitive(False)
            self.__remove_nodes.set_sensitive(True)
            
            #TODO: remove debug code
            #for node in self.__active_osm_object.node_objects:
            #    print len(node.neighbours)

    def __on_remove_nodes(self, widget=None):
        self.__active_osm_object.remove_unused_nodes()
        self.__changed = True

    def __on_show_tiles(self, widget=None):
        self.__toggle_tiles()

    def __on_show_partitions(self, widget=None):
        #self.__active_osm_object.get_partitions().filter_streets('bla')
        self.__toggle_partitions()

    def __on_zoom_in(self, widget=None):
        if self.__map:                
            self.__map.zoom_in()
            self.__apply_map_change()

    def __on_zoom_out(self, widget=None):
        if self.__map:                
            self.__map.zoom_out()
            self.__apply_map_change()

    def __on_show_generalized(self, widget=None, tolerance=0):
        if self.__map:
            if widget.get_active():
                self.__toggle_generalized(tolerance)
    
    def __on_about(self, widget=None):
        about_connect = AboutWindow(self.__main_window)
                
    def __save_message(self, widget):
        save_message = gtk.MessageDialog(parent=None, buttons=gtk.BUTTONS_NONE, 
                                         flags=gtk.DIALOG_DESTROY_WITH_PARENT, 
                                         type=gtk.MESSAGE_WARNING, 
                                         message_format="Save changes?")
        save_message.add_buttons(gtk.STOCK_CANCEL,
                                 gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_CLOSE,
                                 gtk.RESPONSE_CLOSE,
                                 gtk.STOCK_SAVE,
                                 gtk.RESPONSE_OK)
        
        save_message_response = save_message.run()
        
        if save_message_response == gtk.RESPONSE_CANCEL or save_message_response == gtk.RESPONSE_DELETE_EVENT:
            save_message.destroy()
            return
        
        elif save_message_response == gtk.RESPONSE_OK:
            self.__on_save(widget)
        
        save_message.destroy()   

    def __on_key_press_event(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        # TODO: remove debug message
        #print "Key %s (%d) was pressed" % (keyname, event.keyval)
        if self.__map:
            
            # '+' and '-' are already covered by the accelerator keys
            if keyname == 'i':                
                self.__map.zoom_in()
                self.__apply_map_change()

            if keyname == 'o' and self.__last_key != 'Control_L' and self.__last_key != 'Control_R':
                self.__map.zoom_out()
                self.__apply_map_change()
                
            elif keyname in ['Left', 'Right', 'Up', 'Down']:
                self.__map.move(keyname)
                self.__apply_map_change()

            self.__last_key = keyname

        if keyname == 'T':
            self.__show_tiles.set_active(not self.__show_tiles.get_active())
            self.__toggle_tiles()

        if keyname == 'P':
            self.__show_partitions.set_active(not self.__show_partitions.get_active())
            self.__toggle_partitions()
                

    def __apply_map_change(self):
        if self.__map_container:
            self.__vbox.remove(self.__map_container)
        self.__map_container = self.__map.getArea()
        self.__vbox.pack_start(self.__map_container)
        self.__main_window.show_all()
        self.__map_container.set_vadjustment(self.__map.vadj)
        self.__map_container.set_hadjustment(self.__map.hadj)

    def __toggle_tiles(self):
        if self.__map:
            self.__map.show_tiles = self.__show_tiles.get_active()
            self.__map.getArea().queue_draw()

    def __toggle_partitions(self):
        if self.__map:
            show_partitions = self.__show_partitions.get_active()
            self.__map.show_partitions = show_partitions
            self.__map.getArea().queue_draw()

    def __toggle_generalized(self, tolerance):
        if self.__map:
            self.__map.show_generalized = tolerance
            self.__apply_map_change()
            if tolerance == 0:
                self.__apply_generalization.set_sensitive(False)
            else:
                self.__apply_generalization.set_sensitive(True)
            

def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    MainWindow()
    main()
