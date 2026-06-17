import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def coding_client(app, client):
    store = app.state.coding_workspaces
    if store._db is not None:
        await store.close()
    await store.init()
    yield client, app


@pytest.mark.asyncio
async def test_create_list_git_repo(coding_client):
    client, app = coding_client
    r = await client.post("/api/coding/workspaces", json={"name": "demo"})
    assert r.status_code == 200, r.text
    ws = r.json()
    assert ws["id"]
    assert ws["name"] == "demo"
    assert (app.state.data_dir / "coding-workspaces" / ws["id"]).is_dir()
    assert (app.state.data_dir / "coding-workspaces" / ws["id"] / ".git").exists()

    r = await client.get("/api/coding/workspaces")
    assert r.status_code == 200
    assert any(row["id"] == ws["id"] for row in r.json())


@pytest.mark.asyncio
async def test_write_read_and_tree(coding_client):
    client, _app = coding_client
    r = await client.post("/api/coding/workspaces", json={"name": "files"})
    ws = r.json()

    r = await client.put(
        f"/api/coding/workspaces/{ws['id']}/file",
        json={"path": "src/hello.txt", "content": "hello world"},
    )
    assert r.status_code == 200, r.text

    r = await client.get(f"/api/coding/workspaces/{ws['id']}/file", params={"path": "src/hello.txt"})
    assert r.status_code == 200
    assert r.json()["content"] == "hello world"

    r = await client.get(f"/api/coding/workspaces/{ws['id']}/files", params={"subpath": "src"})
    assert r.status_code == 200
    names = {e["name"]: e["is_dir"] for e in r.json()}
    assert names["hello.txt"] is False


@pytest.mark.asyncio
async def test_path_traversal_rejected(coding_client):
    client, _app = coding_client
    r = await client.post("/api/coding/workspaces", json={"name": "jail"})
    ws = r.json()
    wid = ws["id"]

    for params in (
        {"path": "../secret"},
        {"path": "/etc/passwd"},
        {"subpath": ".."},
        {"subpath": "/etc"},
    ):
        if "path" in params:
            r = await client.get(f"/api/coding/workspaces/{wid}/file", params=params)
        else:
            r = await client.get(f"/api/coding/workspaces/{wid}/files", params=params)
        assert r.status_code == 400, params

    r = await client.put(
        f"/api/coding/workspaces/{wid}/file",
        json={"path": "../escape.txt", "content": "nope"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_delete_removes_workspace(coding_client):
    client, app = coding_client
    r = await client.post("/api/coding/workspaces", json={"name": "temp"})
    ws = r.json()
    workspace_dir = app.state.data_dir / "coding-workspaces" / ws["id"]
    assert workspace_dir.is_dir()

    r = await client.delete(f"/api/coding/workspaces/{ws['id']}")
    assert r.status_code == 200

    r = await client.get("/api/coding/workspaces")
    assert all(row["id"] != ws["id"] for row in r.json())
    assert not workspace_dir.exists()


@pytest.mark.asyncio
async def test_list_root_files(coding_client):
    client, _app = coding_client
    r = await client.post("/api/coding/workspaces", json={"name": "root-list"})
    ws = r.json()

    r = await client.put(
        f"/api/coding/workspaces/{ws['id']}/file",
        json={"path": "readme.txt", "content": "hi"},
    )
    assert r.status_code == 200

    r = await client.get(f"/api/coding/workspaces/{ws['id']}/files")
    assert r.status_code == 200
    names = {e["name"] for e in r.json()}
    assert "readme.txt" in names


@pytest.mark.asyncio
async def test_read_binary_file_rejected(coding_client):
    client, app = coding_client
    r = await client.post("/api/coding/workspaces", json={"name": "binary"})
    ws = r.json()
    workspace_dir = app.state.data_dir / "coding-workspaces" / ws["id"]
    (workspace_dir / "blob.bin").write_bytes(b"\xff\xfe\x00\x01")

    r = await client.get(
        f"/api/coding/workspaces/{ws['id']}/file",
        params={"path": "blob.bin"},
    )
    assert r.status_code == 400
    assert r.json()["error"] == "binary file"


@pytest.mark.asyncio
async def test_unknown_workspace_returns_404(coding_client):
    client, _app = coding_client
    wid = "cws-nosuch"
    r = await client.get(f"/api/coding/workspaces/{wid}/files")
    assert r.status_code == 404
    r = await client.get(f"/api/coding/workspaces/{wid}/file", params={"path": "a.txt"})
    assert r.status_code == 404
    r = await client.put(
        f"/api/coding/workspaces/{wid}/file",
        json={"path": "a.txt", "content": "x"},
    )
    assert r.status_code == 404
    r = await client.delete(f"/api/coding/workspaces/{wid}")
    assert r.status_code == 404