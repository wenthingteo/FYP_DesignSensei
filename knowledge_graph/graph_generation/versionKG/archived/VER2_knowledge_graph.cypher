// 1. FIRST CLEAR EXISTING DATA (if testing)
MATCH (n) DETACH DELETE n;

// 2. CREATE CONSTRAINTS
CREATE CONSTRAINT principle_name IF NOT EXISTS FOR (n:Principle) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT pattern_name IF NOT EXISTS FOR (n:Pattern) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (n:Concept) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT practice_name IF NOT EXISTS FOR (n:Practice) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT component_name IF NOT EXISTS FOR (n:Component) REQUIRE n.name IS UNIQUE;

// 3. CREATE ALL NODES FIRST (using MERGE for constrained labels)
MERGE (:Principle {name: "SOLID Principles", description: "Five basic object-oriented design principles"});
MERGE (:Principle {name: "Single Responsibility Principle", description: "A class should have only one reason to change"});
MERGE (:Principle {name: "Open-Closed Principle", description: "Software entities should be open for extension but closed for modification"});
MERGE (:Principle {name: "Liskov Substitution Principle", description: "Objects of a superclass should be replaceable with objects of subclasses"});
MERGE (:Principle {name: "Interface Segregation Principle", description: "Clients should not be forced to depend on interfaces they do not use"});
MERGE (:Principle {name: "Dependency Inversion Principle", description: "Depend on abstractions, not on concrete implementations"});
MERGE (:Component {name: "Class", description: "Blueprint for creating objects"});
MERGE (:Component {name: "Method", description: "Function within a class"});
MERGE (:Practice {name: "Code Style", description: "Standards for formatting and organizing code"});
MERGE (:Concept {name: "Inheritance", description: "A mechanism where a new class derives from an existing class"});
MERGE (:Concept {name: "Polymorphism", description: "The ability of different classes to be treated as instances of a common superclass"});
MERGE (:Concept {name: "Abstract Base Class", description: "A class that defines an interface for subclasses"});
MERGE (:Pattern {name: "Inheritance", description: "A pattern enabling new classes to derive from existing classes"});
MERGE (:Pattern {name: "Delegation", description: "A pattern where an object handles a request by passing it to a second object"});
MERGE (:Component {name: "Layer", description: "An architectural level in software design that separates concerns"});
MERGE (:Component {name: "Parser", description: "A class responsible for parsing input data"});
MERGE (:Component {name: "ParserImplementation", description: "Concrete implementation of the Parser interface"});
MERGE (:Component {name: "ParserRubyImplementation", description: "A specific parser implementation for Ruby language"});
MERGE (:Concept {name: "Interface Segregation", description: "Design approach favoring multiple specific interfaces over a single general-purpose interface"});
MERGE (:Concept {name: "Abstraction", description: "A fundamental concept where details are hidden behind simplified interfaces"});
MERGE (:Concept {name: "Cohesion", description: "Degree to which elements of a module belong together"});
MERGE (:Concept {name: "Coupling", description: "Degree of interdependence between software modules"});
MERGE (:Component {name: "High-level modules", description: "Modules that contain the core logic and depend on abstractions"});
MERGE (:Component {name: "Low-level modules", description: "Modules that implement details and depend on abstractions"});
MERGE (:Component {name: "OutletInterface", description: "An abstraction representing different power outlets"});
MERGE (:Component {name: "Lamp", description: "A device that can be turned on or off, depends on OutletInterface"});
MERGE (:Principle {name: "DRY", description: "Don't Repeat Yourself, a principle to reduce redundancy through abstractions or functional decomposition"});
MERGE (:Principle {name: "YAGNI", description: "You Aren't Gonna Need It, a principle to avoid building unnecessary features"});
MERGE (:Principle {name: "KISS", description: "Keep It Simple, a principle to avoid unnecessary complexity"});
MERGE (:Principle {name: "Occam's Razor", description: "A principle favoring simplicity in design"});
MERGE (:Principle {name: "GRASP", description: "General Responsibility Assignment Software Patterns, guiding principles for assigning responsibilities"});
MERGE (:Pattern {name: "Design Patterns", description: "Reusable solutions to common software design problems"});

// 4. CREATE RELATIONSHIPS (after all nodes exist)
MATCH (s:Principle {name: "SOLID Principles"})
MATCH (sr:Principle {name: "Single Responsibility Principle"})
MERGE (s)-[:CONTAINS]->(sr);

MATCH (s:Principle {name: "SOLID Principles"})
MATCH (ocp:Principle {name: "Open-Closed Principle"})
MERGE (s)-[:CONTAINS]->(ocp);

MATCH (s:Principle {name: "SOLID Principles"})
MATCH (lsp:Principle {name: "Liskov Substitution Principle"})
MERGE (s)-[:CONTAINS]->(lsp);

MATCH (s:Principle {name: "SOLID Principles"})
MATCH (isp:Principle {name: "Interface Segregation Principle"})
MERGE (s)-[:CONTAINS]->(isp);

MATCH (s:Principle {name: "SOLID Principles"})
MATCH (dip:Principle {name: "Dependency Inversion Principle"})
MERGE (s)-[:CONTAINS]->(dip);

MATCH (c:Component {name: "Class"})
MATCH (m:Component {name: "Method"})
MERGE (c)-[:IS_PART_OF]->(m);

MATCH (p:Principle {name: "Open-Closed Principle"})
MATCH (i:Concept {name: "Inheritance"})
MERGE (p)-[:SUPPORTS]->(i);

MATCH (p:Principle {name: "Liskov Substitution Principle"})
MATCH (i:Concept {name: "Inheritance"})
MERGE (p)-[:DEPENDS_ON]->(i);

MATCH (abc:Component {name: "Abstract Base Class"})
MATCH (iface:Concept {name: "Interface"})
MERGE (abc)-[:IS_PART_OF]->(iface);

MATCH (pi:Component {name: "ParserImplementation"})
MATCH (pr:Component {name: "ParserRubyImplementation"})
MERGE (pi)-[:IS_A]->(pr);