import time
import signal
import os
from tkinter import *
from evdev import InputDevice


class BatteryInfo:
    def __init__(self):
        # 1 - AC . 0 - battery
        self.mode = 1
        self.capacity = 100
        self.hours_remain = 2
        self.minutes_remain = 2
        self.brightness_at_start = 100
        self.brightness_in_powersafe_mode = int(self.brightness_at_start / 2)
        self.brightness = 100
        self.get_brightness_at_start()
        # in seconds
        self.dim_time = 5

    def get_power_type(self):
        uevent = open("/sys/class/power_supply/AC/uevent")
        online_string = uevent.read()
        self.mode = int(online_string[-2:])
        if self.mode == 1:
            text.insert(INSERT, "AC mode")
            text.insert(INSERT, '\n')
        else:
            text.insert(INSERT, "Battery mode")
            text.insert(INSERT, '\n')
        uevent.close()

    def get_capacity(self):
        capacity = open("/sys/class/power_supply/BAT0/capacity")
        self.capacity = int(capacity.read())
        text.insert(INSERT, "Capacity: " + str(self.capacity) + "%")
        text.insert(INSERT, '\n')
        capacity.close()

    def get_estimated_time(self):
        if self.mode == 0:
            charge_now_file = open("/sys/class/power_supply/BAT0/charge_now")
            current_now_file = open("/sys/class/power_supply/BAT0/current_now")

            charge_now_int = int(charge_now_file.read())
            current_now_int = int(current_now_file.read())

            if current_now_int != 0:
                time_remain = divmod(charge_now_int, current_now_int)
                self.hours_remain = time_remain[0]
                self.minutes_remain = int((charge_now_int / current_now_int - self.hours_remain) * 60)
                text.insert(INSERT, "Time to full discharge: " + "0" + ":" + str(self.minutes_remain))
                text.insert(INSERT, '\n')

            charge_now_file.close()
            current_now_file.close()

    def get_brightness_at_start(self):
        brightness = open("/sys/class/backlight/nv_backlight/brightness")
        self.brightness_at_start = int(brightness.read())
        self.brightness = self.brightness_at_start
        brightness.close()

    # you need rights to write to brightness file
    def set_powersafe_brightness(self):
        brightness = open("/sys/class/backlight/nv_backlight/brightness", "w")
        brightness.write(str(self.brightness_in_powersafe_mode))
        self.brightness = self.brightness_in_powersafe_mode
        #brightness.close()

    def set_original_brightness(self):
        os.system("xset dpms force on")
        brightness = open("/sys/class/backlight/nv_backlight/brightness", "w")
        brightness.write(str(self.brightness_at_start))
        self.brightness = self.brightness_at_start
        brightness.close()

top = Tk()
text = Text(top)
field = Entry()
text.pack()
field.pack()
info = BatteryInfo()
data_update_time = 3
dim_time = 5
dev = InputDevice('/dev/input/event0')
dev2 = InputDevice('/dev/input/event6')

def signal_handler(signal, frame):
    text.insert(INSERT, 'Backlight settings were restored')
    text.insert(INSERT, '\n')
    info.set_original_brightness()
    dev.close()
    dev2.close()
    sys.exit(0)

def loop(count_time, dim_flag, dim_start_time, start_time, event_flag):
    keyboard_event = dev.read_one()
    mouse_event = dev2.read_one()

    if field.get() != "":

        dim_time = int(field.get())

        if keyboard_event is not None and mouse_event is not None and event_flag is False:
            dim_start_time = time.time()

            # turn off dim
            if info.mode == 0 and info.brightness != info.brightness_at_start and dim_flag is True:
                info.set_original_brightness()
                dim_start_time = time.time()
                dim_flag = False

        # change brightness according to the current battery mode
        if info.mode == 1 and info.brightness != info.brightness_at_start:
            info.set_original_brightness()

        if info.mode == 0 and info.brightness != info.brightness_in_powersafe_mode \
                and dim_start_time + dim_time < time.time() and dim_flag is False:
            os.system("xset dpms force off")
            info.set_powersafe_brightness()
            dim_start_time = time.time()
            dim_flag = True

        if time.time() > count_time + data_update_time:
            count_time = time.time()
            info.get_power_type()
            info.get_capacity()
            info.get_estimated_time()

    top.after(100, loop, count_time, dim_flag, dim_start_time, start_time, event_flag)



if __name__ == '__main__':
    text.insert(INSERT, dev2)
    text.insert(INSERT, '\n')

    signal.signal(signal.SIGINT, signal_handler)
    start_time = time.time()
    dim_start_time = time.time()
    count_time = time.time() - data_update_time
    dim_flag = False
    event_flag = False

    loop(count_time, dim_flag, dim_start_time, start_time, event_flag)
    top.mainloop()


