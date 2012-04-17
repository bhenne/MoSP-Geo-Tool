""" Dialogue windows to start the connection of partitions and to filter streets
@author: C. Protsch
"""
import gtk

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

class PartitionConnectionWindow(object):
    """ Dialogue window to start the connection of partitions """
    def __init__(self, parent):
        self.__thresholds = {}
        partition_connect_window = gtk.Dialog("Partition connection",
                                        parent,
                                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        table = gtk.Table(6, 2, True)
        
        table_head_type = gtk.Label("Threshold Type")
        table_head_value = gtk.Label("Threshold Value")
        
        distance_label = gtk.Label("Search Distance (meter)")
        distance_field = gtk.Entry()
        distance_field.set_text("100")

        projection_label = gtk.Label("Projection Threshold (meter)")
        projection_field = gtk.Entry()
        projection_field.set_text("10")  

        size_label = gtk.Label("Minimum Partition Size (#)")
        size_field = gtk.Entry()
        size_field.set_text("3")

        connection_label = gtk.Label("Maximum Connections (#)")
        connection_field = gtk.Entry()
        connection_field.set_text("2")

        connection_distance_label = gtk.Label("Minimum Node Distance (meter)")
        connection_distance_field = gtk.Entry()
        connection_distance_field.set_text("20")
     
        table.attach(table_head_type, 0, 1, 0, 1)
        table.attach(table_head_value, 1, 2, 0, 1)
        table.attach(distance_label, 0, 1, 1, 2)
        table.attach(distance_field, 1, 2, 1, 2)
        table.attach(projection_label, 0, 1, 2, 3)
        table.attach(projection_field, 1, 2, 2, 3)
        table.attach(size_label, 0, 1, 3, 4)
        table.attach(size_field, 1, 2, 3, 4)
        table.attach(connection_label, 0, 1, 4, 5)
        table.attach(connection_field, 1, 2, 4, 5)
        table.attach(connection_distance_label, 0, 1, 5, 6)
        table.attach(connection_distance_field, 1, 2, 5, 6)
                   
        partition_connect_window.vbox.pack_start(table)

        partition_connect_window.show_all()
        response = partition_connect_window.run()
        
        if response == gtk.RESPONSE_ACCEPT:
            self.__thresholds.setdefault('search',distance_field.get_text())
            self.__thresholds.setdefault('projection',projection_field.get_text())
            self.__thresholds.setdefault('size',size_field.get_text())
            self.__thresholds.setdefault('connection',connection_field.get_text())
            self.__thresholds.setdefault('distance',connection_distance_field.get_text())
   
        partition_connect_window.destroy()
        
    def get_connection_thresholds(self):
        return self.__thresholds

class FilterWindow(object):
    """ Dialogue window to select street types that will be filtered """
    def __init__(self, parent):
        self.__filter = []
        
        filter_selec_window = gtk.Dialog("Filter selection",
                                         parent,
                                         gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                         (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                          gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        highway_types = ['motorway','motorway_link',
                         'trunk', 'trunk_link']
        
        checkbox_list = []
        
        for highway in highway_types:
            checkbox = gtk.CheckButton(highway)
            checkbox_list.append(checkbox)
            filter_selec_window.vbox.pack_start(checkbox)

        filter_selec_window.show_all()
        response = filter_selec_window.run()

        if response == gtk.RESPONSE_ACCEPT:
            for checkbox in checkbox_list:
                if checkbox.get_active():
                    self.__filter.append(checkbox.get_label())
           
                   
        filter_selec_window.destroy()
        
    def get_selection(self):
        return self.__filter
