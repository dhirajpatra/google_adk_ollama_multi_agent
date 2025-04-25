# tools/calendar_tool.py

from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field
import csv
import os
from datetime import datetime
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)

class CalendarToolArgs(BaseModel):
    pass  # Currently no arguments, but good to have for potential future use

def check_calendar(tool_call_id: Optional[str] = None) -> dict:
    """Checks the calendar for meetings scheduled for today's date.

    Returns:
        dict: A dictionary with a 'status' key ('success' or 'error') and a 'report'
              key containing the list of meetings if successful, or an 'error_message'
              if no meetings are found or an error occurs.
    """
    today = datetime.today().strftime("%Y-%m-%d")
    file_path = os.path.join(os.path.dirname(__file__), "calendar.csv")
    logging.info(f"[check_calendar] Checking calendar at {file_path} for meetings on {today}")
    try:
        meetings = []
        if os.path.exists(file_path):
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                meetings = [row['meeting'] for row in reader if row.get('date') == today]
        else:
            logging.warning(f"[check_calendar] Calendar file not found at {file_path}.")
            return {"status": "error", "error_message": f"Calendar file not found."}

        if meetings:
            logging.info(f"[check_calendar] Meetings on {today}: {meetings}")
            return {"status": "success", "report": f"Meetings on {today}: {', '.join(meetings)}"}
        else:
            logging.info(f"[check_calendar] No meetings found for {today}.")
            return {"status": "success", "report": f"No meetings scheduled for today ({today})."}

    except Exception as e:
        logging.error(f"[check_calendar] Error reading calendar: {e}")
        return {"status": "error", "error_message": f"Error reading calendar: {str(e)}"}

# ADK function tool
calendar_tool = FunctionTool(func=check_calendar)