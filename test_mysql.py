
import os
import pymysql
from dotenv import load_dotenv

# Hent databaseindstillinger fra .env
load_dotenv()

try:
    # Opret forbindelse til MySQL
    connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        connect_timeout=5
    )

    print("SUCCESS! Forbindelse til MySQL oprettet.")

    # Find tabellerne i vores database
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

        print("\nTabeller i iot_monitoring:")

        for table in tables:
            print("-", table[0])

    connection.close()

except pymysql.MySQLError as error:
    print("FEJL: Kunne ikke forbinde til MySQL")
    print(error)
