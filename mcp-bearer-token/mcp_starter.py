import os
import uvicorn
from pymongo import MongoClient
from mcp import MCP, Tool, Field
from annotated_types import Annotated
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Database Connection ---
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env file")

client = MongoClient(MONGO_URI)
db = client.get_database("test")
reports_collection = db.get_collection("reports")
print("Successfully connected to MongoDB Atlas!")


# --- MCP Server Setup ---
mcp = MCP(
    auth_token=os.getenv("AUTH_TOKEN"),
)

# --- Tool Definitions ---

# **** THIS IS THE NEW TOOL ****
@mcp.tool(
    description="Validates the user by returning the registered phone number. This is a verification tool."
)
async def validate_user() -> str:
    """Returns the phone number stored in the MY_NUMBER environment variable."""
    my_number = os.getenv("MY_NUMBER")
    if my_number:
        return f"Validation successful. Registered number is {my_number}."
    else:
        return "MY_NUMBER is not configured on this server."

@mcp.tool(
    description="Adds a new road condition report to the database. Requires latitude, longitude, condition type, severity, and comments."
)
async def add_road_report(
    latitude: Annotated[float, Field(description="The latitude of the report location.")],
    longitude: Annotated[float, Field(description="The longitude of the report location.")],
    road_condition_type: Annotated[str, Field(description="The type of road condition (e.g., Pothole, Crack).")],
    severity: Annotated[str, Field(description="The severity of the condition (e.g., Minor, Moderate, Severe).")],
    comments: Annotated[str, Field(description="Additional comments about the issue.")]
) -> str:
    """Adds a new road report to the database."""
    try:
        report_document = {
            "latitude": latitude,
            "longitude": longitude,
            "road_condition_type": road_condition_type,
            "severity": severity,
            "comments": comments,
        }
        reports_collection.insert_one(report_document)
        return "✅ Successfully saved the new road report."
    except Exception as e:
        print(f"Error saving report: {e}")
        return "❌ Sorry, there was an error saving the report."

@mcp.tool(
    description="Retrieves a summary of the most recent road condition reports from the database."
)
async def get_all_reports() -> str:
    """Gets a summary of all road reports."""
    try:
        recent_reports = reports_collection.find().sort("_id", -1).limit(5)
        report_list = list(recent_reports)

        if not report_list:
            return "No road reports have been filed yet."

        response = f"Here are the {len(report_list)} most recent reports:\n\n"
        for i, report in enumerate(report_list):
            response += f"{i + 1}. {report.get('road_condition_type', 'N/A')} ({report.get('severity', 'N/A')}) - Comments: {report.get('comments', 'None')}\n"
        
        return response
    except Exception as e:
        print(f"Error fetching reports: {e}")
        return "❌ Sorry, there was an error fetching the reports."


# --- Main entry point to run the server ---
if __name__ == "__main__":
    uvicorn.run(
        "mcp_starter:mcp.app",
        host="0.0.0.0",
        port=8086,
    )