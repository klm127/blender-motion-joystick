.. blender-motion-joystick documentation master file, created by
   sphinx-quickstart on Tue May 11 12:05:25 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

blender-motion-joystick
=======================

5/11/2021

This is the documentation and lab report for Karl Miller's final project in COMP-430, Systems Fundamentals, with Professor Eglowstein.

The project hardware consists a plastic 2-button joystick containing an accelerometer, wired to a Raspberry PI 3 using I-squared-C and GPIO pins.

The project software consists of an addon for the popular 3D modeling software Blender.

When the blender addon is installed and running, wrist-motion data collected as the user orients the joystick are converted into object rotations and translations in Blender, allowing real-world movement to be effected as manipulations in the virtual 3-D space.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   intro
   wiring
   i2c interfacing <i2c>
   blender addon <blender>
   final thoughts <thoughts>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
