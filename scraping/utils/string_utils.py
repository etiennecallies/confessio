def is_below_byte_limit(s, byte_limit=2704):
    return len(s.encode('utf-8')) < byte_limit
