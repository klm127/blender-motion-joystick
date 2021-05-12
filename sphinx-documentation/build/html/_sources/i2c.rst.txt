i2c Interfacing
===============

How it's implemented
--------------------

Two modules define classes which interface with the sensor. :py:mod:`mpu9250_i2c` collects the raw data. :py:mod:`joystick_reader` stores and averages sensor data over time and makes it available to the Blender addon when needed.

The code for interfacing with the sensor over i2c was largely taken from `this article by Joshua Hrisko <https://makersportal.com/blog/2019/11/11/raspberry-pi-python-accelerometer-gyroscope-magnetometer>`_.


`Source Code for mpu9250_i2c <_modules/mpu9250_i2c.html>`_

`Source Code for joystick_reader <_modules/joystick_reader.html>`_


**Spec Sheets**

- :download:`Regular Manual WaveShare Sensor<../../spec sheets/10-DOF-IMU-Sensor-C-User-Manual-EN.pdf>`

- :download:`Product Specification MPU-9250A<../../spec sheets/PS-MPU-9250A-01-v1.1.pdf>`

- :download:`Registry Map MPU-9255<../../spec sheets/RM-MPU-9255.pdf>`

MPU9250_i2c
-----------

.. automodule:: mpu9250_i2c
   :members:

joystick_reader
---------------

.. automodule:: joystick_reader
   :members:

