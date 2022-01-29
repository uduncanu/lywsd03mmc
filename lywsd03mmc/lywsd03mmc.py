from lywsd02 import Lywsd02Client
import struct
import collections
from datetime import datetime, timedelta

UUID_HISTORY = 'EBE0CCBC-7A0A-4B0C-8A1A-6FF2997DA3A6'  # Last idx 152          READ NOTIFY
UUID_FIRMWARE = '00002a26-0000-1000-8000-00805f9b34fb'   # handle: 0x0012 firmware revision
UUID_HARDWARE = '00002a27-0000-1000-8000-00805f9b34fb'   # handle: 0x0014 hardware revision

# Create a structure to store the data in, which includes battery data 
class SensorDataBattery(collections.namedtuple('SensorDataBase', ['temperature', 'humidity', 'battery'])):
    __slots__ = ()

class Lywsd03mmcClient(Lywsd02Client):
    
    # Temperature units specific to LYWSD03MMC devices
    UNITS = {
        b'\x01': 'F',
        b'\x00': 'C'
    }
    UNITS_CODES = {
        'F': b'\x01',
        'C': b'\x00'
    }

    # Call the parent init with a bigger notification timeout
    def __init__(self, mac, notification_timeout=15.0):
        super().__init__(mac, notification_timeout)

    def _process_sensor_data(self, data):
        temperature, humidity, voltage = struct.unpack_from('<hBh', data)
        temperature /= 100
        voltage /= 1000

        # Estimate the battery percentage remaining
        battery = min(int(round((voltage - 2.1),2) * 100), 100) # 3.1 or above --> 100% 2.1 --> 0 %
        self._data = SensorDataBattery(temperature=temperature, humidity=humidity, battery=battery)

    # Battery data comes along with the temperature and humidity data, so just get it from there
    @property
    def battery(self):
        return self.data.battery
    
    def _get_history_data(self):
        # Get the time the device was first run
        self.start_time
        
        # Work out the expected last record we'll be sent from the device.
        # The current hour doesn't appear until the end of the hour, and the time is recorded as 
        # the end of hour time
        expected_end = datetime.now() - timedelta(hours=1)

        self._latest_record = False
        with self.connect():
            self._subscribe(UUID_HISTORY, self._process_history_data)

            while True:
                if not self._peripheral.waitForNotifications(
                        self._notification_timeout):
                    break

                # Find the last date we have data for, and check if it's for the current hour
                if self._latest_record and self._latest_record >= expected_end:
                    break

    def _process_history_data(self, data):
        (idx, ts, max_temp, max_hum, min_temp, min_hum) = struct.unpack_from('<IIhBhB', data)

        # Work out the time of this record by adding the record time to time the device was started
        ts = self.start_time + timedelta(seconds=ts)
        min_temp /= 10
        max_temp /= 10

        self._latest_record = ts
        self._history_data[idx] = [ts, min_temp, min_hum, max_temp, max_hum]
        self.output_history_progress(ts, min_temp, max_temp)

    # Getting history data is very slow, so output progress updates
    enable_history_progress = False
    def output_history_progress(self, ts, min_temp, max_temp):
        if not self.enable_history_progress:
            return
        print("{}: {} to {}".format(ts, min_temp, max_temp))


    # Locally cache the start time of the device.
    # This value won't change, and caching improves the performance getting the history data
    _start_time = False

    # Work out the start time of the device by taking the current time, subtracting the time
    # taken from the device (the run time), and adding the timezone offset.
    @property
    def start_time(self):
        if not self._start_time:
            start_time_delta = self.time[0] - datetime(1970,1,1) - timedelta(hours=self.tz_offset)
            self._start_time = datetime.now() - start_time_delta
        return self._start_time


    # Disable setting the time and timezone. 
    # LYWSD03MMCs don't have visible clocks
    @property
    def time(self):
        return super().time
    @time.setter
    def time(self, dt: datetime):
        return

    @property
    def tz_offset(self): 
        return super().tz_offset
    @tz_offset.setter
    def tz_offset(self, tz_offset: int):
        return

    @property
    def firmware(self):
        with self.connect():
            ch = self._peripheral.getCharacteristics(uuid=UUID_FIRMWARE)[0]
            value = ch.read()
            firmware = ''.join(map(chr, value))
        return firmware

    @property
    def hardware(self):
        with self.connect():
            ch = self._peripheral.getCharacteristics(uuid=UUID_HARDWARE)[0]
            value = ch.read()
            firmware = ''.join(map(chr, value))
        return firmware
