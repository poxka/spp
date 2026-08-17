from tests.conftest import TEST_PASSWORD, TEST_USERNAME


async def test_login_success(client):
    response = await client.post(
        "/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0


async def test_login_wrong_password(client):
    response = await client.post(
        "/auth/login",
        json={"username": TEST_USERNAME, "password": "wrong-password-000"},
    )
    assert response.status_code == 401


async def test_login_unknown_user_same_response(client):
    response = await client.post(
        "/auth/login",
        json={"username": "ghost-user", "password": "whatever-123456"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


async def test_login_rejects_sqli_username(client):
    response = await client.post(
        "/auth/login",
        json={"username": "' OR '1'='1", "password": "whatever-123456"},
    )
    assert response.status_code == 401


async def test_protected_endpoint_requires_auth(client):
    response = await client.get("/transactions")
    assert response.status_code == 401
