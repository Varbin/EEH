import string, random, os
import time

def rand_string(N=10):
    return ''.join(
        random.choice(''.join((
            string.ascii_uppercase, string.ascii_lowercase, string.digits
            ))) for _ in range(N))

def fn(file):
    return os.path.join(
        os.path.dirname(__file__), "delivery_list", file)


CONFIG_1 = {
    "Allow users file": fn("1.allow"),
    "Deny users file": fn("1.deny"),
    "Update after": 0
}

CONFIG_2 = {
    "Allow users file": fn("2.allow"),
    "Deny users file": fn("2.deny"),
    "Update after": 0
}


from EEHlib.users.list import Driver

def test_allow_all():
    if os.path.isfile(fn("1.allow")):
        os.remove(fn("1.allow"))
    d = Driver(CONFIG_1, "")
    assert os.path.isfile(fn("1.allow"))
    i = rand_string()
    assert d.is_accepted_user(i)
    assert d.resolve_user(i) == [i]
    assert not d.is_accepted_user('not-allowed') 

def test_allow_specific():
    d = Driver(CONFIG_2, "")
    i = rand_string()
    assert d.is_accepted_user("user1")
    assert not d.is_accepted_user("user2")
    assert not d.is_accepted_user("user3")
    assert not d.is_accepted_user("#user3")
    assert not d.is_accepted_user(i)

def test_update():
    d = Driver(CONFIG_2, "")
    assert d.update_if_required()
    time.sleep(.01)
    assert d.update_if_required()
    d.update_after = 10**6
    assert d.update_if_required() is None


if __name__ == "__main__":
    i = None
    for i in globals().keys():
        if i.startswith("test_"):
            print('---', i)
            eval(i).__call__()
