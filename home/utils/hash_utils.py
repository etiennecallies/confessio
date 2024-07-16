import hashlib


def hash_string_to_hex(string_to_hash: str) -> str:
    return hashlib.md5(string_to_hash.encode('utf-8')).hexdigest()


if __name__ == '__main__':
    print(hash_string_to_hex('hello'))
