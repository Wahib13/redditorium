def _register(client, email="user@test.com", password="strongpassword"):
    return client.post("/auth/register", json={"email": email, "password": password})


def _login(client, email="user@test.com", password="strongpassword"):
    return client.post("/auth/login", data={"username": email, "password": password})


def test_register_success(test_client):
    response = _register(test_client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@test.com"
    assert body["admin"] is False
    assert "id" in body


def test_register_duplicate_email(test_client):
    _register(test_client)
    response = _register(test_client)
    assert response.status_code == 400


def test_register_password_too_short(test_client):
    response = _register(test_client, password="short")
    assert response.status_code == 422


def test_login_success(test_client):
    _register(test_client)
    response = _login(test_client)
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(test_client):
    _register(test_client)
    response = _login(test_client, password="wrongpassword")
    assert response.status_code == 401


def test_login_unknown_user(test_client):
    response = _login(test_client, email="nobody@test.com")
    assert response.status_code == 401


def test_me_returns_current_user(test_client):
    _register(test_client)
    token = _login(test_client).json()["access_token"]
    response = test_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "user@test.com"


def test_me_with_invalid_token(test_client):
    response = test_client.get("/auth/me", headers={"Authorization": "Bearer notavalidtoken"})
    assert response.status_code == 401
