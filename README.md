# blender-motion-joystick
Project using MPU-9255 10-DOF IMU Sensor mounted in a Vintage flight joystick handle housing to move objects in Blender. I am unsure on the exact model of the joystick; I bought mine from EBay. 

Needs SDA, SCL (i2c communication for MPU-9255), 2 GPIO pins for joystick buttons, VCC (3-5v), and Ground.

Project is run via as an addon for Blender 2.7.9, which is the highest version that will run a Raspberry Pi. An ethernet cable is used for wiring, and plugs into breadboard attached via Wedge to A Raspberry Pi 3.
