# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
OCIO handling for Nuke

"""

import os
import nuke
import nozonscripts
import tank
from tank import TankError


class NukeOCIONode(tank.platform.Application):

    def init_app(self):
        """
        Called as the application is being initialized
        """

        # remove callbacks from sharedNuke menu.py
        nuke.removeOnScriptLoad(nozonscripts.setOCIO)
        nuke.removeOnScriptSave(nozonscripts.setOCIO)
        nuke.removeOnCreate(nozonscripts.setOCIOContext, nodeClass='OCIODisplay')

        # first deal with nuke root settings: we don't need a context for this

        self._setOCIOSettingsOnRootNode() # if I don't do this and do a File/New in Nuke, the new instance of nuke does not set the OCIO settings on the root node.
        self._add_root_callbacks()
        self.log_debug("Loading tk-nuke-ocio app.")

        if self.context.entity is not None:
            self.event = self.context.entity['name']
            self.camera_colorspace = self._getCameraColorspaceFromShotgun()

            self._setOCIOSettingsOnRootNode()
            self._setOCIODisplayContext()
            self._add_callbacks()

            self.log_debug("The camera colorspace for '%s' has been fetched from Shotgun and is '%s'" % (self.event, self.camera_colorspace))

        


    def destroy_app(self):
        """
        Called when the app is unloaded/destroyed
        """
        self.log_debug("Destroying tk-nuke-ocio app")
        
        # remove any callbacks that were registered by the handler:
        self._remove_root_callbacks()
        self._remove_callbacks()        

    def _add_root_callbacks(self):
        """
        Add callbacks to watch for certain events:
        """

        nuke.addOnCreate(self._setOCIOSettingsOnRootNode, nodeClass='Root' )

    def _remove_root_callbacks(self):
        """
        Removed previously added callbacks
        """
        nuke.removeOnCreate(self._setOCIOSettingsOnRootNode, nodeClass='Root' )


    def _add_callbacks(self):
        """
        Add callbacks to watch for certain events:
        """

        nuke.addOnUserCreate(self._setOCIOColorspaceContext, nodeClass="OCIOColorSpace") 
        nuke.addOnCreate(self._setOCIODisplayContext, nodeClass="OCIODisplay")

        nuke.addOnCreate(self._warningNoCameraColorspace, nodeClass='Root' )

    def _remove_callbacks(self):
        """
        Removed previously added callbacks
        """
        nuke.removeOnUserCreate(self._setOCIOColorspaceContext, nodeClass="OCIOColorSpace") 
        nuke.removeOnCreate(self._setOCIODisplayContext, nodeClass="OCIODisplay")

        nuke.removeOnCreate(self._warningNoCameraColorspace, nodeClass='Root' )

    def _setOCIOColorspaceContext(self):

        ocioNode = nuke.thisNode()

        ocioNode['key1'].setValue('EVENT')
        ocioNode['value1'].setValue(self.event)
        ocioNode['key2'].setValue('CAMERA')
        ocioNode['value2'].setValue(self.camera_colorspace)

    def _setOCIODisplayContext(self):
           
        listVP = nuke.ViewerProcess.registeredNames()
        viewers = nuke.allNodes('Viewer')
        ### ideally I'd like to use :
        #camera_colorspace = self.getCameraColorspaceFromShotgun() 
        # this would update any new viewer with the last value from the camera colorspace field in shotgun
        # but this creates a max recursion bug in the callback
        camera_colorspace = self.camera_colorspace


        for v in viewers:
            for l in listVP:
                if nuke.ViewerProcess.node(l, v['name'].value()):
                    if nuke.ViewerProcess.node(l)['key1'].value() != 'EVENT':
                        nuke.ViewerProcess.node(l)['key1'].setValue('EVENT')
                    if nuke.ViewerProcess.node(l)['value1'].value() != self.event:
                        nuke.ViewerProcess.node(l)['value1'].setValue(self.event)
                    if nuke.ViewerProcess.node(l)['key2'].value() != 'CAMERA':
                        nuke.ViewerProcess.node(l)['key2'].setValue('CAMERA')
                    if nuke.ViewerProcess.node(l)['value2'].value() != camera_colorspace:
                        nuke.ViewerProcess.node(l)['value2'].setValue(camera_colorspace)

    def _getCameraColorspaceFromShotgun(self):

        entity = self.context.entity

        sg_entity_type = entity["type"]  # should be Shot
        sg_filters = [["id", "is", entity["id"]]]  #  code of the current shot
        sg_fields = ['sg_camera_colorspace']

        data = self.shotgun.find_one(sg_entity_type, filters=sg_filters, fields=sg_fields)

        return data['sg_camera_colorspace']

    
    def _warningNoCameraColorspace(self):

        camera_colorspace =  self.camera_colorspace
        #camera_colorspace = self._getCameraColorspaceFromShotgun()

        if camera_colorspace == '' or camera_colorspace == None:
            nuke.message('Warning : The camera colorspace of shot %s could not be determined.\nPlease check the Shot infos on our shotgun website and fill the camera colorspace field (sRGB for pure CGI stuff)' % self.event)
        
        self.log_debug("Checking the camera colorspace in shotgun")


    def _setOCIOSettingsOnRootNode(self):

        ocio_template = self.get_template("ocio_template")
        ocio_path = self.sgtk.paths_from_template(ocio_template, {})[0]
        ocio_path = ocio_path.replace(os.path.sep, "/")

        nuke.root().knob("defaultViewerLUT").setValue("OCIO LUTs") 
        nuke.root().knob("OCIO_config").setValue("custom") 
        nuke.root().knob("customOCIOConfigPath").setValue(ocio_path) 