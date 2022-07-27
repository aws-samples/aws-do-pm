import random

def generate_hash_str(n_char):
    rand_hash_str = ''.join(random.choice('0123456789ABCDEF') for i in range(n_char))
    return rand_hash_str