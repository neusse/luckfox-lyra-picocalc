# Wi-Fi Driver Notes

The PicoCalc build initially had no `wlan0`.

Observed runtime USB modalias:

```text
usb:v2357p011Ed0200dc00dsc00dp00icFFiscFFipFFin00
```

The in-kernel `rtl8xxxu` path did not create `wlan0` and was blacklisted on the
kernel command line:

```text
module_blacklist=rtl8xxxu
```

The working runtime driver was the out-of-tree Realtek `88XXau` module:

```text
88XXau.ko
```

Source used for the working module:

```text
https://github.com/aircrack-ng/rtl8812au
```

Built against:

```text
Kernel source: SDK/kernel-6.1
Compiler: arm-none-linux-gnueabihf-gcc 10.3.1
```

Installed runtime paths on the working image:

```text
/lib/modules/6.1.99/extra/88XXau.ko
/etc/init.d/S04load_88xxau
/etc/init.d/S45wifi
```

Current state:

```text
88XXau loads automatically.
wlan0 exists.
wpa_supplicant and dhcpcd bring the network up.
```

If your physical adapter is an RTL8188FU variant, verify the USB ID and driver
binding before assuming this exact module is correct. On this working system,
Linux binds the observed `2357:011e` adapter with `88XXau`.
