const Report = require('../db.js');

const addRoadReport = {
    name: "add_road_report",
    description: "Adds a new road condition report. Requires latitude, longitude, condition type, severity, and comments.",
    run: async (latitude, longitude, road_condition_type, severity, comments) => {
        try {
            const reportData = { latitude, longitude, road_condition_type, severity, comments };
            const newReport = new Report(reportData);
            await newReport.save();
            return "Successfully saved the new road report.";
        } catch (error) {
            return "Sorry, there was an error saving the report.";
        }
    },
};

const getAllReports = {
    name: "get_all_reports",
    description: "Retrieves a summary of all road condition reports.",
    run: async () => {
        try {
            const reports = await Report.find({}).sort({ timestamp: -1 }).limit(5);
            if (reports.length === 0) return "No reports found.";

            let response = `Found ${reports.length} recent reports:\n`;
            reports.forEach((r, i) => {
                response += `${i + 1}. ${r.road_condition_type} (${r.severity}) - Comments: ${r.comments}\n`;
            });
            return response;
        } catch (error) {
            return "Sorry, there was an error fetching reports.";
        }
    },
};

module.exports = [addRoadReport, getAllReports];