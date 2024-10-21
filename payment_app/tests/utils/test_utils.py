from payment_app.utils import check_ip_in_range, get_api_key_hash

def test_check_ip_in_range():
    ip = "127.0.0.1"
    range = "127.0.0.1"
    result = check_ip_in_range(ip, range)
    assert result == True


def test_check_ip_not_in_range():
    ip = "127.0.0.2"
    range = "127.0.0.1"
    result = check_ip_in_range(ip, range)
    assert result == False


def test_get_api_key_hash():
    result = get_api_key_hash("coneofshame")
    assert result == "8ef3eedcd85b1a4b8ab81af991f444bbbf1e60f6ad4521597dbed7c9ac0af8e5"

