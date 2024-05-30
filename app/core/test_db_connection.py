from postgres_database import PostgresSaver 

def main():
    db_saver = PostgresSaver()
    db_saver.test_connection()

if __name__ == "__main__":
    main()