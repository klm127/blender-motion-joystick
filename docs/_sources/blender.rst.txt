Blender Addon
=============

References
----------

`Official Blender Addon Tutorial <https://docs.blender.org/api/2.79/info_quickstart.html>`_

`Full Source Code for __init__.py available here. <_modules/__init__.html>`_

How it's implemented
--------------------

Blender is written in C, but supports addons written in Python. By following the addon tutorial and referencing other addons, I was able to construct a simple user interface for this project in Blender 2.7.9. Blender 2.7.9 is the latest version supported on the Raspberry Pi.

Everything involved in the Blender addon portion of this project is contained in the `__init__.py` file. It includes a module-level definition, :py:attr:`bl_info <__init__.bl_info>`, which tells Blender where to place the addon in the menus and what it should be named, some module level functions for managing the update thread, and one class, :py:class:`SensorMenu <__init__.SensorMenu>`, which extends a blender :py:class:`Operator <bpy.types.Operator>` to create the menu experience.


The Menu
--------

.. image:: images/menu.png

:py:class:`SensorMenu <__init__.SensorMenu>` manages the blender menu. It extends :py:class:`Operator <bpy.types.Operator>`. Operators are commands that can be executed in Blender by pressing spacebar, searching for the command, and hitting enter. Before they take effect, a menu may be displayed to the user so they can adjust the settings of their command before it takes effect.

`SensorMenu` has class-level attributes that describe each of the menu options and the associated data type. These use 'Property' objects as defined by Blender, such as :py:class:`IntProperty <bpy.types.IntProperty>`.

.. code-block:: python
   :caption: initializing an IntProperty
   :name: exintprop

    top_pin = IntProperty(
        name="Top GPIO pin",
        description="The BCM numbering of the joystick top button pin connection",
        default=5,
        min=1,
        max=21
    )

When the class is selected by the user from the command selected :py:func:`SensorMenu.invoke <__init__.SensorMenu.invoke>` is called. This function tells the blender :py:class:`WindowManager <bpy.types.WindowManager>` to create a window for the user interface. `WindowManager` subsequently calls :py:func:`SensorMenu.draw <__init__.SensorMenu.draw>` to make the menu layout.

:py:func:`SensorMenu.draw <__init__.SensorMenu.draw>` defines how and where each menu option should be displayed by defining rows, columns, and boxes. It uses :py:class:`bpy.types.UILayout` to do so. `UILayout` can return new instances of `UILayout` with the :py:meth:`row <bpy.types.UILayout.row>`, :py:meth:`column <bpy.types.UILayout.column>` and :py:meth:`box <bpy.types.UILayout.box>` methods. When the :py:meth:`prop <bpy.types.UILayout.prop>` method is called, that instance of `UILayout` is populated based on the property type. So by passing the `top_pin` attribute that was defined `above <#exintprop>`_ (which is an IntProperty) , for example, an integer selector with full input validation built in, labeled according to the Property values, populates that region of the layout.

.. code-block:: python
   :caption: Example laying out items

    row_4 = main_box.row()  # type(row_4) == bpy.types.UILayout
    gpio_col = row_4.column()  # UILayout
    gpio_box = gpio_col.box()  # UILayout
    gpio_box.label('Readings')
    trigger_select = gpio_box.row()  # UILayout
    trigger_select.prop(self, "trigger_pin")  #  IntProperty
    top_select = gpio_box.row()  #UILayout
    top_select.prop(self, "top_pin")  # IntProperty
    interval_select = gpio_box.row()  #UILayout
    interval_select.prop(self, "update_interval")  # FloatProperty


Execute
-------
When the user presses the menu's **OK** button, :py:func:`SensorMenu.execute <__init__.SensorMenu.execute>` is called. This function calls :py:class:`self.as_keywords <bpy.types.Operator>` to get all the user menu selections as a dictionary, then passes that dictionary to the `main` function with the blender context.

:py:func:`main <__init__.main>` determines what should happen based on what the user selected. The most important selection is **running**, which is a `BoolProperty` that appears as a checkbox on the menu. If that item is selected, the update thread is created and started and if it is unselected, the update thread is stopped.

.. code-block:: python
   :caption: Example starting/ending the update thread
   :name: start thread

    global run_thread, running
    run_selection = kw_copy.pop('running')
    # ...
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

.. _rotations:

Rotations
---------

The core of the logic that parses sensor data into object rotations is contained in the :py:func:`update_from_joystick <__init__.update_from_joystick>` function, which is executed by the update thread as the program runs. It converts readings from :py:class:`JoystickReader <joystick_reader.JoystickReader>`, based on user settings, into the appropriate rotations. Matrix rotations are used when the rotation mode is absolute and Euler rotations are used when the rotation mode is relative.

Each update, if the program is running, the thread tells `JoystickReader` to get a round of values from the sensor then retrieves the rolling averages (or last value, depending on menu settings) from it.

If the retrieved values indicate that the user is pressing the top button on the joystick, the retrieved values are used to apply rotations to every object the user selected at the time the menu was executed.

If the user had set the rotation mode to Absolute, the objects will be rotated along the world axes in Blender. So pitching the joystick forward, in rotation mode absolute, always causes selected objects to rotate on the world's X axis. The following image shows an Object aligned with the the world axes. The blue line represents the Z axis, the green the Y axis, and the red the X axis. No matter how the object is oriented, those lines will stay pointed in the same direction.

.. image:: images/joystick-axis-visible.png

To perform absolute rotations, matrix math had to be used. Each object has a world matrix which is related to its location, rotation, and scale. The world matrix is first decomposed into its inner values by calling :py:meth:`decompose <mathutils.Matrix.decompose>` on the objects :py:attr:`matrix_world <bpy.types.Object.matrix_world>`.

`decompose` returns a :py:class:`Vector <mathutils.Vector>` for the object translation, a :py:class:`Quaternion <mathutils.Quaternion>` for the object rotation, and a :py:class:`Vector <mathutils.Vector>` for the object scale. Each of these objects have methods to derive Matrix objects, and their references are replaced with Matrices.

Next, a new :py:class:`Matrix <mathutils.Matrix>` called `new_rotation` is initialized to represent the user-input rotation change. For each axis, a new Matrix is created and `new_rotation` is reassigned to the value of itself multiplied by that new matrix.

A new world matrix for the object is then assembled by matrix multiplying:

`new world matrix = original location * new rotation * old rotation * old scale`

For relative rotations, the change can be applied by calling the `rotate_axis` function of the :py:attr:`rotation_euler <bpy.types.Object.rotation_euler>` attribute of the :py:class:`3DObject <bpy.types.Object>` being manipulated and passing in the relative axis.

If the user is pressing the trigger button, the 3d object(s) will also change position based on joystick movement. Pitching forward and back moves the objects forward and back relatively. Their forward vectors are found by taking the second column of the object world matrix, which is a column-major matrix. That vector is multiplied by the change in pitch. Each component of that 3d vector is added to the object's location property to move it forward and backward. The process for moving the object side to side as the joystick yaws is similar, except the first (index 0) column of the world matrix is taken to find the x vector.


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