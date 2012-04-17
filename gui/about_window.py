# -*- coding: iso-8859-15 -*-
""" Dialogue window About the authors
@author: B. Henne
"""

import gtk

__author__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2011, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

class AboutWindow(object):
    
    def __init__(self, parent):
        generalize_window = gtk.Dialog("About",
                                       parent,
                                       gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                       (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        label = gtk.Label(' <b>Mobile Security &amp; Privacy Simulator: Geo Tool</b> \n <i> by Carsten Protsch, Benjamin Henne</i> \n <a href="http://www.dcsec.uni-hannover.de/">Distributed Computing &amp; Security Group</a>, \n Leibniz Universität Hannover, Germany\n')
        label.set_use_markup(True)

        generalize_window.vbox.pack_start(label)
        generalize_window.show_all()
        response = generalize_window.run()
        
        generalize_window.destroy()
