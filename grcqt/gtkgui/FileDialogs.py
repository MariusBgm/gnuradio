"""
Copyright 2007 Free Software Foundation, Inc.
This file is part of GNU Radio

GNU Radio Companion is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

GNU Radio Companion is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""

import pygtk
pygtk.require('2.0')
import gtk
from Dialogs import MessageDialogHelper
from Constants import \
    DEFAULT_FILE_PATH, IMAGE_FILE_EXTENSION, TEXT_FILE_EXTENSION, \
    NEW_FLOGRAPH_TITLE
import Preferences
from os import path
import Utils

##################################################
# Constants
##################################################
OPEN_FLOW_GRAPH = 'open flow graph'
SAVE_FLOW_GRAPH = 'save flow graph'
SAVE_REPORTS = 'save reports'
SAVE_IMAGE = 'save image'

FILE_OVERWRITE_MARKUP_TMPL="""\
File <b>$encode($filename)</b> Exists!\nWould you like to overwrite the existing file?"""

FILE_DNE_MARKUP_TMPL="""\
File <b>$encode($filename)</b> Does not Exist!"""

##################################################
# File Filters
##################################################
##the filter for flow graph files
def get_flow_graph_files_filter():
    filter = gtk.FileFilter()
    filter.set_name('Flow Graph Files')
    filter.add_pattern('*'+Preferences.file_extension())
    return filter

def get_text_files_filter():
    filter = gtk.FileFilter()
    filter.set_name('Text Files')
    filter.add_pattern('*'+TEXT_FILE_EXTENSION)
    return filter

##the filter for image files
def get_image_files_filter():
    filter = gtk.FileFilter()
    filter.set_name('Image Files')
    filter.add_pattern('*'+IMAGE_FILE_EXTENSION)
    return filter

##the filter for all files
def get_all_files_filter():
    filter = gtk.FileFilter()
    filter.set_name('All Files')
    filter.add_pattern('*')
    return filter

##################################################
# File Dialogs
##################################################
class FileDialogHelper(gtk.FileChooserDialog):
    """
    A wrapper class for the gtk file chooser dialog.
    Implement a file chooser dialog with only necessary parameters.
    """

    def __init__(self, action, title):
        """
        FileDialogHelper contructor.
        Create a save or open dialog with cancel and ok buttons.
        Use standard settings: no multiple selection, local files only, and the * filter.

        Args:
            action: gtk.FILE_CHOOSER_ACTION_OPEN or gtk.FILE_CHOOSER_ACTION_SAVE
            title: the title of the dialog (string)
        """
        ok_stock = {gtk.FILE_CHOOSER_ACTION_OPEN : 'gtk-open', gtk.FILE_CHOOSER_ACTION_SAVE : 'gtk-save'}[action]
        gtk.FileChooserDialog.__init__(self, title, None, action, ('gtk-cancel', gtk.RESPONSE_CANCEL, ok_stock, gtk.RESPONSE_OK))
        self.set_select_multiple(False)
        self.set_local_only(True)
        self.add_filter(get_all_files_filter())

class FileDialog(FileDialogHelper):
    """A dialog box to save or open flow graph files. This is a base class, do not use."""

    def __init__(self, current_file_path=''):
        """
        FileDialog constructor.

        Args:
            current_file_path: the current directory or path to the open flow graph
        """
        if not current_file_path: current_file_path = path.join(DEFAULT_FILE_PATH, NEW_FLOGRAPH_TITLE + Preferences.file_extension())
        if self.type == OPEN_FLOW_GRAPH:
            FileDialogHelper.__init__(self, gtk.FILE_CHOOSER_ACTION_OPEN, 'Open a Flow Graph from a File...')
            self.add_and_set_filter(get_flow_graph_files_filter())
            self.set_select_multiple(True)
        elif self.type == SAVE_FLOW_GRAPH:
            FileDialogHelper.__init__(self, gtk.FILE_CHOOSER_ACTION_SAVE, 'Save a Flow Graph to a File...')
            self.add_and_set_filter(get_flow_graph_files_filter())
            self.set_current_name(path.basename(current_file_path))
        elif self.type == SAVE_REPORTS:
            FileDialogHelper.__init__(self, gtk.FILE_CHOOSER_ACTION_SAVE, 'Save Reports to a File...')
            self.add_and_set_filter(get_text_files_filter())
            file_path = path.splitext(path.basename(current_file_path))[0]
            self.set_current_name(file_path) #show the current filename
        elif self.type == SAVE_IMAGE:
            FileDialogHelper.__init__(self, gtk.FILE_CHOOSER_ACTION_SAVE, 'Save a Flow Graph Screen Shot...')
            self.add_and_set_filter(get_image_files_filter())
            current_file_path = current_file_path + IMAGE_FILE_EXTENSION
            self.set_current_name(path.basename(current_file_path)) #show the current filename
        self.set_current_folder(path.dirname(current_file_path)) #current directory

    def add_and_set_filter(self, filter):
        """
        Add the gtk file filter to the list of filters and set it as the default file filter.

        Args:
            filter: a gtk file filter.
        """
        self.add_filter(filter)
        self.set_filter(filter)

    def get_rectified_filename(self):
        """
        Run the dialog and get the filename.
        If this is a save dialog and the file name is missing the extension, append the file extension.
        If the file name with the extension already exists, show a overwrite dialog.
        If this is an open dialog, return a list of filenames.

        Returns:
            the complete file path
        """
        if gtk.FileChooserDialog.run(self) != gtk.RESPONSE_OK: return None #response was cancel
        #############################################
        # Handle Save Dialogs
        #############################################
        if self.type in (SAVE_FLOW_GRAPH, SAVE_REPORTS, SAVE_IMAGE):
            filename = self.get_filename()
            extension = {
                SAVE_FLOW_GRAPH: Preferences.file_extension(),
                SAVE_REPORTS: TEXT_FILE_EXTENSION,
                SAVE_IMAGE: IMAGE_FILE_EXTENSION,
            }[self.type]
            #append the missing file extension if the filter matches
            if path.splitext(filename)[1].lower() != extension: filename += extension
            self.set_current_name(path.basename(filename)) #show the filename with extension
            if path.exists(filename): #ask the user to confirm overwrite
                if MessageDialogHelper(
                    gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, 'Confirm Overwrite!',
                    Utils.parse_template(FILE_OVERWRITE_MARKUP_TMPL, filename=filename),
                ) == gtk.RESPONSE_NO: return self.get_rectified_filename()
            return filename
        #############################################
        # Handle Open Dialogs
        #############################################
        elif self.type in (OPEN_FLOW_GRAPH,):
            filenames = self.get_filenames()
            for filename in filenames:
                if not path.exists(filename): #show a warning and re-run
                    MessageDialogHelper(
                        gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, 'Cannot Open!',
                        Utils.parse_template(FILE_DNE_MARKUP_TMPL, filename=filename),
                    )
                    return self.get_rectified_filename()
            return filenames

    def run(self):
        """
        Get the filename and destroy the dialog.

        Returns:
            the filename or None if a close/cancel occured.
        """
        filename = self.get_rectified_filename()
        self.destroy()
        return filename

class OpenFlowGraphFileDialog(FileDialog): type = OPEN_FLOW_GRAPH
class SaveFlowGraphFileDialog(FileDialog): type = SAVE_FLOW_GRAPH
class SaveReportsFileDialog(FileDialog): type = SAVE_REPORTS
class SaveImageFileDialog(FileDialog): type = SAVE_IMAGE
