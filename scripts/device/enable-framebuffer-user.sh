#!/bin/sh
set -eu

user="${1:-neusse}"

if ! id "$user" >/dev/null 2>&1; then
    echo "user does not exist: $user" >&2
    exit 1
fi

group_exists() {
    if command -v getent >/dev/null 2>&1; then
        getent group video >/dev/null 2>&1
    else
        grep -q '^video:' /etc/group
    fi
}

if ! group_exists; then
    if command -v addgroup >/dev/null 2>&1; then
        addgroup video
    elif command -v groupadd >/dev/null 2>&1; then
        groupadd video
    else
        echo "cannot create video group: addgroup/groupadd not found" >&2
        exit 1
    fi
fi

add_user_to_group_file() {
    group_mode=""
    group_owner=""
    if command -v stat >/dev/null 2>&1; then
        if ! group_mode="$(stat -c '%a' /etc/group 2>/dev/null)"; then
            group_mode=""
        fi
        if ! group_owner="$(stat -c '%u:%g' /etc/group 2>/dev/null)"; then
            group_owner=""
        fi
    fi

    if command -v mktemp >/dev/null 2>&1; then
        tmp="$(mktemp /etc/group.XXXXXX)"
    else
        tmp="/etc/group.$$"
        : >"$tmp"
    fi

    trap 'rm -f "$tmp"' EXIT HUP INT TERM

    if ! cp -p /etc/group "$tmp" 2>/dev/null; then
        cp /etc/group "$tmp"
    fi

    awk -F: -v OFS=: -v user="$user" '
        $1 == "video" {
            found = 0
            count = split($4, members, ",")
            for (i = 1; i <= count; i++) {
                if (members[i] == user) {
                    found = 1
                }
            }
            if (!found) {
                $4 = ($4 == "") ? user : $4 "," user
            }
        }
        { print }
    ' /etc/group >"$tmp"

    if ! grep -q '^video:' "$tmp"; then
        echo "refusing to replace /etc/group: video group missing from updated file" >&2
        exit 1
    fi

    if ! awk -F: -v user="$user" '
        $1 == "video" {
            count = split($4, members, ",")
            for (i = 1; i <= count; i++) {
                if (members[i] == user) {
                    found = 1
                }
            }
        }
        END { exit found ? 0 : 1 }
    ' "$tmp"; then
        echo "refusing to replace /etc/group: video group does not include $user" >&2
        exit 1
    fi

    if [ -n "$group_owner" ] && command -v chown >/dev/null 2>&1; then
        if ! chown "$group_owner" "$tmp" 2>/dev/null; then
            :
        fi
    fi
    if [ -n "$group_mode" ]; then
        if ! chmod "$group_mode" "$tmp" 2>/dev/null; then
            :
        fi
    fi

    mv "$tmp" /etc/group
    trap - EXIT HUP INT TERM
}

if ! id -nG "$user" | tr ' ' '\n' | grep -qx video; then
    if command -v usermod >/dev/null 2>&1; then
        usermod -a -G video "$user"
    elif command -v gpasswd >/dev/null 2>&1; then
        gpasswd -a "$user" video
    elif command -v adduser >/dev/null 2>&1 && adduser "$user" video >/dev/null 2>&1; then
        :
    elif command -v awk >/dev/null 2>&1; then
        add_user_to_group_file
    else
        echo "cannot add $user to video group: no supported group update tool found" >&2
        exit 1
    fi
fi

if [ -e /dev/fb0 ]; then
    if ! chgrp video /dev/fb0; then
        echo "failed to set /dev/fb0 group to video" >&2
        exit 1
    fi
    if ! chmod 0660 /dev/fb0; then
        echo "failed to set /dev/fb0 permissions to 0660" >&2
        exit 1
    fi
fi

echo "$user is configured for framebuffer access"
