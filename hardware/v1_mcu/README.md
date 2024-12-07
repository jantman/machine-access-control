# machine-access-control hardware/v1_mcu

This directory holds information related to the Version 1 Machine Control Unit (MCU) hardware, mainly the designs for the 3D printed enclosure and laser-cut acrylic RFID card/fob holder, as well as the wiring diagram (such as it is). Full details of the electronic components and wiring can be seen in the documentation at https://jantman.github.io/machine-access-control/hardware.html#version-1-hardware

## RFID Card / Fob Holder

The [rfid_holder/](rfid_holder/) subdirectory contains models for the laser-cut acrylic pocket mounted to the front of the enclosure to hold the RFID card/fob. See there for details.

## Enclosure

The enclosure is designed to be 3D printed; prototypes were printed on a (highly modified) Creality CR10S with PLA+ filament. 3D models of the components and the 3d printed enclosure are in the ``.scad`` files, for [OpenSCAD](https://openscad.org/). **Note** that the SCAD files have original dimensions in a mix of inch and metric depending on the original source; they models are dimensioned in mm but have an ``inch()`` function in heavy use to convert from imperial dimensions. I've tried my best to parameterize the models well, but note that cut-outs, screw holes, and standoff bores can have quite close tolerances and may need to be adjusted for your specific printer.

### Printing Notes

I'm slicing with Cura. If the mounting nut catches are enabled, be sure to enable supports and also set your wall line width, initial layer height, and layer height in [config.scad](config.scad).

The connector used for power and control is a GX16-8 style round connector as specified in the [documentation](https://jantman.github.io/machine-access-control/hardware.html#version-1-hardware) and mounts using a single round through-hole of at least 0.615 inches (nominally 5/8" or 16mm). Due to the wide variety of mounting options, this hole is left out of the model and can be drilled after printing in whichever location is most suitable for the final mounting.

### Required Hardware

* M3x4x5mm or M3x6x5mm threaded inserts, qty 4, to secure lid to base.
* M3x10 socket head cap screws, qty 4, to secure lid to base.
* M4x16 flat head or button head screws and M4 nylon lock nuts, qty 6 each, to secure RFID pocket to front of enclosure.
* M2.5x6 flat head screws, qty 10
  * 2 each to mount RFID reader to standoffs.
  * 4 each to mount ESP32 carrier board to standoffs.
  * 4 each to mount relay board to standoffs.
* M2.5x4 or M2.5x5 flat head screws, 4 each, to mount LCD board to standoffs.
* If using mounting holes, M4 hardware as described below.
* Adhesive or hot glue, to mount the Neopixel status LED and (if needed) seal around the LCD display.

### Mounting

The enclosure has (optionally; on by default) nut catches on the sides and back for mounting. These are designed with clearance for an M4 screw and to capture an M4 hex nut or hex head bolt; you can either put nuts on the inside and use a screw from the outside, or put a hex head bolt in the internal nut catch and secure in place with a few drops of CA glue. All of these mounting holes are printed with two layers of filament (0.4 to 0.8 mm using my slicing settings) over the outside of the holes, to seal whichever ones are not used. These can be drilled/punched/cut out to reveal whichever mounting holes are most useful.

The back of the enclosure has four screw catches spaced for M4 screws in a 100x100mm VESA mounting standard. Each side of the enclosure has a pair of M4 screw catches spaced 1.912" on center, designed to match the AMPS hole pattern used on RAM and similar flexible mounts.

### Models

See the hardware docs for details.

* [config.scad](config.scad) - General configuration for the enclosure.
* [esp32.scad](esp32.scad) - ESP32 38-pin wide dev board on screw terminal carrier
* [gx16-8.scad](gx16-8.scad) - GX16-8 locking connector
* [hole_test.scad](hole_test.scad) - 1/8" thick panel with holes for all components, to test hole sizes and patterns.
* [lcd.scad](lcd.scad) - 16x2 character LCD with I2C backpack
* [neopixel.scad](neopixel.scad) - Single addressable RGB LED
* [oops_button.scad](oops_button.scad) - 16mm backlit red button with cover
* [relay.scad](relay.scad) - 3.3v optoisolated relay board
* [rfid.scad](rfid.scad) - RFID reader

### Enclosure Notes

The enclosure itself is built using v3 of [Willem Aandewiel](https://willem.aandewiel.nl/)'s excellent [YAPP_Box](https://github.com/mrWheel/YAPP_Box) OpenSCAD enclosure generator, with a [patch](https://github.com/jantman/machine-access-control/commit/c860e23d8b0bcd43c924b47d14e1e0748aece98f) for custom cutouts.
