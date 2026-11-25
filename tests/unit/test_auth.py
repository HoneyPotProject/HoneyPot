from backend.auth import authenticate_credentials, create_session_token, parse_session_token


def test_valid_credentials():
    assert authenticate_credentials('admin', 'admin')
    assert not authenticate_credentials('admin', 'wrong')
    assert not authenticate_credentials('other', 'admin')


def test_session_roundtrip():
    token = create_session_token('admin')
    assert parse_session_token(token) == 'admin'
    assert parse_session_token(token + 'x') is None
    assert parse_session_token(None) is None
