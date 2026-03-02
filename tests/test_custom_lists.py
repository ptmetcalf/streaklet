from fastapi.testclient import TestClient


def test_list_default_custom_lists(client: TestClient, sample_profiles):
    """Profiles receive template custom lists automatically."""
    response = client.get("/api/custom-lists", cookies={"profile_id": "1"})
    assert response.status_code == 200
    lists = response.json()

    names = [item["name"] for item in lists]
    assert "Shopping" in names


def test_create_custom_list_and_item_flow(client: TestClient, sample_profiles):
    """Custom list items can be created/completed/restored/deleted."""
    create_list = client.post("/api/custom-lists", cookies={"profile_id": "1"}, json={
        "name": "Hardware Store",
        "icon": "hammer",
        "is_enabled": True
    })
    assert create_list.status_code == 201
    list_id = create_list.json()["id"]

    create_item = client.post(f"/api/custom-lists/{list_id}/items", cookies={"profile_id": "1"}, json={
        "title": "AA Batteries",
        "icon": "battery"
    })
    assert create_item.status_code == 201
    item = create_item.json()
    assert item["task_type"] == "custom_list"
    assert item["custom_list_id"] == list_id

    complete = client.post(f"/api/custom-lists/{list_id}/items/{item['id']}/complete", cookies={"profile_id": "1"})
    assert complete.status_code == 200
    assert complete.json()["completed_at"] is not None

    undo = client.delete(f"/api/custom-lists/{list_id}/items/{item['id']}/complete", cookies={"profile_id": "1"})
    assert undo.status_code == 200
    assert undo.json()["completed_at"] is None

    delete_item = client.delete(f"/api/custom-lists/{list_id}/items/{item['id']}", cookies={"profile_id": "1"})
    assert delete_item.status_code == 200


def test_custom_list_profile_isolation(client: TestClient, sample_profiles):
    """Custom list items are isolated by profile."""
    p1_list = client.post("/api/custom-lists", cookies={"profile_id": "1"}, json={
        "name": "Profile1 List",
        "is_enabled": True
    }).json()
    p2_list = client.post("/api/custom-lists", cookies={"profile_id": "2"}, json={
        "name": "Profile2 List",
        "is_enabled": True
    }).json()

    client.post(f"/api/custom-lists/{p1_list['id']}/items", cookies={"profile_id": "1"}, json={"title": "Milk"})
    client.post(f"/api/custom-lists/{p2_list['id']}/items", cookies={"profile_id": "2"}, json={"title": "Eggs"})

    p1_items = client.get("/api/custom-lists/items", cookies={"profile_id": "1"}).json()
    p2_items = client.get("/api/custom-lists/items", cookies={"profile_id": "2"}).json()

    assert len(p1_items) == 1
    assert len(p2_items) == 1
    assert p1_items[0]["title"] == "Milk"
    assert p2_items[0]["title"] == "Eggs"
