# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import tempfile

import nuke
import nukescripts

import tank
from tank import TankError
from tank.platform import constants

# Special exception raised when the work file cannot be resolved.
class TkComputePathError(TankError):
    pass

class TankOCIOHandler(object):
    """
    Handles OCIO nodes.
    """

    ################################################################################################
    # Construction

    def __init__(self, app):
        """
        Construction
        """
        self._app = app

        self.camera_colorspace = self.getCameraColorspaceFromShotgun()
        self.event = self._app.context.entity['name']


        self.setOCIODisplayContext()


        # exemple pour acceder aux preferences de l'app tel que defini dans le shot_step.yml
        # la commande a retenir : self._app.get_setting()
        # cache the profiles:
        # self._profile_names = []
        # self._profiles = {}
        # for profile in self._app.get_setting("write_nodes", []):
        #     name = profile["name"]
           
    


    def add_callbacks(self):
        """
        Add callbacks to watch for certain events:
        """

        nuke.addOnUserCreate(self.setOCIOColorspaceContext, nodeClass="OCIOColorSpace") 
        nuke.addOnCreate(self.setOCIODisplayContext, nodeClass="OCIODisplay")
        
    def remove_callbacks(self):
        """
        Removed previously added callbacks
        """
        nuke.removeOnUserCreate(self.setOCIOColorspaceContext, nodeClass="OCIOColorSpace") 
        nuke.removeOnCreate(self.setOCIODisplayContext, nodeClass="OCIODisplay")

       

    def setOCIOColorspaceContext(self):

        ocioNode = nuke.thisNode()

        ocioNode['key1'].setValue('EVENT')
        ocioNode['value1'].setValue(self.event)
        ocioNode['key2'].setValue('CAMERA')
        ocioNode['value2'].setValue(self.camera_colorspace)
        

    def setOCIODisplayContext(self):

           
        listVP = nuke.ViewerProcess.registeredNames()
        viewers = nuke.allNodes('Viewer')

        for v in viewers:
            for l in listVP:
                if nuke.ViewerProcess.node(l, v['name'].value()):
                    if nuke.ViewerProcess.node(l)['key1'].value() != 'EVENT':
                        nuke.ViewerProcess.node(l)['key1'].setValue('EVENT')
                    if nuke.ViewerProcess.node(l)['value1'].value() != self.event:
                        nuke.ViewerProcess.node(l)['value1'].setValue(self.event)
                    if nuke.ViewerProcess.node(l)['key2'].value() != 'CAMERA':
                        nuke.ViewerProcess.node(l)['key2'].setValue('CAMERA')
                    if nuke.ViewerProcess.node(l)['value2'].value() != self.camera_colorspace:
                        nuke.ViewerProcess.node(l)['value2'].setValue(self.camera_colorspace)



    def setOCIOConfig(self):
        ocio_template = self._app.get_template("ocio_template")
        ocio_path = self._app.sgtk.paths_from_template(ocio_template, {})[0]


        return ocio_path


    def getCameraColorspaceFromShotgun(self):

        entity = self._app.context.entity

        sg_entity_type = entity["type"]  # should be Shot
        sg_filters = [["id", "is", entity["id"]]]  #  code of the current shot
        sg_fields = ['sg_camera_colorspace']

        data = self._app.shotgun.find_one(sg_entity_type, filters=sg_filters, fields=sg_fields)

        return data['sg_camera_colorspace']
