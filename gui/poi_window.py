""" Dialogue windows to select the points of interests
and to connect the POI with the street network
@author: C. Protsch
"""

import gtk

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

class PoiSelectionWindow(object):
    """ Dialogue window to select the points of interests """
    def __init__(self, parent):
        self.__key = None
        self.__value = None
        poi_selec_window = gtk.Dialog("POI selection",
                                        parent,
                                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        key_label = gtk.Label("Enter key")
        key_field = gtk.Entry()
        value_label = gtk.Label("Enter value ('*' for all)")
        value_field = gtk.Entry()
        
        poi_selec_window.vbox.pack_start(key_label)
        poi_selec_window.vbox.pack_start(key_field)
        poi_selec_window.vbox.pack_start(value_label)
        poi_selec_window.vbox.pack_start(value_field)
        poi_selec_window.show_all()
        response = poi_selec_window.run()
        
        if response == gtk.RESPONSE_ACCEPT:
            self.__key = key_field.get_text()
            self.__value = value_field.get_text()
        
        poi_selec_window.destroy()
        
    def get_selection(self):
        if self.__key and self.__value:
            return (self.__key,self.__value)
        else:
            return None

class PoiConnectionWindow(object):
    """ Dialogue window to connect the points of interest with the street network """
    def __init__(self, parent):
        self.__thresholds = {}
        poi_connect_window = gtk.Dialog("POI connection",
                                        parent,
                                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        table = gtk.Table(4, 2, True)
        
        table_head_type = gtk.Label("Threshold Type")
        table_head_value = gtk.Label("Threshold Value")
        
        distance_label = gtk.Label("Search Distance (meter)")
        distance_field = gtk.Entry()
        distance_field.set_text("100")

        projection_label = gtk.Label("Projection Threshold (meter)")
        projection_field = gtk.Entry()
        projection_field.set_text("10")        

        address_label = gtk.Label("Address Threshold (meter)")
        address_field = gtk.Entry()
        address_field.set_text("20")
        
        table.attach(table_head_type, 0, 1, 0, 1)
        table.attach(table_head_value, 1, 2, 0, 1)
        table.attach(distance_label, 0, 1, 1, 2)
        table.attach(distance_field, 1, 2, 1, 2)
        table.attach(projection_label, 0, 1, 2, 3)
        table.attach(projection_field, 1, 2, 2, 3)
        table.attach(address_label, 0, 1, 3, 4)
        table.attach(address_field, 1, 2, 3, 4)
                
        poi_connect_window.vbox.pack_start(table)

        poi_connect_window.show_all()
        response = poi_connect_window.run()
        
        if response == gtk.RESPONSE_ACCEPT:
            self.__thresholds.setdefault('search',distance_field.get_text())
            self.__thresholds.setdefault('projection',projection_field.get_text())
            self.__thresholds.setdefault('address',address_field.get_text())
        
        poi_connect_window.destroy()
        
    def get_connection_thresholds(self):
        return self.__thresholds
