# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Motion Sensor Joystick Controls",
    "author": "klm127",
    "version": (0, 1),
    "blender": (2, 70, 0),
    "location": "Spacebar; search",
    "description": "Create links to acceleration sensor",
    "warning": "",
    "category": "Object"}

import bpy
import threading
import random
import time
import mathutils
from . import joystick_reader

from bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        FloatProperty,
        FloatVectorProperty,
        EnumProperty,
        )

from bpy.types import Operator

running = False
run_thread = None
selected_objects = []
j_reader = None
update_interval = 0.08
settings = {
    "update interval":0.08,
    "averages":True
    }

class SensorMenu(bpy.types.Operator):
    global settings
    
    bl_idname = "object.sensormenu"
    bl_label = "Open Joystick Menu" # this is what comes up on the search
    bl_options = {'PRESET'}
    
    # every property gets added to the window     
            
    running = BoolProperty(
            name="Running",
            description="Whether input should be actively reading",
            default=False
            )
    trigger_pin = IntProperty(
            name="Trigger GPIO pin",
            description="The BCM numbering of the joystick trigger pin connection",
            default=16,
            min=1,
            max=21
            )
    top_pin = IntProperty(
            name="Top GPIO pin",
            description="The BCM numbering of the joystick top button pin connection",
            default=5,
            min=1,
            max=21
            )
    update_interval = FloatProperty(
            name="Update Interval",
            description="How long (in seconds) between sensor readings",
            default=settings["update interval"],
            min=0.02,
            max=1
            )
    averages = BoolProperty(
            name="Averages",
            description="Whether sensor values should be averaged (true) or just the last read (false)",
            default=settings["averages"]
            )
    
    def execute(self, context): # I believe this is what's called when you press "ok"
        keywords = self.as_keywords()
        main(context, **keywords)
        return {'FINISHED'}
        
    def invoke(self, context, event):  # happens when searched for space and selected, opens menu
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=600)
        
    def draw(self, context): # called when menu opened
        global selected_objects
        layout = self.layout
        error_string = ''
        
        # get selected objects
        selected_objects = bpy.context.selected_objects.copy()
        num_selected = len(selected_objects)
        
        main_box = layout.box()
        top_row = main_box.box()
        if num_selected <= 0:
            top_row.label('One or more objects must be selected!')
        else:
            top_row.label('Selected object count: '+str(num_selected))
            list_row = top_row.row()
            for ob in selected_objects:
                ob_col = list_row.column()
                ob_col.label(ob.name)
        
        lower_row = main_box.box()
        
        trigger_select = lower_row.row()
        trigger_select.prop(self, "trigger_pin")
        
        top_select = lower_row.row()
        top_select.prop(self, "top_pin")
        
        interval_select = lower_row.row()
        interval_select.prop(self, "update_interval")

        average_select = lower_row.row()
        average_select.prop(self, "averages")
        
        run_select = lower_row.row()
        run_select.prop(self, "running")
        
        
        
def main(context, **kw):
    global running
    global run_thread
    global j_reader
    global settings
    # get currently selected values 
    kw_copy = kw.copy()
    run_selection = kw_copy.pop('running')
    trigger_pin = kw_copy.pop('trigger_pin')
    top_pin = kw_copy.pop('top_pin')
    settings["update interval"] = kw_copy.pop('update_interval')
    settings["averages"] = kw_copy.pop('averages')
    if not j_reader:
        j_reader = joystick_reader.JoystickReader(trigger_pin, top_pin)
    else:
        j_reader.load_pins(trigger_pin, top_pin)
    
    if run_selection:
        if not running:
            running = True
            run_thread = threading.Thread(target=update_from_joystick)
            run_thread.start()
        else:
            pass
    else:
        running = False
        if run_thread:
            run_thread.join()
            run_thread = None
            
def update_from_joystick():
    global selected_objects
    global settings
    global j_reader
    shrinkage = 0.005
    yaw_shrinkage = shrinkage/10
    accel_shrinkage = 1
    interval = settings["update interval"]
    if settings["averages"]:
        get_func = j_reader.get_averages
    else:
        get_func = j_reader.get_last
    while running:
        j_reader.get_vals_from_sensor()
        vals = get_func()
        for obj3d in selected_objects:
            # print(vals)
            if not vals['top']: # if the top button is pressed
                obj3d.rotation_mode = 'XYZ'
                obj3d.rotation_euler[0] += vals['wx'] * shrinkage # pitch
                obj3d.rotation_euler[1] += vals['wz'] * shrinkage # yaw
                obj3d.rotation_euler[2] += -vals['wy'] * shrinkage # roll
            if not vals['trigger']: # if the trigger is pressed
                # pass
                fwd_vector = obj3d.matrix_world[2]
                move_vec = mathutils.Vector((0,-10,0,0))
                move_new = move_vec.project(fwd_vector)
                obj3d.location[0] += move_new[0]
                obj3d.location[1] += move_new[1]
                obj3d.location[2] += move_new[2]
                
                # obj3d.Translation @ obj3d.Rotation ?
                # obj3d.location[0] += -vals['ax'] * accel_shrinkage
                # obj3d.location[1] += vals['ay'] * accel_shrinkage
                # obj3d.location[2] += vals['az'] * accel_shrinkage
            time.sleep(interval)         

def register(): # gets called when module loaded, either at start or in preferences menu
    bpy.utils.register_class(SensorMenu) # causes class to appear in search (spacebar)
    
def unregister(): # called when module unloaded
    global j_reader
    bpy.utils.unregister_class(SensorMenu)
    if j_reader:
        j_reader.end()
    j_reader = None # needed?
    
    
    
 
    
    
    
