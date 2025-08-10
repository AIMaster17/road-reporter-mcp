import os
import uvicorn
from pymongo import MongoClient
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from typing import List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
MY_NUMBER = os.getenv("MY_NUMBER")

# --- Database Connection ---
client = MongoClient(MONGO_URI)
db = client.get_database("test")
reports_collection = db.get_collection("reports")
print("Successfully connected to MongoDB Atlas!")

# Create the FastAPI app
app = FastAPI()

# --- Tool Logic (our original functions) ---
def add_road_report_logic(latitude, longitude, road_condition_type, severity, comments):
    report_document = {
        "latitude": latitude, "longitude": longitude,
        "road_condition_type": road_condition_type, "severity": severity,
        "comments": comments,
    }
    reports_collection.insert_one(report_document)
    return "✅ Successfully saved the new road report."

def get_all_reports_logic():
    recent_reports = reports_collection.find().sort("_id", -1).limit(5)
    report_list = list(recent_reports)
    if not report_list: return "No road reports found."
    response = f"Here are the {len(report_list)} most recent reports:\n\n"
    for i, report in enumerate(report_list):
        response += f"{i + 1}. {report.get('road_condition_type', 'N/A')} ({report.get('severity', 'N/A')}) - Comments: {report.get('comments', 'None')}\n"
    return response

def validate_user_logic():
    return f"Validation successful. Registered number is {MY_NUMBER}." if MY_NUMBER else "MY_NUMBER is not configured."

# --- MCP Server Endpoint ---
class McpRequest(BaseModel):
    method: str
    params: List[Any]

@app.post("/mcp")
async def mcp_endpoint(request: Request, body: McpRequest):
    # 1. Check Authentication
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 2. Route to the correct tool based on the method name
    method = body.method
    params = body.params
    result = ""

    try:
        if method == "add_road_report":
            result = add_road_report_logic(*params)
        elif method == "get_all_reports":
            result = get_all_reports_logic()
        elif method == "validate_user":
            result = validate_user_logic()
        else:
            raise HTTPException(status_code=404, detail="Method not found")
        
        # 3. Return the successful result
        return {"result": result}
        
    except Exception as e:
        # 4. Return an error if something goes wrong
        return {"error": str(e)}

# --- Main entry point for Uvicorn ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8086)