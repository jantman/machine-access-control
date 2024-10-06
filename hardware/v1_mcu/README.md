# machine-access-control hardware/v1_mcu

This directory holds information related to the Version 1 Machine Control Unit (MCU) hardware, mainly the designs for the 3D printed enclosure and laser-cut acrylic RFID card/fob holder, as well as the wiring diagram (such as it is). Full details of the electronic components and wiring can be seen in the documentation at https://jantman.github.io/machine-access-control/hardware.html#version-1-hardware

## RFID Card / Fob Holder

The [rfid_holder/](rfid_holder/) subdirectory contains models for the laser-cut acrylic pocket mounted to the front of the enclosure to hold the RFID card/fob. See there for details.

## Enclosure

The enclosure is designed to be 3D printed; prototypes were printed on a (highly modified) Creality CR10S with PLA+ filament. 3D models of the components and the 3d printed enclosure are in the ``.scad`` files, for [OpenSCAD](https://openscad.org/). **Note** that the SCAD files have original dimensions in a mix of inch and metric depending on the original source; they models are dimensioned in mm but have an ``inch()`` function in heavy use to convert from imperial dimensions. I've tried my best to parameterize the models well, but note that cut-outs, screw holes, and standoff bores can have quite close tolerances and may need to be adjusted for your specific printer.

### Required Hardware

* 4 each, M3 x ??? flat head screws and threaded inserts, to secure lid to base.
* 6 each, M4 x ??? screws and nylon lock nuts, to secure RFID pocket to front of enclosure. Choose screw head type as desired.
* 2 each, M3 x ??? screws to mount RFID reader to standoffs.
* 4 each, M3 x ??? screws to mount LCD board to standoffs.
* Adhesive or hot glue, to mount the Neopixel status LED and (if needed) seal around the LCD display.

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
