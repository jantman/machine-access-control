.. _hardware:

Hardware
========

The "machine control unit" (MCU) devices use ESP32 microcontrollers; our reference builds use ESP32-DevKitC / ESP32-WROOM-32D boards such as `these from Amazon <https://www.amazon.com/gp/product/B09Z7Q5LKQ/>`__. For reasons described in :ref:`the introduction <introduction.mcu-software>` we use `ESPHome <https://esphome.io/>`__ as the software on the ESP32s.

.. _hardware.v1:

Version 1 Hardware
------------------

This describes the initial Version 1 MCU hardware, essentially a prototype assembled from off-the-shelf components and fitted in a 3D printed enclosure.

.. _hardware.v1.components:

Components
++++++++++

The following table lists the components required for the Version 1 MCU hardware. Costs are approximate as of November 2025 and may vary, and do not include fasteners, hookup wire, and incidental parts.

.. list-table::
   :header-rows: 1
   :widths: 40 10 30 10

   * - Item / Description
     - Qty
     - Link
     - Cost (USD November 2025)
   * - 3D Printed Enclosure and Laser Cut Card Holder
     - 1
     - :ref:`See Enclosure, below <hardware.v1.enclosure>`
     - $9.90
   * - ESP32 38-pin wide dev board [1]_
     - 1
     - `Amazon <https://www.amazon.com/gp/product/B09Z7Q5LKQ/>`__
     - $5.66
   * - Screw terminal breakout board for ESP32
     - 1
     - `Amazon <https://www.amazon.com/gp/product/B0C3QM5ZHP/>`__
     - $8.13
   * - 16x2 backlit character LCD display with I2C backpack (PCF8574T)
     - 1
     - `Amazon <https://www.amazon.com/gp/product/B07T8ZG5D1/>`__
     - $3.99
   * - 4-channel bi-directional 3.3v/5v level converter
     - 1
     - `Amazon <https://www.amazon.com/gp/product/B07F7W91LC/>`__
     - $0.75
   * - Clockless 12mm WS2812-type addressable RGB LED [2]_
     - 1
     - `Amazon <https://www.amazon.com/gp/product/B01AG923GI/>`__
     - $0.32
   * - 3.3v controlled optoisolated relay module (up to 10A) [3]_
     - 1
     - `Amazon <https://www.amazon.com/gp/product/B09SZ71K4L/>`__
     - $1.29
   * - 16mm red LED-backlit momentary pushbutton with shield/cover [4]_
     - 1
     - `Skycraft Surplus - button <https://skycraftsurplus.com/products/spdt-momentary-pushbutton-switch-12v-red.html>`__ and `Amazon cover <https://www.amazon.com/ITROLLE-Waterproof-Anti-Touch-Transparent-Protective/dp/B0F997TQCW/>`__
     - $5.49
   * - Wiegand protocol 3.3-5VDC RFID reader with card present output [5]_
     - 1
     - `AliExpress <https://www.aliexpress.us/item/2255800841398634.html>`__
     - $6.26
   * - M12 8-pin A-code male connector, prewired, for control box [6]_
     - 1
     - `Amazon <https://www.amazon.com/dp/B0DWL6R1N9/>`__
     - $9.80
   * - M12 8-pin A-code female connector to blunt end wire, 1-3m length as needed [6]_
     - 1
     - `Amazon <https://www.amazon.com/dp/B0DNX6NJBC/>`__
     - ~$15.49 (2m)
   * - **Control Box Sub-Total**
     -
     -
     - **$67.08**
   * - *optional* 5VDC 2.5A Power Supply, if needed [7]_
     -
     - `Amazon <https://www.amazon.com/dp/B0FPFPWFLZ/>`__
     - $12.90
   * - *optional* 30A relay for high current machine control [8]_
     -
     - `Amazon <https://www.amazon.com/dp/B07TWH7DZ1/>`__
     - $9.79
   * - *optional* 25A solid state relay for high current machine control [8]_
     -
     - `Amazon <https://www.amazon.com/dp/B0D97D4PB1/>`__
     - $7.49
   * - *optional* 40A 240V contactor 2-pole contactor for 240V machine control [8]_
     -
     - `Amazon <https://www.amazon.com/dp/B08H8X41P6/>`__
     - $11.99
   * - *optional* Junction box for housing high current relays/contactors - Carlon E987R 6x6x4" [9]_
     -
     - `Home Depot <https://www.homedepot.com/p/Carlon-6-in-x-6-in-x-4-in-Gray-Electrical-PVC-Junction-Box-E987R-3-HD-E987R-3-HD/100404096>`__
     - $19.26
   * - *optional* Cord lock for plug-in junction box [9]_
     -
     - `Amazon <https://www.amazon.com/dp/B0DD52D1GG/>`__ (large)
     - $14.98

**Component Notes:**

.. [1] **ESP32 Dev Board:** Such as the Dorhea ESP32-DevKitC WEOOM-32U or similar ESP32-WROOM-32D based boards.

.. [2] **Addressable RGB LED:** I'm currently using LEDs clipped from a string of waterproof 5V LEDs just because I had them on hand. Any WS2812-compatible LED should work.

.. [3] **Relay Module:** Must be able to switch the required current for your application (up to 10A with the linked module).

.. [4] **Pushbutton:** I specifically used the MPJA 34155 SW pushbutton and MPJA 34167 SW transparent shield. The button is now available as `Skycraft Surplus SKU 025726 <https://skycraftsurplus.com/products/spdt-momentary-pushbutton-switch-12v-red.html>`__ and is also available under its generic designation of `16Y-11D` e.g. `from Amazon <https://www.amazon.com/16Y-11D-Button-self-resetting-Switch-24v220v/dp/B0F4QNYRZC/>`__. The protective cover is generic for any 16mm pushbutton and can be found `on Amazon <https://www.amazon.com/ITROLLE-Waterproof-Anti-Touch-Transparent-Protective/dp/B0F997TQCW/>`__. Any standard SPST or SPDT momentary pushbutton will work **as long as** its LED can be driven directly by 3.3VDC.

.. [5] **RFID Reader:** The linked item ships directly from the manufacturer in China. This specific unit is fairly rare in that it can work directly on 3.3VDC with 3.3V communication, so it doesn't require an additional two channels of level converter. Also, it has a ``CST`` line that's pulled high when a RFID tag is within range of the reader.

.. [6] **M12 Connectors:** M12 8-pin A-code connectors are widely available as they're used in industrial automation and sensor applications. They are available in various form factors; connectors with screw terminals are probably the least expensive option, but prewired connectors are easier to work with and the molded boots of prewired cables provide strain relief and protection. I originally specified GX16-8 connectors for this purpose, but switched to M12 connectors for better availability especially of prewired cables.

.. [7] **Power Supply:** A regulated 5VDC power supply is necessary to power the MCU and peripherals. Many machines that already have low voltage DC control systems may have an existing 5VDC supply that can be used; otherwise, a new power supply will be needed. Current draw will depend on specific components used, relay coil sizes, etc. Any suitable 5VDC power supply can be used.

.. [8] **High Current Relays/Contactors:** The control box itself is designed to switch low current control signals (the M12 connector is rated for 2A per contact). If controlling high current loads such as motors, an external relay or contactor must be used. The specific choice will depend on the load requirements of the machine being controlled. Ensure that any relay or contactor used is rated for the voltage and current of the load, and is suitably mounted in a safe location or enclosure.

.. [9] **Junction Box and Cord Lock:** For machines that just plug in to an outlet and are too small to mount the control components internally, a junction box can be used to house high current relays/contactors and a 5VDC power supply. The Carlon E987R 6x6x4" junction box is a suitable option. A cord lock can be used to lock the machine power cord to the junction box output cord, so that the access control system cannot be easily bypassed by unplugging the machine.

.. _hardware.v1.wiring:

Wiring
++++++

This is intended to work with `esphome-configs/2024.6.4/no-current-input.yaml </esphome-configs/2024.6.4/no-current-input.yaml>`__.

.. image:: ../../hardware/v1_mcu/Hardware_v1.png
   :alt: Wiring diagram of system

* RFID Reader - Note that if using the same model that I did, you must add a solder blob on ``S2`` for Wiegand output.

  * ``CST`` to ``GPIO18``
  * ``Gnd`` to ground
  * ``TX/D0`` to ``GPIO16``
  * ``RX/D1`` to ``GPIO4``
  * ``3.3-5V`` to 3v3

* Level Converter

  * Gnd and Gnd to ground
  * LV to ESP32 ``3v3``
  * HV to ESP32 ``5v``
  * 2 - ``LV2`` to ``GPIO22``; ``HV2`` to LCD ``SDA``
  * 3 - ``LV3`` to ``GPIO23``; ``HV3`` to LCD ``SCL``
  * 4 - ``LV4`` to ``GPIO27``; ``HV4`` to Neopixel ``D1``

* Pushbutton

  * LED ``-`` to ``Gnd``
  * LED ``+`` to ``GPIO5``
  * Switch ``NC`` to ``Gnd``
  * Switch ``Com`` to ``GPIO32``

* Neopixel

  * ``5v`` to ``5v`` (often red)
  * ``Gnd`` to ``Gnd`` (often blue)
  * ``D1`` to Level Converter ``HV4`` to ``GPIO27`` (often white)

* LCD Display

  * ``Gnd`` to ``Gnd``
  * ``VCC`` to ``5v``
  * ``SDA`` to Level Converter ``HV2`` to ``GPIO22``
  * ``SCL`` to Level Converter ``HV3`` to ``GPIO23``

* Optoisolated Relay - Output is N.O.

  * ``Gnd`` to ``Gnd``
  * ``In`` to ``GPIO33``
  * ``VCC`` to ``3v3``

* M12 8-pin A-code connector for power, control, and additional inputs. The MCU should have the female socket which has visible pins in it, and the wire going to it should have the male plug which has a housing that accepts those pins. Note that M12 A-code connectors have an alignment notch, a ring of 7 contacts, and one central contact. On the male connector (the one with pins), contacts are numbered 1-7 clockwise from the alignment notch with 8 in the center. There is also an industry-standard color code for the wires, shown below.

  * ``1`` (white) to +5VDC power in
  * ``2`` (brown) to power supply ground
  * ``3`` (green) to relay input / common
  * ``4`` (yellow) to relay output Normally Open
  * ``5`` (grey) to ESP32 ``GPIO12`` for tamper switch (not yet implemented in software)
  * ``6`` (purple) to ESP32 ``GPIO14`` for future use
  * ``7`` (blue) reserved for future ammeter / current clamp use (not implemented in V1)
  * ``8`` (red) reserved for future ammeter / current clamp use (not implemented in V1)

.. _hardware.v1.enclosure:

Enclosure
+++++++++

There is an example enclosure for the unit, 3D printed with a few laser cut parts, in `the hardware/v1_mcu directory of the GitHub repo <https://github.com/jantman/machine-access-control/tree/main/hardware/v1_mcu>`__. See that directory for information on fabrication and assembly.

.. _hardware.esphome-configs:

ESPHome Configurations
----------------------

Example ESPHome configurations for various ESPHome versions and various hardware combinations can be found in the `esphome-configs/ directory of the git repo <https://github.com/jantman/machine-access-control/tree/main/esphome-configs>`__ broken down by ESPHome version.

All of the example ESPHome configurations begin with a ``substitutions`` key, which contains a ``machine_name`` substitution. This must be set to the same name as used in the :ref:`configuration.machines-json` config file. If desired, you can override the ``esphome`` ``name`` and ``friendly_name`` values (though this is not recommended).

The ESPHome configurations are based on a `ESPHome secrets.yaml file <https://esphome.io/guides/faq.html#tips-for-using-esphome>`__ for substituting in sensitive values and installation-specific values using the ``!secrets`` substitution operator. The example configurations expect the following secrets to be defined:

api_encryption_key
    this is needed for the ESPHome web UI functionality, like wirelessly streaming logs. See ESPHome docs.

ota_password
    A password used for OTA updates from ESPHome. See ESPHome docs.

wifi_ssid
    WiFi network SSID to connect to. See ESPHome docs.

wifi_password
    WiFi network password. See ESPHome docs.

domain_name
    Domain name to use for DNS. See ESPHome docs.

mac_url
    the full URL to the /api/machine/update endpoint of the machine-access-control server
