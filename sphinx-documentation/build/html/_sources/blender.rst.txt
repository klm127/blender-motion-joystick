Blender Addon
=============

References
----------

`Official Blender Addon Tutorial <https://docs.blender.org/api/2.79/info_quickstart.html>`_

`Full Source Code for __init__.py available here. <_modules/__init__.html>`_

How it's implemented
--------------------

Blender is written in C, but supports addons written in Python. By Following the addon tutorial and referencing other addons, I was able to construct a simple user interface for this project in Blender 2.7.9. Blender 2.7.9 is the latest version supported on the Raspberry Pi.

Everything involved in the Blender addon portion of this project is contained in the `__init__.py` file. This file uses some top-level variables and functions and extends one Blender class, :py:class:`bpy.types.Operator`, to create the menu experience.

Blender requires some module-level definitions in the `__init__.py` file to read the addon. :py:attr:`bl_info <__init__.bl_info>` tells Blender where to find the addon in the selections, and what it should be named. :py:attr:`bl_idname <__init__.bl_idname>` tells Blender the ID. :py:attr:`bl_label <__init__.bl_label>` gives the label as it will appear in the command search.


The Menu
--------

I wrote a class called :py:class:`SensorMenu <__init__.SensorMenu>` to manage the blender menu. This class extends a blender class called :py:class:`Operator <bpy.types.Operator>`. Operators are commands that can be executed in Blender by pressing spacebar, searching for the command, and hitting enter. Before they take effect, a menu may be displayed to the user so they can adjust the settings of their command before it takes effect.

`SensorMenu` has class-level attributes that describe each of the menu options and the associated data type. These use defined by blender 'Property' objects, such as :py:class:`IntProperty <bpy.types.IntProperty>`.

.. code-block:: python
   :caption: Example IntProperty
   :name: exintprop

    top_pin = IntProperty(
        name="Top GPIO pin",
        description="The BCM numbering of the joystick top button pin connection",
        default=5,
        min=1,
        max=21
    )

When the class is selected by the user from the command selected :py:func:`SensorMenu.invoke <__init__.SensorMenu.invoke>` is called. This function tells the blender :py:class:`WindowManager <bpy.types.WindowManager>` to create a window for the user interface. `WindowManager` subsequently calls :py:func:`SensorMenu.draw <__init__.SensorMenu.draw>` to make the menu layout.

:py:func:`SensorMenu.draw <__init__.SensorMenu.draw>` defines how and where each menu option should be displayed by defining rows, columns, and boxes. It uses :py:class:`bpy.types.UILayout` to do so. `UILayout` can return new instances of `UILayout` with the :py:func:`row <bpy.types.UILayout.row>`, :py:func:`column <bpy.types.UILayout.column>` and :py:func:`box <bpy.types.UILayout.box>` methods. When the :py:func:`prop <bpy.types.UILayout.prop>` method is called, that portion of the layout is populated based on the property type. So by passing the `top_pin` attribute that was defined `above <#exintprop>`_ , for example, an integer selector with full input validation built in, labeled according to the Property values, populates that region of the layout.

.. code-block:: python
   :caption: Example laying out items

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



Rotations
---------

The core of the logic that parses sensor data into object rotations is contained in the `update_from_joystick` function, which is executed by the update thread as the program runs. It converts readings from `JoystickReader`, based on user settings, into the appropriate rotations. Matrix rotations are used when the rotation mode is absolute and Euler rotations are used when the rotation mode is relative.

:py:func:`__init__.update_from_joystick` is reproduced here:

 .. code-block:: python
    :name: main_func

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


joystick_control (the blender files)
------------------------------------

.. automodule:: __init__
   :members: