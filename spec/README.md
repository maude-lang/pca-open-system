Specification of the PCA unit
=============================

This directory contains the Maude specification of the PCA unit suitable for formal analyses. The objects enumerated in the parent readme are available in the following files:

* [`pca.maude`](pca.maude) specifies the `Pca` class that controls the PCA unit. Its content is almost identical the [corresponding file](../spec/pca.maude) in `open system`.
* [`pca2.maude`](pca2.maude) is a second version of the `Pca` controller that fixes a flaw that let the patient receive an overdose of analgesia under some conditions.
* [`gui.maude`](gui.maude) and [`gui2.maude`](gui2.maude) simulates a graphical user interface where buttons are pressed and value change events occur nondeterministically.
* [`database.maude`](database.maude) implements a simple database in Maude as a list of JSON values.
* [`monitor.maude`](monitor.maude) monitors the event logs to detect overdose during a sliding time window. This file is copied as is in the `open system` version.
* [`open-system.maude`](open-system.maude) declares the constants and some common definitions for all files. However, the values of the constants are defined in [`pca.maude`](pca.maude).
* [`sensor.maude`](sensor.maude) simulates heart rate and temperature sensors whose measurements are obtained nondeterministically.
* [`actuator.maude`](actuator.maude) is a dummy actuator that simply consumes the messages it receives.
* [`time.maude`](time.maude) imitates the external time object in Maude with a purely equational specification.

Other files are used by the previous, like [`json.maude`](json.maude) for representing JSON values, [`configuration.maude`](configuration.maude) for the object-oriented configuration infrastructure (it differs from the predefined `CONFIGURATION` module in that newlines are added between attributes and objects in the configuration), and [`real-time-maude.maude`](real-time-maude.maude) for the [Real-Time Maude](https://olveczky.se/RealTimeMaude) infrastructure. Checks are available in [`checks`](checks) (for `pca.maude`) and [`checks2`](checks2) (for `pca2.maude`).


Requirements
------------

Maude 3.4 or a newer version is required to run the examples. It can be downloaded from https://github.com/SRI-CSL/Maude/releases.



Running the example
-------------------

Running `./maude pca.maude` (or `./maude pca2.maude` for the fixed version) will start a Maude command prompt where to introduce the desired commands. Example properties are available at `checks`. They can be executed with `./maude checks/check-1.maude` and so on.

For example, an invariant of the system should be that the amount administered by the actuator does not exceed a constant `ROUND-AMOUNT` in the whole round. Thanks to an attribute `amount` in the `Actuator` class, this invariant can be [refuted through bounded search](https://maude.lcc.uma.es/maude-manual/maude-manualch11.html):
```
search { <PCA> create(Pca, oid(0), oid(1)), 0 }
  =>∗ { < A : Actuator | amount : F > Conf, Tm }
  such that F > float(ROUND−AMOUNT) .
```

