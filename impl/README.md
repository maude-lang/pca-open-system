Implementation of the PCA unit
==============================

This directory contains the Maude implementation of the PCA unit connected to external objects. The following files are included:

* [`pca.maude`](pca.maude) specifies the `Pca` class that controls the PCA unit. It is almost a copy of the [corresponding file](../spec/pca.maude) in the `spec` directory.
* [`pca2.maude`](pca2.maude) fixes a problem in the specification of [`pca.maude`](pca.maude) revealed by its formal verification.
* [`main.py`](main.py) is the entry point of the PCA example. It simply connects the special operator for the GUI external object, runs the sensor and actuators servers, and execute the `erewrite` of the Maude implementation in `pca.maude`.
* [`gui.maude`](gui.maude) is the interface of the GUI implemented as an external object in Python using [special operators](https://fadoss.github.io/maude-bindings/#custom-special-operators).
* [`mongodb.maude`](mongodb.maude) implements the `Database` class by connecting to a [MongoDB](https://www.mongodb.com) server. The official command-line interface `mongosh` is run as an [external process from Maude](https://maude.lcc.uma.es/maude-manual/maude-manualch9.html) for this purpose.
* [`monitor.maude`](monitor.maude) is the same [`monitor.maude`](../spec/monitor.maude) included in the specification. However, its queries are handled in this case by the MongoDB database.
* [`open-system.maude`](open-system.maude) declares constants and provides common definitions.
* [`sensor.maude`](sensor.maude) implements `Sensor` objects that communicate with external sensors by [TCP sockets](https://maude.lcc.uma.es/maude-manual/maude-manualch9.html).
* [`sensor.c`](sensor.c) is a simulated sensor server, implemented in C. The syntax of the command is `sensor-bin <port> <data>`, where `data` is the path of a file with a collection of floating-point values, each in one line. A TCP local server is started on port `port` and answers with a line of that file every time an `m` character is received.
* [`data`](data) (directory) contains some real time series of [pulse](https://web.archive.org/web/20221210020709/http://ecg.mit.edu/time-series/) (`p*.txt`) and [temperature](https://doi.org/10.13026/jpan-6n92) (`s*.txt`) measurements from public datasets.
* [`actuator.maude`](actuator.maude) implements `Actuator` objects that communicate with a simulated PCA pump by writing on its *device* file with [file I/O external objects](https://maude.lcc.uma.es/maude-manual/maude-manualch9.html).
* [`actuator.c`](actuator.c) is a simulated actuator, implemented in C. The syntax of the command is `actuator-bin [<pipe-path>]` where `pipe-path` is the path of the named pipe that will be used to communicate with the simulated actuator (by default, `actuator.pipe`).
* [`Makefile`](Makefile) can be used to automate the build of those C programs.


Requirements
------------

* A POSIX-compliant system like Linux or macOS.
* The [`maude` Python package](https://github.com/fadoss/maude-bindings), which can be installed with `pip install maude`.
* A C compiler to build and run the actuator and sensor binaries.
* MongoDB and its command-line client `mongosh`. It can be installed as explained [here](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/). Another possibility is using the official [`mongo` Docker image](https://hub.docker.com/_/mongo).

The `make` utility can be used to build the actuator and sensor binaries at once by running `make` on this directory. Otherwise, these programs can be build manually with the simple commands that appear in the `Makefile`.


Running the example
-------------------

The example is executed with the following commands:

1. Run `make` to build the actuator and sensor binaries (if not already done).
2. Start a MongoDB instance in the local or an external machine. Its address and port must be written to the `DATABASE-URI` constant in the `pca.maude` file with the format `mongosh://<address>:<port>/pcadb`. For example, this can be done
   * in macOS using brew, with the command `brew services start mongodb-community@7.0`, while `brew services stop mongodb-community@7.0` is used to stop the database server.
   * using Docker, with the command `docker run -tp 27017:27017 --rm mongo`
3. Run `python main.py`. This run the first version of the specification (`pca.maude`), `-2` should be passed to run the second version (`pca2.maude`).

Two windows will appear and messages will be printed on the terminal.
