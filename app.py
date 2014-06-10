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

        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the Set Frame Range application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")

        # remove any callbacks from sharedNuke menu.py
        nuke.removeOnScriptLoad(nozonscripts.setOCIO)
        nuke.removeOnScriptSave(nozonscripts.setOCIO)

        nuke.removeOnCreate(nozonscripts.setOCIOContext, nodeClass='OCIODisplay')

        # import module and create handler
        tk_nuke_ocio = self.import_module("tk_nuke_ocio")
        self.__ocio_node_handler = tk_nuke_ocio.TankOCIOHandler(self)

        # patch handler onto nuke module for access in OCIO knobs
        nuke._shotgun_ocio_node_handler = self.__ocio_node_handler

        # add callbacks:
        self.__ocio_node_handler.add_callbacks()

        self.log_debug("Loading tk-nuke-ocio app")

    def destroy_app(self):
        """
        Called when the app is unloaded/destroyed
        """
        self.log_debug("Destroying tk-nuke-ocio app")
        
        # remove any callbacks that were registered by the handler:
        self.__ocio_node_handler.remove_callbacks()
        
        # clean up the nuke module:
        if hasattr(nuke, "_shotgun_write_node_handler"):
            del nuke._shotgun_ocio_node_handler
        
    



