
import pytest
import pymysql
from unittest.mock import MagicMock

import app as api_module


# Opret en Flask-testklient
@pytest.fixture
def client():
    api_module.app.config["TESTING"] = True
    return api_module.app.test_client()


# Simuler en database uden at ændre rigtig MySQL-data
@pytest.fixture
def fake_db(monkeypatch):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.lastrowid = 42

    monkeypatch.setattr(
        api_module,
        "get_db_connection",
        lambda: connection
    )

    return connection, cursor


# Standardmåling til vores tests
def sensor_data(value=65):
    return {
        "sensor_id": "PUMP-01-TEMP",
        "asset_id": "PUMP-01",
        "value": value,
        "unit": "C",
        "timestamp": "2026-11-19T10:35:00Z"
    }


# Test 1: Normal temperatur
def test_normal_temperature(client, fake_db):
    connection, cursor = fake_db

    response = client.post(
        "/api/measurements",
        json=sensor_data(65)
    )

    assert response.status_code == 201
    assert response.json["status"] == "NORMAL"
    assert response.json["event"] == "Sensor Value Received"
    assert cursor.execute.call_count == 2
    connection.commit.assert_called_once()


# Test 2: For høj temperatur
def test_high_temperature(client, fake_db):
    connection, cursor = fake_db

    response = client.post(
        "/api/measurements",
        json=sensor_data(95)
    )

    assert response.status_code == 201
    assert response.json["status"] == "ALARM"
    assert response.json["event"] == "Anomaly Detected"
    assert cursor.execute.call_count == 4
    connection.commit.assert_called_once()


# Test 3: Præcis på grænseværdien
def test_threshold_boundary(client, fake_db):
    response = client.post(
        "/api/measurements",
        json=sensor_data(80)
    )

    assert response.status_code == 201
    assert response.json["status"] == "NORMAL"


# Test 4: Manglende sensor-ID
def test_missing_sensor_id(client):
    data = sensor_data()
    del data["sensor_id"]

    response = client.post(
        "/api/measurements",
        json=data
    )

    assert response.status_code == 400
    assert response.json["error"] == "Missing fields"


# Test 5: Ugyldig temperaturværdi
def test_invalid_temperature(client):
    response = client.post(
        "/api/measurements",
        json=sensor_data("invalid")
    )

    assert response.status_code == 400
    assert response.json["error"] == "Invalid value"


# Test 6: Database er utilgængelig
def test_database_unavailable(client, monkeypatch):

    def failing_connection():
        raise pymysql.MySQLError("Simulated database failure")

    monkeypatch.setattr(
        api_module,
        "get_db_connection",
        failing_connection
    )

    response = client.post(
        "/api/measurements",
        json=sensor_data(95)
    )

    assert response.status_code == 500
    assert response.json["error"] == "Database error"
