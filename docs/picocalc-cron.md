# PicoCalc Cron

BusyBox `crond` is enabled by `/etc/init.d/S58crond`.

The service runs:

```sh
/usr/sbin/crond -c /etc/crontabs -l 8 -S
```

Crontabs are stored persistently in `/etc/crontabs`. The normal BusyBox default
path `/var/spool/cron/crontabs` is symlinked there at boot because `/var` is
temporary on this image.

Use `crontab` to install changes so BusyBox cron notices updates:

```sh
crontab -l
crontab -e
```

For scripted edits:

```sh
cat > /tmp/rootcron <<'EOF'
# Example: run a maintenance script at 03:15.
15 3 * * * /usr/local/sbin/picocalc-maintenance >/dev/null 2>&1
EOF
crontab /tmp/rootcron
```

Clock sync is handled by `/etc/init.d/S47ntpd`, not cron.

The idle daemon cost measured on the Lyra was roughly 270 KB PSS and no
measurable idle CPU over a one-minute interval.
