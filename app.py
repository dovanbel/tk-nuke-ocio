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

        # this app should not do anything if nuke is run without gui.

        if nuke.env['gui']:
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

        else:
            pass


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
        '''
        Setting up the knobs of the OCIOColorspace node
        If the node is created as a child of a read node use the read node filepath to try to populate the event number,
        the camera colorspace and set the in colorspace to the colorspace defined in the string of the filepath
        If the node is created with no close connection to a read node we assume the node should be related to the current
        context, so we use the event number and the camera colorspace from Shotgun
        '''

        ocioNode = nuke.thisNode()

        # First we setup the node to the event number and camera colorspace from the current context
        
        ocioNode['key1'].setValue('EVENT')
        ocioNode['value1'].setValue(self.event)
        ocioNode['key2'].setValue('CAMERA')
        ocioNode['value2'].setValue(self.camera_colorspace)

        # Now let's try to detect a read node in the upstream nodes

        if not nuke.selectedNodes(): # no nodes selected, stop here
            return
        selNode = nuke.selectedNode()
        upstreamNodes = [] # we will store an arbitrary number of upstream nodes in this list
        upstreamNodes.append(selNode)

        for i in range(10):
            selNode = selNode.dependencies() # take the list of upstream dependent nodes, usually one but can be more if we have a node with multiple inputs
            if selNode: selNode = selNode[0] #we take only the first dependent upstream node, so we stay on the B side
            else: break # if there's nothing we have reached the end of the tree
            upstreamNodes.append(selNode)

        readNode = None
        for n in upstreamNodes:
            if n.Class() == 'Read':
                readNode = n
                break
        else : return # stop here if we have found no read node
        

        filename = os.path.basename(readNode.knob('file').getValue())
        # find event by assuming it's the first part in front of the filename, just before the first underscore 
        event = filename.split('_')[0]
        ocioNode['value1'].setValue(event)
        # find colorspace in filename string:
        colorspaceList = self.get_setting('colorspaces')
        for cs in colorspaceList:
            if cs in filename:
                colorspace = cs
                break
        else: colorspace = None
        if colorspace:
            ocioNode.knob('in_colorspace').setValue(colorspace)
            ocioNode.knob('value2').setValue(colorspace)
            ocioNode.knob('out_colorspace').setValue('Flat')


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
            nuke.message('Warning : The camera colorspace of shot %s could not be determined.\n\
                Please check the Shot infos on our shotgun website and fill the camera colorspace field (sRGB for pure CGI stuff)' % self.event)
        
        self.log_debug("Checking the camera colorspace in shotgun")


    def _setOCIOSettingsOnRootNode(self):

        ocio_template = self.get_template("ocio_template")
        ocio_path = self.sgtk.paths_from_template(ocio_template, {})[0]
        ocio_path = ocio_path.replace(os.path.sep, "/")

        '''
        First case : the viewer process LUTs is set to 'Nuke Root LUTs'.
        In this case we assume the user has not intervened, Nuke is using it's default values
        So we change it to use the project ocio config without asking the user
        ''' 
        if nuke.root().knob("defaultViewerLUT").value() == 'Nuke Root LUTs':

            nuke.root().knob("defaultViewerLUT").setValue("OCIO LUTs") 
            nuke.root().knob("OCIO_config").setValue("custom") 
            nuke.root().knob("customOCIOConfigPath").setValue(ocio_path) 

        '''
        Second case : the viewer process LUTs is configured to use OCIO Luts
        '''
        if nuke.root().knob("defaultViewerLUT").value() == 'OCIO LUTs':
            # if the ocio config is not set to custom or if the ocio config file path is not correct we ask the user if he allows us to correct it
            nuke_ocio_path = nuke.root().knob("customOCIOConfigPath").value()
            nuke_ocio_path = nuke.filenameFilter(nuke_ocio_path) # for cross platform compatibility
            if nuke.root().knob("OCIO_config").value() != "custom" or nuke_ocio_path.lower() != ocio_path.lower():
                anwser = nuke.ask('Warning. Your OCIO settings do not match the correct settings for this project<p> \
                    Nuke is currently using the %s OCIO config located in:<br><i>%s</i><p>\
                    It is supposed to use the custom OCIO config for this project located in:<br><i>%s</i><p>\
                    Do you want me to correct the OCIO settings ?<br>Please be aware that changing the OCIO config is going to reset all ocio nodes.' % (nuke.root().knob("OCIO_config").value(), nuke.root().knob("customOCIOConfigPath").value(), ocio_path))
                if anwser:
                    nuke.root().knob("defaultViewerLUT").setValue("OCIO LUTs") 
                    nuke.root().knob("OCIO_config").setValue("custom") 
                    nuke.root().knob("customOCIOConfigPath").setValue(ocio_path) 