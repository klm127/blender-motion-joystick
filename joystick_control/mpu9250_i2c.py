"""
This module interfaces directly with the sensor.

This code was largely taken from `this article by Joshua Hrisko <https://makersportal.com/blog/2019/11/11/raspberry-pi-python-accelerometer-gyroscope-magnetometer>`_.

"""

if __name__ == '__main__':
    import smbus, time

def MPU6050_start():
    """

    This function initializes the sensor in the following manner:

    1. Set the sample rate div to zero (no change in the sample rate.)
    2. Set the power management register to all zeros, with the following effects:

        *  Set to not sleep mode.
        *  Set to normal sample mode.
        *  Set to normal gyro power mode.
        *  Set to normal voltage generator mode.
        *  Set to default clock speed.

    3. Write the power management register again, to reset internal registers.
    4. Write the config register with all zeros, with the following effects:

        * Set FIFO mode to normal.
        * Set FSYNC to normal.
        * Set DLPF_CFG to normal.

    5. Write all zeros to the GYRO_CONFIG register with the following effects:

        * Set sample rate to 250 degrees/second
        * Do not bypass DPLF

    6. Write all zeros to the ACCEL_CONFIG register, setting the accel sample rate to +- 2g/second.

    7. Write a 1 to INT_ENABLE register, to enable interrupt when sensor gets any reading.

    :return: A tuple of (gyro sample rate, acceleration sample rate)
    :rtype: tuple
    """
    # alter sample rate (stability)
    samp_rate_div = 0 # sample rate = 8 kHz/(1+samp_rate_div)
    bus.write_byte_data(MPU6050_ADDR, SMPLRT_DIV, samp_rate_div)
    time.sleep(0.1)
    # reset all sensors
    bus.write_byte_data(MPU6050_ADDR,PWR_MGMT_1,0x00)
    time.sleep(0.1)
    # power management and crystal settings
    bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0x01)
    time.sleep(0.1)
    #Write to Configuration register
    bus.write_byte_data(MPU6050_ADDR, CONFIG, 0)
    time.sleep(0.1)
    #Write to Gyro configuration register
    gyro_config_sel = [0b00000,0b010000,0b10000,0b11000] # byte registers
    gyro_config_vals = [250.0,500.0,1000.0,2000.0] # degrees/sec
    gyro_indx = 0
    bus.write_byte_data(MPU6050_ADDR, GYRO_CONFIG, int(gyro_config_sel[gyro_indx]))
    time.sleep(0.1)
    #Write to Accel configuration register
    accel_config_sel = [0b00000,0b01000,0b10000,0b11000] # byte registers
    accel_config_vals = [2.0,4.0,8.0,16.0] # g (g = 9.81 m/s^2)
    accel_indx = 0                            
    bus.write_byte_data(MPU6050_ADDR, ACCEL_CONFIG, int(accel_config_sel[accel_indx]))
    time.sleep(0.1)
    # interrupt register (related to overflow of data [FIFO])
    bus.write_byte_data(MPU6050_ADDR, INT_ENABLE, 1)
    time.sleep(0.1)
    return gyro_config_vals[gyro_indx],accel_config_vals[accel_indx]
    
def read_raw_bits(register):
    """
    This reads the raw bits at a high sensor register and the raw bits at the subsequent register (the low byte). It combines those value to get the total read for the sensor.

    :param register: The high byte of a sensor read register.
    :type register: byte
    :return: The sensor reading.
    :rtype: int
    """
    # read accel and gyro values
    high = bus.read_byte_data(MPU6050_ADDR, register)
    low = bus.read_byte_data(MPU6050_ADDR, register+1)

    # combine high and low for unsigned bit value
    value = ((high << 8) | low)
    
    # convert to +- value
    if(value > 32768):
        value -= 65536
    return value

def mpu6050_conv():
    """
    Gets the sensor readings for each register by calling :py:func:`read_raw_bits` for each sensor register.

    Converts those readings to floats of the appropriate magnitude by multiplying by the quantity per second that the sensor is set to.

    :return: A tuple of (ax, ay, az, wx, wy, wz)
    :rtype: tuple
    """
    # raw acceleration bits
    acc_x = read_raw_bits(ACCEL_XOUT_H)
    acc_y = read_raw_bits(ACCEL_YOUT_H)
    acc_z = read_raw_bits(ACCEL_ZOUT_H)

    # raw temp bits
##    t_val = read_raw_bits(TEMP_OUT_H) # uncomment to read temp
    
    # raw gyroscope bits
    gyro_x = read_raw_bits(GYRO_XOUT_H)
    gyro_y = read_raw_bits(GYRO_YOUT_H)
    gyro_z = read_raw_bits(GYRO_ZOUT_H)

    #convert to acceleration in g and gyro dps
    a_x = (acc_x/(2.0**15.0))*accel_sens
    a_y = (acc_y/(2.0**15.0))*accel_sens
    a_z = (acc_z/(2.0**15.0))*accel_sens

    w_x = (gyro_x/(2.0**15.0))*gyro_sens
    w_y = (gyro_y/(2.0**15.0))*gyro_sens
    w_z = (gyro_z/(2.0**15.0))*gyro_sens

##    temp = ((t_val)/333.87)+21.0 # uncomment and add below in return
    return a_x,a_y,a_z,w_x,w_y,w_z

def AK8963_start():
    # not used
    bus.write_byte_data(AK8963_ADDR,AK8963_CNTL,0x00)
    time.sleep(0.1)
    AK8963_bit_res = 0b0001 # 0b0001 = 16-bit
    AK8963_samp_rate = 0b0110 # 0b0010 = 8 Hz, 0b0110 = 100 Hz
    AK8963_mode = (AK8963_bit_res <<4)+AK8963_samp_rate # bit conversion
    bus.write_byte_data(AK8963_ADDR,AK8963_CNTL,AK8963_mode)
    time.sleep(0.1)
    
def AK8963_reader(register):
    # not used
    # read magnetometer values
    low = bus.read_byte_data(AK8963_ADDR, register-1)
    high = bus.read_byte_data(AK8963_ADDR, register)
    # combine higha and low for unsigned bit value    
    value = ((high << 8) | low)
    # convert to +- value
    if(value > 32768):
        value -= 65536
    return value

def AK8963_conv():
    # raw magnetometer bits
    # not used

    loop_count = 0
    while 1:
        mag_x = AK8963_reader(HXH)
        mag_y = AK8963_reader(HYH)
        mag_z = AK8963_reader(HZH)

        # the next line is needed for AK8963
        #if bin(bus.read_byte_data(AK8963_ADDR,AK8963_ST2))=='0b10000':
        #    break
        loop_count+=1
        
    #convert to acceleration in g and gyro dps
    m_x = (mag_x/(2.0**15.0))*mag_sens
    m_y = (mag_y/(2.0**15.0))*mag_sens
    m_z = (mag_z/(2.0**15.0))*mag_sens

    return m_x,m_y,m_z

# MPU6050 Registers
MPU6050_ADDR = 0x68  # 104
"""
The i2c address of the sensor, which is 104.
"""
PWR_MGMT_1   = 0x6B  # 107
"""
Power management register 

.. csv-table:: Bit Mapping
   :header: "Bit","Name","Description"
   
   "7","H_RESET","1 resets internal registers and restores default. Auto clears."
   "6","SLEEP","Sets chip to sleep mode."
   "5","CYCLE","Sets chip to a single sample mode. (Not used)"
   "4","GYRO_STANDBY","Lower power mode for Gyros."
   "3","PD_PTAT","Power done internal PTAT voltage generator. (Not used)"
   "2-0","CLKSEL","Selects clock speed."
   
"""
SMPLRT_DIV   = 0x19  # 25
"""
Sample Rate Divider register. 

Internal sample rate divided by this number to generate the final sample rate.

.. csv-table:: Bit Mapping
   :header: "Bit","Name","Description"
   
   "7-0", "SMPLRT_DIV", "Sample Rate Divider"

`Final Sample Rate` = Internal_Sample_Rate / (1 + SMPLRT_DIV)

"""
CONFIG       = 0x1A  # 26
"""
Configuration. 

.. csv-table:: Bit Mapping
   :header: "Bit","Name","Description"
   
   "7","-","reserved"
   "6","FIFO_MODE","1 means additional writes will not be added to fifo"
   "5-3","EXT_SYNC_SET","Enables FSYNC pin data to be sampled for short strobes"
   "2-0", DLPF_CFG","Not used"
   
"""
GYRO_CONFIG  = 0x1B  # 27
"""
**Gyroscope configuration**

.. csv-table:: Bit Mapping
   :header: "Bit","Name","Description"
   
   "7","XGYRO_Cten","X Gyro Self Test"
   "6","YGYRO_Cten","Y Gyro Self Test"
   "5","ZGYRO_Cten","Z Gyro Self Test"
   "4-3","GYRO_FS_SEL","Sets Gyro sample rate"
   "2","-","reserved"
   "1","Fchoice_b","Bypass dplf - not used"
   
GYRO_FS_SEL sample rates are:
 - 00 = +250 degrees/second
 - 01 = +500 degrees/second
 - 10 = +1000 degrees/second
 - 11 = +2000 degrees/second

"""
ACCEL_CONFIG = 0x1C  # 28
"""
**Accelerometer configuration**

.. csv-table:: Bit Mapping
   :header: "Bit","Name","Description"
   
   "7","ax_st_en","X Accel Self Test"
   "6","ay_st_en","Y Accel Self Test"
   "5","az_st_en","Z Accel Self Test"
   "4-3","ACCEL_FS_SEL","Sets Accel Sample rate"
   "2-0","-","reserved"
   
ACCEL_FS_SEL sample rates are:
 - 00 = +-2 g/second
 - 01 = +-4 g/second
 - 10 = +-8 g/second
 - 11 = +-16 g/second
 
"""
INT_ENABLE   = 0x38  # 56
"""
**Interrupt Enable**

.. csv-table:: Bit Mapping
   :header: "Bit","Name","Description"
   
   "7","WOM_EN","1 - enable interrupt for wake on motion"
   "6","-","reserved"
   "5","FIFO_OVERFLOW_EN","1 - enable interrupt fifo overflow"
   "4","FSYNC_INT_EN","1 - enable fsync interrupt"
   "3","-","reserved"
   "2","-","reserved"
   "1","RAW_RDY_EN","1 - enable raw sensor data ready interrupt"
   
"""
ACCEL_XOUT_H = 0x3B  # 59
"""
X-Accelerometer High Byte
"""
ACCEL_YOUT_H = 0x3D  # 61
"""
Y-Accelerometer High Byte
"""
ACCEL_ZOUT_H = 0x3F  # 63
"""
Z-Accelerometer High Byte
"""
TEMP_OUT_H   = 0x41  # 65
GYRO_XOUT_H  = 0x43  # 67
"""
X-Gyro High Byte
"""
GYRO_YOUT_H  = 0x45  # 69
"""
Y-Gyro High Byte
"""
GYRO_ZOUT_H  = 0x47  # 71
"""
Z-Gyro High Byte
"""
#AK8963 registers
AK8963_ADDR   = 0x77  # 119
AK8963_ST1    = 0x02  # 2
HXH          = 0x04  # 4
HYH          = 0x06  # 6
HZH          = 0x08  # 8
AK8963_ST2   = 0x09  # 9
AK8963_CNTL  = 0x0A  # 10
mag_sens = 4900.0 # magnetometer sensitivity: 4800 uT

if __name__ == '__main__':
    # start I2C driver
    bus = smbus.SMBus(1) # start comm with i2c bus
    gyro_sens,accel_sens = MPU6050_start() # instantiate gyro/accel
    # AK8963_start() # instantiate magnetometer
else:
    bus = None
    """
    bus is initialized to smbus
    
    :type: :py:class:`smbus2.SMBus`
    
    """
    gyro_sens = 250
    """
    set to returned value from :py:func:`MPU6050_start`, which is 250 degrees per second
    """
    accel_sens = 2
    """
    set to returned value from :py:func:`MPU6050_start`, which is 2 Gs per second
    """
