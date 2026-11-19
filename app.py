

import os
import math
import pymysql
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Hent databaseindstillinger fra .env
load_dotenv()

app = Flask(__name__)

THRESHOLD = 80


# Opret forbindelse til vores MySQL-database
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5
    )


# Modtag temperaturmålinger fra IoT-simulatoren
@app.route("/api/measurements", methods=["POST"])
def receive_measurement():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    required = [
        "sensor_id", "asset_id", "value",
        "unit", "timestamp"
    ]

    if any(field not in data for field in required):
        return jsonify({"error": "Missing fields"}), 400

    value = data["value"]

    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        return jsonify({"error": "Invalid value"}), 400

    for field, max_length in [
        ("sensor_id", 100),
        ("asset_id", 100),
        ("unit", 10)
    ]:
        item = data[field]
        if (
            not isinstance(item, str)
            or not item.strip()
            or len(item) > max_length
        ):
            return jsonify({"error": f"Invalid {field}"}), 400

    try:
        # Konverter tidsstemplet til UTC
        measured_at = datetime.fromisoformat(
            data["timestamp"].replace("Z", "+00:00")
        )

        if measured_at.tzinfo is None:
            raise ValueError("Timezone missing")

        measured_at = measured_at.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

    except (ValueError, TypeError, AttributeError):
        return jsonify({"error": "Invalid timestamp"}), 400

    # Undersøg om temperaturen er for høj
    is_alarm = value > THRESHOLD
    status = "ALARM" if is_alarm else "NORMAL"

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:

            # 1. Gem sensormålingen
            cursor.execute("""
                INSERT INTO sensor_measurements
                (sensor_id, asset_id, value, unit,
                 measured_at, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data["sensor_id"],
                data["asset_id"],
                value,
                data["unit"],
                measured_at,
                status
            ))

            measurement_id = cursor.lastrowid

            # 2. Registrer Sensor Value Received
            cursor.execute("""
                INSERT INTO domain_events
                (measurement_id, event_type)
                VALUES (%s, %s)
            """, (
                measurement_id,
                "Sensor Value Received"
            ))

            # 3. Registrer afvigelse og opret alarm
            if is_alarm:

                cursor.execute("""
                    INSERT INTO domain_events
                    (measurement_id, event_type)
                    VALUES (%s, %s)
                """, (
                    measurement_id,
                    "Anomaly Detected"
                ))

                cursor.execute("""
                    INSERT INTO alarms
                    (measurement_id, status, message)
                    VALUES (%s, %s, %s)
                """, (
                    measurement_id,
                    "OPEN",
                    f"Temperature {value} exceeds {THRESHOLD}"
                ))

        # Gem alle ændringer permanent
        connection.commit()

        return jsonify({
            "measurement_id": measurement_id,
            "sensor_id": data["sensor_id"],
            "value": value,
            "status": status,
            "event": (
                "Anomaly Detected"
                if is_alarm else "Sensor Value Received"
            )
        }), 201

    except pymysql.MySQLError:
        if connection:
            connection.rollback()

        app.logger.exception("Database operation failed")
        return jsonify({"error": "Database error"}), 500

    finally:
        if connection:
            connection.close()


# Hent gemte sensormålinger
@app.route("/api/measurements", methods=["GET"])
def get_measurements():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, sensor_id, asset_id,
                       value, unit, measured_at, status
                FROM sensor_measurements
                ORDER BY id DESC
            """)
            measurements = cursor.fetchall()

        return jsonify(measurements)

    except pymysql.MySQLError:
        app.logger.exception("Failed to fetch measurements")
        return jsonify({"error": "Database error"}), 500

    finally:
        if connection:
            connection.close()


# Hent registrerede alarmer
@app.route("/api/alarms", methods=["GET"])
def get_alarms():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT a.id, a.measurement_id,
                       a.status, a.message, a.created_at
                FROM alarms AS a
                ORDER BY a.id DESC
            """)
            alarms = cursor.fetchall()

        return jsonify(alarms)

    except pymysql.MySQLError:
        app.logger.exception("Failed to fetch alarms")
        return jsonify({"error": "Database error"}), 500

    finally:
        if connection:
            connection.close()


# Start Flask API'et
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
