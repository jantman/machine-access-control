# Hardware Test Procedure

This document describes the standalone hardware test configuration for the Machine Access Control system.

## Purpose

The `hardware-test.yaml` ESPHome configuration provides a **standalone, non-networked** test environment for validating all hardware components without requiring the MAC server or network connectivity. All diagnostics are performed locally on the device.

## Hardware Components Tested

- **16x2 LCD Display** (I2C PCF8574 on GPIO22/23)
- **Wiegand RFID Reader** (D0: GPIO16, D1: GPIO4)
- **Card Present Sensor** (GPIO18)
- **Oops Button** (GPIO32 input with pullup)
- **Oops LED** (GPIO5 output)
- **Relay Output** (GPIO33)
- **NeoPixel Status LED** (GPIO27 WS2812)

## Flashing the Test Config

```bash
# From the esphome-configs/2024.6.4/ directory
esphome run hardware-test.yaml
```

On first flash, you'll need to connect via USB. Subsequent updates can use ESPHome's web interface if you temporarily enable WiFi.

## Test Procedures

### 1. Power-On Test

**Expected Behavior:**
- LCD displays: `MAC:` followed by the WiFi MAC address (e.g., `AA:BB:CC:DD:EE:FF`)
- Status LED: Solid **BLUE**
- Relay: OFF
- Oops LED: OFF

**Verification:**
- ✅ LCD is readable and shows MAC address
- ✅ Status LED is lit blue
- ✅ All outputs are off

---

### 2. Idle Display Cycling

**Expected Behavior:**
Every 5 seconds when idle (no card present), the LCD cycles between:
1. `MAC:` + MAC address
2. `Uptime:` + time in `HH:MM:SS` format

**Verification:**
- ✅ Display automatically cycles every 5 seconds
- ✅ Uptime increments correctly
- ✅ Status LED remains blue

---

### 3. RFID Reader Test

**Procedure:**
1. Present an RFID card/fob to the reader

**Expected Behavior:**
- LCD displays: `RFID:` followed by the tag code (e.g., `0001234567`)
- **Relay: Turns ON** (you should hear/see it click)
- Status LED: Solid **GREEN**
- Card present sensor activates

**Verification:**
- ✅ LCD shows the RFID code
- ✅ Relay energizes (LED on relay board lights up)
- ✅ Status LED is green
- ✅ RFID code is logged to serial console

---

### 4. Card Removal Test

**Procedure:**
1. With card inserted, remove the RFID card

**Expected Behavior:**
- LCD displays: `Card Removed` for 2 seconds
- **Relay: Turns OFF**
- Status LED: Brief **YELLOW** flash (500ms), then returns to **BLUE**
- Display returns to cycling between MAC and uptime after 2 seconds

**Verification:**
- ✅ Relay de-energizes immediately
- ✅ Yellow flash is visible
- ✅ Display returns to normal cycling

---

### 5. Oops Button Test

**Procedure:**
1. Press the oops button (momentary press)

**Expected Behavior:**
- **Oops LED: Toggles ON** (first press) or **OFF** (second press)
- LCD displays: `OOPS! LED: ON` or `OOPS! LED:OFF`
- Status LED: **RED** while button is held, returns to previous color on release

**Verification:**
- ✅ Oops LED toggles with each press
- ✅ LCD shows current LED state
- ✅ Status LED turns red during press
- ✅ Status LED returns to blue (idle) or green (card present) after release

**Note:** The oops button does NOT affect the relay. The relay is only controlled by card insertion/removal.

---

### 6. Combined Test

**Procedure:**
1. Insert RFID card (relay ON, green LED)
2. Press oops button (toggle oops LED, red LED while held)
3. Release oops button (status LED returns to green)
4. Remove card (relay OFF, yellow flash, return to blue)

**Verification:**
- ✅ All components respond correctly in combination
- ✅ Status LED returns to appropriate color based on system state
- ✅ No unexpected behavior or crashes

---

## Status LED Color Reference

| Color | Meaning | When Active |
|-------|---------|-------------|
| **Blue** | Idle/Ready | No card present, system waiting |
| **Green** | Card Present | RFID card inserted, relay active |
| **Yellow** | Card Removed | Brief flash when card is removed |
| **Red** | Oops Button | While oops button is held down |

## Serial Console Monitoring

Connect via USB and monitor at 115200 baud to see detailed logs:

```
[INFO] [BOOT] WiFi MAC Address: AA:BB:CC:DD:EE:FF
[INFO] [BOOT] Hardware test initialized
[INFO] [TAG] Received RFID tag: 0001234567
[INFO] [CARD] Card inserted
[INFO] [CARD] Card removed
[INFO] [OOPS] Oops button pressed - toggling LED
```

## Troubleshooting

### LCD shows nothing
- Check I2C connections (SDA: GPIO22, SCL: GPIO23)
- Verify LCD I2C address is 0x27
- Adjust LCD contrast potentiometer if present

### RFID not reading
- Check wiegand connections (D0: GPIO16, D1: GPIO4)
- Verify card present wire on GPIO18
- Check serial logs for wiegand errors

### Relay not clicking
- Verify relay connection on GPIO33
- Check relay power supply
- Listen for click sound or check relay LED

### Status LED not lighting
- Check NeoPixel connection on GPIO27
- Verify WS2812 LED is powered
- Try different brightness levels

### Oops LED not working
- Check GPIO5 connection
- Verify LED polarity (if direct connection)
- Check for current-limiting resistor if needed

## Success Criteria

All tests pass when:
- ✅ LCD displays all information correctly
- ✅ RFID codes are read and displayed
- ✅ Relay turns ON with card, OFF without card
- ✅ All four status LED colors function correctly
- ✅ Oops button toggles oops LED reliably
- ✅ Card present sensor detects insertion/removal
- ✅ Display cycling works in idle mode
- ✅ No crashes or unexpected resets

## Notes

- This configuration is **completely standalone** - no WiFi or network required
- All state changes are logged to the serial console
- The MAC address displayed is the **WiFi interface** MAC (even though WiFi is disabled)
- Uptime resets to 00:00:00 on every reboot
- The configuration uses **no external files** or secrets
