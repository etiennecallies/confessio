from scheduling.utils.hash_utils import hash_string_to_hex


def get_color_from_string(s: str) -> str:
    # Generate a hash of the string
    hash_hex = hash_string_to_hex(s)

    # Convert first 3 bytes of hash to RGB values
    r = int(hash_hex[:2], 16)
    g = int(hash_hex[2:4], 16)
    b = int(hash_hex[4:6], 16)

    # Convert to hex color code
    return f"#{r:02x}{g:02x}{b:02x}"
