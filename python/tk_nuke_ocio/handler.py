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
        #self._script_template = self._app.get_template("template_script_work")
        

        # exemple pour acceder aux preferences de l'app tel que defini dans le shot_step.yml
        # la commande a retenir : self._app.get_setting()
        # cache the profiles:
        # self._profile_names = []
        # self._profiles = {}
        # for profile in self._app.get_setting("write_nodes", []):
        #     name = profile["name"]
           
           
        
        #self.__path_preview_cache = {}
            
    ################################################################################################
    # Properties
            
    #@property
    
            
    ################################################################################################
    # Public methods
            
    

    def add_callbacks(self):
        """
        Add callbacks to watch for certain events:
        """

        nuke.addOnCreate(self.__test, nodeClass="OCIOColorSpace") 

        
    def remove_callbacks(self):
        """
        Removed previously added callbacks
        """
        nuke.removeOnCreate(self.__test, nodeClass="OCIOColorSpace") 


    ################################################################################################
    # Public methods called from gizmo - although these are public, they should 
    # be considered as private and not used directly!




    ################################################################################################
    # Private methods

    

    def __test(self):
        
        ocioNode = nuke.thisNode()

        testTab = nuke.Tab_Knob('Test', 'Test')
        ocioNode.addKnob(testTab)


    

