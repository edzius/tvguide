# TVGuide

CLI TV guide listing tool

## Requirements

* Python (v2/3?)
* Python BeautifulSoup

## Implementation

* TV guide currently grabbed from tvprograma.lt.
* Settings file format:
```
[DEFAULT]
BASE_DIR=
STORAGE_DIR=storage/
ARCHIVE_DIR=archive/
CACHE_DIR=cache/
LOG_DIR=logs/
LOG_LEVEL=debug
LOG_DECAY=7
```
* Logging to file/stdout not implemeted YET.

### Directories

* storage/ -- repository dir for parsed tv shows
* archive/ -- archived failed HTML parse attempts
* cache/ -- HTTP get buffer, HTML temporary storage
* logs/ -- logs should go here

## Usage 
```
usage: guide.py [-h] [-c | -g] [-s SHOW] [-d DATE] [--date-from DATE_FROM]
                [--date-to DATE_TO] [-t TIME] [--time-from TIME_FROM]
                [--time-to TIME_TO]
                [CHANNEL|CATEGORY [CHANNEL|CATEGORY ...]]

TV Guide harvest tool

optional arguments:
  -h, --help      show this help message and exit
  -c, --channels  List available TV guide channels
  -g, --groups    List available TV guide channel categories
```

### Scenarios

|  Action  | Command |  Notes  |
|----------|---------|---------|
| List all available channel names | ./guide.py -c | |
| List all possible channel categories | ./guide.py -g | |
| Show what's on TV now on all available channels | ./guide.py | WARNING: This cation needs to request for each channel. This could make admins unhappy |
| Show current day TV guide for one channel | ./guide.py <channel-name> | |
| Show current day TV guide for few channels | ./guide.py <channel1-name> <channel2-name> | |
| Show current day TV guide for channels category | ./guide.py <channels-category> | |
| Show some channel TV guide for yesteday | ./guide.py -d d-1 <channel-name> | |
| Show some channel TV guide after one week | ./guide.py -d w+1 <channel-name> | |
| Show some channel TV guide for precise day | ./guide.py -d 2016.01.01 <channel-name> | |
| Show some channel show for precise time | ./guide.py -t 09:00 <channel-name> | |
| Show some channel show for previous hour and half | ./guide.py -t h-1,m-1 <channel-name> | |
| Show only shows on some category containting some string pattern | ./guide.py -s <pattern> <channels-category> | |
