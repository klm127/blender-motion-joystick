i2c Interfacing
===============

References
----------

The code for interfacing with the sensor over i2c was largely taken from `this article by Joshua Hrisko <https://makersportal.com/blog/2019/11/11/raspberry-pi-python-accelerometer-gyroscope-magnetometer>`_.


`Source Code for mpu9250_i2c <_modules/mpu9250_i2c.html>`_

`Source Code for joystick_reader <_modules/joystick_reader.html>`_


**Spec Sheets**

- :download:`Regular Manual WaveShare Sensor<../../spec sheets/10-DOF-IMU-Sensor-C-User-Manual-EN.pdf>`

- :download:`Product Specification MPU-9250A<../../spec sheets/PS-MPU-9250A-01-v1.1.pdf>`

- :download:`Registry Map MPU-9255<../../spec sheets/RM-MPU-9255.pdf>`

How it's implemented
--------------------

Two modules define classes which interface with the sensor. :py:mod:`mpu9250_i2c` collects the raw data. :py:mod:`joystick_reader` stores and averages sensor data over time and makes it available to the Blender addon when needed.

The sensor uses inter-integrated circuit, or "i squared c" to communicate with the Raspberry Pi. I2C consists of two wires; the SDA (Serial data line) and SCL (Serial clock line) and pull up resistors which keep those lines high until pulled low. The SCL switches between high and low at a fixed rate. Based on the offset between the highs and lows of the SCL line and highs and lows of the SDA line, I2C devices can interpret bit data. i2C transfers data grouped into 8 bits (1 byte). The first byte of the transfer is always the address of the receiving device so more than one device can be connected at a time, except for the last bit, which indicates whether the master device should write (0) or read (1) bits from the slave device.

The next address of a transfer is the address of the internal register of the receiving I2C device. This is generally followed with data to write starting at that location.

:py:mod:`mpu9250_i2c` handles the I2C communication in this project. It initializes the accelerometer by transmitting bytes to appropriate registers to reset it to a standard mode with the :py:func:`mpu9250_i2c.MPU6050_start` function. This tells the sensor, among other things, to sample the gyroscope at 250 degrees per second.

As the blender addon thread loops, :py:func:`mpu9250_i2c.mpu6050_conv` is called regularly. This function uses :py:func:`mpu9250_i2c.read_raw_bits` to extract bits from the registers in the mpu9250 where sensor readings are stored. It actually extracts one byte from the specified register and then extracts the byte from the subsequent register. Those two bytes, the high byte and the low byte, together form the reading for that sensor. Each reading is converted to degrees and adjusted based on the sensitivity setting of the sensor (250 degrees per second).

The :py:class:`~joystick_reader.JoystickReader` class is used to interface between the blender addon and the mpu9250 conversion module. `JoystickReader` contains an instance of :py:class:`~joystick_reader.Axis` for each of the 3 acceleration sensors and each of the 3 gyroscope sensors, 6 total. `JoystickReader` collects values from `mpu6050_conv` and passes them to the `Axis` objects. The `Axis` objects keep running averages of recently read values based on their settings. `JoystickReader` also tracks what GPIO pins the trigger button and the top button of the Joystick are wired to. It sets up the GPIO system using the `RPi.GPIO <https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/>`_ library.

When :py:func:`JoystickReader.get_averages <joystick_reader.JoystickReader.get_averages>` is called by the blender addon, `JoystickReader` retrieves the current average (or the last read, if that setting is selected) from each `Axis`. `JoystickReader` also determines whether the GPIO lines that the trigger and top are wired to are high or low. `JoystickReader` then assembles that in a dictionary and returns it for use by the Blender addon.

.. code-block:: python
   :caption: Example return dictionary from JoystickReader.get_averages

   return {
    'ax':self.acceleration_x.average,
    'ay':self.acceleration_y.average,
    'az':self.acceleration_z.average,
    'wx':self.gyro_x.average,
    'wy':self.gyro_y.average,
    'wz':self.gyro_z.average,
    'top': GPIO.input(self.top_pin),
    'trigger': GPIO.input(self.trigger_pin)
   }



MPU9250_i2c
-----------

.. automodule:: mpu9250_i2c
   :members:

joystick_reader
---------------

.. automodule:: joystick_reader
   :members:

