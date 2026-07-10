def test_get_keywords(test_client):
    response = test_client.get("/keywords/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
