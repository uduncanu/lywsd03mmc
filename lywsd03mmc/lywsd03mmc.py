from lywsd02 import Lywsd02Client
import struct
import collections
from datetime import datetime, timedelta

import re
from bluepy.btle import Scanner, DefaultDelegate
import bluepy

UUID_HISTORY = 'EBE0CCBC-7A0A-4B0C-8A1A-6FF2997DA3A6'  # Last idx 152          READ NOTIFY
UUID_FIRMWARE = '00002a26-0000-1000-8000-00805f9b34fb'   # handle: 0x0012 firmware revision
UUID_HARDWARE = '00002a27-0000-1000-8000-00805f9b34fb'   # handle: 0x0014 hardware revision


def valid_miflora_mac(mac):
    refilter = r"(A4:C1:38)|(A4:C1:38):[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}"
    pat = re.compile(refilter)
    """Check for valid mac adresses."""
    if not pat.match(mac.upper()):
        return False
    return True


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
        battery = min(int(round((voltage - 2.1), 2) * 100), 100)  # 3.1 or above --> 100% 2.1 --> 0 %
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
            start_time_delta = self.time[0] - datetime(1970, 1, 1) - timedelta(hours=self.tz_offset)
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


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if valid_miflora_mac(dev.addr) is False:
            return
        if isNewDev:
            print("Discovered device", dev.addr)
        elif isNewData:
            print("Received new data from", dev.addr)


class AtcMiThermometerDevice():

    def _process_sensor_data(self, data):
        datas = []
        for i in range(0, 15):
            datas.append(data[i*2:2+i*2])
        self._mac = ':'.join(datas[2:8]).upper()
        self._temp = int('0x' + ''.join(datas[8:10]), base=16)/10
        self._hum = int('0x' + ''.join(datas[10:11]), base=16)
        self._battery = int('0x' + ''.join(datas[11:12]), base=16)
        self._volts = int('0x' + ''.join(datas[12:14]), base=16)/1000
        self._skip = False
        if datas[14] == '':
            print('skip')
            self._skip = True
        self._rssi = None

    def __init__(self, data):
        self._process_sensor_data(data)

    def __str__(self):
        result = '{}: \t{}'.format('mac', self._mac)
        result += '\n{}: \t{} °C'.format('temp', self._temp)
        result += '\n{}: \t{} %'.format('hum', self._hum)
        result += '\n{}: \t{} %'.format('batt', self._battery)
        result += '\n{}: \t{} V'.format('volts', self._volts)
        result += '\n{}: \t{} dB'.format('rssi', self._rssi)
        result += '\n{}: \t{}'.format('skip', self._skip)
        return result

    @property
    def mac(self):
        return self._mac

    @property
    def temp(self):
        return self._temp

    @property
    def hum(self):
        return self._hum

    @property
    def battery(self):
        return self._battery

    @property
    def volts(self):
        return self._volts

    @property
    def skip(self):
        return self._skip

    @property
    def rssi(self):
        return self._rssi

    @rssi.setter
    def rssi(self, value):
        self._rssi = value
        return


class AtcMiThermometerClient():

    def __init__(self, scan_for=15.0, retry=3):
        self._scan_for = scan_for
        self._retry = retry
        self._devices = []
        self._thermometers = []

    def get_datas(self):
        devices = []
        scanner = Scanner().withDelegate(ScanDelegate())
        try:
            devices = scanner.scan(self._scan_for)
        except (bluepy.btle.BTLEManagementError,
                bluepy.btle.BTLEDisconnectError) as err:
            print(err)
            print('Proceed...')
            # exit()
        self._devices = devices
        self._process_datas()

    def _process_datas(self):
        for dev in self._devices:
            if valid_miflora_mac(dev.addr) is False:
                continue
            strf = "Device {} ({}), RSSI={} dB"
            # print(strf.format(dev.addr, dev.addrType, dev.rssi))
            local_name = ''
            value = ''
            for (adtype, desc, val) in dev.getScanData():
                print("  %s = %s" % (desc, val))
                if desc == "16b Service Data":
                    value = val
                elif desc == "Complete Local Name":
                    local_name = val

            # print('{} : {}'.format(local_name, value))
            if (local_name == '') or (value == ''):
                continue
            # print("  %s = %s" % (desc, value))

            thermometer = AtcMiThermometerDevice(value)
            thermometer.rssi = dev.rssi
            print(thermometer)
            self._thermometers.append(thermometer)

    @property
    def scan_for(self):
        return self._scan_for

    @scan_for.setter
    def scan_for(self, value):
        self._scan_for = value
        return

    @property
    def retry(self):
        return self._retry

    @retry.setter
    def retry(self, value):
        self._retry = value
        return

    @property
    def thermometers(self):
        return self._thermometers


def main():
    atc = AtcMiThermometerClient()
    atc.get_datas()


if __name__ == '__main__':
    main()