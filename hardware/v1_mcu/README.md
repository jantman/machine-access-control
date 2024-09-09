# machine-access-control hardware/v1_mcu

This directory holds information related to the Version 1 Machine Control Unit (MCU) hardware.

For full details, see the documentation at: https://jantman.github.io/machine-access-control/hardware.html#version-1-hardware

3D models of the components and the 3d printed enclosure are in the ``.scad`` files, for [OpenSCAD](https://openscad.org/). **Note** that the SCAD files are dimensioned in inches; when slicing for 3d printing, they almost certainly need to be converted to metric.

The models are designed with the Z origin as follows:

* For through-hole objects that are glued to the inside of the enclosure sticking out (i.e. the neopixel), the Z origin is at the inner surface of the enclosure.
* For through-hole objects that screw to the enclosure walls (i.e. the button and connector), the Z origin is at the outer surface of the enclosure.
* For objects that mount on standoffs, the Z origin is at the top of the standoff, on the side facing the standoff.
