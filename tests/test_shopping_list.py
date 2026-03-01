from fastapi.testclient import TestClient


def test_create_shopping_item(client: TestClient, sample_profiles):
    """Shopping list item can be created via API."""
    response = client.post("/api/shopping-list", json={
        "title": "Dish soap",
        "is_active": True
    })

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Dish soap"
    assert data["task_type"] == "shopping_list"
    assert data["is_required"] is False
    assert data["completed_at"] is None


def test_complete_and_uncomplete_shopping_item(client: TestClient, sample_profiles):
    """Shopping item can be marked purchased and then restored."""
    create_response = client.post("/api/shopping-list", json={"title": "Paper towels"})
    item_id = create_response.json()["id"]

    complete_response = client.post(f"/api/shopping-list/{item_id}/complete")
    assert complete_response.status_code == 200
    assert complete_response.json()["completed_at"] is not None

    uncomplete_response = client.delete(f"/api/shopping-list/{item_id}/complete")
    assert uncomplete_response.status_code == 200
    assert uncomplete_response.json()["completed_at"] is None


def test_list_shopping_items_excluding_completed(client: TestClient, sample_profiles):
    """List endpoint can exclude completed shopping items."""
    first = client.post("/api/shopping-list", json={"title": "Coffee beans"}).json()
    second = client.post("/api/shopping-list", json={"title": "Laundry detergent"}).json()
    client.post(f"/api/shopping-list/{second['id']}/complete")

    response = client.get("/api/shopping-list?include_completed=false")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == first["id"]
    assert data[0]["completed_at"] is None


def test_delete_shopping_item(client: TestClient, sample_profiles):
    """Shopping item can be deleted."""
    created = client.post("/api/shopping-list", json={"title": "Trash bags"}).json()
    item_id = created["id"]

    delete_response = client.delete(f"/api/shopping-list/{item_id}")
    assert delete_response.status_code == 200

    list_response = client.get("/api/shopping-list")
    ids = [item["id"] for item in list_response.json()]
    assert item_id not in ids


def test_shopping_list_profile_isolation(client: TestClient, sample_profiles):
    """Shopping items are isolated by profile cookie."""
    client.post("/api/shopping-list", json={"title": "Milk"}, cookies={"profile_id": "1"})
    client.post("/api/shopping-list", json={"title": "Eggs"}, cookies={"profile_id": "2"})

    profile_one_items = client.get("/api/shopping-list", cookies={"profile_id": "1"}).json()
    profile_two_items = client.get("/api/shopping-list", cookies={"profile_id": "2"}).json()

    assert len(profile_one_items) == 1
    assert len(profile_two_items) == 1
    assert profile_one_items[0]["title"] == "Milk"
    assert profile_two_items[0]["title"] == "Eggs"
