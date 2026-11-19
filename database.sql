
USE iot_monitoring;

-- Tabel 1: Gemmer alle sensormålinger
CREATE TABLE IF NOT EXISTS sensor_measurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(100) NOT NULL,
    asset_id VARCHAR(100) NOT NULL,
    value DOUBLE NOT NULL,
    unit VARCHAR(10) NOT NULL,
    measured_at DATETIME(6) NOT NULL,
    status VARCHAR(20) NOT NULL
);

-- Tabel 2: Gemmer domain events
CREATE TABLE IF NOT EXISTS domain_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    measurement_id INT NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (measurement_id)
        REFERENCES sensor_measurements(id)
);

-- Tabel 3: Gemmer alarmer
CREATE TABLE IF NOT EXISTS alarms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    measurement_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    message VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (measurement_id)
        REFERENCES sensor_measurements(id)
);

-- Kontroller at tabellerne eksisterer
SHOW TABLES;
