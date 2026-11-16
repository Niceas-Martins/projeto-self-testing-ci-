
def test_complete_http_flow(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}
    a = client.post("/accounts", json={"owner": "Maria", "initial_balance": "100.00"})
    b = client.post("/accounts", json={"owner": "João", "initial_balance": "25.00"})
    assert a.status_code == 201 and b.status_code == 201
    source, target = a.json()["id"], b.json()["id"]
    data = {"origin_id": source, "destination_id": target, "amount": "30.00"}
    first = client.post("/transfers", json=data, headers={"Idempotency-Key": "http-1"})
    assert first.status_code == 201
    replay = client.post("/transfers", json=data, headers={"Idempotency-Key": "http-1"})
    assert replay.json()["replayed"] is True
    assert replay.json()["transfer_id"] == first.json()["transfer_id"]
    assert client.get(f"/accounts/{source}").json()["balance"] == "70.00"
    assert client.get(f"/accounts/{target}").json()["balance"] == "55.00"
    debit = client.get(f"/accounts/{source}/statement?kind=debit")
    credit = client.get(f"/accounts/{target}/statement?kind=credit")
    assert debit.status_code == 200
    assert [item["amount"] for item in debit.json()] == ["30.00"]
    assert [item["amount"] for item in credit.json()] == ["25.00", "30.00"]


def test_http_errors(client):
    assert client.get("/accounts/9999").status_code == 404
    assert client.post("/accounts", json={"owner": "A", "initial_balance": "-1"}).status_code == 400
    assert client.post("/transfers", json={"origin_id": 1, "destination_id": 2, "amount": "1"}).status_code == 422
    assert client.get("/accounts/1/statement?kind=invalid").status_code == 422


def test_http_date_filters(client):
    response = client.post("/accounts", json={"owner": "A", "initial_balance": "5"})
    account = response.json()["id"]
    assert len(client.get(f"/accounts/{account}/statement?start=2000-01-01&end=2100-01-01").json()) == 1
    assert client.get(f"/accounts/{account}/statement?start=2100-01-01&end=2100-01-02").json() == []
