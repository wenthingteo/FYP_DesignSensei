# Software Design Sensei
A GraphRAG chatbot for teaching software design

Instruction to start the chatbot
1. FRONTEND
```
cd frontend
cd src
npm run start
```

2. BACKEND
```
cd backend
python manage.py runserver
```

Note
1. To check is the Neo4j DB has been keeping alive, use this query
MATCH (h:Heartbeat {id: "aura_keep_alive"})
RETURN h.lastUpdated AS lastUpdatedTimestamp, h.status AS status, h.id AS id

2. use http://127.0.0.1:3000/ to connect the chatbot
3. create virtual env
```
   a. python -m venv venv
   b. venv\Scripts\activate
```
___
## Knowledge Graph
1. Change Design Principle Domain label by removing UNKNOWNLABEL node
(name & SET need to change accordingly)

```
MATCH (n:UnknownLabel {name: 'CodeStructure Domain'})
REMOVE n:UnknownLabel
SET n:CodeStructureDomain
RETURN n.name, labels(n)
```

2. Find any node according their name

```
MATCH (n:UnknownLabel)
RETURN n
```

3. Find node relationship & graph
(change the name and a accordingly)

```
MATCH (a:DesignPattern {name: 'Filter Chain'})-[r]->(n)
RETURN r, n
```
