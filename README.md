# blender-motion-joystick

[Click here for documentation and lab report](https://www.quaffingcode.com/blender-motion-joystick/)

Project using WaveShare MPU-9255 10-DOF IMU Sensor mounted in a Vintage flight joystick handle housing to move objects in Blender. I am unsure on the exact model of the joystick; I bought mine from EBay. Any two-button joystick should work for this.  

Needs SDA, SCL (i2c communication for MPU-9255), 2 GPIO pins for joystick buttons, VCC (3-5v), and Ground.

Project is run via as an addon for Blender 2.7.9, which is the highest version that will run a Raspberry Pi without modifications. An ethernet cable is used for wiring, and plugs into breadboard attached via Wedge to A Raspberry Pi 3.

## Install Blender on Raspberry Pi 

On Raspberry Pi, should be able to run `sudo apt-get install blender` to install blender 

There may be ways to run 2.8 or higher on Rpi, and it's likely this addon will still work, but have not tested it.

## Add addon 

Copy the folder `joystick_control` to `/user/share/blender/scripts/addons`

## Add additional dependencies

Blender runs its own version of Python. That means that it may not have access to certain libs this program needs out of the box. If that's the case, you have to add them manually. That means going into your python folder and copying the `RPi.GPIO` lib and possibly `smbus` over to the Blender/2.79/scripts/modules directory.

Or you can create a virtual environment (haven't tried)
```
virtualenv -p python3 venv
source venv/bin/activate
pip3 install smbus
cp -r venv/lib/python3.5/site-packages/smbus/ ~.config/blender/2.7.9/scripts/modules
```
[link to those instructions](http://lacuisine.tech/blog/2017/10/19/how-to-install-python-libs-in-blender-part-1/)


## Activate addon

Found in user preferences > addons > Object: Motion Sensor Joystick Controls. Check box to activate. 

## Run addon 

Spacebar to bring up commands. Search `Open Joystick Menu` and run it.

Pressing the top button on the joystick allows tilting joystick to move camera angle. Pressing trigger moves joystick forward. 

## Credit

[This article by Joshua Hrisko](https://makersportal.com/blog/2019/11/11/raspberry-pi-python-accelerometer-gyroscope-magnetometer) was indispensable to this project
