Programming Open Distributed Systems in Maude
=============================================

This repository contains a [Maude](https://maude.cs.illinois.edu) specification and implementation of a [*Patient Controlled Analgesia*](https://en.wikipedia.org/wiki/Patient-controlled_analgesia) (PCA) unit, as a case study for the specification of open distributed systems in Maude. PCA is a widely used method for relieving pain efficiently and safely in hospitalized patients.


The content of this repository is organized in three directories:

* [`spec`](spec) is a self-contained Maude specification of the PCA unit suitable for formal verification. Some safety checks are executed using Maude bounded search. These checks revealed some flaw that let the patient receive an overdose of analgesia, which is fixed in a second version (by replacing the file [`pca.maude`](spec/pca.maude) with [`pca2.maude`](spec/pca2.maude)).
* [`impl`](impl) replaces the external-world components (sensors, actuators, databases, GUI, etc.) of the specification in [`spec`](spec) with Maude external objects connecting to external hardware or software outside Maude.

Instructions on how to run these examples can be found in their corresponding directories. [Here](http) is a video showing the behavior of the open system implementation.


Open system components
----------------------

The PCA unit is an [object-oriented system](https://maude.lcc.uma.es/maude-manual/maude-manualch6.html) that results from the interactions via asynchronous messages of several objects belonging to different classes, each implemented in a separate file:

* `Pca` ([`pca.maude`](spec/pca.maude) and [`pca2.maude`](spec/pca2.maude)) is the class of the main object of the PCA specification. It controls and maintains the state of the system, and interacts with all other components.
* `Gui` ([`gui.maude`](spec/gui.maude)) is in charge of the interaction with the users (patient or clinician) through a graphical user interface.
* `Database` ([`database.maude`](spec/database.maude) or [`mongodb.maude`](impl/mongobd.maude)) maintains the logs of the system events for traceability and runtime monitoring using a database.
* `Monitor` ([`monitor.maude`](spec/monitor.maude)) monitors system events through checks on the database to detect undesired behavior and notify the `Pca` object. In particular, the absence of overdose is checked on a sliding time window.
* `Sensor` ([`sensor.maude`](spec/sensor.maude)) provides on demand measurements of the vitals of the patient (heart rate and temperature).
* `Actuator` ([`actuator.maude`](spec/actuator.maude)) controls the PCA pump that administers analgesia to the patient.

Following the Maude convention, `Pca` will create most objects dynamically by sending a message to a manager object, `guiManager`, `databaseManager`, `monitorManager`, `sensorManager`, or `actuatorManager`. These objects will be fully implemented in Maude in the specification, while they will be or interact with external objects in the implementation. However, the `Pca` class (as well as the `Monitor` class) is shared between both variants.

Constants and common declarations for all these objects are kept in [`open-system.maude`](spec/open-system.maude). Other files, like [`configuration.maude`](configuration.maude), [`json.maude`](json.maude), or [`real-time.maude`](real-time.maude), provide the equational infrastructure for the specification.
