import struct

from deezer.crypto import md5hex, hexaescrypt


def genurlkey(songid, md5origin, mediaver=4, fmt=1):
    """Calculate the deezer download url given the songid, origin and media+format"""
    data_concat = b"\xa4".join(
        _
        for _ in [
            md5origin.encode(),
            str(fmt).encode(),
            str(songid).encode(),
            str(mediaver).encode(),
        ]
    )
    data = b"\xa4".join([md5hex(data_concat), data_concat]) + b"\xa4"
    if len(data) % 16 != 0:
        data += b"\0" * (16 - len(data) % 16)
    return hexaescrypt(data, "jo6aey6haid2Teih")


def writeid3v1_1(fo, song):
    def song_get(song, key):
        try:
            return song.get(key).encode("utf-8")
        except:
            return b""

    def album_get(key):
        global album_Data
        try:
            return album_Data.get(key).encode("utf-8")
        except:
            return b""

    # what struct.pack expects
    # B => int
    # s => bytes
    data = struct.pack(
        "3s30s30s30s4s28sBBB",
        b"TAG",  # header
        song_get(song, "SNG_TITLE"),  # title
        song_get(song, "ART_NAME"),  # artist
        song_get(song, "ALB_TITLE"),  # album
        album_get("PHYSICAL_RELEASE_DATE"),  # year
        album_get("LABEL_NAME"),
        0,  # comment
        int(song_get(song, "TRACK_NUMBER")),  # tracknum
        255,  # genre
    )

    fo.write(data)


downloaded_pictures_cache = {}


def download_picture(session, pic_idid):
    global downloaded_pictures_cache

    # Clear cache
    if len(downloaded_pictures_cache) > 100:
        downloaded_pictures_cache = {}

    # Cache album pictures
    if pic_idid not in downloaded_pictures_cache:
        res = session.get(get_picture_link(pic_idid))
        picture_bytes = res.content
        downloaded_pictures_cache.update({pic_idid: picture_bytes})

    return downloaded_pictures_cache[pic_idid]


def get_picture_link(pic_idid):
    setting_domain_img = "https://cdn-images.dzcdn.net/images"
    url = setting_domain_img + "/cover/" + pic_idid + "/1200x1200.jpg"
    return url


def writeid3v2(session, fo, song):
    def make28bit(x):
        return (
            ((x << 3) & 0x7F000000)
            | ((x << 2) & 0x7F0000)
            | ((x << 1) & 0x7F00)
            | (x & 0x7F)
        )

    def maketag(tag, content):
        return struct.pack(">4sLH", tag.encode("ascii"), len(content), 0) + content

    def album_get(key):
        global album_Data
        try:
            return album_Data.get(key)
        except:
            # raise
            return ""

    def song_get(song, key):
        try:
            return song[key]
        except:
            # raise
            return ""

    def makeutf8(txt):
        # return b"\x03" + txt.encode('utf-8')
        return "\x03{}".format(txt).encode()

    def makepic(data):
        # Picture type:
        # 0x00     Other
        # 0x01     32x32 pixels 'file icon' (PNG only)
        # 0x02     Other file icon
        # 0x03     Cover (front)
        # 0x04     Cover (back)
        # 0x05     Leaflet page
        # 0x06     Media (e.g. lable side of CD)
        # 0x07     Lead artist/lead performer/soloist
        # 0x08     Artist/performer
        # 0x09     Conductor
        # 0x0A     Band/Orchestra
        # 0x0B     Composer
        # 0x0C     Lyricist/text writer
        # 0x0D     Recording Location
        # 0x0E     During recording
        # 0x0F     During performance
        # 0x10     Movie/video screen capture
        # 0x11     A bright coloured fish
        # 0x12     Illustration
        # 0x13     Band/artist logotype
        # 0x14     Publisher/Studio logotype
        imgframe = (
            b"\x00",  # text encoding
            b"image/jpeg",
            b"\0",  # mime type
            b"\x03",  # picture type: 'Cover (front)'
            b""[:64],
            b"\0",  # description
            data,
        )

        return b"".join(imgframe)

    # get Data as DDMM
    try:
        phyDate_YYYYMMDD = album_get("PHYSICAL_RELEASE_DATE").split("-")  #'2008-11-21'
        phyDate_DDMM = phyDate_YYYYMMDD[2] + phyDate_YYYYMMDD[1]
    except:
        phyDate_DDMM = ""

    # get size of first item in the list that is not 0
    try:
        FileSize = [
            song_get(song, i)
            for i in (
                "FILESIZE_AAC_64",
                "FILESIZE_MP3_320",
                "FILESIZE_MP3_256",
                "FILESIZE_MP3_64",
                "FILESIZE",
            )
            if song_get(song, i)
        ][0]
    except:
        FileSize = 0

    try:
        track = "%02s" % song["TRACK_NUMBER"]
        track += "/%02s" % album_get("TRACKS")
    except:
        pass

    # http://id3.org/id3v2.3.0#Attached_picture
    id3 = [
        maketag(
            "TRCK", makeutf8(track)
        ),  # The 'Track number/Position in set' frame is a numeric string containing the order number of the audio-file on its original recording. This may be extended with a "/" character and a numeric string containing the total numer of tracks/elements on the original recording. E.g. "4/9".
        maketag(
            "TLEN", makeutf8(str(int(song["DURATION"]) * 1000))
        ),  # The 'Length' frame contains the length of the audiofile in milliseconds, represented as a numeric string.
        maketag(
            "TORY", makeutf8(str(album_get("PHYSICAL_RELEASE_DATE")[:4]))
        ),  # The 'Original release year' frame is intended for the year when the original recording was released. if for example the music in the file should be a cover of a previously released song
        maketag(
            "TYER", makeutf8(str(album_get("DIGITAL_RELEASE_DATE")[:4]))
        ),  # The 'Year' frame is a numeric string with a year of the recording. This frames is always four characters long (until the year 10000).
        maketag(
            "TDAT", makeutf8(str(phyDate_DDMM))
        ),  # The 'Date' frame is a numeric string in the DDMM format containing the date for the recording. This field is always four characters long.
        maketag(
            "TPUB", makeutf8(album_get("LABEL_NAME"))
        ),  # The 'Publisher' frame simply contains the name of the label or publisher.
        maketag(
            "TSIZ", makeutf8(str(FileSize))
        ),  # The 'Size' frame contains the size of the audiofile in bytes, excluding the ID3v2 tag, represented as a numeric string.
        maketag("TFLT", makeutf8("MPG/3")),
    ]  # decimal, no term NUL
    id3.extend(
        [
            maketag(ID_id3_frame, makeutf8(song_get(song, ID_song)))
            for (ID_id3_frame, ID_song) in (
                (
                    "TALB",
                    "ALB_TITLE",
                ),  # The 'Album/Movie/Show title' frame is intended for the title of the recording(/source of sound) which the audio in the file is taken from.
                (
                    "TPE1",
                    "ART_NAME",
                ),  # The 'Lead artist(s)/Lead performer(s)/Soloist(s)/Performing group' is used for the main artist(s). They are seperated with the "/" character.
                (
                    "TPE2",
                    "ART_NAME",
                ),  # The 'Band/Orchestra/Accompaniment' frame is used for additional information about the performers in the recording.
                (
                    "TPOS",
                    "DISK_NUMBER",
                ),  # The 'Part of a set' frame is a numeric string that describes which part of a set the audio came from. This frame is used if the source described in the "TALB" frame is divided into several mediums, e.g. a double CD. The value may be extended with a "/" character and a numeric string containing the total number of parts in the set. E.g. "1/2".
                (
                    "TIT2",
                    "SNG_TITLE",
                ),  # The 'Title/Songname/Content description' frame is the actual name of the piece (e.g. "Adagio", "Hurricane Donna").
                (
                    "TSRC",
                    "ISRC",
                ),  # The 'ISRC' frame should contain the International Standard Recording Code (ISRC) (12 characters).
            )
        ]
    )

    try:
        id3.append(
            maketag("APIC", makepic(download_picture(session, song["ALB_PICTURE"])))
        )
    except Exception as e:
        print("ERROR: no album cover?", e)

    id3data = b"".join(id3)
    # >      big-endian
    # s      char[]  bytes
    # H      unsigned short  integer 2
    # B      unsigned char   integer 1
    # L      unsigned long   integer 4

    hdr = struct.pack(
        ">3sHBL",
        "ID3".encode("ascii"),
        0x300,  # version
        0x00,  # flags
        make28bit(len(id3data)),
    )

    fo.write(hdr)
    fo.write(id3data)


def generate_playlist_m3u(playlist_dir, playlist_name, songs):
    import os

    output_file = os.path.join(playlist_dir, f"{playlist_name}.m3u")

    with open(output_file, "w") as of:
        of.write("#EXTM3U\n")

        for song in songs:
            of.write(f"{song}\n")
