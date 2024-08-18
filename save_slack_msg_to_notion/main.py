import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

load_dotenv()

# Notion setup
notion = Client(auth=os.getenv("NOTION_INTEGRATION_SECRET"))
database_id = os.getenv("NOTION_DB_ID")
exclude_channel_list = os.getenv("EXCLUDE_CHANNEL_LIST").split(",")


def get_existing_timestamps():
    existing_timestamps = set()
    has_more = True
    start_cursor = None

    while has_more:
        response = notion.databases.query(
            database_id=database_id,
            start_cursor=start_cursor,
            page_size=100,  # Adjust as needed
        )
        for page in response["results"]:
            timestamp = page["properties"]["Timestamp"]["title"][0]["text"]["content"]
            existing_timestamps.add(timestamp)

        has_more = response["has_more"]
        start_cursor = response.get("next_cursor")

    logger.info(
        f"Retrieved {len(existing_timestamps)} existing timestamps from the database."
    )
    return existing_timestamps


def process_slack_archive(root_dir, existing_timestamps):
    for channel_dir in os.listdir(root_dir):
        if channel_dir in exclude_channel_list:
            continue
        channel_path = os.path.join(root_dir, channel_dir)
        if os.path.isdir(channel_path):
            process_channel(channel_path, channel_dir, existing_timestamps)


def process_channel(channel_path, channel_name, existing_timestamps):
    for file_name in os.listdir(channel_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(channel_path, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                messages = json.load(file)
                for index, message in enumerate(messages, start=1):
                    logger.info(
                        f"Processing message {index} of {len(messages)} in channel {channel_name}"
                    )
                    add_to_notion(message, channel_name, existing_timestamps)


def add_to_notion(message, channel_name, existing_timestamps):
    timestamp_float = float(message.get("ts", 0))
    timestamp_str = str(timestamp_float)

    if timestamp_str in existing_timestamps:
        logger.info(f"Skipping duplicate message with timestamp {timestamp_str}")
        return

    timestamp_datetime = datetime.fromtimestamp(timestamp_float)

    properties = {
        "Timestamp": {"title": [{"text": {"content": timestamp_str}}]},
        "Channel": {"select": {"name": channel_name}},
        "User": {
            "rich_text": [
                {
                    "text": {
                        "content": message.get("user_profile", {}).get(
                            "real_name", "Unknown"
                        )
                    }
                }
            ]
        },
        "Message": {
            "rich_text": [{"text": {"content": message.get("text", "")[:2000]}}]
        },
        "Datetime": {"date": {"start": timestamp_datetime.isoformat()}},
    }

    try:
        response = notion.pages.create(
            parent={"database_id": database_id}, properties=properties
        )
        logger.debug(f"Notion API Response: {response}")
        existing_timestamps.add(timestamp_str)  # Add the new timestamp to the set
    except APIResponseError as e:
        logger.error(f"Notion API Error: {str(e)}")
        logger.error(f"Error details: {e.body}")


def main():
    root_directory = os.getenv("SLACK_ARCHIVE_PATH")
    logger.info(f"Starting to process Slack archive in {root_directory}")

    existing_timestamps = get_existing_timestamps()
    process_slack_archive(root_directory, existing_timestamps)

    logger.info("Finished processing Slack archive")
