import uuid


async def test_create_and_get_transaction(client, auth_headers):
    payload = {
        "amount": "42.50",
        "currency": "MXN",
        "card_token": str(uuid.uuid4()),
    }
    created = await client.post("/transactions", json=payload, headers=auth_headers)
    assert created.status_code == 201

    body = created.json()
    assert body["amount"] == "42.50"
    assert body["currency"] == "MXN"
    assert body["status"] == "created"

    fetched = await client.get(f"/transactions/{body['id']}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


async def test_create_rejects_unknown_currency(client, auth_headers):
    payload = {
        "amount": "10.00",
        "currency": "XYZ",
        "card_token": str(uuid.uuid4()),
    }
    response = await client.post("/transactions", json=payload, headers=auth_headers)
    assert response.status_code == 422


async def test_create_rejects_negative_amount(client, auth_headers):
    payload = {
        "amount": "-5.00",
        "currency": "USD",
        "card_token": str(uuid.uuid4()),
    }
    response = await client.post("/transactions", json=payload, headers=auth_headers)
    assert response.status_code == 422


async def test_create_rejects_bad_card_token(client, auth_headers):
    payload = {
        "amount": "10.00",
        "currency": "USD",
        "card_token": "not-a-uuid",
    }
    response = await client.post("/transactions", json=payload, headers=auth_headers)
    assert response.status_code == 422


async def test_get_missing_transaction_returns_404(client, auth_headers):
    response = await client.get(f"/transactions/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


async def test_list_transactions_scoped_to_owner(client, auth_headers):
    payload = {
        "amount": "1.00",
        "currency": "EUR",
        "card_token": str(uuid.uuid4()),
    }
    await client.post("/transactions", json=payload, headers=auth_headers)

    response = await client.get("/transactions", headers=auth_headers)
    assert response.status_code == 200

    items = response.json()
    assert len(items) == 1
    assert items[0]["currency"] == "EUR"
