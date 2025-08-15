import asyncio
from typing import Annotated
import os
from dotenv import load_dotenv
from textwrap import dedent

from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp.server.auth.provider import AccessToken
from pydantic import Field

from pymongo import MongoClient

# --- Load environment variables ---
load_dotenv()
TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER")
MONGO_URI = os.environ.get("MONGO_URI")

assert TOKEN is not None, "Please set AUTH_TOKEN in your .env file"
assert MY_NUMBER is not None, "Please set MY_NUMBER in your .env file"
assert MONGO_URI is not None, "Please set MONGO_URI in your .env file"

# --- Database Connection ---
client = MongoClient(MONGO_URI)
db = client.get_database("test")
reports_collection = db.get_collection("reports")
print("Successfully connected to MongoDB Atlas!")

# --- Auth Provider (from official starter) ---
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token, client_id="puch-client", scopes=["*"], expires_at=None
            )
        return None

# --- MCP Server Setup ---
mcp = FastMCP(
    "Road Condition Reporter MCP",
    auth=SimpleBearerAuthProvider(TOKEN),
)

# --- Tool Definitions ---

# Recommended "about" tool
@mcp.tool
async def about() -> dict[str, str]:
    server_name = "Road Condition Reporter MCP"
    server_description = dedent(
        """
        This MCP server provides tools to report and retrieve information about road conditions,
        primarily focused on issues like potholes, cracks, and waterlogging in Pune, India.
        """
    )
    return {"name": server_name, "description": server_description}

# **** THIS IS THE NEW TOOL WE ARE ADDING ****
@mcp.tool(description="Provides the public link to the interactive web app map.")
async def open_map_view() -> str:
    """Returns the link to the live web application map."""
    return "Here is the link to the live map of all road issues: https://road-reporter-webapp-production.up.railway.app/"

# Required "validate" tool
@mcp.tool
async def validate() -> str:
    return MY_NUMBER

# Our custom "add_road_report" tool
@mcp.tool(description="Adds a new road condition report to the database.")
async def add_road_report(
    latitude: Annotated[float, Field(description="The latitude of the report location.")],
    longitude: Annotated[float, Field(description="The longitude of the report location.")],
    road_condition_type: Annotated[str, Field(description="The type of road condition (e.g., Pothole, Crack).")],
    severity: Annotated[str, Field(description="The severity of the condition (e.g., Minor, Moderate, Severe).")],
    comments: Annotated[str, Field(description="Additional comments about the issue.")]
) -> str:
    try:
        report_document = {
            "latitude": latitude, "longitude": longitude,
            "road_condition_type": road_condition_type, "severity": severity,
            "comments": comments,
        }
        reports_collection.insert_one(report_document)
        return "✅ Successfully saved the new road report."
    except Exception as e:
        return f"❌ Error saving report: {e}"

# Our custom "get_all_reports" tool
@mcp.tool(description="Retrieves a summary of the most recent road condition reports.")
async def get_all_reports() -> str:
    try:
        recent_reports = reports_collection.find().sort("_id", -1)
        report_list = list(recent_reports)
        if not report_list: return "No road reports have been filed yet."
        
        response = f"Here are the {len(report_list)} most recent reports:\n"
        for i, report in enumerate(report_list):
            response += f"{i+1}. {report.get('road_condition_type', 'N/A')} ({report.get('severity', 'N/A')}) - Comments: {report.get('comments', 'None')}\n"
        return response
    except Exception as e:
        return f"❌ Error fetching reports: {e}"

# --- Run MCP Server (from official starter) ---
async def main():
    print("🚀 Starting MCP server on http://0.0.0.0:8086")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())