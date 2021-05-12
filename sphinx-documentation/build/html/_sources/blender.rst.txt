Blender Addon
=============

How it's implemented
--------------------

Blender is written in C, but supports addons written in Python. Following the `official tutorial <https://docs.blender.org/api/2.79/info_quickstart.html>`_, and referencing other addons, I was able to construct a simple user interface for this project in Blender 2.7.9. Blender 2.7.9 is the latest version supported on the Raspberry Pi.

Everything involved in the Blender addon portion of this project is contained in the `__init__.py` file. This file uses some top-level variables and functions and extends one Blender class, :py:class:`bpy.types.Operator`, to create the menu experience.


`Full Source Code for __init__.py available here. <_modules/__init__.html>`_

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