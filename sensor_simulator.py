
import time
import requests
from datetime import datetime, timezone

# Adresse til vores Flask REST API
API_URL = "http://127.0.0.1:5006/api/measurements"

# Simulerede temperaturmålinger
temperatures = [62, 65, 68, 73, 79, 84, 90, 94, 76, 67]

for temperature in temperatures:

    # Data som sendes til API'et
    sensor_data = {
        "sensor_id": "PUMP-01-TEMP",
        "asset_id": "PUMP-01",
        "value": temperature,
        "unit": "C",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print(f"Sender temperatur: {temperature} °C")

    try:
        # Send sensordata med HTTP POST
        response = requests.post(
            API_URL,
            json=sensor_data,
            timeout=5
        )

        response.raise_for_status()
        print("API response:", response.json())

    except requests.RequestException as error:
        print("Fejl ved forbindelse:", error)

    # Vent 2 sekunder før næste måling
    time.sleep(2)

print("Simulering afsluttet!")
