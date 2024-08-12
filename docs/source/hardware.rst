.. _hardware:

Hardware
========

The "machine control unit" devices use ESP32 microcontrollers; our reference builds use ESP32-DevKitC / ESP32-WROOM-32D boards such as `these from Amazon <https://www.amazon.com/gp/product/B09Z7Q5LKQ/>_. For reasons described in :ref:`the introduction <introduction.mcu-software>` we use `ESPHome <https://esphome.io/>`__ as the software on the ESP32s.

.. _hardware.esphome-configs:

ESPHome Configurations
----------------------

Example ESPHome configurations for various ESPHome versions and various hardware combinations can be found in the `esphome-configs/ directory of the git repo <https://github.com/jantman/machine-access-control/tree/main/esphome-configs>`__ broken down by ESPHome version.

All of the example ESPHome configurations begin with a ``substitutions`` key, which contains a ``machine_name`` substitution. This must be set to the same name as used in the :ref:`configuration.machines-json` config file. If desired, you can override the ``esphome`` ``name`` and ``friendly_name`` values (though this is not recommended).

The ESPHome configurations are based on a `ESPHome secrets.yaml file <https://esphome.io/guides/faq.html#tips-for-using-esphome>`__ for substituting in sensitive values and installation-specific values using the ``!secrets`` substitution operator. The example configurations expect the following secrets to be defined:

ota_password
    A password used for OTA updates from ESPHome.

wifi_ssid
    WiFi network SSID to connect to.

wifi_password
    WiFi network password.

domain_name
    Domain name to use for DNS.
