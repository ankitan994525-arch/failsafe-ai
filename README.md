# FailSafe AI – Predictive Maintenance System

FailSafe AI is an AI-powered full-stack application that monitors industrial machine sensor data (temperature, vibration, RPM) and predicts machine health risks in real time.

This system helps industries detect failures early and reduce downtime using a rule-based predictive maintenance approach.

## 🚀 Features
- Real-time machine health prediction
- Risk classification (Safe / Medium / High)
- Multi-sensor monitoring (Temperature, Vibration, RPM)
- Interactive dashboard visualization
- Risk trend graph using Chart.js
- History tracking with MongoDB

## 🧠 How It Works
The system collects sensor inputs and sends them to a FastAPI backend.  
A rule-based AI engine calculates a risk score:

- Temperature > 80°C → +30 risk  
- Vibration > 1.5 mm/s → +40 risk  
- RPM > 5000 → +20 risk  

### Risk Levels:
- 0–39 → Safe  
- 40–70 → Medium Risk  
- 70+ → High Risk  

The results are stored in MongoDB and displayed on a React dashboard.

## 🏗️ Tech Stack
- Frontend: React.js + Tailwind CSS  
- Backend: FastAPI (Python)  
- Database: MongoDB  
- Visualization: Chart.js  

## 🔗 API Endpoints
- POST `/machine-health/check` → Predict machine risk  
- GET `/machine-health/history` → View past records  
- GET `/machine-health/stats` → Analytics  
- GET `/machine-health/export` → Export data  

## 📊 System Flow
Sensor Input → FastAPI API → Risk Engine → MongoDB → Dashboard Visualization

## 👨‍💻 Author
Ankita
