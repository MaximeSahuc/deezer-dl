# Deezer Downloader

Download music directly from Deezer.


## Install

```
pipx install git+https://github.com/MaximeSahuc/deezer-dl.git --force
```


## Features

- Download Tracks, Playlists and Albums
- Support for FLAC quality or MP3
- File metadata: cover, title, artist


## Usage

### Download a track / album / playlist
```
deezer-dl url https://www.deezer.com/xx/album/0123456789
```

### Download all favorite tracks of the logged-in user
```
deezer-dl favorites
```

### Download all playlists of the logged-in user
```
deezer-dl all-playlists
```

### Download all albums of the logged-in user
```
deezer-dl all-albums
```


### Download all songs and albums from given artist
```
deezer-dl all-from-artist <artist id or url>
```

### Download all favorite tracks, albums and playlists of the logged-in user
```
deezer-dl all
```

## Acknowledgement

Thanks to kmille hard work: https://github.com/kmille/deezer-downloader