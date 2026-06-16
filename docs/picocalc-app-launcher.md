# PicoCalc App Launcher

`picocalc-app` starts PicoCalc apps with the project Python path and non-root
Python environment configured. It fixes imports such as `picofb` when running
apps directly from a PicoCalc login shell.

Installed device commands:

```sh
picocalc-app weather --once
picocalc-weather --once
weather --once
weather
```

The launcher expects the synced development tree at:

```text
/home/neusse/luckfox-dev
```

It sets:

```sh
PYTHONPATH=/home/neusse/luckfox-dev/python
VIRTUAL_ENV=/home/neusse/venvs/nonroot
PATH=/home/neusse/venvs/nonroot/bin:$PATH
```

`weather --once` renders one frame and exits. `weather` runs the live dashboard:

- Weather refresh: every 5 minutes.
- Clock redraw: every 30 seconds.

If an app is already running, the launcher exits instead of starting a second
copy. For example:

```text
weather is already running on the PicoCalc console as PID 3268.
Not starting a second copy.
Stop it with: kill 3268
For a one-shot render after stopping it: picocalc-app weather --once
```

## Adding Apps

Add new app scripts to `/home/neusse/luckfox-dev`, then register a short name in
`scripts/device/picocalc-app`:

```python
APP_SCRIPTS = {
    "weather": "picocalc_weather.py",
}
```

If the app should also run from a direct command, add an alias:

```python
APP_ALIASES = {
    "weather": "weather",
}
```

Install the launcher to the device:

```powershell
$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
& $adb push .\scripts\device\picocalc-app /usr/local/bin/picocalc-app
& $adb shell 'chmod 755 /usr/local/bin/picocalc-app; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-app; ln -sf /usr/local/bin/picocalc-app /usr/bin/weather; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-weather'
```
