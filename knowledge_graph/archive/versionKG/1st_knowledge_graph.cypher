// Knowledge Graph Creation Script
// Generated from software design documents
// Total queries: 0

CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT principle_name IF NOT EXISTS FOR (n:Principle) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT pattern_name IF NOT EXISTS FOR (n:Pattern) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (n:Concept) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT practice_name IF NOT EXISTS FOR (n:Practice) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT component_name IF NOT EXISTS FOR (n:Component) REQUIRE n.name IS UNIQUE;

// Queries from 12-design-principles.pdf