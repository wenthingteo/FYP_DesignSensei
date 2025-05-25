// Knowledge Graph Creation Script
// Generated from software design documents
// Total queries: 5

CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT principle_name IF NOT EXISTS FOR (n:Principle) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT pattern_name IF NOT EXISTS FOR (n:Pattern) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (n:Concept) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT practice_name IF NOT EXISTS FOR (n:Practice) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT component_name IF NOT EXISTS FOR (n:Component) REQUIRE n.name IS UNIQUE;

// Queries from 12-design-principles.pdf
CREATE (:Principle {name: "SOLID Principles", description: "Five basic object-oriented design principles"})",
    "CREATE (:Principle {name: "Single Responsibility Principle", description: "A class should have only one reason to change"})",
    "CREATE (:Principle {name: "Open-Closed Principle", description: "Software entities should be open for extension but closed for modification"})",
    "CREATE (:Principle {name: "Liskov Substitution Principle", description: "Objects of a superclass should be replaceable with objects of subclasses"})",
    "CREATE (:Principle {name: "Interface Segregation Principle", description: "Clients should not be forced to depend on interfaces they do not use"})",
    "CREATE (:Principle {name: "Dependency Inversion Principle", description: "Depend on abstractions, not on concrete implementations"})",
    "CREATE (:Component {name: "Class", description: "Blueprint for creating objects"})",
    "CREATE (:Component {name: "Method", description: "Function within a class"})",
    "CREATE (:Practice {name: "Code Style", description: "Standards for formatting and organizing code"})",
    "CREATE (s:Principle {name: "SOLID Principles"})-[:CONTAINS]->(sr:Principle {name: "Single Responsibility Principle"})",
    "CREATE (s)-[:CONTAINS]->(ocp:Principle {name: "Open-Closed Principle"})",
    "CREATE (s)-[:CONTAINS]->(lsp:Principle {name: "Liskov Substitution Principle"})",
    "CREATE (s)-[:CONTAINS]->(isp:Principle {name: "Interface Segregation Principle"})",
    "CREATE (s)-[:CONTAINS]->(dip:Principle {name: "Dependency Inversion Principle"})",
    "CREATE (c:Component {name: "Class"})-[:IS_PART_OF]->(m:Component {name: "Method"})
CREATE (:Principle {name: "Single Responsibility Principle", description: "A class should have only one reason to change"})",
    "CREATE (:Principle {name: "Open-Closed Principle", description: "Software entities should be open for extension but closed for modification"})",
    "CREATE (:Principle {name: "Liskov Substitution Principle", description: "Objects of a superclass should be replaceable with objects of subclasses"})",
    "CREATE (:Concept {name: "Inheritance", description: "A mechanism where a new class derives from an existing class"})",
    "CREATE (:Concept {name: "Polymorphism", description: "The ability of different classes to be treated as instances of a common superclass"})",
    "CREATE (:Concept {name: "Abstract Base Class", description: "A class that defines an interface for subclasses"})",
    "CREATE (:Pattern {name: "Inheritance", description: "A pattern enabling new classes to derive from existing classes"})",
    "CREATE (:Pattern {name: "Delegation", description: "A pattern where an object handles a request by passing it to a second object"})",
    "CREATE (:Component {name: "Layer", description: "An architectural level in software design that separates concerns"})
CREATE (:Principle {name: "OpenClosed Principle", description: "Design principle that promotes software entities being open for extension but closed for modification"})",
    "CREATE (:Principle {name: "Liskov Substitution Principle", description: "Design principle that states objects of subtypes should be replaceable with objects of supertypes without affecting correctness"})",
    "CREATE (:Concept {name: "Inheritance", description: "Object-oriented concept allowing new classes to extend existing classes"})",
    "CREATE (:Concept {name: "Polymorphism", description: "Ability of different classes to be treated as instances of a common superclass, typically via interfaces"})",
    "CREATE (:Component {name: "Abstract Base Class", description: "A class that defines a common interface for its subclasses"})",
    "CREATE (:Component {name: "Parser", description: "A class responsible for parsing input data"})",
    "CREATE (:Component {name: "ParserImplementation", description: "Concrete implementation of the Parser interface"})",
    "CREATE (:Component {name: "ParserRubyImplementation", description: "A specific parser implementation for Ruby language"})",
    "MATCH (p:Principle {name: "OpenClosed Principle"}), (i:Concept {name: "Inheritance"}) CREATE (p)-[:SUPPORTS]->(i)",
    "MATCH (p:Principle {name: "Liskov Substitution Principle"}), (i:Concept {name: "Inheritance"}) CREATE (p)-[:DEPENDS_ON]->(i)",
    "MATCH (abc:Component {name: "Abstract Base Class"}), (iface:Concept {name: "Interface"}) CREATE (abc)-[:IS_PART_OF]->(iface)",
    "MATCH (p:Parser), (pi:Component {name: "ParserImplementation"}) CREATE (p)-[:IS_A]->(pi)",
    "MATCH (pi:Component {name: "ParserImplementation"}), (pr:Component {name: "ParserRubyImplementation"}) CREATE (pi)-[:IS_A]->(pr)
CREATE (:Principle {name: "Liskov Substitution Principle", description: "A principle stating that objects of a superclass should be replaceable with objects of subclasses without affecting correctness"})",
    "CREATE (:Principle {name: "Interface Segregation Principle", description: "A principle stating that clients should not be forced to depend on interfaces they do not use"})",
    "CREATE (:Principle {name: "Dependency Inversion Principle", description: "A principle stating that high-level modules should not depend on low-level modules, but both should depend on abstractions"})",
    "CREATE (:Concept {name: "Interface Segregation", description: "Design approach favoring multiple specific interfaces over a single general-purpose interface"})",
    "CREATE (:Concept {name: "Abstraction", description: "A fundamental concept where details are hidden behind simplified interfaces"})",
    "CREATE (:Concept {name: "Cohesion", description: "Degree to which elements of a module belong together"})",
    "CREATE (:Concept {name: "Coupling", description: "Degree of interdependence between software modules"})",
    "CREATE (:Component {name: "High-level modules", description: "Modules that contain the core logic and depend on abstractions"})",
    "CREATE (:Component {name: "Low-level modules", description: "Modules that implement details and depend on abstractions"})
CREATE (:Principle {name: "Dependency Inversion Principle", description: "A design principle that emphasizes decoupling high-level modules from low-level modules through abstractions"})",
    "CREATE (:Component {name: "OutletInterface", description: "An abstraction representing different power outlets"})",
    "CREATE (:Component {name: "Lamp", description: "A device that can be turned on or off, depends on OutletInterface"})",
    "CREATE (:Principle {name: "DRY", description: "Dont Repeat Yourself, a principle to reduce redundancy through abstractions or functional decomposition"})",
    "CREATE (:Principle {name: "YAGNI", description: "You Arent Gonna Need It, a principle to avoid building unnecessary features"})",
    "CREATE (:Principle {name: "KISS", description: "Keep It Simple, a principle to avoid unnecessary complexity"})",
    "CREATE (:Principle {name: "Occam's Razor", description: "A principle favoring simplicity in design"})",
    "CREATE (:Principle {name: "GRASP", description: "General Responsibility Assignment Software Patterns, guiding principles for assigning responsibilities"})",
    "CREATE (:Pattern {name: "Design Patterns", description: "Reusable solutions to common software design problems"})",
    "CREATE (:Principle {name: "SOLID", description: "A set of object-oriented design principles"})