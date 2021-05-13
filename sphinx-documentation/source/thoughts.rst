Final Thoughts
==============

Project Challenges
------------------
Getting the proper Blender environment set up on the Raspberry Pi was involved. Blender uses its own version of Python, which doesn't have critical libraries like RPi.GPIO and smbus. These must be copied to the Blender directory manually. Generally, there was a lot to learn about how Blender handles addons, but the documentation is thorough. I also made the mistake of studying a later version of Blender on another machine, though much of that was still useful.

The single most difficult part of the project was getting matrix rotations to function properly, especially when rotating on the absolute axis. This is an important feature, because the relative axis mode is really only useful when controlling the camera - when rotating an object separate from the user's view, only absolute rotations are intuitive. I haven't yet taken Linear Algebra and was not familiar with matrices. Physics also has not covered Quaternions. Eventually, after combing StackOverflow and the Blender forums, I was able to find the solution, which is described in the :ref:`rotations` section of the Blender page.

Some oddball problems also slowed me down. For example, the inertia sensors were not available domestically and had to be ordered from China, which had a 1 month+ ship time. I found a reseller in England who, while twice as expensive, could ship in under 2 weeks. Unfortunately, this sensor was stolen from my front porch and I had to wait for the ones from China to arrive before I could start testing my low-level communication. During that time, I focused on learning what I needed about Blender.

Another issue was finding a use for the accelerometer and using the magnetometer data. I know that the accelerometer was reading accurately, as it gave the Y axis value as -1g when the joystick was held upright. However, I was not able to incorporate accleration-as-movement in this project. This may be, in part, because to determine the absolute direction the joystick is moving (i.e., its overall z is increasing when raised up perpindicular to the ground ), one likely must combine information from all 3 sensors based on their orientation. The matrix math and/or linear algebra involved in that was beyond the levels I have attained thus far in my learning, and I was unable to conceptualize how to effect that, nor was I able to find convenient tutorials. In some ways, it's a miracle that I got the gyroscope portion working properly.

Future Versions
---------------
If I were to extend this project in a future version, there are several things I would like to change and add.

- Move SensorMenu to its own .py file rather than have it in __init__.py. (Messy)
- See if sensor hardware settings can be tweaked for better performance.
- Have Options in the Blender UI for changing low-level sensor options, like sample rate and sample division.
- Explore other ways to implement the addon in Blender.
- Use the accelerometer to enable movement by pressing trigger and moving joystick. This was something I wanted to implement, but it wasn't performing correctly. Accelerometer sampling may need to be tweaked, or its something else.
- Additional sensors in 3D printed housings for a full motion capture suit.
- Add bluetooth capability and battery to joystick.

Conclusion
----------
This was a fun class that taught me a lot in an area I was really weak in, understanding how low-level electronics function. I'm proud of this final project, even though I shot a bit higher than where I landed. I will work with i2c again on a side project in the future, and am glad I learned about it.

.. image:: images/fly-around.png