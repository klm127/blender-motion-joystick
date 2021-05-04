from tkinter import *

from mpu9250_i2c import *

import time

import RPi.GPIO as GPIO

print('loading')

TRIGGER = 6
TOP=12

GPIO.setmode(GPIO.BCM)

GPIO.setup( [TOP, TRIGGER], GPIO.IN, pull_up_down = GPIO.PUD_UP)        

root = Tk()
base_frame = Frame(root)
accel_label = Label(base_frame, text='acceleration (g)')
x_a_label = Label(base_frame, text='x:')
x_a = StringVar()
x_a_show = Label(base_frame, textvariable=x_a,width=6)
y_a_label = Label(base_frame, text='y:')
y_a = StringVar()
y_a_show = Label(base_frame, textvariable=y_a, width=6)
z_a_label = Label(base_frame, text='z:')
z_a = StringVar()
z_a_show = Label(base_frame, textvariable=z_a)

accel_label.grid(row=0, column=0, columnspan=6, sticky=(N,S,E,W))
x_a_label.grid(row=1, column=0, sticky=E)
y_a_label.grid(row=1, column=2, sticky=E)
z_a_label.grid(row=1, column=4, sticky=E)
x_a_show.grid(row=1, column=1, sticky=W)
y_a_show.grid(row=1, column=3, sticky=W)
z_a_show.grid(row=1, column=5, sticky=W)

accel_avg_label = Label(base_frame, text='acceleration avg')
x_a_avg_label = Label(base_frame, text='x:')
x_a_avg = StringVar()
x_a_avg_show = Label(base_frame, textvariable=x_a_avg,width=6)
y_a_avg_label = Label(base_frame, text='y:')
y_a_avg = StringVar()
y_a_avg_show = Label(base_frame, textvariable=y_a_avg, width=6)
z_a_avg_label = Label(base_frame, text='z:')
z_a_avg = StringVar()
z_a_avg_show = Label(base_frame, textvariable=z_a_avg)

accel_avg_label.grid(row=2, column=0, columnspan=7, sticky=(N,S,E,W))
x_a_avg_label.grid(row=3, column=0, sticky=E)
x_a_avg_show.grid(row=3, column=1, sticky=W)
y_a_avg_label.grid(row=3, column=2, sticky=E)
y_a_avg_show.grid(row=3, column=3, sticky=W)
z_a_avg_label.grid(row=3, column=4, sticky=E)
z_a_avg_show.grid(row=3, column=5, sticky=W)

gyro_label = Label(base_frame, text='gyroscope')
x_g_label = Label(base_frame, text='x:')
x_g = StringVar()
x_g_show = Label(base_frame, textvariable=x_g, width=6)
y_g_label = Label(base_frame, text='y:')
y_g = StringVar()
y_g_show = Label(base_frame, textvariable=y_g, width=6)
z_g_label = Label(base_frame, text='z:')
z_g = StringVar()
z_g_show = Label(base_frame, textvariable=z_g, width=6)

gyro_label.grid(row=4, column=0, columnspan=7, sticky=(N,S,E,W))
x_g_label.grid(row=5, column=0, sticky=E)
x_g_show.grid(row=5, column=1, sticky=W)
y_g_label.grid(row=5, column=2, sticky=E)
y_g_show.grid(row=5, column=3, sticky=W)
z_g_label.grid(row=5, column=4, sticky=E)
z_g_show.grid(row=5, column=5, sticky=W)

gyro_avg_label = Label(base_frame, text='gyroscope avg')
x_g_avg_label = Label(base_frame, text='x:')
x_g_avg = StringVar()
x_g_avg_show = Label(base_frame, textvariable=x_g_avg, width=6)
y_g_avg_label = Label(base_frame, text='y:')
y_g_avg = StringVar()
y_g_avg_show = Label(base_frame, textvariable=y_g_avg, width=6)
z_g_avg_label = Label(base_frame, text='z:')
z_g_avg = StringVar()
z_g_avg_show = Label(base_frame, textvariable=z_g_avg, width=6)

gyro_avg_label.grid(row=6, column=0, columnspan=7, sticky=(N,S,E,W))
x_g_avg_label.grid(row=7, column=0, sticky=E)
x_g_avg_show.grid(row=7, column=1, sticky=W)
y_g_avg_label.grid(row=7, column=2, sticky=E)
y_g_avg_show.grid(row=7, column=3, sticky=W)
z_g_avg_label.grid(row=7, column=4, sticky=E)
z_g_avg_show.grid(row=7, column=5, sticky=W)

pitch_text = StringVar()
pitch_label = Label(base_frame, textvariable=pitch_text)
pitch_label.grid(row=8,columnspan=7)
yaw_text = StringVar()
yaw_label = Label(base_frame, textvariable=yaw_text)
yaw_label.grid(row=9,columnspan=7)
roll_text = StringVar()
roll_label = Label(base_frame, textvariable=roll_text)
roll_label.grid(row=10,columnspan=7)


# place window on screen
screen_width = str(round(root.winfo_screenwidth()/2))
screen_height = str(round(root.winfo_screenheight()/4))
base_frame.grid(sticky=(E,W))
# root.geometry = f"+{screen_height}+{screen_width}"
root.geometry(f"+{screen_width}+{screen_height}")



global looping
looping = True

def on_closing():
    looping = False
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

x_a_avg_tuple = ([], x_a_avg)
y_a_avg_tuple = ([], y_a_avg)
z_a_avg_tuple = ([], z_a_avg)

x_g_avg_tuple = ([], x_g_avg)
y_g_avg_tuple = ([], y_g_avg)
z_g_avg_tuple = ([], z_g_avg)

keep_vals = 10

def add_avg_val(val, avg_tuple):
    avg_tuple[0].append(val)
    if len(avg_tuple[0]) > keep_vals:
        avg_tuple[0].pop(0)
    tot = 0
    for each in avg_tuple[0]:
        tot += each
    avg_tuple[1].set(str(round(tot/len(avg_tuple[0]),3)))

x_gyro_off = 0
y_gyro_off = 0
z_gyro_off = 0

last_x_g = 0
last_y_g = 0
last_z_g = 0

def set_offsets(empty):
    x_gyro_off = last_x_g
    y_gyro_off = last_y_g
    z_gyro_off = last_z_g

GPIO.add_event_detect(TOP, GPIO.RISING, callback=set_offsets, bouncetime=200)


i = 0
while looping:
    if looping:
        root.update()
    try:
        ax, ay, az, wx, wy, wz = mpu6050_conv()
        last_x_g = wx
        last_y_g = wy
        last_z_g = wz
        x_a.set(str(round(ax,3)))
        add_avg_val(ax, x_a_avg_tuple)
        y_a.set(str(round(ay,3)))
        add_avg_val(ay, y_a_avg_tuple)
        z_a.set(str(round(az,3)))
        add_avg_val(ay, z_a_avg_tuple)
        x_g.set(str(round(wx-x_gyro_off,3)))
        add_avg_val(wx-x_gyro_off, x_g_avg_tuple)
        y_g.set(str(round(wy-x_gyro_off,3)))
        add_avg_val(wy-x_gyro_off, y_g_avg_tuple)
        z_g.set(str(round(wz-x_gyro_off,3)))
        add_avg_val(wz-x_gyro_off, z_g_avg_tuple)

        if wx-x_gyro_off > 10:
            pitch_text.set('Pitch backward!')
        elif wx-x_gyro_off < -10:
            pitch_text.set('Pitch forward!')
        else:
            pitch_text.set('')

        if wy-y_gyro_off > 10:
            yaw_text.set('Yaw right!')
        elif wy-y_gyro_off < -10:
            yaw_text.set('Yaw left!')
        else:
            yaw_text.set('')

        if wz-z_gyro_off > 10:
            # roll right
            roll_text.set('Roll right!')
        elif wz-z_gyro_off < -10:
            roll_text.set('Roll left!')
        else:
            roll_text.set('')
            
        # mx, my, mz = AK8963_conv()
        # m_x.set(str(round(mx,3)))
        # m_y.set(str(round(my,3)))
        # m_z.set(str(round(mz,3)))
    except:
        time.sleep(0.1)
        continue
    time.sleep(0.1)

