# SDbot
A GraphRAG chatbot for teaching software design

Instruction to start the chatbot
1. FRONTEND
cd frontend
cd src
npm run start
2. BACKEND
cd backend
python manage.py runserver

Note
1. To check is the Neo4j DB has been keeping alive, use this query
MATCH (h:Heartbeat {id: "aura_keep_alive"})
RETURN h.lastUpdated AS lastUpdatedTimestamp, h.status AS status, h.id AS id

2. use http://127.0.0.1:3000/ to connect the chatbot