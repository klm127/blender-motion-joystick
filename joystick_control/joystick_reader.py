import random # just for testing, gen random vals


try:
    import RPi.GPIO as GPIO
    from . import mpu9250_i2c
    error_message = False
except ImportError:
    error_message = True

    
class Axis:
    """
    Stores rolling average of recorded values for an axis.

    :param name: name of the axis, e.g. 'ax','wy',etc.
    :type name: str
    :param keep_vals: number of recently read values to keep for averaging.
    :type keep_vals: int
    :param weight: factor to weigh last-read value
    :type weight: float
    """
    def __init__(self, name, keep_vals=10, weight=0):
        self.name = name
        """ 
        name of the axis 
        
        :type: str
        """
        self.vals = []
        """ 
        last few values recorded 
        
        :type: list
        """
        self.average = 0.0
        """ 
        current average 
        
        :type: float
        """
        self.keep_vals = keep_vals
        """ 
        number of values to keep 
        
        :type: int
        """
        self.weight=weight
        """ 
        weights the last reading 
        :type: float
        """
        
    def add_val(self, val):
        """
        Append value to recently-read values and update average based on weighting.

        :param val: value to add
        :type val: number
        """
        self.vals.append(val)
        while len(self.vals) > self.keep_vals:
            self.vals.pop(0)
        total = 0
        for each in self.vals:
            total += each
        self.average = (total + val*self.weight)/ (len(self.vals)+self.weight)
        # print(f"{val} added to {self.name}, new avg: {self.average}")
        
    def get_last_val(self):
        """
        Get the last read value of this axis.

        :returns: last value
        :rtype: number
        """
        return self.vals[len(self.vals)-1]

    def zero(self):
        """
        Clear stored values and zero average.
        """
        self.vals = []
        self.average = 0


class JoystickReader:
    """
    Interfaces with sensor and updates axis objects with readings.

    :param trigger_pin: The raspberry Pi GPIO pin that the trigger button is wired to.
    :type trigger_pin: int
    :param top_pin: The raspberry Pi GPIO pin that the top button is wired to.
    :type top_pin: int
    :param keep_vals: The number of sensor readings each axes will store for averaging.
    :type keep_vals: int
    :param weight: The factor by which each axis will weight the last-read sensor value.
    :type weight: float
    """
    def __init__(self, trigger_pin, top_pin, keepvals=10, weight=0):
        """
        Interfaces with sensor and updates axis objects with readings.

        :param trigger_pin: The raspberry Pi GPIO pin that the trigger button is wired to.
        :type trigger_pin: int
        :param top_pin: The raspberry Pi GPIO pin that the top button is wired to.
        :type top_pin: int
        :param keep_vals: The number of sensor readings each axes will store for averaging.
        :type keep_vals: int
        :param weight: The factor by which each axis will weight the last-read sensor value.
        :type weight: float
        """
        self.trigger_pin = trigger_pin
        self.top_pin = top_pin
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup( [self.trigger_pin, self.top_pin], GPIO.IN, pull_up_down = GPIO.PUD_UP)
        self.acceleration_x = Axis('acceleration x', keep_vals=keepvals, weight=weight)
        self.acceleration_y = Axis('acceleration y', keep_vals=keepvals, weight=weight)
        self.acceleration_z = Axis('acceleration z', keep_vals=keepvals, weight=weight)
        self.gyro_x = Axis('gyro x', keep_vals=keepvals, weight=weight)
        self.gyro_y = Axis('gyro y', keep_vals=keepvals, weight=weight)
        self.gyro_z = Axis('gyro z', keep_vals=keepvals, weight=weight)
        self.axes = []
        """
        A list of the used axes. 
        
        Includes self.acceleration_x, self.acceleration_y, self.acceleration_z, self.gyro_x, self.gyro_y, and self.gyro_z 
        
        :ref: `joystick_reader.Axis`
        
        
        :type: Axis
         
        """
        self.axes.append(self.acceleration_x)
        self.axes.append(self.acceleration_y)
        self.axes.append(self.acceleration_z)
        self.axes.append(self.gyro_x)
        self.axes.append(self.gyro_y)
        self.axes.append(self.gyro_z)
        
    def load_pins(self, trigger_pin, top_pin):
        """
        Change the RPi.GPIO pins for the top and trigger line.

        Turns off input detection for previously active pins.

        :param trigger_pin: The raspberry Pi GPIO pin that the trigger button is wired to.
        :type trigger_pin: int
        :param top_pin: The raspberry Pi GPIO pin that the top button is wired to.
        :type top_pin: int
        """
        GPIO.setup([self.trigger_pin, self.top_pin], GPIO.IN, pull_up_down = GPIO.PUD_OFF)
        self.trigger_pin = trigger_pin
        self.top_pin = top_pin
        GPIO.setup( [self.trigger_pin, self.top_pin], GPIO.IN, pull_up_down = GPIO.PUD_UP)

    def load_keep_vals_and_weight(self, new_keep_vals, new_weight):
        """
        Changes retained values length and last value weighting for all axes.
        
        :param keep_vals: The number of sensor readings each axes will store for averaging.
        :type keep_vals: int
        :param weight: The factor by which each axis will weight the last-read sensor value.
        :type weight: float
        
        """
        for ax in self.axes:
            ax.weight = new_weight
            ax.keep_vals = new_keep_vals
        
    def end(self):
        """
        Turns off detection for currently active RPi.GPIO pins.
        """
        GPIO.setup([self.trigger_pin, self.top_pin], GPIO.IN, pull_up_down = GPIO.PUD_OFF)
        
    def get_round_of_random_values(self): # for testing without RPi.GPIO
        """
        Adds a value between -5 and 5 to each Axis.
        """
        rand_min = -5
        rand_max = 5
        ax = random.randrange(rand_min,rand_max)/100
        ay = random.randrange(rand_min,rand_max)/100
        az = random.randrange(rand_min,rand_max)/100
        wx = random.randrange(rand_min,rand_max)/100
        wy = random.randrange(rand_min,rand_max)/100
        wz = random.randrange(rand_min,rand_max)/100
        self.acceleration_x.add_val(ax)
        self.acceleration_y.add_val(ay)
        self.acceleration_z.add_val(az)
        self.gyro_x.add_val(wx)
        self.gyro_y.add_val(wy)
        self.gyro_z.add_val(wz)

    def zero_gyro(self):
        """
        Zeros gyroscopes.
        """
        self.gyro_x.zero()
        self.gyro_y.zero()
        self.gyro_z.zero()

    def get_vals_from_sensor(self):
        """
        Gets values from :py:mod:`mpu9250_i2c.py` , which interfaces with the sensor.

        Passes sensor reads to appropriate Axis object.

        If sensor fails to read, sets global error flag.
        """
        global error_message
        try:
            ax, ay, az, wx, wy, wz = mpu9250_i2c.mpu6050_conv()
            # print(wx,wy,wz)
            # self.acceleration_x.add_val(ax)
            # self.acceleration_y.add_val(ay) + 0.98  # grav offset
            # self.acceleration_z.add_val(az)
            self.gyro_x.add_val(wx)
            self.gyro_y.add_val(wy)
            self.gyro_z.add_val(wz)
            error_message = False
        except ( NameError, ModuleNotFoundError ):
            error_message = True
        
        
    def get_averages(self):
        """

        Returns average readings for each Axis object as a dictionary.

        :returns: Axis averages and GPIO pin reads.
        :rtype: dict
        """
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
    
    def get_last(self):
        """
        Returns last readings for each Axis object as a dictionary.

        :returns: Axis last-reads and GPIO pin reads.
        :rtype: dict
        
        """
        return {
            'ax':self.acceleration_x.get_last_val(),
            'ay':self.acceleration_y.get_last_val(),
            'az':self.acceleration_z.get_last_val(),
            'wx':self.gyro_x.get_last_val(),
            'wy':self.gyro_y.get_last_val(),
            'wz':self.gyro_z.get_last_val(),
            'top': GPIO.input(self.top_pin),
            'trigger': GPIO.input(self.trigger_pin)
        }
        
