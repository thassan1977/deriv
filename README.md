Neural Fraud Detection EngineA high-performance backend service designed to 
analyze transactional data in real-time, leveraging machine learning to 
detect fraudulent behavior and provide actionable insights for forensic investigators.

Features
Real-time Analytics: WebSocket-driven live feed of incoming cases.
AI Narrative Analysis: Automated summary of behavioral flags and transaction anomalies.
Case Management: Comprehensive workflow for approving or blocking transactions based on risk probability.
Command Center UI: High-density dashboard for SOC investigators.

Technology StackBackend: Java 17+, Spring Boot
Database: PostgreSQL
Real-time: WebSockets
AI module: Python
Frontend: React, Material-UI, Recharts

# Clone the repository
git clone https://github.com/yourusername/fraud-detection-engine.git

# Navigate to the project directory
cd fraud-detection-engine

# Build the project
mvn clean package

# Run the application
java -jar target/fraud-detection-engine-0.0.1-SNAPSHOT.jar
API Documentation
   Endpoint          Method     Description
   /api/cases        GET        Retrieve all active fraud cases.
   /api/cases/{id}   GETGet     detailed analysis for a specific case.
   /api/stats        GETGet     real-time statistics (Blocked/Approved/Manual).


# there are three branches:
1- main : for java spring boot app.
2- python-ai: for populating data in DB and for publishig transactions to redis queue on java and to do the ai analysis part.
2- dashboard: a small react (2 screens) for showing current dashboard stats in realtime and check individual case to approve or block it.
