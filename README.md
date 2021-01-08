# WISEBox Logfile Server

A simple web.py application for viewing
[WISEBox Logger](https://github.com/Horizon-WISEBox/wisebox-logger) logfiles.

## Getting Started

### Dependencies

Requires an HTTP server configured for [web.py](https://webpy.org/). Any version
of Python 3.5 and up should be compatible. All of the Python dependencies can
be found in the [Pipfile](Pipfile). Usage of
[Pipenv](https://pypi.org/project/pipenv/) is recommended for setting up the
Python environment and installing dependencies.

### Installing

* Clone the repository
* Change the Python version in the Pipfile to your preferred version
* Install the dependencies with Pipenv
* See the [web.py](https://webpy.org/) documentation for installing with
  your preferred HTTP server

### Executing program

```
usage: server [-h] [--config CONFIG] [--version] interface log.dir

Simple server for display of WISEBox log files

positional arguments:
  interface             capture interface, e.g. wlan0
  log.dir               directory log files are stored in

optional arguments:
  -h, --help            show this help message and exit
  ARG:   --config CONFIG
  --version             show program's version number and exit
```

## Version History

* v1.1.1
  * Updated Favicon
  * See [commit change](https://github.com/Horizon-WISEBox/wisebox-logfile-server/commit/363768b)
* v1.1.0
  * WISEParks renamed to WISEBox
  * See [commit change](https://github.com/Horizon-WISEBox/wisebox-logfile-server/commit/986c6c4)
* v1.0.1
  * Configuration can be stored in a config file
  * See [commit change](https://github.com/Horizon-WISEBox/wisebox-logfile-server/commit/e4e58eb)
* v1.0.0
  * Initial Release
  * Added logfile versioning
  * See [commit change](https://github.com/Horizon-WISEBox/wisebox-logfile-server/commit/97181ec)

## License

This project is licensed under the GNU Affero General Public License, Version 3
\- see the [LICENSE](LICENSE) file for details
