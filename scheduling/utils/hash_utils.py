import hashlib


def hash_string_to_hex(string_to_hash: str) -> str:
    return hashlib.md5(string_to_hash.encode('utf-8')).hexdigest()


def hash_dict_to_hex(dict_to_hash: dict) -> str:
    dict_string = str(sorted(dict_to_hash.items()))
    return hash_string_to_hex(dict_string)


if __name__ == '__main__':
    print(hash_string_to_hex('hello'))
