import os
import json
import logging
import csv
from datetime import datetime
from dotenv import load_dotenv

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Load environment variables
load_dotenv()


def process_slack_archive(root_dir, output_csv):
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        csvwriter = csv.writer(csvfile)
        # Write header
        csvwriter.writerow(["Timestamp", "Channel", "User", "Message", "Datetime"])

        for channel_dir in os.listdir(root_dir):
            channel_path = os.path.join(root_dir, channel_dir)
            if os.path.isdir(channel_path):
                process_channel(channel_path, channel_dir, csvwriter)


def process_channel(channel_path, channel_name, csvwriter):
    for file_name in os.listdir(channel_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(channel_path, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                messages = json.load(file)
                for message in messages:
                    add_to_csv(message, channel_name, csvwriter)


def add_to_csv(message, channel_name, csvwriter):
    timestamp_float = float(message.get("ts", 0))
    timestamp_datetime = datetime.fromtimestamp(timestamp_float)

    user = message.get("user_profile", {}).get("real_name", "Unknown")
    text = message.get("text", "")[:2000]  # Limit text to 2000 characters

    csvwriter.writerow(
        [str(timestamp_float), channel_name, user, text, timestamp_datetime.isoformat()]
    )


def get_output_csv_path(slack_archive_path):
    # Get the directory name of the Slack archive
    archive_dir_name = os.path.basename(slack_archive_path)

    # Create the output filename
    output_filename = f"{archive_dir_name}_slack_messages.csv"

    # Ensure the ./data directory exists
    data_dir = "./data"
    os.makedirs(data_dir, exist_ok=True)

    # Construct the full output path
    output_path = os.path.join(data_dir, output_filename)

    return output_path


def main():
    slack_archive_path = os.getenv("SLACK_ARCHIVE_PATH")
    if not slack_archive_path:
        logger.error("SLACK_ARCHIVE_PATH environment variable is not set.")
        return

    output_csv = get_output_csv_path(slack_archive_path)

    logger.info(f"Starting to process Slack archive in {slack_archive_path}")
    process_slack_archive(slack_archive_path, output_csv)
    logger.info(f"Finished processing Slack archive. Output CSV: {output_csv}")

    print(
        f"""
CSV file has been created at: {output_csv}

To import this CSV into Notion:
1. Go to your Notion database
2. Click on the '...' menu in the top right corner
3. Select 'Merge with CSV'
4. Upload the generated CSV file
5. Map the columns to your Notion properties
6. Click 'Confirm' to start the import

Make sure your Notion database has the following properties:
- Timestamp (Title)
- Channel (Select)
- User (Text)
- Message (Text)
- Datetime (Date)

Adjust the property types as needed before importing.
    """
    )


if __name__ == "__main__":
    main()
