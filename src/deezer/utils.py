def get_song_filename(song_artist, song_title, file_extension=None):
    if file_extension:
        filename = f"{song_artist} - {song_title}.{file_extension}"
    else:
        filename = f"{song_artist} - {song_title}"

    # Replace with DIVISION SLASH and not forward slash
    return filename.replace("/", "\u2215")


def sanitize_folder_name(name, item_type):
    import re
    import random
    from unidecode import unidecode

    # Generate a unique 6-digit hex suffix (e.g. "_a3b7f2")
    hex_suffix = f"_{random.getrandbits(24):06x}"

    # Default name in case of invalid input (e.g. "playlist_a3b7f2")
    default_name = f"{item_type}{hex_suffix}"

    # Default name for empty or whitespace-only inputs
    if not name.strip():
        return default_name

    sanitized_name = name

    # Replace non-ASCII characters with ASCII equivalents or underscores
    sanitized_name = unidecode(sanitized_name)

    # Replace spaces and other problematic characters with underscores
    sanitized_name = re.sub(r"[^a-zA-Z0-9_]+", "_", sanitized_name)

    # Collapse multiple consecutive underscores into a single underscore
    sanitized_name = re.sub(r"_{2,}", "_", sanitized_name)

    # Remove leading and trailing underscores
    sanitized_name = sanitized_name.strip("_")

    # Ensure the name is not empty after sanitization
    if not sanitized_name:
        return default_name

    return sanitized_name


def create_link(src, dest, link_type):
    import os

    match link_type.lower():
        case "symlink":
            os.symlink(src, dest)

        case "hardlink":
            os.link(src, dest)

        case _:
            raise ValueError(f"Unknown link type : {link_type}")


def extract_id_from_url(url):
    import re

    try:
        return re.search(r"\d+", url).group(0)
    except AttributeError:
        print(f"Error: Regex (\\d+) for url failed. You gave me '{url}'")
        return None


def download_image(session, file_output, url):
    response = session.get(url)
    picture_bytes = response.content

    with open(file_output, "wb") as of:
        of.write(picture_bytes)
