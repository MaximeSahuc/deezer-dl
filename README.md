# Deezer Downloader

Download music directly from deezer.

You will need a file `settings.ini` file in your `~/.config/deezer-dl`.

Only works for linux.

```ini
;;; base config

[deezer]
; login manually using your web browser and take the arl cookie
cookie_arl = <deezer-cookie>

; user id for favorite song to be downloaded
user_id = 0123456789

; music diriectory
music_dir = /tmp/deezer-dl

; deezer country
country = us
```

## Install

```
$ pip install -U git+https://github.com/MaximeSahuc/deezer-dl.git
```

## Feature

Download a playlist
```
deezer-dl https://www.deezer.com/fr/playlist/0123456789
```

Download a single track
```
deezer-dl https://www.deezer.com/us/track/0123456789
```

Download favorites
```
deezer-dl favorites
```

Check connectivity to Deezer
```
deezer-dl check
```

## Acknowledgement

Thanks to kmile hardwork see : https://github.com/kmille/deezer-downloader

Forked from : https://github.com/rllola/deezer-dl