""" Dialogue window for the line generalization application 
@author: C. Protsch
"""

import gtk

__author__ = "C. Protsch"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

class GeneralizeWindow(object):
    """ Dialogue window to start the line generalization application """
    def __init__(self, parent):
        self.__tolerance = ''
        generalize_window = gtk.Dialog("Generalize",
                                       parent,
                                       gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        tolerance_label = gtk.Label("Enter tolerance value (meter)")
        tolerance_field = gtk.Entry()
        tolerance_field.set_text("10")

        generalize_window.vbox.pack_start(tolerance_label)
        generalize_window.vbox.pack_start(tolerance_field)
        generalize_window.show_all()
        response = generalize_window.run()
        
        if response == gtk.RESPONSE_ACCEPT:
            tolerance = int(tolerance_field.get_text())
            if tolerance > 0:
                self.__tolerance = tolerance
        
        generalize_window.destroy()
        
    def get_tolerance(self):
        return (self.__tolerance)
