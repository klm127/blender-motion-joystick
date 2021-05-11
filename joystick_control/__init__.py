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
"""
`joystick_control/.__init__` contains all the references that interact with Blender, including the menu and
functions which modify the selected objects.

The folder `joystick_control` should be placed in `Blender/scripts/addons` directory. It will then appear in Blender as
`Object: Motion Sensor Joystick Controls'` in the list of available addons in the settings > addons menu.

Once installed, pressing spacebar and searching for `Open Joystick Menu` provides access to the in-blender User Interface.

"""

bl_info = {
    "name": "Motion Sensor Joystick Controls",
    "author": "klm127",
    "version": (0, 1),
    "blender": (2, 70, 0),
    "location": "Spacebar; search",
    "description": "Create links to acceleration sensor",
    "warning": "",
    "category": "Object"}
"""
:envar:

bl_info sets the addon information. Every blender addon file module must start with a dict named bl_info.
"""

if __name__ == '__main__':  # fix documentation problems with blender imports
    import bpy
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

else:
    from fake_bpy279 import bpy
    from fake_bpy279.bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        FloatProperty,
        FloatVectorProperty,
        EnumProperty,
    )

import threading
import random
import time

running = False
"""
Whether it is currently looping and updating the 3d render.

:type: bool
"""
run_thread = None
"""
A thread. Initialized to None - when the program is running, references active update thread.

:type: threading.Thread
"""
selected_objects = []
"""
The objects user currently has selected.

:type: list<:py:class:`bpy.types.Object`>
"""
j_reader = None
"""
The Joystick reader
:type: JoystickReader
"""
settings = {
    "update interval": 0.08,
    "averages": True,
    "keep vals": 10,
    "weight": 0,
    "movement_modifier": 0.05,
    "shrinkage": 0.03,
    "yaw active": True,
    "pitch active": True,
    "roll active": True,
    "movement forward": True,
    "movement side": True,
    "rotation type": "Absolute"
}
"""
Default settings.
"""


class SensorMenu(bpy.types.Operator):
    """
    SensorMenu defines the popup menu that appears in Blender when the Command is run.

    :type: :py:class:`bpy.types.Operator`
    """
    global settings

    bl_idname = "object.sensormenu"
    """
    Required name for blender reference.
    """
    bl_label = "Open Joystick Menu"  # this is what comes up on the search
    """
    Required label for command search.
    """
    bl_options = {'PRESET'}

    # every property gets added to the window     

    running = BoolProperty(
        name="Running",
        description="Whether input should be actively reading",
        default=False
    )
    """
    Selection data controlling whether addon should be updating objects.
    
    :type: :py:class:`bpy.types.BoolProperty`
    """
    trigger_pin = IntProperty(
        name="Trigger GPIO pin",
        description="The BCM numbering of the joystick trigger pin connection",
        default=16,
        min=1,
        max=21
    )
    """
    Selection data controlling what GPIO pin Trigger button is wired to.
    
    :type: :py:class:`bpy.types.IntProperty`
    """
    top_pin = IntProperty(
        name="Top GPIO pin",
        description="The BCM numbering of the joystick top button pin connection",
        default=5,
        min=1,
        max=21
    )
    """
    Selection data controlling what GPIO pin Top button is wired to.
    
    :type: :py:class:`bpy.types.IntProperty`
    """
    update_interval = FloatProperty(
        name="Update Interval",
        description="How long (in seconds) between sensor readings",
        default=settings["update interval"],
        min=0.02,
        max=1
    )
    """
    Selection data controlling how long between sensor readings and updates.
    
    Minimum 0.02, maximum 1 second.
    
    :type: :py:class:`bpy.types.FloatProperty`
    """
    averages = BoolProperty(
        name="Averages",
        description="Whether sensor values should be averaged (true) or just the last read (false)",
        default=settings["averages"]
    )
    """
    Whether sensor reads should be averaged or just the last read.
    
    Default is True.
    
    :type: :py:class:`bpy.types.BoolProperty`
    """

    keepvals = IntProperty(
        name="Keep Values",
        description="How many values to store for averaging",
        default=settings["keep vals"],
        min=1,
        max=30
    )
    """
    How many values the sensor should store for averaging.
    
    Default is 10.
    
    :type: :py:class:`bpy.types.IntProperty`
    """

    weight = IntProperty(
        name="Weight",
        description="How much to weight the last reading",
        default=settings["weight"],
        min=0,
        max=10
    )
    """
    How much to weight the last reading.
    
    Default is 10.
    
    :type: :py:class:`bpy.types.IntProperty`
    """

    shrinkage = FloatProperty(
        name="Gyro Sensitivity",
        description="Multiplies gyro reads by a fraction to reduce sensitivity",
        default=settings["shrinkage"],
        min=0.01,
        max=0.5
    )
    """
    Multiplies gyroscope readings by this fraction to reduce sensitivity.
    
    Minimum is 0.01. Maximum is 0.5
    
    :type: :py:class:`bpy.types.FloatProperty`
    """

    movement_shrinkage = FloatProperty(
        name="Movement Sensitivity",
        description="Multiplies gyro reads by fraction to reduce senstivity for movement",
        default=settings["movement_modifier"],
        min=0.0001,
        max=0.5
    )
    """
    Multiplies gyroscope readings by this fraction when performing translations (during trigger press).
    
    This is more sensitive than rotations are, so it needs to be reduced more.
    
    Minimum is 0.0001. Maximum is 0.5
    
    :type: :py:class:`bpy.types.FloatProperty`
    """
    yaw_enabled = BoolProperty(
        name="Yaw",
        description="Whether yaw rotations are enabled",
        default=settings["yaw active"]
    )
    """
    Whether yawing the joystick causes the selected object to yaw when running.
    
    :type: :py:class:`bpy.types.BoolProperty`
    """
    pitch_enabled = BoolProperty(
        name="Pitch",
        description="Whether pitch rotations are enabled",
        default=settings["pitch active"]
    )
    """
    Whether pitching the joystick causes the selected object to pitch when running.
    
    :type: :py:class:`bpy.types.BoolProperty`
    """
    roll_enabled = BoolProperty(
        name="Roll",
        description="Whether roll rotations are enabled",
        default=settings["roll active"]
    )
    """
    Whether rolling the joystick causes the selected object to roll when running.
    
    :type: :py:class:`bpy.types.BoolProperty`
    """
    movement_forward = BoolProperty(
        name="Forward",
        description="Whether object moves forward when trigger pressed based on pitch",
        default=settings["movement forward"]
    )
    """
    Whether pitching the joystick forward/back with the trigger pressed causes the object to move in its forward/back direction.
    
    :type: :py:class:`bpy.types.BoolProperty`
    """
    movement_side = BoolProperty(
        name="Side",
        description="Whether object moves sideways when trigger pressed based on roll",
        default=settings["movement side"]
    )
    """
    Whether rolling the joystick with the trigger pressed causes the object to move in its left/right direction.
    
    :type: :py:class:`bpy.types.BoolProperty`
    """
    rotation_type = EnumProperty(
        name="Rotation Type",
        description="Whether to rotate the object relatively or on the absolute axes",
        items=(('Absolute', 'Rotate on the global axes', ''),
               ('Relative', 'Shift rotation axes as object rotates', '')
               ),
        default=settings["rotation type"]
    )
    """
    Whether to rotate the object relatively or on its absolute axis.
    
    :type: :py:class:`bpy.types.EnumProperty`
    """

    def execute(self, context):  # I believe this is what's called when you press "ok"
        """
        Executed when "OK" is pressed on the popup menu.

        Sends user selection to :py:func:`main` for execution.

        :param context: The blender context, referencing the selection and active window.
        :type context: :py:class:`bpy.types.Context`
        """
        keywords = self.as_keywords()
        main(context, **keywords)
        return {'FINISHED'}

    def invoke(self, context, event):  # happens when searched for space and selected, opens menu
        """
        Executed when addon is executed from the command selector (spacebar in Blender).

        Creates the :py:class:`bpy.types.WindowManager`, then causes draw to execute based on SensorMenu attributes.

        :param context: The blender context, referencing the selection and active window.
        :type context: :py:class:`bpy.types.Context`
        :param event:
        """
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=600)

    def draw(self, context):  # called when menu opened
        """
        Called when the menu is opened.

        Gets the selected objects. Reads user selections into settings.

        Creates a new update thread if running is active which begins reading sensor info and applying it to blender objects.

        :param context: The blender context, referencing the selection and active window.
        :type context: :py:class:`bpy.types.Context`
        """
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
            top_row.label('Selected object count: ' + str(num_selected))
            list_row = top_row.row()
            for ob in selected_objects:
                ob_col = list_row.column()
                ob_col.label(ob.name)

        row_2 = main_box.row()

        if not joystick_reader.error_message:  # if import error w/ sensor lib

            absolute_col = row_2.column()
            absolute_box = absolute_col.box()
            absolute_box.label('Rotation Type')
            absolute_select = absolute_box.column()
            absolute_select.prop(self, "rotation_type")

            row_3 = main_box.row()

            rotations_bool_col = row_3.column()
            rotations_box = rotations_bool_col.box()
            rotations_inner_row = rotations_box.row()
            rotations_inner_row.label("Active Axes")
            yaw_col = rotations_inner_row.column()
            yaw_col.prop(self, "yaw_enabled")
            pitch_col = rotations_inner_row.column()
            pitch_col.prop(self, "pitch_enabled")
            roll_col = rotations_inner_row.column()
            roll_col.prop(self, "roll_enabled")

            movement_bool_col = row_3.column()
            movement_box = movement_bool_col.box()
            movement_inner_row = movement_box.row()
            movement_inner_row.label("Movement")
            forward_col = movement_inner_row.column()
            forward_col.prop(self, "movement_forward")
            side_col = movement_inner_row.column()
            side_col.prop(self, "movement_side")

            row_4 = main_box.row()

            gpio_col = row_4.column()
            gpio_box = gpio_col.box()
            gpio_box.label('Readings')
            trigger_select = gpio_box.row()
            trigger_select.prop(self, "trigger_pin")
            top_select = gpio_box.row()
            top_select.prop(self, "top_pin")
            interval_select = gpio_box.row()
            interval_select.prop(self, "update_interval")

            average_col = row_4.column()
            average_box = average_col.box()
            average_select = average_box.row()
            average_select.prop(self, "averages")
            keep_vals_select = average_box.row()
            keep_vals_select.prop(self, "keepvals")
            weight_select = average_box.row()
            weight_select.prop(self, "weight")

            modifier_col = row_4.column()
            modifier_box = modifier_col.box()
            modifier_box.label('Sensitivity')
            shrinkage_select = modifier_box.row()
            shrinkage_select.prop(self, "shrinkage")
            movement_shrinkage_select = modifier_box.row()
            movement_shrinkage_select.prop(self, "movement_shrinkage")

            run_select = main_box.row()
            run_select.prop(self, "running")

        else:
            row_2.label("Error occurred in the mpu9250.py file. Check connections are properly configured.")


def main(context, **kw):
    """
    Called after "OK" is pressed on the UI Window. Parses user selection to control program behavior.

    Starts the update thread if one doesn't exist and the user selected "running".

    Stops and deletes the update thread if one does exist and the user did not select "running".

    The thread executes :py:func:`update_from_joystick`

    :param context: The blender context, referencing the selection and active window.
    :type context: :py:class:`bpy.types.Context`

    :param kw: Represents user selection
    :type kw: list
    """
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
    settings["weight"] = kw_copy.pop('weight')
    settings["shrinkage"] = kw_copy.pop('shrinkage') / 10
    settings["movement_shrinkage"] = kw_copy.pop('movement_shrinkage')
    settings["keep vals"] = kw_copy.pop('keepvals')
    settings["yaw active"] = kw_copy.pop('yaw_enabled')
    settings["pitch active"] = kw_copy.pop('pitch_enabled')
    settings["roll active"] = kw_copy.pop('roll_enabled')
    settings["movement forward"] = kw_copy.pop('movement_forward')
    settings["movement side"] = kw_copy.pop('movement_side')
    settings["rotation type"] = kw_copy.pop('rotation_type')
    # kw copying might not be totally necessary, but if it ain't broke...

    if not j_reader:
        j_reader = joystick_reader.JoystickReader(trigger_pin, top_pin, keepvals=settings["keep vals"],
                                                  weight=settings["weight"])
        # create reader if doesn't exist (first run)

    else:
        j_reader.load_pins(trigger_pin, top_pin) # update reader with user selection if reader exists
        j_reader.load_keep_vals_and_weight(settings["keep vals"], settings["weight"])

    if run_selection:
        if not running: # create the update thread
            running = True
            run_thread = threading.Thread(target=update_from_joystick)
            run_thread.start()
        else:
            pass
    else:
        running = False
        if run_thread:
            run_thread.join() # destroy the update thread
            run_thread = None


def update_from_joystick():
    """
    This function is what is executed by `run_thread` every update interval.

    Gets raw data from the joystick reader and applies it to the selected objects in Blender.

    """
    global selected_objects
    global settings
    global j_reader
    shrinkage = settings["shrinkage"]
    movement_modifier = settings["movement_shrinkage"]
    yaw_shrinkage = shrinkage / 2
    interval = settings["update interval"]
    if settings["averages"]:
        get_func = j_reader.get_averages
    else:
        get_func = j_reader.get_last
    while running:
        j_reader.get_vals_from_sensor()
        vals = get_func()
        for obj3d in selected_objects:
            if not vals['top']:  # if the top button is pressed
                if settings["rotation type"] == "Absolute":  # use operator for absolute rotations
                    location, rotation, scale = obj3d.matrix_world.decompose()
                    location = mathutils.Matrix.Translation(location)
                    # location is given as a vector and has to be a matrix for recomposition
                    rotation = rotation.to_matrix().to_4x4()
                    # rotation is given as a Quat and has to be a matrix for recomposition
                    scale = mathutils.Matrix.Scale(scale[0], 4, (1, 0, 0))
                    # same with scale (a vector)
                    new_rotation = mathutils.Matrix.Rotation(0, 4, 'X')
                    # start with a 0 rotation
                    if settings["yaw active"]:
                        new_rotation *= mathutils.Matrix.Rotation(-vals["wy"] * yaw_shrinkage, 4, 'Z')
                    if settings["pitch active"]:
                        new_rotation *= mathutils.Matrix.Rotation(vals["wx"] * shrinkage, 4, 'X')
                    if settings["roll active"]:
                        new_rotation *= mathutils.Matrix.Rotation(vals["wz"] * shrinkage, 4, 'Y')
                    obj3d.matrix_world = location * new_rotation * rotation * scale
                    # to perform absolute rotations, they have to be added before the existing rotation
                    # as the matrix is re-assembled from its components
                else:  # perform relative rotations
                    if settings["yaw active"]:
                        obj3d.rotation_euler.rotate_axis("Z", -vals['wz'] * yaw_shrinkage)  # yaw
                    if settings["pitch active"]:
                        obj3d.rotation_euler.rotate_axis("X", vals['wx'] * shrinkage)  # pitch
                    if settings["roll active"]:
                        obj3d.rotation_euler.rotate_axis("Y", -vals['wy'] * shrinkage)  # roll
            if not vals['trigger']:  # if the trigger is pressed
                if settings["movement forward"]:
                    forward_vector = obj3d.matrix_local.col[2]  # column major matrix, 3rd col is fwd vector
                    new_vec = forward_vector * 1  # just copies the vector
                    new_vec.resize_3d()  # make it 3 instead of 4
                    new_vec.normalize()
                    new_vec *= -vals['wx']  # pitch controls forward/backward when trig pressed
                    obj3d.location.x -= new_vec.x * movement_modifier
                    obj3d.location.y -= new_vec.y * movement_modifier
                    obj3d.location.z -= new_vec.z * movement_modifier
                if settings["movement side"]:
                    left_right_vector = obj3d.matrix_local.col[0]
                    new_vec = left_right_vector * 1
                    new_vec.resize_3d()
                    new_vec.normalize()
                    new_vec *= -vals['wz']  # yaw controls left/right when trig pressed
                    obj3d.location.x -= new_vec.x * movement_modifier
                    obj3d.location.y -= new_vec.y * movement_modifier
                    obj3d.location.z -= new_vec.z * movement_modifier
            time.sleep(interval)


def register():  # gets called when module loaded, either at start or in preferences menu
    """
    Required for blender addons. Called by Blender to register classes.

    In this case, just registers SensorMenu.

    """
    bpy.utils.register_class(SensorMenu)  # causes class to appear in search (spacebar)


def unregister():  # called when module unloaded
    """
    Required for blender addons. Called by Blender when addon is deactivated.

    In this case, just unregisters SensorMenu.

    """
    global j_reader
    bpy.utils.unregister_class(SensorMenu)
    if j_reader:
        j_reader.end()
    j_reader = None  # needed?
