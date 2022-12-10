# -*- coding: utf-8 -*-
#!/usr/bin/env python
# displayExiv2 module
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009-2011 Rob G. Healey <robhealey1@gmail.com>
#               2019      Paul Culley <paulr2787@gmail.com>
#               2022      Arnold Wiegert nscg111@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

#-------------------------------------------------------------------------
#
# GNOME modules
#
#-------------------------------------------------------------------------
from gi.repository import GObject, Gtk

## display image metadata using GExiv2 library instead of Exiftool
# *****************************************************************************
# Python Modules
# *****************************************************************************
import os

"""
Display Exiv2 Gramplet
"""
#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from gramps.gen.plug import Gramplet
from gramps.gen.utils.file import media_path_full
from gi.repository import Gtk
import gi
gi.require_version('GExiv2', '0.10')
from gi.repository import GExiv2
##from gi.repository.GExiv2 import Metadata

# code from: - only good for JPGs
# https://www.thepythoncode.com/article/extracting-image-metadata-in-python
from PIL import Image
from PIL.ExifTags import TAGS



#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------

from gramps.gui.listmodel import ListModel
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
from gramps.gen.utils.place import conv_lat_lon
from fractions import Fraction
from gramps.gen.lib import Date
from gramps.gen.datehandler import displayer
from datetime import datetime

# ----------------------------------------------------------

class DisplayExiv2(Gramplet):
    """
    Displays the metadata of an image.
    """
    
    def init(self):
        self.defer_draw = False
        self.defer_draw_id = None
        self.set_text( "Exiv2 Metadata" )
        gexiv2Version = GExiv2.get_version()
        self.gui.WIDGET = self.build_gui()
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add(self.gui.WIDGET)
        self.gui.WIDGET.show()
    
    # ----------------------------------------------------------    
    def db_changed(self):
        self.connect_signal('Media', self.update)
    
    # ----------------------------------------------------------
    def build_gui(self):
        """
        Build the GUI interface.
        """
        self.view = MetadataView3()
        return self.view
    # ----------------------------------------------------------
    def main(self):
        if not self.defer_draw_id:
            self.defer_draw_id = GObject.timeout_add(250, self.handle_draw)
        else:
            self.defer_draw = True

    def handle_draw(self):
        if self.defer_draw:
            self.defer_draw = False
            return True
        self.defer_draw = False
        active_handle = self.get_active('Media')
        if active_handle:
            media = self.dbstate.db.get_media_from_handle(active_handle)
            if media:
                full_path = media_path_full(self.dbstate.db, media.get_path())
                has_data = self.view.display_metadata(full_path)
                self.set_has_data(has_data)
            else:
                self.set_has_data(False)
        else:
            self.set_has_data(False)
        GObject.source_remove(self.defer_draw_id)
        self.defer_draw_id = None
        return False

# ----------------------------------------------------------

class MetadataView3(Gtk.TreeView):

    def __init__(self):
        Gtk.TreeView.__init__(self)
        self.sections = {}
        titles = [(_('Key'), 1, 235),
                  (_('Value'), 2, 325)]
        self.model = ListModel(self, titles, list_mode="tree")


    # ----------------------------------------------------------
    def display_metadata(self, full_path):
        """
        Display the metadata
        """
        self.sections = {}
        self.model.clear()

        ver = GExiv2.get_version()
        """ Make sure the file exists"""
        if not os.path.exists(full_path):
            head, tail = os.path.split( full_path )
            label = tail  
            node = self.__add_section('File not found')
            label = tail
            human_value = head
            self.model.add((label, human_value), node=node)  
            return False

        lastLeadin = ""
        retval = False
        #logLeadIn = True 
        logLeadIn = False
        #logData = True 
        logData = False
   
        with open(full_path, 'rb') as fd:
            try:
                buf = fd.read()
                metadata = GExiv2.Metadata()
                metadata.open_buf(buf)
                # # add header to identify GExiv2
                label = 'GExiv2 Version'
                node = self.__add_section("Metadata")
                self.model.add((label, GExiv2._version), node=node)
                self.model.add((label, str(ver) ), node=node)


                get_human = metadata.get_tag_interpreted_string
                # handle Exif tags
                for key in metadata.get_exif_tags():
                    tagType = metadata.get_tag_type(key)
                    label = metadata.get_tag_label(key)
                    human_value = get_human(key)
                    leadin = key.split('.',2)
                    section = leadin[0]
                    if logData:
                        print(f"{key:50}: {human_value}")
                    if lastLeadin != section: 
                        lastLeadin = section
                        if logLeadIn:
                            print( "  section: " + section +" lastLeadin: " + lastLeadin + "\n" ) 
                        
                    node = self.__add_section(section)
                    if human_value is None:
                        human_value = ''
                    self.model.add((label, human_value), node=node)

                # handle IPTC tags
                for key in metadata.get_iptc_tags():
                    label = metadata.get_tag_label(key)
                    human_value = get_human(key)
                    leadin = key.split('.',3)
                    section = leadin[0]
                    if logData:
                        print(f"{key:50}: {human_value}")
                    if lastLeadin != section:
                        lastLeadin = section
                        if logLeadIn:
                            print( "  section: " + section +" lastLeadin: " + lastLeadin + "\n" ) 
                        
                    cleanName = leadin[2]
                    # See the IPTC Spec IIMV4.1.pdf
                    if cleanName == "CharacterSet":
                        if human_value == "\x1b%G":
                            human_value = 'UTF8 - ESC%G'
                        else:
                            temp = human_value
                            human_value = 'Unknown char set: ' + temp

                    node = self.__add_section(section)
                    if human_value is None:
                        human_value = ''
                    self.model.add((label, human_value), node=node)

                # handle XMP tags
                for key in metadata.get_xmp_tags():
                    label = metadata.get_tag_label(key)
                    human_value = get_human(key)
                    leadin = key.split('.',3)
                    section = leadin[0]
                    if logData:
                        print(f"{key:50}: {human_value}")
                    if lastLeadin != section:
                        lastLeadin = section
                        if logLeadIn:
                            print( "  section: " + section +" lastLeadin: " + lastLeadin + "\n" ) 
                        
                    cleanName = leadin[2]
                    # # See the IPTC Spec IIMV4.1.pdf
                    # if cleanName == "CharacterSet":
                    #     if human_value == "\x1b%G":
                    #         human_value = 'UTF8 - \x1b%G'
                    #     else:
                    #         temp = human_value
                    #         human_value = 'Unknown char set: ' + temp

                    node = self.__add_section(section)
                    if human_value is None:
                        human_value = ''
                    self.model.add((label, human_value), node=node)

                
                #n = self.model.count
                if self.model.count <= 3:
                    head, tail = os.path.split( full_path )
                    label = tail  
                    node = self.__add_section('No Metadata found in: ')
                    label = tail
                    human_value = ''
                    self.model.add((label, human_value), node=node)  
                self.model.tree.expand_all()
                #retval = self.model.count > 0
            except:
                pass

        return retval

    # ----------------------------------------------------------
    def __add_section(self, section):
        """
        Add the section heading node to the model.
        """
        if section not in self.sections:
            node = self.model.add([section, ''])
            self.sections[section] = node
        else:
            node = self.sections[section]
        return node

    # ----------------------------------------------------------
    def get_has_data(self, full_path):
        """
        Return True if the gramplet has data, else return False.
        """
        if not os.path.exists(full_path):
            return False
        with open(full_path, 'rb') as fd:
            retval = False
            try:
                buf = fd.read()
                metadata = GExiv2.Metadata()
                metadata.open_buf(buf)
                for tag in TAGS:
                    if tag in metadata.get_exif_tags():
                        retval = True
                        break
            except:
                pass
        return retval
		
# ---------------------------- eof ------------------------------
