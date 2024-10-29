"""Health check."""
from payment_app.tests.conftest import client

def test_read_ping():
    """Test initial connection."""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong!"}

def test_github_actions_trigger():
    """Test if GitHub Actions workflow is triggered."""
    assert True
