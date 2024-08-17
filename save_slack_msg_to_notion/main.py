import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

load_dotenv()

# Notion setup
notion = Client(auth=os.getenv("NOTION_INTEGRATION_SECRET"))
database_id = os.getenv("NOTION_DB_ID")


def process_slack_archive(root_dir):
    for channel_dir in os.listdir(root_dir):
        channel_path = os.path.join(root_dir, channel_dir)
        if os.path.isdir(channel_path):
            process_channel(channel_path, channel_dir)


def process_channel(channel_path, channel_name):
    for file_name in os.listdir(channel_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(channel_path, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                messages = json.load(file)
                for index, message in enumerate(messages, start=1):
                    logger.info(f"Processing message {index} of {len(messages)} in channel {channel_name}")
                    add_to_notion(message, channel_name)
            logger.info(f"Finished processing {len(messages)} messages in channel {channel_name}")


def add_to_notion(message, channel_name):
    # Map message content to Notion properties
    timestamp_float = float(message.get("ts", 0))
    timestamp_datetime = datetime.fromtimestamp(timestamp_float)
    properties = {
        "Timestamp": {"title": [{"text": {"content": str(timestamp_float)}}]},
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
        },  # Note Notion's limit
        "Datetime": {"date": {"start": timestamp_datetime.isoformat()}},
    }

    # Add page to Notion database
    notion.pages.create(parent={"database_id": database_id}, properties=properties)


def main():
    root_directory = os.getenv("SLACK_ARCHIVE_PATH")
    logger.info(f"Starting to process Slack archive in {root_directory}")
    process_slack_archive(root_directory)
    logger.info("Finished processing Slack archive")
