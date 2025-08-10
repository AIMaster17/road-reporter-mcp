const mongoose = require('mongoose');
const mongoURI = 'PASTE_YOUR_CONNECTION_STRING_HERE';

mongoose.connect(mongoURI)
  .then(() => console.log('MCP Server successfully connected to MongoDB Atlas!'))
  .catch(err => console.error('MCP Connection error:', err));

const reportSchema = new mongoose.Schema({
  latitude: Number,
  longitude: Number,
  road_condition_type: String,
  severity: String,
  comments: String,
  timestamp: { type: Date, default: Date.now }
});

const Report = mongoose.model('Report', reportSchema);
module.exports = Report;