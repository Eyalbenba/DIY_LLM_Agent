import os
import json
import logging
from pymongo import MongoClient
from datetime import datetime
def get_mongo_client(uri):
    client = MongoClient(uri)
    return client


def setup_logger(log_directory):
    """
    Set up a logger that writes to a file with the current date and time.

    Parameters:
    - log_directory: The directory where the log file will be stored.

    Returns:
    - logger: Configured logger instance.
    """
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Generate the log file name with the current date and time
    log_filename = datetime.now().strftime("scraped_data_%Y%m%d_%H%M%S.log")
    log_path = os.path.join(log_directory, log_filename)

    # Set up the logger
    logger = logging.getLogger("ScrapedDataLogger")
    logger.setLevel(logging.DEBUG)

    # Create a file handler for writing logs
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)

    # Create a console handler for outputting logs to the console (optional)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Set up log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
def process_instructables_data(client, instructables_scraped_data_dir, save_to_mongo=True):
    """
    Traverse the folder structure, with the first-level folders as databases, and second-level folders as collections.

    Parameters:
    - client: MongoDB client instance
    - instructables_scraped_data_dir: The root directory containing categories and subcategories
    - save_to_mongo: Boolean flag to control whether to actually save to MongoDB or just print the operations (for testing)
    """
    print(f"Starting to walk through directory: {instructables_scraped_data_dir}")

    # Traverse the first-level folder (this will be treated as the database name)
    for category_root, category_folders, _ in os.walk(instructables_scraped_data_dir):
        # The first iteration of os.walk includes the root, so skip processing it
        if category_root == instructables_scraped_data_dir:
            continue

        category = os.path.basename(category_root)  # First-level directory as category (db)
        print(f"\nProcessing category (database): {category}")

        # Create a new database for the category (first-level folder)
        db = client[category]
        print(f"Using database: {category}")

        # Traverse the second-level folders (collections)
        for subcategory_root, subcategory_folders, subcategory_files in os.walk(category_root):
            subcategory = os.path.basename(subcategory_root)  # Second-level folder as subcategory (collection)
            print(f"  Processing subcategory (collection): {subcategory}")

            # Create a collection for each subcategory (second-level folder)
            collection = db[subcategory]
            print(f"  Collection created for subcategory: {subcategory}")

            # Process each file in the subcategory folder
            for file in subcategory_files:
                file_path = os.path.join(subcategory_root, file)
                print(f"    Processing file: {file} at {file_path}")

                # Check if the file is a JSON file
                if file.endswith(".json"):
                    print(f"    File {file} is a JSON file. Attempting to load...")

                    # Attempt to load the JSON file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as json_file:
                            json_content = json.load(json_file)
                            print(f"    Successfully loaded JSON file: {file}")

                            # Insert the JSON content as a document into the collection
                            if save_to_mongo:
                                collection.insert_one(json_content)
                                print(f"    Inserted JSON content into MongoDB collection '{subcategory}'")
                            else:
                                print(
                                    f"    [TEST MODE] JSON content would be inserted into MongoDB collection '{subcategory}'")

                    except json.JSONDecodeError as e:
                        print(f"    Failed to parse JSON file: {file}. Error: {e}")
                    except Exception as e:
                        print(f"    An error occurred while processing file {file}. Error: {e}")
                else:
                    print(f"    File {file} is not a JSON file. Skipping...")

    print("Data processing complete.")



def insert_all_json_data(client, directory_path, log_directory, save_to_mongo=True):
    """
    Traverse the input directory and insert all JSON files into a single MongoDB collection.

    Parameters:
    - client: MongoDB client instance
    - directory_path: The root directory containing JSON files
    - log_directory: Directory to save the log file
    - save_to_mongo: Boolean flag to control whether to actually save to MongoDB or just log the operations (for testing)
    """
    # Set up the logger
    logger = setup_logger(log_directory)

    # Use the database "all_scraped_data"
    db = client['all_scraped_data']
    # Use the collection "all_data"
    collection = db['all_data']

    logger.info(f"Starting to walk through directory: {directory_path}")

    # Traverse the directory structure and find all JSON files
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                # Get the parts of the path
                path_parts = file_path.split(os.sep)

                # Extract the last three parts, joining them with the correct path separator
                cat_subcat_file_path = os.path.join(*path_parts[-3:])
                logger.info(f"Processing file: {file} at {cat_subcat_file_path}")

                # Attempt to load the JSON file
                try:
                    with open(file_path, 'r', encoding='utf-8') as json_file:
                        json_content = json.load(json_file)
                        logger.info(f"  Successfully loaded JSON file: {file}")

                        # Insert the JSON content as a document into the collection
                        if save_to_mongo:
                            collection.insert_one(json_content)
                            logger.info(f"  Inserted JSON content into 'all_data' collection")
                        else:
                            logger.info(f"  [TEST MODE] JSON content would be inserted into 'all_data' collection")

                except json.JSONDecodeError as e:
                    logger.error(f"  Failed to parse JSON file: {file}. Error: {e}")
                except Exception as e:
                    logger.error(f"  An error occurred while processing file {file}. Error: {e}")

    logger.info("Data processing complete.")


# Example usage
if __name__ == "__main__":
    # Connect to MongoDB (replace with your connection details)
    print("Connecting to MongoDB...")
    uri = "mongodb+srv://Eyal:Mongodb1997@cluster0.iw8ap.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = get_mongo_client(uri)
    print("Connected to MongoDB.")


    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    # # Define the directory containing JSON files
    # directory_path = '/Users/eyalbenbarouch/Documents/My Stuff/Handyman_LLM_Agent/Instructables_Scraped_Data'
    #
    # # Define the log directory
    # log_directory = '/Users/eyalbenbarouch/Documents/My Stuff/Handyman_LLM_Agent/run_logs/data_logs'
    #
    # # Call the function to insert all JSON data (pass save_to_mongo=False to test without saving)
    # insert_all_json_data(client, directory_path, log_directory, save_to_mongo=False)

    # Close the MongoDB connection
    print("Closing MongoDB connection...")
    client.close()
    print("MongoDB connection closed.")
