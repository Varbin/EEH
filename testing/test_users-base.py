import string, random

def rand_string(N=10):
    return ''.join(
        random.choice(''.join((
            string.ascii_uppercase, string.ascii_lowercase, string.digits
            ))) for _ in range(N))

from EEHlib.users.base import BaseDriver

def test_users():
    b = BaseDriver('')
    assert not b.update()
    assert not b.update_if_required()
    assert not b.is_accepted_user(rand_string())
    assert not b.resolve_user(rand_string())
