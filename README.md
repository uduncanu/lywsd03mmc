# LYWSD03MMC 

A Python library for working with Xiaomi Mijia LYWSD03MMC bluetooth temperature and humidity sensors.

Updating the firmware on the devices is *not* required.

For battery savings or additional features the firmware can be upgraded to:
[ATC1441 - ATC MiThermometer](https://github.com/atc1441/ATC_MiThermometer)
or the fork
[PVVX - ATC MiThermometer](https://github.com/pvvx/ATC_MiThermometer).
For PVVX version please change the Bluetooth Advertising Format to "ATC1441".

After flashing, ```Lywsd03mmcClient``` can't be used. ```AtcMiThermometerClient``` must be used as client.

This package is built on top of the lywsd02 package, which may include additional useful information.

## Installation

This relies on bluepy installed via python pip, which itself needs libglib2 to install:
```
sudo apt-get install python3-pip libglib2.0-dev
```

The LYWSD03MMC package can then be installed from [PyPi](https://pypi.org/project/lywsd03mmc/), using the following command:

```
pip3 install lywsd03mmc
```

### Installation forked package

```
git clone https://github.com/0xD0M1M0/lywsd03mmc.git
cd lywsd03mmc
pip3 install .
```

## Finding the MAC address of the devices
From the Xiaomi Home app:
1. Go into the details of the device
2. Click on the three dots to get into the settings
3. Click "About" (near the top of the list)
4. And make a note of the MAC address shown.

It is also possible to find the addresses of all devices by running `sudo hcitool lescan` and looking for devices labelled "LYWSD03MMC"

## Tools

Two helper commands are distributed here:

### `lywsd03mmc` - Current data

This shows the current temperature, humidity and battery level of the device.

Example usage: 
`lywsd03mmc -m A4:C1:38:12:34:56`

### `lywsd03mmc2csv` - Export history

This exports the history to a CSV file, containing the maximum and minimum temperature and humidity for each hour there is data for.

This can be very slow, and may take up to about 10 minutes to download all the data from the device.

Example usage: 
`lywsd03mmc2csv A4:C1:38:12:34:56 --output data.csv`

## Library Usage

The library interface closely matches the [LYWSD02](https://github.com/h4/lywsd02) package, with the following changes:

* Setting the time has been removed
* Battery data is available from the main data export
* An extra option has been included to estimate the time the device was started
* History data times are calculated based on the start time of the device

### Connecting and retrieving information

Here's an example of getting the basic information out of the device:

```
from lywsd03mmc import Lywsd03mmcClient
client = Lywsd03mmcClient("A4:C1:38:12:34:56")

data = client.data
print('Temperature: ' + str(data.temperature))
print('Humidity: ' + str(data.humidity))
print('Battery: ' + str(data.battery))
print('Display units: ' + client.units)
```

### History

Times given in the history output are for the end of the hour in which data was recorded.

Downloading the history data can take a significant amount of time (up to about 10 minutes).

A property is available on the client to output data from each record retrieved, to allow you to see the progress:

```
# Create the client
from lywsd03mmc import Lywsd03mmcClient
client = Lywsd03mmcClient("A4:C1:38:12:34:56")

# Enable history output
client.enable_history_progress = True

# Retrieve the history data
history = client.history_data
```

# ATC_MiThermometer

If you use Custom firmware for the Xiaomi Thermometer LYWSD03MMC and Telink Flasher via USB to Serial converter you can get device informations without connecting.
[ATC_MiThermometer](https://github.com/atc1441/ATC_MiThermometer)

After flashing, ```Lywsd03mmcClient``` can't be used. ```AtcMiThermometerClient``` must be used as client.

### Retrieving information without connecting

Here's an example of getting the basic information out of the device:

```
from lywsd03mmc import AtcMiThermometerClient
client = AtcMiThermometerClient()

client.get_datas()

for thermometer in client.thermometers:
    print('----\n', thermometer) # print all data 
```

Display with on retry (3 retries by default):

```
Discovered device a4:c1:38:xx:xx:xx
Discovered device a4:c1:38:yy:yy:yy
Device disconnected
Proceed...
Discovered device a4:c1:38:xx:xx:xx
Discovered device a4:c1:38:yy:yy:yy
Received new data from a4:c1:38:xx:xx:xx
----
 mac:   A4:C1:38:xx:xx:xx - ATC_xxxxxx
temp:   22.8 °C
hum:    37 %
batt:   86 %
volts:  2.98 V
rssi:   -54 dB
skip:   False
----
 mac:   A4:C1:38:yy:yy:yy - ATC_yyyyyy
temp:   21.7 °C
hum:    42 %
batt:   88 %
volts:  2.996 V
rssi:   -71 dB
skip:   False
```

### Retrieving information without connecting - command line

```
lywsd03mmc -s
```

## Troubleshooting

AtcMiThermometerClient() standard parameters:
```
scan_for=15.0
retry=3
debug=False
```

Example
```
AtcMiThermometerClient(scan_for=30.0, debug=True)
```

### Failed to connect to peripheral

Check you are connecting to the correct MAC address, and are in range of the device.

If those are correct, this can normally be fixed by retrying the connection.
