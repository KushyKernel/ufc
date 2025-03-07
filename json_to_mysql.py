import json             # For working with JSON data
import mysql.connector  # For connecting to MySQL

def load_json_data(json_file):
    """
    Loads and returns data from the given JSON file.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def insert_data_into_mysql(data):
    """
    Connects to the MySQL database, creates the fighter_profiles table if it doesn't exist,
    clears any existing data, and inserts the new fighter records.
    """
    # Connect to the MySQL database
    conn = mysql.connector.connect(
        host='localhost',            # MySQL server address (change if remote)
        user='IrateKnight',          # Your MySQL username
        password='3Xh$cARqQk+Ssv70',   # Your MySQL password
        database='mma_project'       # The database you created earlier
    )
    cursor = conn.cursor()

    # Optional: Increase the InnoDB lock wait timeout for this session
    cursor.execute("SET innodb_lock_wait_timeout = 120")

    # Create the table if it doesn't exist
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS fighter_profiles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        ufc_url VARCHAR(255) NOT NULL,
        sherdog_url VARCHAR(255)
    );
    '''
    cursor.execute(create_table_query)
    conn.commit()  # Commit table creation

    # Clear existing data to avoid duplicates
    cursor.execute("DELETE FROM fighter_profiles")
    conn.commit()

    # Prepare the insert query
    insert_query = '''
    INSERT INTO fighter_profiles (name, ufc_url, sherdog_url)
    VALUES (%s, %s, %s)
    '''
    # Insert each fighter record into the table
    for fighter in data:
        cursor.execute(insert_query, (fighter['name'], fighter['ufc_url'], fighter['sherdog_url']))
    conn.commit()  # Commit all insertions

    # Clean up: close cursor and connection
    cursor.close()
    conn.close()
    print("Data successfully inserted into the MySQL database.")

def main():
    # Load the JSON data produced by the scraping script
    json_file = "merged_data.json"
    data = load_json_data(json_file)
    
    # Insert the loaded data into the MySQL database
    insert_data_into_mysql(data)

if __name__ == '__main__':
    main()
