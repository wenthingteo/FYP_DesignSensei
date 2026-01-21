"""
Management command to populate ground truth database with comprehensive software design questions
Usage: python manage.py populate_ground_truth
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import GroundTruth


class Command(BaseCommand):
    help = 'Populate ground truth database with verified software design questions and answers'

    def handle(self, *args, **options):
        self.stdout.write('Populating ground truth database...')

        ground_truths = [
            # Domain-Driven Design (DDD)
            {
                "question": "What is Domain-Driven Design?",
                "ground_truth": "Domain-Driven Design (DDD) is a software development approach that focuses on modeling software to match the business domain. It emphasizes collaboration between technical experts and domain experts to create a shared understanding. Key concepts include: Bounded Contexts (clear boundaries between different parts of the system), Entities (objects with unique identity), Value Objects (immutable objects defined by their attributes), Aggregates (clusters of related objects), Repositories (abstraction for data access), and the Ubiquitous Language (shared vocabulary between developers and domain experts).",
                "context": "Software design methodology",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is a bounded context in DDD?",
                "ground_truth": "A Bounded Context is a central pattern in Domain-Driven Design that defines explicit boundaries within which a particular domain model applies. Each bounded context has its own ubiquitous language and model that is consistent within its boundaries but may differ from other contexts. This helps manage complexity in large systems by allowing different parts of the system to use different models for the same concept. For example, a 'Customer' in the Sales context might have different attributes and behaviors than a 'Customer' in the Support context.",
                "context": "DDD pattern",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is an aggregate in Domain-Driven Design?",
                "ground_truth": "An Aggregate is a cluster of domain objects (entities and value objects) that are treated as a single unit for data changes. Each aggregate has a root entity called the Aggregate Root, which is the only member of the aggregate that outside objects can hold references to. The aggregate root ensures the consistency of changes within the aggregate boundary. For example, an Order aggregate might contain OrderLine entities, but external code can only access OrderLines through the Order root. This enforces consistency and encapsulation.",
                "context": "DDD tactical pattern",
                "verified": True,
                "created_by": "system"
            },
            
            # Design Patterns
            {
                "question": "What is the Repository pattern?",
                "ground_truth": "The Repository pattern mediates between the domain and data mapping layers, acting like an in-memory collection of domain objects. It provides a more object-oriented view of the persistence layer and encapsulates the logic required to access data sources. Benefits include: separation of concerns between business logic and data access, centralized data access logic, easier unit testing through mocking, and abstraction from specific data storage technology. A typical implementation includes interfaces like IUserRepository with methods such as GetById(), GetAll(), Add(), Update(), and Delete().",
                "context": "Data access pattern",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is the Singleton pattern?",
                "ground_truth": "The Singleton pattern ensures that a class has only one instance throughout the application and provides a global point of access to that instance. It's useful for managing shared resources like database connections, configuration settings, or logging. Implementation involves: a private constructor to prevent direct instantiation, a private static instance variable, and a public static method (often called GetInstance) that returns the single instance. However, Singletons can make testing difficult and create hidden dependencies, so they should be used carefully. Modern alternatives include dependency injection containers.",
                "context": "Creational design pattern",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is the Strategy pattern?",
                "ground_truth": "The Strategy pattern defines a family of algorithms, encapsulates each one, and makes them interchangeable. It lets the algorithm vary independently from clients that use it. This pattern is useful when you have multiple ways to perform an operation and want to choose the appropriate one at runtime. For example, a payment processing system might have different strategies for CreditCardPayment, PayPalPayment, and BankTransferPayment. Each strategy implements a common PaymentStrategy interface, and the client can switch between strategies without changing its code.",
                "context": "Behavioral design pattern",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is the Observer pattern?",
                "ground_truth": "The Observer pattern defines a one-to-many dependency between objects so that when one object (the subject) changes state, all its dependents (observers) are notified and updated automatically. This pattern is fundamental to event-driven programming and the MVC architecture. Key components include: Subject (maintains list of observers and provides methods to attach/detach them), Observer (defines an update interface), ConcreteSubject (stores state and notifies observers of changes), and ConcreteObserver (implements the update interface). Common uses include GUI event handling, pub-sub systems, and reactive programming.",
                "context": "Behavioral design pattern",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is the Factory pattern?",
                "ground_truth": "The Factory pattern provides an interface for creating objects without specifying their exact classes. It delegates the instantiation logic to subclasses or factory methods. There are several variations: Simple Factory (a class with a method that creates objects based on parameters), Factory Method (defines an interface for creating objects but lets subclasses decide which class to instantiate), and Abstract Factory (provides an interface for creating families of related objects). Benefits include loose coupling, easier testing, and centralized object creation logic. For example, a DocumentFactory might create PDFDocument, WordDocument, or ExcelDocument based on file type.",
                "context": "Creational design pattern",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is the Decorator pattern?",
                "ground_truth": "The Decorator pattern attaches additional responsibilities to an object dynamically. It provides a flexible alternative to subclassing for extending functionality. Decorators wrap the original object and add new behaviors while maintaining the same interface. For example, in a coffee shop system, you might have a basic Coffee class and decorators like MilkDecorator, SugarDecorator, and WhipDecorator that can be combined in any way. Each decorator adds its own price and description while delegating to the wrapped object. This follows the Open/Closed Principle - open for extension, closed for modification.",
                "context": "Structural design pattern",
                "verified": True,
                "created_by": "system"
            },
            
            # SOLID Principles
            {
                "question": "What are the SOLID principles?",
                "ground_truth": "SOLID is an acronym for five design principles intended to make software designs more understandable, flexible, and maintainable: 1) Single Responsibility Principle (SRP) - a class should have only one reason to change, 2) Open/Closed Principle (OCP) - open for extension, closed for modification, 3) Liskov Substitution Principle (LSP) - subtypes must be substitutable for their base types, 4) Interface Segregation Principle (ISP) - clients shouldn't depend on interfaces they don't use, 5) Dependency Inversion Principle (DIP) - depend on abstractions, not concretions. These principles help create loosely coupled, highly cohesive code.",
                "context": "Object-oriented design principles",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is the Single Responsibility Principle?",
                "ground_truth": "The Single Responsibility Principle (SRP) states that a class should have only one reason to change, meaning it should have only one job or responsibility. This promotes high cohesion and low coupling. For example, a UserService class that handles both user authentication and email sending violates SRP. Instead, it should be split into AuthenticationService and EmailService. Benefits include: easier testing (smaller, focused classes), better maintainability (changes in one area don't affect others), and clearer code organization. A class should encapsulate a single piece of business logic or technical concern.",
                "context": "SOLID principles",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is the Dependency Inversion Principle?",
                "ground_truth": "The Dependency Inversion Principle (DIP) states that: 1) High-level modules should not depend on low-level modules; both should depend on abstractions, 2) Abstractions should not depend on details; details should depend on abstractions. This principle inverts the traditional dependency structure. Instead of concrete classes depending on other concrete classes, they depend on interfaces or abstract classes. For example, instead of OrderService directly instantiating a SqlServerRepository, it should depend on an IRepository interface. The concrete implementation is then injected via dependency injection. This makes code more flexible, testable, and maintainable.",
                "context": "SOLID principles",
                "verified": True,
                "created_by": "system"
            },
            
            # Architecture Patterns
            {
                "question": "What is the MVC pattern?",
                "ground_truth": "Model-View-Controller (MVC) is an architectural pattern that separates an application into three interconnected components: 1) Model - represents the data and business logic, manages the state of the application, 2) View - displays the model data to the user, handles presentation logic, 3) Controller - handles user input, updates the model, and selects views. The flow is: user interacts with View → Controller processes input → Model is updated → View reflects changes. Benefits include separation of concerns, easier testing, multiple views for the same model, and parallel development. Common in web frameworks like ASP.NET MVC, Ruby on Rails, and Django.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is Microservices architecture?",
                "ground_truth": "Microservices architecture is an approach where an application is built as a collection of small, independent services that communicate over network protocols. Each service: runs in its own process, is independently deployable, owns its own database, and focuses on a specific business capability. Benefits include: scalability (scale individual services), technology flexibility (use different tech stacks), fault isolation (one service failure doesn't crash the system), and easier deployment. Challenges include: distributed system complexity, network latency, data consistency, and operational overhead. Common patterns include API Gateway, Service Discovery, and Circuit Breaker.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is Clean Architecture?",
                "ground_truth": "Clean Architecture, proposed by Robert Martin, organizes code into concentric layers with dependencies pointing inward: 1) Entities (enterprise business rules), 2) Use Cases (application business rules), 3) Interface Adapters (controllers, presenters, gateways), 4) Frameworks & Drivers (web, DB, UI). The key principle is the Dependency Rule: source code dependencies can only point inward. Inner layers know nothing about outer layers. Benefits include: framework independence, testability, UI independence, database independence, and independence from external agencies. This architecture emphasizes separation of concerns and makes the business logic the center of the application.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is CQRS pattern?",
                "ground_truth": "Command Query Responsibility Segregation (CQRS) is a pattern that separates read operations (queries) from write operations (commands). Instead of using the same model for both reading and writing, CQRS uses different models: Command Model (optimized for writes, enforces business rules) and Query Model (optimized for reads, provides efficient data retrieval). Benefits include: performance optimization (separate scaling for reads and writes), simplified complex domains, security (different access controls), and eventual consistency support. Often combined with Event Sourcing. Useful in systems with different read/write patterns or complex business logic. Drawback is increased complexity.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "system"
            },
            
            # Testing & Quality
            {
                "question": "What is Test-Driven Development?",
                "ground_truth": "Test-Driven Development (TDD) is a software development approach where tests are written before the actual code. The TDD cycle follows Red-Green-Refactor: 1) Red - write a failing test that defines desired functionality, 2) Green - write minimal code to make the test pass, 3) Refactor - improve code quality while keeping tests passing. Benefits include: better code design (testable code is usually well-designed), comprehensive test coverage, documentation through tests, and confidence in refactoring. TDD encourages small iterations and forces developers to think about requirements before implementation. Common frameworks include JUnit, NUnit, pytest, and Jest.",
                "context": "Development methodology",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is the difference between unit tests and integration tests?",
                "ground_truth": "Unit tests and integration tests serve different purposes: Unit Tests - test individual components in isolation (classes, methods), use mocks/stubs for dependencies, run fast, focus on logic correctness, should be numerous (70-80% of tests). Integration Tests - test how components work together, use real dependencies (databases, APIs, file systems), run slower, focus on interactions and integration points, verify end-to-end workflows. For example, a unit test checks if UserService.CreateUser() validates email format, while an integration test verifies that creating a user saves to the database and sends a welcome email. Both are essential for comprehensive testing.",
                "context": "Software testing",
                "verified": True,
                "created_by": "system"
            },
            
            # Database & Data Access
            {
                "question": "What is the difference between Repository and DAO patterns?",
                "ground_truth": "Both Repository and DAO (Data Access Object) patterns abstract data access, but they have different focuses: DAO is data-centric, provides CRUD operations for database tables, methods map closely to database operations (getUserById, insertUser), and is technology-specific. Repository is domain-centric, provides collection-like interface for domain objects, methods use domain language (findUsersByRole, saveCustomer), and is technology-agnostic. For example, UserDAO might have methods like 'selectUserById()', while UserRepository has 'findById()'. Repository is preferred in DDD as it better aligns with domain modeling, while DAO is more straightforward for simple CRUD applications.",
                "context": "Data access patterns",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is database normalization?",
                "ground_truth": "Database normalization is the process of organizing database tables to reduce redundancy and improve data integrity. The main normal forms are: 1NF (First Normal Form) - eliminate repeating groups, each cell contains atomic values; 2NF - achieve 1NF and remove partial dependencies (non-key attributes must depend on the entire primary key); 3NF - achieve 2NF and remove transitive dependencies (non-key attributes must not depend on other non-key attributes); BCNF (Boyce-Codd) - stricter version of 3NF. Benefits include: reduced data redundancy, better data integrity, easier maintenance. However, over-normalization can hurt performance, requiring denormalization for read-heavy systems.",
                "context": "Database design",
                "verified": True,
                "created_by": "system"
            },
            
            # API Design
            {
                "question": "What are RESTful API design principles?",
                "ground_truth": "RESTful API design follows these key principles: 1) Resource-based URLs (nouns, not verbs: /users, not /getUsers), 2) HTTP methods properly used (GET for retrieval, POST for creation, PUT for update, DELETE for deletion), 3) Stateless (each request contains all needed information), 4) Proper status codes (200 OK, 201 Created, 400 Bad Request, 404 Not Found, 500 Server Error), 5) JSON as data format, 6) Versioning (/api/v1/users), 7) HATEOAS (Hypermedia as the Engine of Application State) for discoverability. Best practices include: filtering and pagination (/users?role=admin&page=2), consistent naming, proper error messages, and documentation. REST promotes scalability, simplicity, and standardization.",
                "context": "API design",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is API rate limiting?",
                "ground_truth": "API rate limiting restricts the number of requests a client can make within a specified time period. Common strategies include: 1) Fixed Window (e.g., 100 requests per hour), 2) Sliding Window (more accurate, considers rolling time window), 3) Token Bucket (requests consume tokens that refill at a steady rate), 4) Leaky Bucket (smooths bursts). Implementation typically returns HTTP 429 (Too Many Requests) with headers indicating limits (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset). Benefits include: preventing abuse, ensuring fair usage, protecting server resources, and enabling tiered pricing models. Rate limits can be per user, per IP, or per API key.",
                "context": "API design",
                "verified": True,
                "created_by": "system"
            },
            
            # Security
            {
                "question": "What is JWT authentication?",
                "ground_truth": "JSON Web Token (JWT) is a compact, URL-safe token format for authentication and authorization. A JWT consists of three parts separated by dots: Header (token type and algorithm), Payload (claims/data), and Signature (verifies integrity). Flow: 1) User logs in with credentials, 2) Server validates and returns JWT, 3) Client stores JWT (localStorage/cookie), 4) Client includes JWT in requests (Authorization: Bearer <token>), 5) Server validates signature and extracts user info. Benefits include: stateless (no server-side session storage), scalable, works across different domains. Security considerations: use HTTPS, set expiration times, validate signatures, never store sensitive data in payload (it's base64, not encrypted).",
                "context": "Authentication",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is SQL injection and how to prevent it?",
                "ground_truth": "SQL injection is a security vulnerability where attackers inject malicious SQL code through user inputs to manipulate database queries. Example: if a query is built as 'SELECT * FROM users WHERE username = ' + userInput, an attacker could input ' OR '1'='1 to bypass authentication. Prevention methods: 1) Use parameterized queries/prepared statements (most important), 2) Input validation and sanitization, 3) Use ORMs that handle escaping, 4) Principle of least privilege (limited database permissions), 5) Avoid displaying detailed error messages, 6) Use stored procedures. Parameterized queries separate SQL logic from data, making injection impossible. Example: cursor.execute('SELECT * FROM users WHERE username = ?', (username,))",
                "context": "Security",
                "verified": True,
                "created_by": "system"
            },
            
            # Performance & Scalability
            {
                "question": "What is caching and when should it be used?",
                "ground_truth": "Caching stores frequently accessed data in fast-access storage to reduce latency and database load. Types include: 1) In-memory caching (Redis, Memcached), 2) Browser caching (HTTP cache headers), 3) CDN caching (static assets), 4) Application-level caching. Strategies: Cache-Aside (app checks cache first, loads from DB on miss), Write-Through (write to cache and DB simultaneously), Write-Behind (write to cache, async write to DB). Use caching for: frequently read data, expensive computations, external API responses, session data. Considerations: cache invalidation (hardest problem), memory limits, consistency requirements, cache stampede prevention. Set appropriate TTL (Time To Live) and use cache warming for critical data.",
                "context": "Performance optimization",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is database indexing?",
                "ground_truth": "Database indexing creates data structures that improve query performance by allowing faster data retrieval without scanning entire tables. Common types: 1) B-Tree Index (default, good for range queries), 2) Hash Index (exact match lookups), 3) Composite Index (multiple columns), 4) Unique Index (enforces uniqueness). Indexes speed up SELECT, WHERE, ORDER BY, and JOIN operations but slow down INSERT, UPDATE, DELETE (index must be updated). Best practices: index frequently queried columns, foreign keys, columns in WHERE clauses, avoid over-indexing (storage overhead), use EXPLAIN to analyze query plans. Trade-off: faster reads vs slower writes and increased storage. For example, indexing email in users table makes login queries faster.",
                "context": "Database optimization",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is horizontal vs vertical scaling?",
                "ground_truth": "Vertical scaling (scale up) means adding more resources to a single server (more CPU, RAM, storage). Pros: simple, no code changes, no data partitioning. Cons: physical limits, single point of failure, downtime during upgrades, expensive. Horizontal scaling (scale out) means adding more servers to distribute load. Pros: better fault tolerance, no theoretical limit, cost-effective with commodity hardware. Cons: increased complexity, data consistency challenges, requires load balancing, stateless design needed. Cloud services make horizontal scaling easier with auto-scaling groups. Modern architectures prefer horizontal scaling for better reliability and flexibility. Vertical scaling suits traditional databases; horizontal suits web servers, microservices, and distributed systems.",
                "context": "Scalability",
                "verified": True,
                "created_by": "system"
            },
            
            # Additional Patterns
            {
                "question": "What is the Adapter pattern?",
                "ground_truth": "The Adapter pattern (also called Wrapper) allows incompatible interfaces to work together by converting one interface into another that clients expect. It acts as a bridge between two incompatible interfaces. Use cases: integrating third-party libraries, working with legacy code, making incompatible interfaces compatible. There are two types: Class Adapter (uses inheritance) and Object Adapter (uses composition). Example: if your code expects IPaymentProcessor but you need to use a third-party StripePayment class with different methods, create StripePaymentAdapter that implements IPaymentProcessor and internally calls StripePayment methods. This follows the Open/Closed Principle and promotes code reusability.",
                "context": "Structural design pattern",
                "verified": True,
                "created_by": "system"
            },
            {
                "question": "What is dependency injection?",
                "ground_truth": "Dependency Injection (DI) is a design pattern where objects receive their dependencies from external sources rather than creating them internally. This implements Inversion of Control (IoC). Types: 1) Constructor Injection (dependencies passed via constructor, preferred method), 2) Property/Setter Injection (dependencies set via properties after creation), 3) Method Injection (dependencies passed to specific methods). Benefits: loose coupling, easier testing (can inject mocks), better separation of concerns, supports SOLID principles. DI containers/frameworks (Spring, .NET Core DI, Angular) automate dependency resolution. Example: instead of OrderService creating new EmailService(), inject IEmailService via constructor. This makes OrderService testable and flexible.",
                "context": "Design pattern and principle",
                "verified": True,
                "created_by": "system"
            },
            
            # ============================================
            # EXPERT LEVEL GROUND TRUTHS
            # ============================================
            
            # Advanced Domain-Driven Design
            {
                "question": "What is Event Sourcing and how does it relate to DDD?",
                "ground_truth": "Event Sourcing is an architectural pattern where state changes are stored as a sequence of immutable events rather than storing current state. Instead of updating a record, you append new events to an event store. To get current state, you replay all events from the beginning (or from a snapshot). In DDD context, domain events become the source of truth. Benefits: complete audit trail, temporal queries (state at any point in time), debugging (replay events), event-driven integration. Challenges: event versioning, eventual consistency, query complexity (often combined with CQRS for read optimization). Example: instead of updating Order.Status = 'Shipped', store OrderShipped event. The aggregate rebuilds by replaying OrderCreated, ItemsAdded, OrderShipped events.",
                "context": "Advanced DDD and architecture",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is a Domain Event and how is it different from an Integration Event?",
                "ground_truth": "Domain Events represent something significant that happened within a bounded context in the domain language. They are internal to the domain model and capture side effects of domain operations. Integration Events are used for communication between bounded contexts or microservices. Key differences: Domain Events are internal, synchronous or async within context, use domain language (OrderPlaced), and are handled by domain services. Integration Events are external, always async, may be transformed/filtered, require eventual consistency handling, and often use a message broker. Pattern: Domain Event triggers local side effects → if needed, publish Integration Event for external systems. Example: OrderPlaced (domain) triggers inventory reservation locally, then OrderPlacedIntegrationEvent notifies shipping service.",
                "context": "DDD event patterns",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Anti-Corruption Layer pattern in DDD?",
                "ground_truth": "The Anti-Corruption Layer (ACL) is a strategic DDD pattern that protects a bounded context from external models that don't align with its domain. It acts as a translation layer between your domain and external systems (legacy systems, third-party APIs, other bounded contexts). The ACL translates external concepts into your domain's ubiquitous language and vice versa. Components include: Facades (simplified interfaces), Adapters (interface translation), Translators (data mapping). Benefits: domain purity (external changes don't corrupt your model), easier refactoring, cleaner domain code. Example: if integrating with a legacy CRM that uses 'Client' with different attributes, ACL translates between 'Client' and your 'Customer' entity, shielding your domain from legacy terminology and structure.",
                "context": "Strategic DDD pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "How do you handle transactions across multiple aggregates in DDD?",
                "ground_truth": "In DDD, the rule is one transaction per aggregate to maintain consistency boundaries. For cross-aggregate operations, use eventual consistency through Domain Events. Patterns: 1) Saga Pattern - sequence of local transactions with compensating actions for rollback. Choreography (events trigger next steps) or Orchestration (central coordinator). 2) Process Manager - stateful workflow coordinating multiple aggregates. 3) Outbox Pattern - store events in same transaction as aggregate changes, then publish reliably. Example: placing an order involves Order and Inventory aggregates. OrderPlaced event triggers InventoryReserved event. If inventory fails, publish InventoryReservationFailed which triggers order cancellation. Accept eventual consistency; design for failure recovery rather than distributed transactions which don't scale.",
                "context": "DDD transaction patterns",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is a Domain Service vs an Application Service in DDD?",
                "ground_truth": "Domain Services contain domain logic that doesn't naturally fit within an entity or value object, operating on multiple aggregates or requiring external domain concepts. They are stateless, named using ubiquitous language, and are part of the domain layer. Application Services orchestrate use cases, coordinate domain objects, handle transactions, and implement application-specific logic. They belong to the application layer and call domain services/repositories. Key differences: Domain Service - domain logic involving multiple aggregates (TransferService.Transfer(fromAccount, toAccount, amount)), pure domain operations. Application Service - use case coordination (PlaceOrderUseCase.Execute()), handles DTOs, transactions, authorization, logging. Example: PricingService (domain) calculates prices using business rules; OrderApplicationService (application) coordinates creating order, calling pricing, and triggering events.",
                "context": "DDD service patterns",
                "verified": True,
                "created_by": "expert"
            },
            
            # Advanced Design Patterns
            {
                "question": "What is the Specification pattern?",
                "ground_truth": "The Specification pattern encapsulates business rules into reusable, composable objects that can be combined with boolean logic. Each specification answers a question about whether an object satisfies certain criteria. Core operations: And(), Or(), Not() for combining specifications. Benefits: reusable business rules, composable queries, domain-expressive code, testable rule objects. Implementation: ISpecification<T> interface with IsSatisfiedBy(T entity) method. Example: ActiveCustomerSpec, PremiumCustomerSpec, HasOutstandingOrdersSpec can be combined: (ActiveCustomerSpec.And(PremiumCustomerSpec)).Or(HasOutstandingOrdersSpec). Use cases: validation rules, query criteria (translating to WHERE clauses), access control rules. The pattern keeps business rules in the domain layer while enabling flexible composition and repository queries.",
                "context": "Enterprise pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Unit of Work pattern?",
                "ground_truth": "The Unit of Work pattern maintains a list of objects affected by a business transaction and coordinates writing changes to the database. It tracks new, modified, and deleted objects, then commits all changes in a single transaction. Benefits: transactional consistency (all-or-nothing), batched database operations (performance), simplified transaction management. Components: identity map (tracks loaded objects), change tracking (detects modifications), transactional boundary. Relationship with Repository: repositories work within Unit of Work scope; UoW commits changes from multiple repositories atomically. ORMs like Entity Framework and Hibernate implement UoW internally (DbContext, Session). Example: UnitOfWork.Begin() → modify multiple entities via repositories → UnitOfWork.Commit() persists all changes. If any fails, rollback entire transaction.",
                "context": "Data access pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Circuit Breaker pattern?",
                "ground_truth": "The Circuit Breaker pattern prevents cascading failures in distributed systems by failing fast when a service is unavailable. States: Closed (normal operation, requests pass through), Open (failures exceeded threshold, requests fail immediately without calling service), Half-Open (after timeout, allows limited requests to test recovery). Metrics tracked: failure count, success count, timeout duration. When failure threshold is reached, circuit opens. After reset timeout, it moves to half-open; successful requests close it, failures reopen. Benefits: fail fast (no waiting for timeouts), prevents resource exhaustion, allows system recovery, graceful degradation. Implementation: wrap remote calls with circuit breaker logic. Libraries: Polly (.NET), Resilience4j (Java), Hystrix. Example: if payment service fails 5 times in 10 seconds, circuit opens for 30 seconds, returning cached/default response.",
                "context": "Resilience pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Bulkhead pattern?",
                "ground_truth": "The Bulkhead pattern isolates components or resources to prevent a failure in one from cascading to others, similar to ship compartments preventing total flooding. Implementation approaches: 1) Thread pool isolation (separate thread pools per service call), 2) Connection pool isolation (dedicated connections per dependency), 3) Process isolation (separate processes/containers), 4) Semaphore isolation (limit concurrent calls). Benefits: fault isolation, prevents resource exhaustion, maintains partial functionality during failures. Example: if your application calls PaymentService and InventoryService, separate thread pools ensure that if PaymentService becomes slow and consumes all threads, InventoryService calls still work. Combine with Circuit Breaker for comprehensive resilience. Trade-offs: increased resource usage, more complex configuration. Used in microservices, cloud-native applications.",
                "context": "Resilience pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Strangler Fig pattern for legacy system migration?",
                "ground_truth": "The Strangler Fig pattern incrementally replaces a legacy system by gradually building new functionality around it until the old system can be decommissioned. Named after strangler fig trees that grow around host trees. Steps: 1) Identify components to migrate, 2) Build new implementation alongside legacy, 3) Route traffic gradually to new system (using facade/proxy), 4) Remove legacy components as they become unused. Benefits: reduced risk (incremental migration), continuous delivery (don't wait for big-bang), learning from production. Implementation: API Gateway or facade routes requests; feature flags control traffic split. Anti-Corruption Layer translates between systems during transition. Example: migrating monolith to microservices - extract OrderService first, route order-related traffic to new service while other features stay in monolith. Eventually, entire monolith is replaced.",
                "context": "Migration pattern",
                "verified": True,
                "created_by": "expert"
            },
            
            # Advanced Architecture Concepts
            {
                "question": "What is the difference between Eventual Consistency and Strong Consistency?",
                "ground_truth": "Strong Consistency guarantees that after a write, all subsequent reads return the updated value immediately. All nodes see the same data at the same time. Used in traditional RDBMS, requires synchronization, limits scalability. Eventual Consistency guarantees that if no new updates are made, all replicas will eventually converge to the same value. Reads may temporarily return stale data. Benefits: higher availability, better performance, horizontal scalability. CAP theorem context: Strong consistency sacrifices availability during partitions; Eventual consistency sacrifices immediate consistency for availability. Patterns for eventual consistency: compensation, idempotency, conflict resolution (last-write-wins, merge). Example: social media 'like' count can be eventually consistent (few seconds delay acceptable); bank account balance requires strong consistency. Choose based on business requirements and acceptable consistency window.",
                "context": "Distributed systems",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the CAP theorem?",
                "ground_truth": "The CAP theorem states that a distributed system can provide only two of three guarantees: Consistency (all nodes see the same data at the same time), Availability (every request receives a response), Partition Tolerance (system continues operating despite network partitions). Since network partitions are inevitable in distributed systems, the real choice is between CP (Consistency + Partition Tolerance) and AP (Availability + Partition Tolerance). CP systems (MongoDB, HBase): during partition, may reject requests to maintain consistency. AP systems (Cassandra, DynamoDB): during partition, may serve stale data but remain available. Modern understanding: CAP is about behavior during partitions; normally systems can provide all three. PACELC extends this: if Partition, choose A or C; Else (normal operation), choose Latency or Consistency.",
                "context": "Distributed systems theory",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Saga pattern for distributed transactions?",
                "ground_truth": "The Saga pattern manages data consistency across microservices without distributed transactions by breaking a transaction into a sequence of local transactions with compensating actions for rollback. Two coordination approaches: 1) Choreography - services publish events, other services react (decentralized, event-driven, complex to trace), 2) Orchestration - central coordinator directs saga steps (centralized control, easier to understand, single point of failure). Each step has a compensating transaction to undo changes if later steps fail. Example: Order saga: CreateOrder → ReserveInventory → ProcessPayment → ShipOrder. If payment fails, compensate by: CancelShipment (no-op) → ReleaseInventory → CancelOrder. Design considerations: idempotent operations, handling concurrent sagas, eventual consistency, debugging complexity. Use when strong consistency isn't required and operations can be compensated.",
                "context": "Distributed transaction pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Outbox pattern?",
                "ground_truth": "The Outbox pattern ensures reliable message publishing in distributed systems by storing messages in a database table (outbox) within the same transaction as business data changes. A separate process reads the outbox and publishes messages to the message broker. Steps: 1) Business operation updates domain data, 2) Same transaction inserts message into outbox table, 3) Transaction commits atomically, 4) Message relay reads outbox, publishes to broker, marks as processed. Benefits: at-least-once delivery guarantee, no distributed transaction needed, survives broker failures. Considerations: consumers must be idempotent (messages may be delivered multiple times), message ordering, outbox cleanup. Variants: Transaction Log Tailing (CDC) reads database transaction log instead of polling table. Example: OrderService creates order and inserts OrderCreated event to outbox atomically; relay service publishes to RabbitMQ.",
                "context": "Messaging pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Sidecar pattern in microservices?",
                "ground_truth": "The Sidecar pattern deploys helper components alongside a service in their own process or container, extending service functionality without modifying service code. The sidecar shares the same lifecycle as the parent service. Use cases: logging/monitoring agents, service mesh proxies (Envoy, Istio), configuration management, security (TLS termination), health checks. Benefits: separation of concerns, language-agnostic (sidecar can be different language), independent deployment and updates, consistent cross-cutting concerns. The sidecar communicates with the main service via localhost (low latency). In Kubernetes, implemented as multi-container pods. Service mesh example: Envoy sidecar handles service discovery, load balancing, circuit breaking, TLS, observability - main service just makes localhost calls. Trade-offs: increased resource usage, added complexity, debugging challenges.",
                "context": "Microservices pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the API Gateway pattern?",
                "ground_truth": "The API Gateway pattern provides a single entry point for all client requests in a microservices architecture, routing requests to appropriate services. Responsibilities: request routing, API composition (aggregating multiple service responses), protocol translation, authentication/authorization, rate limiting, caching, load balancing, request/response transformation, monitoring. Benefits: simplified client (one endpoint), cross-cutting concerns centralized, backend flexibility (can change services without affecting clients), BFF (Backend for Frontend) variants for different clients. Challenges: single point of failure (requires high availability), potential bottleneck, added latency, deployment coupling. Implementations: Kong, AWS API Gateway, Azure API Management, Netflix Zuul, custom solutions. Example: mobile app calls /api/user-profile, gateway fetches from UserService, OrderService, and RecommendationService, combines responses. Consider: Gateway vs Service Mesh (gateway for north-south, mesh for east-west traffic).",
                "context": "Microservices pattern",
                "verified": True,
                "created_by": "expert"
            },
            
            # Advanced Testing
            {
                "question": "What is Contract Testing in microservices?",
                "ground_truth": "Contract Testing verifies that services can communicate correctly by testing against agreed-upon contracts rather than actual service implementations. Consumer-Driven Contract Testing: consumers define expectations (contracts), providers verify they meet those contracts. Tools: Pact, Spring Cloud Contract. Benefits: faster feedback (no need to spin up all services), independent deployments (contract verification), catches integration issues early, documentation of service interactions. Process: 1) Consumer writes contract test defining expected request/response, 2) Contract is shared with provider, 3) Provider runs verification against their actual implementation, 4) CI/CD pipeline enforces contract compatibility. Complements integration tests; doesn't replace E2E but reduces need for extensive E2E testing. Example: OrderService (consumer) expects specific JSON format from InventoryService (provider); contract test ensures both sides agree without deploying both.",
                "context": "Testing patterns",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Chaos Engineering?",
                "ground_truth": "Chaos Engineering is the discipline of experimenting on distributed systems to build confidence in their ability to withstand turbulent conditions in production. Principles: 1) Build hypothesis around steady state behavior, 2) Introduce real-world events (server failures, network issues, dependency failures), 3) Run experiments in production (or production-like), 4) Automate experiments as continuous process, 5) Minimize blast radius. Tools: Chaos Monkey (random instance termination), Gremlin, LitmusChaos. Experiments: kill instances, inject latency, corrupt network packets, fill disk, exhaust CPU. Benefits: discover weaknesses before outages, build resilience, validate disaster recovery, improve incident response. Practice: start small (dev/staging), expand gradually, have rollback plans, monitor carefully. Netflix pioneered this with Simian Army. Example: terminate a database replica during peak hours to verify failover works correctly.",
                "context": "Reliability engineering",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Test Pyramid and how should tests be distributed?",
                "ground_truth": "The Test Pyramid is a testing strategy visualizing the ideal distribution of tests. Layers from bottom to top: 1) Unit Tests (base, largest portion ~70%) - fast, isolated, test single components, many tests. 2) Integration Tests (middle ~20%) - test component interactions, databases, APIs, slower but more realistic. 3) E2E/UI Tests (top ~10%) - test complete user journeys, slowest, most brittle, fewest tests. Rationale: unit tests are fast and cheap, providing quick feedback; higher-level tests are slower and more expensive but verify system integration. Anti-patterns: Ice Cream Cone (too many E2E, few unit tests), Hourglass (missing integration layer). Modern variations: Testing Trophy (emphasizes integration tests for modern apps). Best practices: fast feedback from unit tests, confidence from integration tests, critical path coverage from E2E. Balance cost, speed, and confidence at each level.",
                "context": "Testing strategy",
                "verified": True,
                "created_by": "expert"
            },
            
            # Advanced Security
            {
                "question": "What is OAuth 2.0 and how do its flows work?",
                "ground_truth": "OAuth 2.0 is an authorization framework that enables third-party applications to obtain limited access to user resources without exposing credentials. Key roles: Resource Owner (user), Client (app requesting access), Authorization Server (issues tokens), Resource Server (hosts protected resources). Main flows: 1) Authorization Code (web apps) - most secure, involves redirect and code exchange, 2) Authorization Code with PKCE (mobile/SPA) - adds code verifier for public clients, 3) Client Credentials (machine-to-machine) - no user, service account access, 4) Implicit (deprecated) - token in URL fragment, security risks. Tokens: Access Token (short-lived, resource access), Refresh Token (long-lived, obtain new access tokens). Scopes limit permissions. Best practices: use Authorization Code + PKCE, validate tokens, short expiry, secure token storage. Example: 'Login with Google' uses Authorization Code flow.",
                "context": "Authentication and authorization",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the difference between authentication and authorization?",
                "ground_truth": "Authentication (AuthN) verifies identity - 'Who are you?' Proves the user is who they claim to be through credentials (passwords, biometrics, tokens). Methods: passwords, MFA, SSO, certificates, OAuth/OIDC tokens. Authorization (AuthZ) determines permissions - 'What can you do?' Controls access to resources based on verified identity. Methods: RBAC (Role-Based Access Control), ABAC (Attribute-Based Access Control), ACLs (Access Control Lists), policy engines. Flow: Authentication happens first, then authorization uses authenticated identity to make access decisions. Example: logging into email (authentication), then having permission to read inbox but not admin settings (authorization). Common mistake: implementing only authentication without proper authorization. Security principle: verify identity, then enforce least privilege access based on roles/attributes.",
                "context": "Security fundamentals",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is CORS and why is it important?",
                "ground_truth": "Cross-Origin Resource Sharing (CORS) is a browser security mechanism that controls how web pages can request resources from different origins (domain, protocol, or port). Same-Origin Policy blocks cross-origin requests by default. CORS headers allow servers to specify who can access resources. Key headers: Access-Control-Allow-Origin (allowed origins), Access-Control-Allow-Methods (allowed HTTP methods), Access-Control-Allow-Headers (allowed request headers), Access-Control-Allow-Credentials (allow cookies). Preflight requests: browsers send OPTIONS request for non-simple requests to check permissions before actual request. Configuration: specific origins (secure) vs wildcard * (less secure, no credentials). Security implications: misconfigured CORS can expose APIs to unauthorized domains. Example: frontend on app.example.com calling API on api.example.com requires CORS configuration. Backend must return appropriate headers for cross-origin requests to succeed.",
                "context": "Web security",
                "verified": True,
                "created_by": "expert"
            },
            
            # Advanced Database Concepts
            {
                "question": "What are ACID properties in databases?",
                "ground_truth": "ACID properties ensure reliable database transactions: Atomicity - transaction is all-or-nothing; if any part fails, entire transaction rolls back. Consistency - transaction brings database from one valid state to another, maintaining all constraints and rules. Isolation - concurrent transactions execute as if sequential; intermediate states are invisible to other transactions. Isolation levels: Read Uncommitted, Read Committed, Repeatable Read, Serializable (trade-off between consistency and performance). Durability - committed transactions survive system failures, typically through write-ahead logging. ACID is fundamental to relational databases. NoSQL databases often relax ACID for performance/scalability (BASE: Basically Available, Soft state, Eventually consistent). Example: bank transfer must be atomic (both debit and credit succeed or neither), consistent (balance can't go negative), isolated (concurrent transfers don't interfere), durable (transfer persists after power failure).",
                "context": "Database fundamentals",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is database sharding?",
                "ground_truth": "Database sharding horizontally partitions data across multiple database instances (shards), each containing a subset of data. Each shard is an independent database. Sharding strategies: 1) Range-based (data partitioned by ranges, e.g., users A-M on shard1), 2) Hash-based (hash function determines shard, better distribution), 3) Directory-based (lookup table maps data to shards), 4) Geographic (data by region). Benefits: horizontal scalability, improved performance, data locality. Challenges: cross-shard queries (expensive joins), rebalancing when adding shards, maintaining referential integrity, application complexity. Considerations: shard key selection is critical (should be high cardinality, well-distributed, used in queries), hotspots (uneven distribution), consistent hashing for rebalancing. Example: user data sharded by user_id hash - user operations hit single shard, but 'all users' query requires scatter-gather across all shards. Often combined with replication for availability.",
                "context": "Database scalability",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the difference between optimistic and pessimistic locking?",
                "ground_truth": "Pessimistic Locking assumes conflicts are likely; locks resources before modification, preventing concurrent access. Implementation: SELECT FOR UPDATE, database row locks. Benefits: guaranteed consistency, simple logic. Drawbacks: reduced concurrency, potential deadlocks, lock management overhead. Best for: high-contention scenarios, short transactions. Optimistic Locking assumes conflicts are rare; allows concurrent access, checks for conflicts at commit time. Implementation: version column or timestamp; update includes version check (UPDATE WHERE version = X, increment version). If version changed, operation fails and retries. Benefits: better concurrency, no lock overhead. Drawbacks: retry logic needed, wasted work on conflicts. Best for: low-contention, read-heavy scenarios. Example: wiki editing - optimistic locking detects if someone else edited while you were editing; pessimistic would lock article while you edit.",
                "context": "Concurrency control",
                "verified": True,
                "created_by": "expert"
            },
            
            # Software Quality Attributes
            {
                "question": "What is the difference between scalability and elasticity?",
                "ground_truth": "Scalability is the ability to handle increased load by adding resources. Can be vertical (more powerful hardware) or horizontal (more instances). A scalable system is designed to grow. Elasticity is the ability to automatically provision and de-provision resources based on current demand. It's dynamic scalability. An elastic system scales up during peak load and scales down during low load automatically. Key difference: scalability is the capability to scale; elasticity is automatic, dynamic scaling in response to demand. Example: A scalable e-commerce site can add servers for Black Friday (planned scaling). An elastic system automatically spins up instances when traffic spikes and terminates them when traffic drops, often within minutes. Cloud platforms enable elasticity through auto-scaling groups, serverless functions. Elasticity optimizes costs by matching resources to actual demand.",
                "context": "Quality attributes",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is technical debt and how should it be managed?",
                "ground_truth": "Technical debt refers to the implied cost of future rework caused by choosing an easy but limited solution now instead of a better approach that would take longer. Types: 1) Deliberate (conscious trade-offs for speed), 2) Inadvertent (lack of knowledge or mistakes), 3) Bit rot (degradation over time). Manifestations: code duplication, missing tests, outdated dependencies, poor documentation, architectural shortcuts. Management strategies: make debt visible (track in backlog), allocate regular time for paydown (e.g., 20% of sprints), prioritize by impact and interest (accumulating cost), prevent new debt (code reviews, standards), refactor incrementally. Metrics: defect rates, development velocity trends, code quality tools. Like financial debt, some technical debt is acceptable if managed; excessive debt slows development and increases risk. Document decisions that incur debt. Never let debt compound indefinitely - the interest (maintenance cost) eventually exceeds principal.",
                "context": "Software quality",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Open/Closed Principle and how do you apply it?",
                "ground_truth": "The Open/Closed Principle (OCP) states that software entities (classes, modules, functions) should be open for extension but closed for modification. You should be able to add new functionality without changing existing code. Implementation approaches: 1) Inheritance/Polymorphism - define abstract base class/interface, extend with new implementations, 2) Strategy Pattern - inject different algorithms without modifying client, 3) Decorator Pattern - wrap objects to add behavior, 4) Plugin architecture - load extensions dynamically. Example: instead of modifying PaymentProcessor with if/else for each payment type, define IPaymentMethod interface; add new payment types by implementing interface, not changing processor. Benefits: reduced regression risk, easier maintenance, promotes good abstractions. Caveat: don't over-engineer; apply OCP where change is anticipated. Requires identifying extension points through domain understanding. Violation sign: frequently modifying switch/if-else statements to add features.",
                "context": "SOLID principles",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Liskov Substitution Principle and how can it be violated?",
                "ground_truth": "The Liskov Substitution Principle (LSP) states that objects of a superclass should be replaceable with objects of its subclasses without altering program correctness. Subtypes must be behaviorally compatible with their base types. Common violations: 1) Strengthening preconditions (subclass requires more than parent), 2) Weakening postconditions (subclass guarantees less), 3) Throwing unexpected exceptions, 4) Changing method semantics. Classic violation: Square extends Rectangle - setting width on Square also changes height, breaking Rectangle behavior. Signs of violation: type checking (instanceof), empty method overrides, NotImplementedException. Proper design: favor composition over inheritance, use interfaces wisely, design by contract. If you find yourself checking types, LSP is likely violated. Example fix: both Square and Rectangle implement IShape interface rather than inheritance. LSP ensures polymorphism works correctly and maintains system reliability.",
                "context": "SOLID principles",
                "verified": True,
                "created_by": "expert"
            },
            
            # Modern Architecture Concepts
            {
                "question": "What is a Service Mesh?",
                "ground_truth": "A Service Mesh is a dedicated infrastructure layer for handling service-to-service communication in microservices architectures. It provides: traffic management (load balancing, routing, retries), security (mTLS, access control), observability (metrics, tracing, logging), and resilience (circuit breaking, rate limiting). Architecture: sidecar proxies (data plane) deployed alongside each service handle traffic; control plane configures and manages proxies. Popular implementations: Istio, Linkerd, Consul Connect. Benefits: consistent cross-cutting concerns, language-agnostic (proxies handle networking), separation from business logic, zero-code changes for existing services. Trade-offs: complexity, latency overhead, resource consumption, learning curve. Use when: many services, polyglot environment, need consistent security/observability. Example: Envoy sidecars intercept all traffic, automatically enable mTLS between services, collect metrics, and implement retries - application code just makes HTTP calls to localhost.",
                "context": "Cloud native architecture",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the difference between synchronous and asynchronous communication in microservices?",
                "ground_truth": "Synchronous communication: client sends request and waits for response (blocking). Protocols: REST/HTTP, gRPC. Benefits: simple, immediate response, easy debugging. Drawbacks: tight coupling, cascading failures, reduced availability (if service down, client fails), latency accumulation. Asynchronous communication: client sends message and continues without waiting. Protocols: message queues (RabbitMQ, Kafka), events. Benefits: loose coupling, better resilience, service independence, handles load spikes (queue buffers). Drawbacks: eventual consistency, debugging complexity, message ordering challenges. Patterns: Request-Reply async, Event-Driven, Publish-Subscribe. Choose sync for: queries requiring immediate response, simple CRUD. Choose async for: long-running operations, event notifications, decoupled services, high availability requirements. Hybrid approach common: sync for queries, async for commands. Example: place order (sync response for confirmation) → process payment (async event to fulfillment service).",
                "context": "Microservices communication",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Hexagonal Architecture (Ports and Adapters)?",
                "ground_truth": "Hexagonal Architecture (Ports and Adapters), proposed by Alistair Cockburn, structures applications so that core business logic is isolated from external concerns. The core (hexagon) contains domain logic and defines ports (interfaces) for interaction. Adapters implement ports to connect external systems. Primary/Driving Ports: how the outside world talks to the application (HTTP controllers, CLI, message consumers). Secondary/Driven Ports: how the application talks to external systems (database, email, external APIs). Benefits: testability (mock adapters), technology independence (swap adapters without changing core), clear boundaries, focus on domain. Structure: Domain layer (entities, services) → Application layer (use cases, ports) → Infrastructure layer (adapters). Similar to Clean Architecture and Onion Architecture. Example: UserPort interface in core; UserRepositoryAdapter implements it for database, MockUserAdapter for testing. The hexagon metaphor emphasizes that all external systems are equivalent - whether UI or database.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Event-Driven Architecture?",
                "ground_truth": "Event-Driven Architecture (EDA) is a software design pattern where the flow of the program is determined by events - significant changes in state. Components: Event Producers (emit events), Event Channel/Broker (transports events), Event Consumers (react to events). Event types: 1) Domain Events (business occurrences), 2) Integration Events (cross-system), 3) Event-Carried State Transfer (events contain data). Patterns: Event Notification (minimal data, consumers query for details), Event-Carried State Transfer (full data in event), Event Sourcing (events as source of truth), CQRS + Events. Benefits: loose coupling, scalability, real-time processing, audit trail. Challenges: eventual consistency, event ordering, debugging complexity, duplicate handling (idempotency). Technologies: Kafka, RabbitMQ, AWS EventBridge. Example: OrderPlaced event triggers inventory update, payment processing, notification sending - each handled by independent consumers. Design events as immutable facts that happened.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "expert"
            },
            
            # ============================================
            # ADDITIONAL EXPERT GROUND TRUTHS - DOMAIN SPECIFIC
            # ============================================
            
            # Gang of Four Design Patterns (not yet covered)
            {
                "question": "What is the Builder pattern?",
                "ground_truth": "The Builder pattern separates the construction of a complex object from its representation, allowing the same construction process to create different representations. It's useful when an object has many optional parameters or requires step-by-step construction. Components: Builder (abstract interface for creating parts), ConcreteBuilder (implements Builder, constructs and assembles parts), Director (constructs object using Builder interface), Product (the complex object being built). Benefits: avoids telescoping constructors (constructors with many parameters), allows immutable objects, readable fluent API. Example: StringBuilder, or building a House: new HouseBuilder().setWalls(4).setRoof('tile').setGarage(true).build(). Fluent Builder variant returns 'this' for method chaining. Use when: object creation involves multiple steps, object has many optional parameters, you want immutable objects with complex construction.",
                "context": "Creational design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Prototype pattern?",
                "ground_truth": "The Prototype pattern creates new objects by copying an existing object (prototype) rather than creating from scratch. It uses cloning to avoid the overhead of creating objects via constructors. Components: Prototype (interface with clone method), ConcretePrototype (implements cloning). Types of cloning: Shallow Copy (copies primitive values, references point to same objects) vs Deep Copy (recursively clones referenced objects). Use cases: when object creation is expensive (database operations, complex calculations), when you need many similar objects with slight variations, to avoid subclass explosion for object creation. Example: Cell cloning in spreadsheets, document templates. Implementation: implement Cloneable interface (Java) or ICloneable (.NET), or use copy constructors. Consider: prototype registry for managing available prototypes.",
                "context": "Creational design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Abstract Factory pattern?",
                "ground_truth": "The Abstract Factory pattern provides an interface for creating families of related or dependent objects without specifying their concrete classes. It's a 'factory of factories'. Components: AbstractFactory (declares creation methods for abstract products), ConcreteFactory (implements creation for specific product family), AbstractProduct (interface for a product type), ConcreteProduct (specific product implementation). Benefits: ensures compatibility between created objects (products from same family work together), isolates concrete classes, easy to exchange product families. Example: UI toolkit factory creating buttons, checkboxes, menus - WindowsFactory creates WindowsButton, WindowsCheckbox; MacFactory creates MacButton, MacCheckbox. Use when: system should be independent of product creation, system needs to work with multiple product families, family of products is designed to work together.",
                "context": "Creational design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Composite pattern?",
                "ground_truth": "The Composite pattern composes objects into tree structures to represent part-whole hierarchies. It lets clients treat individual objects and compositions of objects uniformly. Components: Component (common interface for leaf and composite), Leaf (represents end objects with no children), Composite (stores child components, implements child-related operations). Benefits: simplifies client code (uniform treatment), easy to add new component types, natural representation of hierarchies. Example: file system (File is Leaf, Directory is Composite), GUI components (Button is Leaf, Panel is Composite containing other components), organization charts. Operations can propagate through the tree (e.g., calculateSize() sums sizes of all children). Design consideration: where to declare child management methods (Component vs Composite) - trade-off between transparency and safety.",
                "context": "Structural design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Facade pattern?",
                "ground_truth": "The Facade pattern provides a simplified, unified interface to a complex subsystem, making it easier to use. It doesn't encapsulate the subsystem but provides a convenient entry point. Components: Facade (simplified interface delegating to subsystem), Subsystem classes (complex functionality). Benefits: reduces coupling between clients and subsystem, simplifies API, hides complexity, provides good entry point for layered architectures. Example: a HomeTheaterFacade wrapping TV, Amplifier, DVDPlayer, Lights with methods like watchMovie() that coordinates all components. Use when: you need a simple interface to a complex system, there are many dependencies between clients and implementation classes, you want to layer your subsystems. Note: clients can still access subsystem directly if needed; facade is optional convenience, not a restriction.",
                "context": "Structural design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Flyweight pattern?",
                "ground_truth": "The Flyweight pattern minimizes memory usage by sharing as much data as possible with similar objects. It separates intrinsic state (shared, context-independent) from extrinsic state (unique, context-dependent). Components: Flyweight (interface for receiving extrinsic state), ConcreteFlyweight (stores intrinsic state, shared), FlyweightFactory (creates and manages flyweights, ensures sharing). Example: text editor where Character objects share font data (intrinsic) but have unique positions (extrinsic). In games, Tree objects share mesh/texture data but have unique positions. Benefits: significant memory savings when many similar objects exist. Trade-offs: increased complexity, computation time for extrinsic state. Use when: application uses large numbers of similar objects, storage costs are high, most object state can be made extrinsic, identity of objects is not important.",
                "context": "Structural design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Proxy pattern?",
                "ground_truth": "The Proxy pattern provides a surrogate or placeholder for another object to control access to it. The proxy implements the same interface as the real object. Types: 1) Virtual Proxy (lazy initialization, creates expensive objects on demand), 2) Protection Proxy (access control based on permissions), 3) Remote Proxy (represents object in different address space, like RMI), 4) Caching Proxy (stores results of expensive operations), 5) Logging Proxy (logs requests before forwarding). Components: Subject (common interface), RealSubject (actual object), Proxy (controls access to RealSubject). Example: image viewer using virtual proxy to load images only when displayed, security proxy checking user permissions before database access. Differs from Decorator (adds behavior) and Adapter (changes interface). Proxy maintains same interface and controls access.",
                "context": "Structural design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Chain of Responsibility pattern?",
                "ground_truth": "The Chain of Responsibility pattern passes a request along a chain of handlers, where each handler decides either to process the request or pass it to the next handler. Components: Handler (interface with handle method and successor reference), ConcreteHandler (handles requests it's responsible for, forwards others). Benefits: decouples sender from receivers, flexibility in assigning responsibilities, handlers can be added/removed dynamically. Example: customer support escalation (helpdesk → specialist → manager), middleware chain in web frameworks (authentication → authorization → logging → handler), DOM event bubbling. Implementation: each handler holds reference to next handler, processes or forwards. Variations: pure (only one handler processes) vs impure (multiple handlers can process). Use when: more than one object may handle a request, handler isn't known a priori, handlers should be flexible.",
                "context": "Behavioral design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Command pattern?",
                "ground_truth": "The Command pattern encapsulates a request as an object, allowing parameterization of clients with different requests, queuing of requests, and logging of operations. Components: Command (interface with execute method), ConcreteCommand (binds receiver and action), Invoker (asks command to execute), Receiver (performs the actual work). Benefits: decouples invoker from receiver, supports undo/redo (store command history), supports queuing and scheduling, enables macro commands (composite of commands). Example: menu items in GUI (each menu item is a command), transaction systems, task schedulers. Implementation: ConcreteCommand stores receiver reference and parameters; execute() calls receiver methods. Memento pattern often combined for undo state. Use when: you need callback functionality, support for undo, queuing/logging operations, building macro commands.",
                "context": "Behavioral design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Mediator pattern?",
                "ground_truth": "The Mediator pattern defines an object that encapsulates how a set of objects interact, promoting loose coupling by preventing objects from referring to each other explicitly. Components: Mediator (interface for colleague communication), ConcreteMediator (implements coordination logic, knows all colleagues), Colleague (communicates via mediator, doesn't know other colleagues). Benefits: reduces coupling between components, centralizes complex communications, simplifies object protocols. Example: chat room (users communicate through room, not directly), air traffic control (planes communicate via tower), dialog boxes (components interact through dialog controller). Trade-off: mediator can become a 'god object' if too complex. Differs from Facade (unidirectional simplification) - Mediator enables bidirectional communication. Use when: objects communicate in complex but well-defined ways, reusing objects is difficult due to dependencies.",
                "context": "Behavioral design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the State pattern?",
                "ground_truth": "The State pattern allows an object to alter its behavior when its internal state changes, appearing to change its class. It encapsulates state-specific behavior into separate state objects. Components: Context (maintains current state, delegates behavior), State (interface for state-specific behavior), ConcreteState (implements behavior for a specific state). Benefits: eliminates complex conditionals (if/switch on state), organizes state-specific code, makes state transitions explicit, easy to add new states. Example: vending machine (HasCoin, NoCoin, Dispensing states), document workflow (Draft, Review, Published), TCP connection (Listening, Established, Closed). Implementation: Context holds reference to current State object; state transitions by changing this reference. State objects may hold reference to Context to trigger transitions. Similar to Strategy but intent differs - State transitions are automatic based on context.",
                "context": "Behavioral design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Template Method pattern?",
                "ground_truth": "The Template Method pattern defines the skeleton of an algorithm in a base class, letting subclasses override specific steps without changing the algorithm's structure. Components: AbstractClass (defines template method with algorithm skeleton, abstract/hook methods for steps), ConcreteClass (implements abstract steps, optionally overrides hooks). Template method is typically final (non-overridable). Hook methods have default implementations that can be overridden. Benefits: code reuse (common algorithm structure), controlled extension points, inverts control (Hollywood Principle - 'don't call us, we'll call you'). Example: data processing framework (read → process → write), game loop (init → update → render), document generation (header → body → footer). Use when: algorithm has invariant parts and customizable parts, common behavior should be factored into a base class, control subclass extensions.",
                "context": "Behavioral design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Visitor pattern?",
                "ground_truth": "The Visitor pattern lets you add new operations to existing object structures without modifying them by separating algorithms from the objects they operate on. Uses double dispatch to call the right method based on both visitor and element types. Components: Visitor (declares visit methods for each element type), ConcreteVisitor (implements operations for each element), Element (accepts visitor), ConcreteElement (implements accept, calls visitor.visit(this)). Benefits: add new operations without changing classes, gather related operations in one class, accumulate state while traversing. Example: compiler syntax tree (nodes accept visitors for type checking, code generation, optimization), document rendering (elements accept visitors for different output formats). Trade-offs: hard to add new element types (all visitors must change), breaks encapsulation. Use when: object structure rarely changes but operations frequently added.",
                "context": "Behavioral design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Iterator pattern?",
                "ground_truth": "The Iterator pattern provides a way to access elements of an aggregate object sequentially without exposing its underlying representation. Components: Iterator (interface with hasNext(), next(), etc.), ConcreteIterator (implements traversal for specific aggregate), Aggregate (interface for creating iterators), ConcreteAggregate (collection implementing iterator creation). Benefits: simplifies aggregate interface, supports multiple simultaneous traversals, provides uniform traversal interface, hides internal structure. Types: external (client controls iteration) vs internal (iterator controls, client provides callback). Example: most collection frameworks (Java Iterable/Iterator, Python's __iter__/__next__, C# IEnumerable/IEnumerator). Modern languages build iteration into for-each loops. Use when: accessing aggregate contents without exposing internals, supporting multiple traversal methods, providing uniform interface for different aggregates.",
                "context": "Behavioral design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Memento pattern?",
                "ground_truth": "The Memento pattern captures and externalizes an object's internal state so it can be restored later without violating encapsulation. Components: Originator (creates memento with current state, restores from memento), Memento (stores originator's state, opaque to other objects), Caretaker (stores mementos, never operates on their contents). Benefits: preserves encapsulation (memento is opaque), simplifies originator (state management externalized), supports undo/redo. Example: text editor undo (each memento stores document state), game save points, transaction rollback. Implementation: Memento should be immutable; only Originator can access Memento internals. Memory consideration: consider incremental mementos or compression for large states. Often combined with Command pattern for undo functionality. Use when: you need snapshots of object state, direct state access would violate encapsulation.",
                "context": "Behavioral design pattern",
                "verified": True,
                "created_by": "expert"
            },
            
            # Refactoring Concepts
            {
                "question": "What is code refactoring and why is it important?",
                "ground_truth": "Refactoring is the process of restructuring existing code without changing its external behavior. Goals: improve code readability, reduce complexity, improve maintainability, and remove technical debt. Key principles: keep tests passing (refactoring should not break functionality), make small incremental changes, refactor before adding features. Common refactoring techniques: Extract Method (break long methods into smaller ones), Rename (improve clarity), Move Method/Field (better class responsibility), Replace Conditional with Polymorphism, Introduce Parameter Object. When to refactor: Rule of Three (duplication), adding new features requires changes, code review feedback, fixing bugs reveals deeper issues. Tools: IDEs provide automated refactoring. Red-Green-Refactor cycle in TDD. Refactoring is continuous improvement, not a one-time activity.",
                "context": "Code quality",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What are code smells?",
                "ground_truth": "Code smells are surface indications of deeper design problems in code. They're not bugs but suggest refactoring opportunities. Common code smells: 1) Long Method (do too much), 2) Large Class (too many responsibilities), 3) Feature Envy (method uses other class's data excessively), 4) Data Clumps (groups of data appearing together), 5) Primitive Obsession (using primitives instead of small objects), 6) Switch Statements (may indicate missing polymorphism), 7) Parallel Inheritance Hierarchies, 8) Lazy Class (does too little), 9) Speculative Generality (unnecessary abstraction), 10) Temporary Field (fields only used sometimes), 11) Duplicate Code, 12) Dead Code (unused code), 13) Comments (may indicate unclear code). Detection: code reviews, static analysis tools (SonarQube, CodeClimate). Treatment: apply appropriate refactoring patterns.",
                "context": "Code quality",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the DRY principle?",
                "ground_truth": "DRY (Don't Repeat Yourself) states that every piece of knowledge should have a single, unambiguous representation in a system. Duplication leads to: inconsistency (one copy updated, others not), maintenance burden, bugs. Types of duplication: 1) Code duplication (copy-paste), 2) Knowledge duplication (same concept represented differently), 3) Data duplication (same data in multiple places). Applying DRY: Extract Method/Class for code, constants for magic values, single source of truth for data, configuration over hardcoding. Caution: DRY is about knowledge, not just syntax. Two similar code blocks might represent different concepts and shouldn't be merged. Over-applying DRY (wrong abstraction) is worse than duplication. Related: WET (Write Everything Twice - deliberate duplication), AHA (Avoid Hasty Abstractions). Abstract when you see the pattern, not before.",
                "context": "Design principles",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the KISS principle?",
                "ground_truth": "KISS (Keep It Simple, Stupid) advocates for simplicity in design. Simple solutions are easier to understand, maintain, debug, and extend. Guidelines: solve the problem at hand, not imaginary future problems; avoid premature optimization; choose straightforward approaches over clever ones; reduce moving parts; prefer composition over complex inheritance. Signs of over-complexity: excessive abstraction layers, design patterns used without clear need, code that requires extensive comments to understand. Balance: simplicity doesn't mean primitive - use appropriate abstractions for your domain. Related principles: YAGNI (You Aren't Gonna Need It), Occam's Razor. Quote: 'Any fool can write code that a computer can understand. Good programmers write code that humans can understand.' - Martin Fowler. Simple code has fewer bugs and is easier to change.",
                "context": "Design principles",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the YAGNI principle?",
                "ground_truth": "YAGNI (You Aren't Gonna Need It) is a practice of Extreme Programming that states not to implement functionality until it's actually needed. Avoid building features based on speculation about future requirements. Rationale: predicted features often aren't needed, requirements change, time spent on unnecessary features delays valuable ones, unused code becomes maintenance burden. Apply YAGNI to: features, abstractions, optimizations, flexibility provisions. Exceptions: security, architecture foundations, regulatory requirements. Balance with extensibility: design for change (Open/Closed Principle) but implement only what's needed. YAGNI complements KISS and DRY. Example: don't build a plugin architecture 'just in case' - wait until you actually need to support plugins. Focus on current iteration's requirements; refactor when new requirements emerge.",
                "context": "Design principles",
                "verified": True,
                "created_by": "expert"
            },
            
            # Code Organization
            {
                "question": "What is coupling and cohesion in software design?",
                "ground_truth": "Coupling measures the degree of interdependence between modules. Low coupling is desirable - modules should be independent. Types (worst to best): Content coupling (module modifies another's data), Common coupling (shared global data), External coupling (shared external format), Control coupling (one controls another's flow), Stamp coupling (pass composite data, use only part), Data coupling (only necessary data passed), Message coupling (communication via messages). Cohesion measures how strongly related elements within a module are. High cohesion is desirable. Types (worst to best): Coincidental (random grouping), Logical (similar functions), Temporal (executed together), Procedural (execution order), Communicational (operate on same data), Sequential (output of one is input to next), Functional (single well-defined purpose). Goal: HIGH cohesion, LOW coupling. This makes code modular, testable, maintainable, and reusable.",
                "context": "Software design fundamentals",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the difference between packages, modules, and namespaces?",
                "ground_truth": "These terms vary by language but share the goal of organizing code: Packages (Java, Python) - directory-based organization containing modules/classes. Define visibility scope, enable access control, prevent naming collisions. Example: com.company.project.feature. Modules - compilation units containing related code. Python: single .py file. JavaScript ES6: file with import/export. Provide encapsulation and reusability. Namespaces (C++, C#, TypeScript) - logical grouping of identifiers preventing name collisions without requiring directory structure. Can span multiple files. Example: namespace Company.Project { }. Components (modern sense) - higher-level units of deployment/reuse containing related functionality. Key considerations: organize by feature not layer (screaming architecture), keep related code together, respect dependency direction (depend on stable abstractions), limit package scope. Good organization enables team autonomy and independent deployability.",
                "context": "Code organization",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Law of Demeter?",
                "ground_truth": "The Law of Demeter (LoD), or Principle of Least Knowledge, states that a unit should only communicate with its immediate associates. A method M of object O may only call methods of: O itself, M's parameters, objects created by M, O's direct component objects. Violation example: customer.getWallet().getMoney().pay() - the method knows too much about internal structure. Better: customer.pay() - let Customer handle its internals. Benefits: reduced coupling, better encapsulation, easier testing and maintenance. Trade-offs: may create many wrapper methods (but consider if object has too many responsibilities). Related: Tell, Don't Ask - tell objects what to do rather than asking for data and acting on it. Train Wreck antipattern: chained method calls violating LoD. Apply judiciously: DTOs and fluent interfaces may intentionally violate LoD.",
                "context": "Design principles",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Interface Segregation Principle?",
                "ground_truth": "The Interface Segregation Principle (ISP) states that clients should not be forced to depend on interfaces they don't use. Large, 'fat' interfaces should be split into smaller, specific ones. Violation example: IPrinter interface with print(), scan(), fax() methods - a basic printer implementing this must provide empty fax() and scan() implementations. Solution: split into IPrinter, IScanner, IFax interfaces. Benefits: reduces coupling (clients depend only on what they need), easier mocking in tests, better cohesion, supports composition. Signs of violation: empty method implementations, ISupportedCheck methods (if hasFeature()), frequent changes affecting unrelated clients. Application: define interfaces based on client needs (role interfaces), prefer many specific interfaces over one general-purpose. Related: smaller interfaces align with Single Responsibility. In dynamic languages, duck typing naturally supports ISP.",
                "context": "SOLID principles",
                "verified": True,
                "created_by": "expert"
            },
            
            # Layered Architecture
            {
                "question": "What is a Layered Architecture?",
                "ground_truth": "Layered Architecture organizes code into horizontal layers where each layer has specific responsibilities and can only depend on layers below it. Classic layers: 1) Presentation Layer (UI, controllers, API endpoints), 2) Business/Application Layer (business logic, use cases), 3) Domain Layer (domain entities, business rules), 4) Data/Persistence Layer (database access, repositories), 5) Infrastructure Layer (external services, frameworks). Rules: strict layering (layer only accesses adjacent layer below) or relaxed (can skip layers). Benefits: separation of concerns, testability, replaceability of layers, organized codebase. Challenges: can lead to anemic domain model, tight coupling within layers, shotgun surgery across layers for features. Alternatives: vertical slices (organize by feature, not layer), Clean/Hexagonal Architecture. Choose based on team size, project complexity, and change patterns.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Onion Architecture?",
                "ground_truth": "Onion Architecture, proposed by Jeffrey Palermo, organizes code in concentric layers with dependencies pointing inward toward the domain core. Layers from inside out: 1) Domain Model (entities, value objects - no dependencies), 2) Domain Services (domain operations), 3) Application Services (use cases, orchestration), 4) Infrastructure (database, external APIs, UI). Key principle: outer layers depend on inner layers; inner layers know nothing about outer layers. Domain model is at the center, free from infrastructure concerns. Dependency Inversion: interfaces defined in inner layers, implemented in outer layers. Example: IUserRepository defined in domain layer, SqlUserRepository implemented in infrastructure. Benefits: domain independence from frameworks/databases, testability (mock infrastructure), focus on domain. Similar to Clean Architecture and Hexagonal Architecture; all share Dependency Inversion as core principle.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "expert"
            },
            
            # Software Quality Attributes
            {
                "question": "What is software maintainability?",
                "ground_truth": "Maintainability is the ease with which software can be modified to fix defects, improve performance, or adapt to changes. Sub-characteristics (ISO 25010): 1) Modularity - composed of discrete components, 2) Reusability - can be used in multiple systems, 3) Analysability - ease of diagnosing issues, 4) Modifiability - ease of making changes, 5) Testability - ease of testing modifications. Factors affecting maintainability: code complexity (cyclomatic complexity), documentation, coding standards, architecture clarity, test coverage, dependency management. Practices improving maintainability: consistent naming conventions, small focused functions/classes, SOLID principles, comprehensive tests, code reviews, refactoring, avoiding clever code. Metrics: lines of code, coupling/cohesion measures, code churn, bug fix time. Maintainability is often sacrificed for short-term speed but costs more long-term.",
                "context": "Quality attributes",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is software testability?",
                "ground_truth": "Testability is the degree to which a software system supports testing. High testability means tests are easy to write, fast to run, and provide reliable results. Factors: 1) Controllability (can set system to desired state), 2) Observability (can examine outputs and states), 3) Isolatability (can test components independently), 4) Determinism (same inputs produce same outputs). Design for testability: dependency injection (inject mocks), interface-based design, avoid static/global state, separate pure functions from side effects, small focused units, avoid deep nesting. Anti-patterns: hidden dependencies, singletons, direct framework coupling, mixed concerns. Practices: TDD forces testable design, test pyramid for balanced coverage, continuous integration for frequent testing. Trade-off: testable design often equals good design, but over-engineering for testability adds unnecessary complexity.",
                "context": "Quality attributes",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is software reliability?",
                "ground_truth": "Reliability is the probability that software performs its required functions under stated conditions for a specified time. Sub-characteristics: 1) Maturity - meets reliability needs under normal operation, 2) Availability - operational when needed (uptime percentage, e.g., 99.99% = 52 minutes downtime/year), 3) Fault Tolerance - operates despite faults, 4) Recoverability - can recover from failures. Design for reliability: redundancy (replicas, failover), graceful degradation, circuit breakers, retries with backoff, timeouts, health checks, data replication. Practices: defensive programming, input validation, error handling, monitoring and alerting, chaos engineering (test failure scenarios). Metrics: Mean Time Between Failures (MTBF), Mean Time To Recovery (MTTR), error rates. SLAs define reliability requirements. Trade-offs: reliability often conflicts with cost and complexity; design to appropriate level for business needs.",
                "context": "Quality attributes",
                "verified": True,
                "created_by": "expert"
            },
            
            # Modern Development Practices
            {
                "question": "What is Behavior-Driven Development?",
                "ground_truth": "Behavior-Driven Development (BDD) extends TDD by writing tests in natural language that describe system behavior from user perspective. Uses Given-When-Then format: Given (preconditions/context), When (action/trigger), Then (expected outcome). Benefits: shared understanding between developers, testers, and business (ubiquitous language), living documentation, focus on behavior not implementation. Tools: Cucumber, SpecFlow, Behave - use feature files with Gherkin syntax. Example: 'Given a customer with $100 balance, When they withdraw $30, Then balance should be $70'. Process: 1) Write scenarios with stakeholders, 2) Implement step definitions, 3) Write code to pass scenarios. Complements DDD (scenarios use domain language). Challenges: maintaining scenarios as documentation, step definition reuse, scenario explosion. Use for acceptance tests and critical business rules.",
                "context": "Development methodology",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Continuous Integration and Continuous Deployment?",
                "ground_truth": "Continuous Integration (CI) is the practice of frequently merging code changes into a shared repository with automated build and test verification. Principles: maintain single source repository, automate the build, make build self-testing, commit frequently, fix broken builds immediately. Benefits: early bug detection, reduced integration problems, always deployable code. Continuous Delivery (CD) extends CI to automatically deploy to staging environments; production deployment is manual. Continuous Deployment extends further with automatic production deployment. Pipeline stages: source → build → test → deploy to staging → (manual approval for delivery) → deploy to production. Tools: Jenkins, GitHub Actions, GitLab CI, CircleCI, Azure DevOps. Prerequisites: version control, automated testing, infrastructure as code. Metrics: deployment frequency, lead time, failure rate, recovery time (DORA metrics).",
                "context": "DevOps practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Domain-Driven Design Strategic Design?",
                "ground_truth": "Strategic Design in DDD addresses large-scale system organization and team boundaries. Key concepts: 1) Bounded Context - explicit boundary where a domain model applies; different contexts may have different models for same concept. 2) Context Mapping - documenting relationships between bounded contexts. Relationships include: Shared Kernel (shared subset), Customer-Supplier (upstream/downstream), Conformist (adopt upstream model), Anti-Corruption Layer (translate external models), Open Host Service (API for integration), Published Language (shared schema). 3) Subdomains - Core (competitive advantage, build in-house), Supporting (necessary but not differentiating), Generic (common problems, buy/use existing solutions). Strategic design guides: team organization (Conway's Law), investment priorities, integration strategies, technology choices per context. Start with subdomain analysis, then define bounded contexts aligned with teams.",
                "context": "DDD strategic patterns",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is a Value Object in Domain-Driven Design?",
                "ground_truth": "A Value Object is a domain object defined by its attributes rather than a unique identity. Two value objects with the same attributes are considered equal. Characteristics: 1) Immutability - once created, cannot be changed (new instance for changes), 2) Equality by value - compared by attribute values, not identity, 3) Side-effect-free behavior - methods return new instances. Examples: Money (amount, currency), Address (street, city, zip), DateRange (start, end), Email. Benefits: no identity management overhead, naturally thread-safe (immutable), express domain concepts explicitly, prevent primitive obsession. Implementation: override equals/hashCode, make fields final, no setters. Use for: measurements, descriptive characteristics, quantities, ranges. Contrast with Entities: entities have identity and change over time; value objects are replaced entirely. Value objects can contain other value objects but shouldn't reference entities directly.",
                "context": "DDD tactical patterns",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the difference between monolithic and distributed architectures?",
                "ground_truth": "Monolithic Architecture: single deployable unit containing all functionality. Characteristics: single codebase, shared database, in-process communication, single deployment pipeline. Advantages: simpler development and testing, easier debugging, no network latency, straightforward transactions. Disadvantages: scaling requires scaling entire app, technology lock-in, large codebase complexity, deployment affects entire system. Distributed Architecture (e.g., microservices): multiple independently deployable services. Characteristics: separate codebases, service-specific databases, network communication (REST, messaging), independent deployment. Advantages: independent scaling, technology flexibility, team autonomy, fault isolation, easier to understand individual services. Disadvantages: network complexity (latency, failures), distributed transactions, operational overhead, eventual consistency. Choice factors: team size (small teams favor monolith), scale requirements, organizational structure, deployment frequency. Start monolith, extract services when beneficial. Modular monolith is a middle ground.",
                "context": "Architectural patterns",
                "verified": True,
                "created_by": "expert"
            },
            
            # ============================================
            # EXTENDED EXPERT GROUND TRUTHS (100+ MORE)
            # ============================================
            
            # Object-Oriented Design Fundamentals
            {
                "question": "What is polymorphism in object-oriented programming?",
                "ground_truth": "Polymorphism allows objects of different types to be treated through a common interface. Types: 1) Compile-time (static) - method overloading (same name, different parameters), operator overloading. 2) Runtime (dynamic) - method overriding (subclass redefines parent method), resolved at runtime via virtual method table. Benefits: code flexibility, extensibility without modification, substitutability. Example: Shape interface with draw() method; Circle, Square, Triangle implement draw() differently. Client code calls shape.draw() without knowing specific type. Polymorphism enables: Strategy pattern (swap algorithms), Template Method (customizable steps), Open/Closed Principle (extend without modifying). Languages implement via: virtual functions (C++), all methods virtual by default (Java), duck typing (Python). Polymorphism is fundamental to achieving loose coupling and extensible designs.",
                "context": "OOP fundamentals",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is encapsulation in object-oriented programming?",
                "ground_truth": "Encapsulation bundles data (attributes) and methods (behavior) that operate on the data within a single unit (class), while hiding internal implementation details from outside. Two aspects: 1) Bundling - grouping related data and behavior together, 2) Information Hiding - restricting direct access to internal state. Implementation: access modifiers (private, protected, public), getters/setters for controlled access. Benefits: controlled modification (validation in setters), implementation flexibility (change internals without affecting clients), reduced complexity (hide details), better maintainability. Example: BankAccount class with private balance; deposit() and withdraw() methods enforce business rules. Poor encapsulation: public fields, getter/setter for everything (anemic domain model). Good encapsulation: expose behavior, not data. Tell objects what to do rather than asking for data and acting on it.",
                "context": "OOP fundamentals",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is inheritance in object-oriented programming?",
                "ground_truth": "Inheritance allows a class (subclass/child) to inherit properties and methods from another class (superclass/parent). Types: 1) Single inheritance (one parent), 2) Multiple inheritance (multiple parents - supported in C++, Python), 3) Multilevel inheritance (chain of inheritance), 4) Hierarchical (multiple children). Benefits: code reuse, polymorphism, hierarchical classification. Problems: tight coupling, fragile base class (changes affect all children), inheritance hierarchy can become complex, inherited behavior may not fit. Liskov Substitution Principle: subclasses must be substitutable for parents. Prefer composition over inheritance: HAS-A is often better than IS-A. Use inheritance when: true IS-A relationship exists, substitution makes sense, shared behavior is stable. Alternatives: interfaces, composition, delegation, mixins/traits. Example: Employee inherits from Person only if Employee IS-A Person and Liskov holds.",
                "context": "OOP fundamentals",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is abstraction in software design?",
                "ground_truth": "Abstraction is the process of hiding complex implementation details while exposing only the essential features. It manages complexity by creating simplified models of reality. Levels: 1) Data abstraction (abstract data types hide structure), 2) Procedural abstraction (functions hide implementation), 3) Object abstraction (objects hide state and behavior), 4) Architectural abstraction (layers hide lower-level details). Implementation: abstract classes (partial implementation), interfaces (pure contract), access modifiers, modules/packages. Benefits: reduced complexity, focus on what not how, easier to understand and use, implementation can change without affecting users. Example: driving a car - you use steering wheel and pedals (abstraction) without knowing engine internals. In code: List interface abstracts ArrayList, LinkedList implementations. Good abstractions: stable over time, hide volatile details, represent meaningful concepts.",
                "context": "Design fundamentals",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is composition over inheritance?",
                "ground_truth": "Composition over inheritance is a design principle favoring object composition (HAS-A relationship) over class inheritance (IS-A relationship) for code reuse. Composition: objects contain references to other objects providing needed functionality. Benefits: flexible (change behavior at runtime by swapping components), loose coupling (components are independent), avoids inheritance pitfalls (fragile base class, deep hierarchies), easier testing (mock individual components). Implementation: delegate behavior to composed objects rather than inheriting. Example: instead of Car extends Engine, use Car has-a Engine. Change engine without modifying Car class. Strategy pattern exemplifies composition - swap algorithms without inheritance. When to use inheritance: true IS-A relationship, Liskov Substitution holds, hierarchy is stable and shallow. Composition is generally safer and more flexible. Java's lack of multiple inheritance pushes toward composition.",
                "context": "Design principles",
                "verified": True,
                "created_by": "expert"
            },
            
            # More Architecture Patterns
            {
                "question": "What is the Pipes and Filters architecture?",
                "ground_truth": "Pipes and Filters is an architectural pattern for processing data streams through a sequence of independent processing steps. Components: Filters (process/transform data, independent units), Pipes (connect filters, transfer data). Each filter: receives input, processes it, produces output; is independent and stateless; has no knowledge of adjacent filters. Benefits: flexibility (add/remove/reorder filters), reusability (filters can be reused), parallelism (filters can run concurrently), testability (test filters independently). Examples: Unix shell commands (cat file | grep pattern | sort), compiler stages (lexer | parser | optimizer | code generator), image processing pipelines, ETL processes. Variations: push (producer-driven), pull (consumer-driven), mixed. Trade-offs: data transformation overhead between filters, not suitable for interactive systems, debugging across filters. Use for batch processing, data transformation, content processing.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Blackboard architecture pattern?",
                "ground_truth": "The Blackboard pattern is an architectural approach for problems with no deterministic solution strategy, where multiple specialized subsystems collaborate to build a solution incrementally. Components: 1) Blackboard (shared knowledge repository, central data structure), 2) Knowledge Sources (specialized modules that can read/write to blackboard), 3) Controller (monitors blackboard, decides which knowledge source to activate). Process: knowledge sources contribute partial solutions; controller orchestrates until solution is complete or satisfactory. Use cases: AI systems, speech recognition, image interpretation, complex planning systems. Benefits: flexible problem-solving, easy to add knowledge sources, supports experimentation. Challenges: difficult to test deterministically, control strategy is complex, performance can be unpredictable. Related: publish-subscribe (knowledge sources react to blackboard changes). Example: speech recognition with phoneme, word, sentence knowledge sources progressively building understanding.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Broker architecture pattern?",
                "ground_truth": "The Broker pattern structures distributed systems with decoupled components that interact through a broker intermediary. The broker is responsible for coordinating communication, locating services, and forwarding requests. Components: 1) Clients (request services), 2) Servers (provide services), 3) Broker (mediates between clients and servers, handles service registration and lookup), 4) Bridges (connect multiple brokers). Benefits: location transparency (clients don't need to know where services are), interoperability, flexibility in adding/removing services. Examples: CORBA, message brokers (RabbitMQ), service registries (Consul, Eureka), RPC frameworks. Challenges: broker is single point of failure (needs replication), added latency, broker can become bottleneck. Modern variations: service mesh (decentralized broker via sidecars), API gateway (centralized entry point). Use when: distributed services need location transparency and dynamic discovery.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Space-Based Architecture?",
                "ground_truth": "Space-Based Architecture (SBA) achieves linear scalability by removing the central database bottleneck, using distributed in-memory data grids. Components: 1) Processing Unit (self-contained unit with application logic and in-memory data), 2) Virtualized Middleware (manages processing units - messaging grid, data grid, processing grid), 3) Data Pumps (asynchronously write to database), 4) Data Readers (load data on startup). Key concept: processing units contain both the application and the data they need, eliminating database as bottleneck. Data is replicated across units via data grid. Benefits: extreme scalability, high performance (in-memory), fault tolerance (data replication). Trade-offs: eventual consistency, complex data synchronization, higher memory costs, limited transaction support. Use for: high-throughput systems, auction sites, trading platforms, gaming. Technologies: Hazelcast, Apache Ignite, GigaSpaces.",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is a Modular Monolith?",
                "ground_truth": "A Modular Monolith is an architectural approach that maintains a single deployable unit (like a monolith) but with well-defined internal module boundaries (like microservices). Each module: has clear boundaries and interfaces, owns its data (separate schemas/tables), communicates via defined APIs, could potentially be extracted to a service later. Benefits: simpler deployment and operations than microservices, avoids distributed system complexity, enables team autonomy within modules, easier refactoring path to microservices if needed. Structure: modules organized by domain/feature (not technical layers), explicit dependencies between modules, private data per module. Enforcement: separate packages/projects per module, architectural fitness functions (ArchUnit, NDepend), code reviews. Use when: you want microservices benefits without distributed complexity, or as stepping stone before extracting services. Combines best of monolith (simplicity) and microservices (modularity).",
                "context": "Architectural pattern",
                "verified": True,
                "created_by": "expert"
            },
            
            # Concurrency Patterns
            {
                "question": "What is the Producer-Consumer pattern?",
                "ground_truth": "Producer-Consumer is a concurrency pattern where producer threads generate data and place it in a shared buffer, while consumer threads take data from the buffer and process it. The buffer decouples producers from consumers. Components: Producer (generates items), Consumer (processes items), Buffer/Queue (thread-safe shared storage). Synchronization: producers wait when buffer is full, consumers wait when buffer is empty (typically using condition variables, semaphores, or blocking queues). Benefits: decouples production from consumption rates, enables parallelism, handles burst traffic via buffering, producers and consumers can run at different speeds. Implementation: BlockingQueue (Java), queue.Queue (Python), channels (Go). Variations: multiple producers/consumers, bounded vs unbounded buffers, priority queues. Use for: task distribution, event processing, I/O buffering, work queues. Related: thread pools often implement this pattern.",
                "context": "Concurrency pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Thread Pool pattern?",
                "ground_truth": "Thread Pool pattern maintains a pool of worker threads that execute submitted tasks, avoiding the overhead of creating/destroying threads for each task. Components: Task Queue (holds pending tasks), Worker Threads (execute tasks from queue), Pool Manager (manages thread lifecycle, queue). Benefits: reduced thread creation overhead, controlled concurrency (limit active threads), resource management, improved performance for many short tasks. Configuration: core pool size, maximum pool size, keep-alive time, queue type (bounded vs unbounded). Rejection policies when pool/queue full: throw exception, run in caller thread, discard oldest, discard current. Implementation: ExecutorService (Java), ThreadPoolExecutor (Python), Task Parallel Library (.NET). Use for: web servers (handle requests), batch processing, parallel computations. Sizing: CPU-bound tasks (threads ≈ CPU cores), I/O-bound tasks (more threads to utilize wait time).",
                "context": "Concurrency pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the difference between concurrency and parallelism?",
                "ground_truth": "Concurrency is about dealing with multiple things at once (structure); Parallelism is about doing multiple things at once (execution). Concurrency: managing multiple tasks that can start, run, and complete in overlapping time periods; doesn't require multiple processors; focuses on responsiveness and structure. Example: single-core CPU switching between tasks. Parallelism: actually executing multiple tasks simultaneously; requires multiple processors/cores; focuses on throughput. Example: multi-core CPU running tasks on different cores. Relationship: parallelism is a subset of concurrency; concurrent programs may run in parallel on multiple cores. Concurrency patterns: async/await, event loops, coroutines. Parallelism patterns: data parallelism (same operation on multiple data), task parallelism (different operations simultaneously). Languages approach differently: Go (goroutines), JavaScript (single-threaded with async), Java (threads, CompletableFuture). Design concurrent first, parallelize for performance.",
                "context": "Concurrency fundamentals",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is a deadlock and how do you prevent it?",
                "ground_truth": "Deadlock occurs when two or more threads are blocked forever, each waiting for a resource held by another. Four necessary conditions (Coffman): 1) Mutual Exclusion (exclusive resource access), 2) Hold and Wait (hold resources while waiting for more), 3) No Preemption (resources can't be forcibly taken), 4) Circular Wait (circular chain of waiting). Prevention strategies: 1) Lock ordering (always acquire locks in consistent order - prevents circular wait), 2) Lock timeout (try-lock with timeout - prevents indefinite waiting), 3) Deadlock detection (detect and recover - kill one thread), 4) Avoid nested locks (minimize lock scope). Best practices: keep lock scope small, avoid calling external code while holding locks, use higher-level abstractions (concurrent collections), prefer lock-free algorithms. Tools: thread dumps show deadlocks, static analysis tools detect potential deadlocks. Example deadlock: Thread A holds Lock1 waiting for Lock2; Thread B holds Lock2 waiting for Lock1.",
                "context": "Concurrency fundamentals",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Actor model?",
                "ground_truth": "The Actor model is a concurrency paradigm where actors are the fundamental unit of computation. Each actor: has private state (no shared state), communicates exclusively via asynchronous messages, can create new actors, can send messages to known actors, processes one message at a time. Benefits: no shared state eliminates race conditions, location transparency (actors can be remote), fault tolerance (supervisor hierarchies), natural for distributed systems. Message passing: asynchronous, ordered delivery to each actor, actors have mailboxes (queues). Supervision: parent actors monitor children, handle failures with strategies (restart, stop, escalate). Implementations: Akka (JVM), Erlang/Elixir (OTP), Microsoft Orleans (.NET). Use for: highly concurrent systems, distributed systems, real-time applications. Trade-offs: debugging message flows is complex, eventual consistency, message ordering challenges across actors.",
                "context": "Concurrency model",
                "verified": True,
                "created_by": "expert"
            },
            
            # More Testing Concepts
            {
                "question": "What is mutation testing?",
                "ground_truth": "Mutation testing evaluates test suite quality by introducing small changes (mutations) to source code and checking if tests detect them. Process: 1) Generate mutants (modify code slightly), 2) Run tests against each mutant, 3) If tests fail, mutant is 'killed' (good); if tests pass, mutant 'survives' (tests are weak). Mutation operators: replace operators (+→-), modify constants, remove statements, change conditionals (>→>=), negate conditions. Mutation score = killed mutants / total mutants. High score indicates strong tests. Benefits: measures test effectiveness beyond code coverage, finds weak tests, improves test suite. Challenges: computationally expensive (many mutants), equivalent mutants (semantically identical, can't be killed), time-consuming. Tools: PIT (Java), mutmut (Python), Stryker (JavaScript). Use for: critical code paths, improving test quality, validating test-driven development. Complements but doesn't replace code coverage.",
                "context": "Testing methodology",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is property-based testing?",
                "ground_truth": "Property-based testing verifies that code satisfies properties (invariants) that should hold for all inputs, using randomly generated test data. Instead of example-based tests with specific inputs, you define properties the code must satisfy. Process: 1) Define property (invariant), 2) Framework generates random inputs, 3) Check property holds for all inputs, 4) On failure, framework shrinks input to minimal failing case. Example properties: reversing a list twice gives original (reverse(reverse(list)) == list), sorting produces sorted output, encoding then decoding gives original. Benefits: explores edge cases automatically, finds unexpected bugs, tests behavior not examples, better specification of requirements. Tools: QuickCheck (Haskell, original), Hypothesis (Python), jqwik (Java), fast-check (JavaScript). Use for: pure functions, data transformations, serialization, algorithms. Combine with example-based tests for documentation value.",
                "context": "Testing methodology",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Test Fixture and Test Double?",
                "ground_truth": "Test Fixture: the fixed state and environment used as baseline for running tests. Includes: test data, system under test setup, external dependencies preparation. Setup creates fixture before test; teardown cleans up after. Methods: setUp()/tearDown() (per test), setUpClass()/tearDownClass() (per class), fixtures files. Goal: consistent, reproducible test conditions. Test Doubles: objects that replace real dependencies during testing. Types: 1) Dummy - passed but never used, fills parameter lists, 2) Stub - provides canned answers to calls, 3) Spy - stub that records how it was called, 4) Mock - pre-programmed with expectations, verifies interactions, 5) Fake - working implementation with shortcuts (in-memory database). Use: Stubs for queries (return test data), Mocks for commands (verify calls happened). Libraries: Mockito (Java), unittest.mock (Python), Moq (.NET). Prefer real objects when practical; use doubles for slow, non-deterministic, or unavailable dependencies.",
                "context": "Testing concepts",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is code coverage and its limitations?",
                "ground_truth": "Code coverage measures how much code is executed by tests. Types: 1) Line/Statement coverage - lines executed, 2) Branch coverage - decision branches taken (if/else), 3) Path coverage - unique execution paths, 4) Condition coverage - boolean sub-expressions, 5) MC/DC - modified condition/decision coverage (safety-critical). Benefits: identifies untested code, indicates testing thoroughness, guides additional test writing. Limitations: high coverage ≠ good tests (can achieve 100% with no assertions), doesn't measure test quality, misses integration issues, may encourage testing unimportant code. Example: testing getter/setters achieves coverage without value. Guidance: 70-80% line coverage is typical target; focus on critical paths; combine with mutation testing for quality; don't game metrics. Tools: JaCoCo (Java), coverage.py (Python), Istanbul (JavaScript). Coverage is necessary but not sufficient for test quality.",
                "context": "Testing metrics",
                "verified": True,
                "created_by": "expert"
            },
            
            # API Design
            {
                "question": "What is GraphQL and how does it differ from REST?",
                "ground_truth": "GraphQL is a query language for APIs that allows clients to request exactly the data they need. Key differences from REST: 1) Single endpoint (POST /graphql) vs multiple endpoints, 2) Client specifies data shape vs server defines response, 3) Query, Mutation, Subscription types vs HTTP methods, 4) Strongly typed schema vs implicit structure. Benefits: no over-fetching (get only needed fields), no under-fetching (get related data in one request), introspection (schema is queryable), strong typing, real-time with subscriptions. Challenges: caching is complex (no HTTP caching), N+1 query problems, query complexity attacks, learning curve. Use GraphQL for: complex data relationships, mobile apps (bandwidth optimization), rapidly evolving APIs. Use REST for: simple CRUD, public APIs, caching-heavy scenarios. Tools: Apollo, Relay, graphql-js. Can coexist with REST in same system.",
                "context": "API design",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is gRPC and when should you use it?",
                "ground_truth": "gRPC is a high-performance RPC framework using Protocol Buffers for serialization and HTTP/2 for transport. Features: strongly typed contracts (.proto files), code generation for multiple languages, bidirectional streaming, deadline propagation, built-in authentication. Benefits: efficient binary serialization (smaller, faster than JSON), HTTP/2 multiplexing, streaming support, strong typing, excellent for service-to-service communication. Comparison to REST: faster but less human-readable, requires code generation, better for internal services, not browser-friendly (needs proxy). Use cases: microservices communication, real-time systems, polyglot environments, performance-critical applications. When not to use: public APIs (REST more accessible), browser clients (limited support), simple CRUD. Implementation: define service in .proto → generate stubs → implement service → call from client. Tools: protoc compiler, grpcurl (testing), Envoy (proxy).",
                "context": "API design",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is API versioning and what strategies exist?",
                "ground_truth": "API versioning manages changes to APIs while maintaining backward compatibility. Strategies: 1) URL Path (/api/v1/users) - simple, visible, but changes URLs, 2) Query Parameter (/api/users?version=1) - optional, less RESTful, 3) Header (Accept: application/vnd.api.v1+json) - clean URLs, harder to test, 4) Media Type versioning - in Accept header, true content negotiation. Best practices: version when breaking changes occur, support multiple versions simultaneously, deprecation timeline, version documentation. Breaking changes: removing fields, changing field types, removing endpoints, changing response structure. Non-breaking: adding optional fields, new endpoints, adding optional parameters. Semantic versioning for APIs: major (breaking), minor (features), patch (fixes). Migration: provide upgrade guides, use deprecation warnings, sunset timeline. Goal: minimize breaking changes through good initial design, additive changes, and tolerant readers.",
                "context": "API design",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is idempotency in API design?",
                "ground_truth": "Idempotency means that making the same request multiple times produces the same result as making it once. Critical for reliable distributed systems where retries are common. HTTP methods by design: GET (idempotent), PUT (idempotent), DELETE (idempotent), POST (not idempotent). Making POST idempotent: use idempotency keys (client-generated unique ID per request), server stores and checks key, duplicate requests return cached response. Example: payment API with X-Idempotency-Key header - client can safely retry without double-charging. Implementation: store idempotency key with request hash and response, check before processing, return stored response for duplicates. Benefits: safe retries, resilience to network failures, simpler client error handling. Considerations: key storage (TTL for cleanup), key scope (per user?), response caching duration. Essential for: payment processing, resource creation, any operation with side effects that shouldn't repeat.",
                "context": "API design",
                "verified": True,
                "created_by": "expert"
            },
            
            # Security Patterns
            {
                "question": "What is the principle of least privilege?",
                "ground_truth": "The Principle of Least Privilege (PoLP) states that every program, user, and system component should operate with the minimum privileges necessary to complete its function. Application: 1) Users - role-based access, no admin access unless required, 2) Services - limited database permissions (read-only if sufficient), 3) Processes - run as non-root, restricted file access, 4) API endpoints - scope-limited tokens, 5) Network - firewall rules limiting access. Benefits: limits damage from compromises, reduces attack surface, contains failures, supports audit compliance. Implementation: start with no permissions, add only what's needed; use roles/groups over individual permissions; regular access reviews; time-bound elevated access. Examples: database user with SELECT only (not DROP), microservice accessing only its data, Lambda functions with minimal IAM policies. Violation signs: everyone is admin, shared credentials, overly permissive IAM roles. Part of defense in depth strategy.",
                "context": "Security principles",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Cross-Site Scripting (XSS) and how to prevent it?",
                "ground_truth": "Cross-Site Scripting (XSS) is a vulnerability where attackers inject malicious scripts into web pages viewed by other users. Types: 1) Stored XSS - malicious script stored in database (comments, profiles), affects all viewers, 2) Reflected XSS - script in URL parameter reflected back in response, requires victim to click link, 3) DOM-based XSS - client-side JavaScript vulnerability, script never hits server. Prevention: 1) Output encoding/escaping - encode data based on context (HTML, JavaScript, URL, CSS), 2) Content Security Policy (CSP) - restrict script sources, 3) HttpOnly cookies - prevent JavaScript access to session cookies, 4) Input validation - whitelist allowed characters, 5) Use modern frameworks - React, Vue auto-escape by default. Libraries: DOMPurify for sanitization. Never trust user input; encode on output, not input. Test with OWASP ZAP, Burp Suite.",
                "context": "Security vulnerabilities",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Cross-Site Request Forgery (CSRF) and how to prevent it?",
                "ground_truth": "Cross-Site Request Forgery (CSRF) tricks authenticated users into performing unwanted actions on a web application. Attack: user is logged into bank.com; visits malicious site; malicious site sends request to bank.com using user's session cookie; bank.com executes action thinking it's legitimate user. Prevention: 1) CSRF tokens - unique, unpredictable token per session/request, validated server-side, 2) SameSite cookies - restrict cookie sending in cross-origin requests (SameSite=Strict or Lax), 3) Check Referer/Origin headers - verify request origin, 4) Re-authentication for sensitive actions - require password for critical operations. Token implementation: embed in forms as hidden field, include in AJAX headers, verify on server. Modern frameworks include CSRF protection: Django middleware, Spring Security. SameSite cookies provide good default protection in modern browsers. Always use POST/PUT/DELETE for state-changing operations (GET should be safe).",
                "context": "Security vulnerabilities",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is defense in depth security strategy?",
                "ground_truth": "Defense in depth is a security strategy using multiple layers of protection so that if one layer fails, others still provide security. Layers typically include: 1) Perimeter (firewalls, DMZ, WAF), 2) Network (segmentation, VPNs, intrusion detection), 3) Host (OS hardening, anti-malware, host firewalls), 4) Application (input validation, authentication, authorization, secure coding), 5) Data (encryption at rest/transit, access controls, backup). Principles: assume each layer will fail; no single point of failure; layers should be diverse (different technologies); detection at each layer. Additional practices: least privilege, security monitoring, incident response plan, regular security audits. Example: web app has WAF (perimeter), network segmentation (network), container security (host), OWASP practices (application), encrypted database (data). Each layer provides opportunity to detect and stop attacks. Defense in depth aligns with zero-trust architecture concepts.",
                "context": "Security strategy",
                "verified": True,
                "created_by": "expert"
            },
            
            # Cloud and Infrastructure Patterns
            {
                "question": "What is Infrastructure as Code?",
                "ground_truth": "Infrastructure as Code (IaC) manages and provisions infrastructure through machine-readable configuration files rather than manual processes. Approaches: 1) Declarative (desired state - Terraform, CloudFormation) - define end state, tool figures out changes, 2) Imperative (procedural - scripts, Ansible) - define exact steps. Benefits: version control for infrastructure, reproducibility (same config = same environment), automation (CI/CD for infrastructure), documentation as code, disaster recovery, consistency across environments. Tools: Terraform (multi-cloud), CloudFormation (AWS), ARM/Bicep (Azure), Pulumi (code-based), Ansible (configuration management). Best practices: modularize configurations, use variables for environments, store state securely, review changes before apply, immutable infrastructure (replace, don't modify). Workflow: code → version control → review → plan → apply. IaC enables DevOps and GitOps practices.",
                "context": "DevOps practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the difference between containers and virtual machines?",
                "ground_truth": "Virtual Machines (VMs) virtualize hardware, running complete operating systems with dedicated resources. VMs include: hypervisor, guest OS per VM, full isolation. Heavy but strong isolation. Containers virtualize the OS, sharing the host kernel while isolating applications. Containers include: container runtime (Docker), shared kernel, process-level isolation. Lightweight but share kernel. Comparison: Startup time: VMs (minutes), Containers (seconds). Size: VMs (GBs), Containers (MBs). Isolation: VMs (strong, separate kernels), Containers (process-level, shared kernel). Density: fewer VMs, many containers per host. Portability: containers more portable (consistent environment). Use VMs for: different OSes, strong isolation requirements, legacy apps. Use containers for: microservices, cloud-native apps, consistent dev/prod environments, rapid scaling. Often combined: containers on VMs for security + efficiency. Kubernetes orchestrates containers; VMware orchestrates VMs.",
                "context": "Infrastructure concepts",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Kubernetes and what problems does it solve?",
                "ground_truth": "Kubernetes (K8s) is a container orchestration platform for automating deployment, scaling, and management of containerized applications. Core concepts: Pods (smallest deployable unit, one or more containers), Deployments (manage replica sets), Services (stable networking), ConfigMaps/Secrets (configuration), Ingress (external access). Problems solved: 1) Scaling - automatic horizontal pod scaling based on metrics, 2) Self-healing - restarts failed containers, replaces unhealthy nodes, 3) Service discovery - built-in DNS, load balancing, 4) Rolling updates - zero-downtime deployments, rollback capability, 5) Resource management - CPU/memory limits, scheduling optimization. Architecture: Control Plane (API server, scheduler, controller manager, etcd) + Worker Nodes (kubelet, container runtime, kube-proxy). Ecosystem: Helm (package management), Istio (service mesh), Prometheus (monitoring). Use when: running multiple containers, need scaling/reliability, microservices architecture. Complexity trade-off for smaller applications.",
                "context": "Container orchestration",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is serverless architecture?",
                "ground_truth": "Serverless architecture runs code without managing servers; the cloud provider handles infrastructure, scaling, and availability. Types: 1) Function as a Service (FaaS) - AWS Lambda, Azure Functions, Google Cloud Functions - event-triggered functions, 2) Backend as a Service (BaaS) - managed services for auth, database, storage (Firebase, Auth0). Characteristics: pay-per-execution (no idle costs), automatic scaling (zero to thousands), stateless functions, event-driven (HTTP, queue, schedule triggers). Benefits: no server management, cost-effective for variable load, fast time to market, focus on business logic. Challenges: cold starts (startup latency), vendor lock-in, debugging/monitoring complexity, execution time limits, statelessness constraints. Use for: event processing, APIs with variable load, scheduled tasks, webhooks. Not suitable for: long-running processes, high-performance computing, applications needing persistent connections. Combine with containers for hybrid approach.",
                "context": "Cloud architecture",
                "verified": True,
                "created_by": "expert"
            },
            
            # More Database Concepts
            {
                "question": "What is the difference between SQL and NoSQL databases?",
                "ground_truth": "SQL databases are relational, using tables with predefined schemas and SQL language. Characteristics: ACID transactions, strong consistency, normalized data, joins for relationships. Examples: PostgreSQL, MySQL, Oracle. NoSQL databases are non-relational with flexible schemas. Types: 1) Document (MongoDB, CouchDB) - JSON-like documents, 2) Key-Value (Redis, DynamoDB) - simple lookup, 3) Column-family (Cassandra, HBase) - column-based storage, 4) Graph (Neo4j) - relationships as first-class. Characteristics: horizontal scaling, eventual consistency (often), schema flexibility. Choose SQL for: complex queries, ACID requirements, well-defined schema, reporting. Choose NoSQL for: large scale, flexible schema, specific access patterns, high write throughput. Many systems use both (polyglot persistence). Modern SQL databases adopt NoSQL features (JSON columns); NoSQL adds SQL-like queries. Decision factors: data structure, query patterns, consistency requirements, scale needs.",
                "context": "Database design",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is database replication?",
                "ground_truth": "Database replication copies data across multiple database servers for availability, fault tolerance, and performance. Types: 1) Master-Slave/Primary-Replica - one writable master, multiple read replicas; reads distributed across replicas; simple but master is bottleneck, 2) Master-Master/Multi-Master - multiple writable nodes; complex conflict resolution needed, 3) Synchronous - transaction waits for all replicas; strong consistency, higher latency, 4) Asynchronous - transaction commits before replicating; lower latency, potential data loss. Use cases: read scaling (distribute reads), high availability (failover to replica), geographic distribution (local reads), disaster recovery (off-site backup). Considerations: replication lag (stale reads from replica), conflict resolution (multi-master), failover automation, network bandwidth. Technologies: MySQL replication, PostgreSQL streaming replication, MongoDB replica sets. Combine with sharding for write scaling. Trade-offs per CAP theorem.",
                "context": "Database infrastructure",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is a database transaction isolation level?",
                "ground_truth": "Transaction isolation levels control how transaction integrity is visible to other concurrent transactions. Levels (weakest to strongest): 1) Read Uncommitted - can read uncommitted changes (dirty reads); rarely used, 2) Read Committed - only reads committed data; can have non-repeatable reads, 3) Repeatable Read - same query returns same results within transaction; can have phantom reads (new rows), 4) Serializable - transactions execute as if serial; no concurrency anomalies. Anomalies prevented per level: dirty reads (Read Committed+), non-repeatable reads (Repeatable Read+), phantom reads (Serializable only). Trade-off: higher isolation = more locking = lower concurrency = lower throughput. Default varies: PostgreSQL (Read Committed), MySQL InnoDB (Repeatable Read). Set per transaction based on needs. MVCC (Multi-Version Concurrency Control) in modern databases provides isolation without heavy locking. Choose lowest acceptable isolation for best performance.",
                "context": "Database transactions",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is a materialized view?",
                "ground_truth": "A materialized view is a database object storing the results of a query physically, unlike regular views which execute the query each time. Benefits: dramatically faster reads for complex queries, precomputed aggregations, reduces database load for repeated queries. Trade-offs: storage space, stale data (needs refresh), refresh overhead. Refresh strategies: 1) Complete refresh - recompute entirely, simple but expensive, 2) Incremental/fast refresh - apply changes only, requires change tracking (materialized view logs), 3) On-demand - manual trigger, 4) On-commit - refresh after each transaction (expensive), 5) Scheduled - periodic refresh. Use cases: reporting dashboards, complex aggregations, denormalized data for reads, caching query results. Implementation varies by database: Oracle (full support), PostgreSQL (manual refresh), MySQL (not native). Design: balance freshness requirements against refresh cost. Combine with CQRS pattern for read-optimized models.",
                "context": "Database optimization",
                "verified": True,
                "created_by": "expert"
            },
            
            # More DDD Concepts
            {
                "question": "What is the Repository pattern in Domain-Driven Design?",
                "ground_truth": "In DDD, Repository is a tactical pattern providing collection-like interface for accessing aggregates, mediating between domain and data mapping layers. Characteristics: one repository per aggregate root, uses domain language (not SQL), returns complete aggregates, abstracts persistence mechanism. Interface defined in domain layer; implementation in infrastructure layer (Dependency Inversion). Methods: findById(), findBySpecification(), save(), remove(). NOT for querying across aggregates (use read models/query services). Benefits: testable domain logic (mock repository), technology agnostic domain, encapsulates query construction, provides illusion of in-memory collection. Anti-patterns: generic repository (loses domain meaning), exposing IQueryable (leaks ORM), repository per entity (should be per aggregate). Testing: use in-memory fake repository for unit tests; real database for integration tests. Repositories work with Unit of Work for transaction management.",
                "context": "DDD tactical patterns",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Factory pattern in Domain-Driven Design?",
                "ground_truth": "In DDD, Factory is a tactical pattern responsible for creating complex aggregates and entities while encapsulating creation logic. When to use: complex object creation involving validation, creation requires domain knowledge, multiple entities must be created together, object creation involves enforcing invariants. Types: 1) Factory Method on aggregate root - create child entities (Order.addLineItem()), 2) Standalone Factory - create aggregates with complex requirements (OrderFactory.createFromCart()), 3) Abstract Factory - create families of related objects. Factory responsibilities: create valid aggregates (enforce invariants), reconstitute from persistence (separate from regular creation), generate IDs if needed. NOT repository's job: repositories retrieve existing aggregates; factories create new ones. Reconstitution vs Creation: reconstitution rebuilds from stored data (relaxes some validation); creation is fresh construction. Factory encapsulates 'how' of creation, keeping domain model focused on behavior.",
                "context": "DDD tactical patterns",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the difference between Entity and Value Object in DDD?",
                "ground_truth": "Entities have unique identity that persists over time; equality is based on identity, not attributes. Characteristics: tracked across state changes, mutable, have lifecycle, require ID management. Examples: User (userId), Order (orderId), Product (SKU). Value Objects are defined by their attributes; equality is based on all attributes matching. Characteristics: immutable (create new instance for changes), no identity, interchangeable if equal, side-effect-free operations. Examples: Money, Address, DateRange, Email. Design guidance: prefer Value Objects when possible (simpler, safer). Entity identification: ask 'does it matter which one?' - if two users have same name, are they different? Yes → Entity. If two $10 amounts are interchangeable? Yes → Value Object. Implementation: Entities override equals() by ID; Value Objects override equals() by all fields. Value Objects can be embedded in Entities. In persistence: Entities typically map to tables with IDs; Value Objects can be embedded columns or separate tables.",
                "context": "DDD tactical patterns",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Context Mapping in Domain-Driven Design?",
                "ground_truth": "Context Mapping documents relationships between bounded contexts, showing how they integrate and communicate. Relationship patterns: 1) Shared Kernel - shared subset of model, tight coupling, requires coordination, 2) Customer-Supplier - upstream (supplier) and downstream (customer), downstream can request features, 3) Conformist - downstream adopts upstream model without influence, 4) Anti-Corruption Layer - downstream translates to protect its model from upstream, 5) Open Host Service - upstream provides well-defined API for integrators, 6) Published Language - shared schema format (XML schema, JSON schema), 7) Separate Ways - no integration, independence, 8) Partnership - mutual coordination, evolve together. Mapping process: identify bounded contexts, identify integration points, classify relationships, document on context map diagram. Context map guides: team collaboration, integration strategy, technology choices. Update as system evolves. Used for: planning migrations, understanding dependencies, identifying coupling.",
                "context": "DDD strategic patterns",
                "verified": True,
                "created_by": "expert"
            },
            
            # Performance Patterns
            {
                "question": "What is the N+1 query problem and how to solve it?",
                "ground_truth": "The N+1 query problem occurs when code executes one query to get N records, then N additional queries to fetch related data for each record. Example: fetch all orders (1 query), then for each order fetch customer (N queries) = N+1 total. Performance impact: excessive database round trips, high latency, database load. Detection: SQL query logging, ORM query monitoring, slow response times. Solutions: 1) Eager loading - fetch related data upfront (JOIN or separate batch query), 2) JOIN queries - single query with joined tables, 3) Batch loading - load related data in batches (WHERE id IN (...)), 4) Subquery loading - subquery for related data. ORM specific: Entity Framework (.Include()), Django (select_related(), prefetch_related()), Hibernate (@Fetch, JOIN FETCH), ActiveRecord (.includes()). Prevention: review generated SQL, use query profiling, design APIs to fetch needed relations. Trade-off: eager loading may fetch unneeded data; lazy loading may cause N+1.",
                "context": "Performance optimization",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is lazy loading vs eager loading?",
                "ground_truth": "Lazy Loading defers loading of related data until it's actually accessed. The relationship is loaded on first access. Benefits: loads only what's needed, simpler initial queries. Drawbacks: N+1 query problem, unpredictable query timing, harder to track database calls. Eager Loading loads related data immediately with the initial query. Uses JOINs or additional queries upfront. Benefits: predictable performance, avoids N+1 problem, all data available immediately. Drawbacks: may load unused data, larger initial queries. Choosing: Lazy loading when relationships rarely needed; Eager loading when relationships always/usually needed. Hybrid approach: default to lazy, explicitly eager-load known needs. ORM settings: Entity Framework (lazy loading via proxies), Hibernate (FetchType.LAZY/EAGER), Django (lazy by default, prefetch_related for eager). Best practice: be explicit about loading strategy; don't rely on ORM defaults; monitor generated queries.",
                "context": "Performance optimization",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is connection pooling?",
                "ground_truth": "Connection pooling maintains a cache of database connections that can be reused, avoiding the overhead of creating new connections for each request. Problem without pooling: connection creation is expensive (TCP handshake, authentication, protocol negotiation); under load, many connections exhaust resources. How it works: pool maintains min/max connections; requests borrow connection from pool; after use, connection returns to pool; pool manages lifecycle, validation. Configuration: minimum pool size, maximum pool size, connection timeout, idle timeout, validation query. Benefits: reduced latency (reuse established connections), resource efficiency, controlled database connections. Considerations: connection leaks (not returning to pool), pool exhaustion (too many concurrent requests), stale connections (need validation). Technologies: HikariCP (Java, fastest), c3p0, Apache DBCP, built into most ORMs and frameworks. Sizing: depends on workload, database limits; monitor pool metrics. Similar concept applies to HTTP clients, thread pools.",
                "context": "Performance optimization",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is content delivery network (CDN)?",
                "ground_truth": "A Content Delivery Network (CDN) is a geographically distributed network of proxy servers that cache content closer to end users, reducing latency and origin server load. How it works: user requests content → CDN edge server responds if cached, else fetches from origin → caches for future requests. Content types: static (images, CSS, JS, videos), dynamic (personalized content with edge computing). Benefits: reduced latency (geographic proximity), reduced origin load, improved availability (distributed), DDoS protection, bandwidth cost reduction. CDN features: SSL/TLS termination, image optimization, compression, cache rules, edge functions, analytics. Cache control: TTL settings, cache headers (Cache-Control, ETag), purge APIs. Providers: Cloudflare, AWS CloudFront, Akamai, Fastly. Configuration: point DNS to CDN, configure origin, set cache rules. Trade-offs: cache invalidation complexity, cost for high bandwidth, privacy considerations. Essential for global applications.",
                "context": "Performance and scalability",
                "verified": True,
                "created_by": "expert"
            },
            
            # Software Engineering Practices
            {
                "question": "What is pair programming?",
                "ground_truth": "Pair programming is an agile practice where two programmers work together at one workstation: the Driver writes code while the Navigator reviews, suggests, and thinks strategically. Roles rotate frequently. Benefits: real-time code review (fewer bugs), knowledge sharing (reduces silos), collective code ownership, faster onboarding, maintains focus, better design decisions (two perspectives). Styles: 1) Driver-Navigator (classic), 2) Ping-Pong (alternating TDD roles), 3) Strong-style (navigator thinks, driver types). When effective: complex problems, learning new codebase, critical code, onboarding. Challenges: personality clashes, fatigue, perceived inefficiency (two developers one output). Research: pairs produce fewer defects, similar time to completion considering rework avoided. Remote pairing: screen sharing tools, VS Code Live Share, Tuple. Not for all tasks: routine work, spikes, personal flow state tasks. Part of Extreme Programming (XP) practices. Complements code review, doesn't replace it.",
                "context": "Development practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is code review and why is it important?",
                "ground_truth": "Code review is systematic examination of source code by peers before merging. Purpose: find defects, ensure quality standards, share knowledge, maintain consistency. Process: developer submits pull/merge request → reviewers examine code, leave comments → developer addresses feedback → approval → merge. What to review: correctness, design, readability, test coverage, security, performance, coding standards. Benefits: catches bugs early (cheaper to fix), knowledge sharing across team, mentorship, consistency, collective ownership. Best practices: small PRs (easier to review), meaningful PR description, automated checks first (linting, tests), constructive feedback (focus on code not person), timely reviews (don't block too long). Metrics: time to review, PR size, comment patterns. Tools: GitHub PRs, GitLab MRs, Bitbucket, Gerrit, Crucible. Review checklist helps consistency. Automation: pre-commit hooks, CI checks, static analysis reduce manual review burden. Code review culture matters - should be collaborative, not adversarial.",
                "context": "Development practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is technical documentation and best practices?",
                "ground_truth": "Technical documentation explains how software works and how to use it. Types: 1) API documentation - endpoints, parameters, responses, examples, 2) Architecture documentation - system design, components, decisions, 3) Code documentation - comments, docstrings, README, 4) User documentation - guides, tutorials, FAQs, 5) Operations documentation - deployment, monitoring, troubleshooting. Best practices: keep documentation close to code (README in repo), document why not just what, use examples, maintain alongside code changes, automate where possible (API docs from code), version documentation, make it searchable. Tools: OpenAPI/Swagger (APIs), JSDoc/Sphinx (code), Docusaurus/GitBook (sites), diagrams as code (Mermaid, PlantUML). Architecture Decision Records (ADRs) capture why decisions were made. Documentation as code: stored in version control, reviewed in PRs, deployed automatically. Signs of good docs: new developers can onboard, answers common questions, reduces repeated explanations.",
                "context": "Development practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is feature flagging?",
                "ground_truth": "Feature flags (feature toggles) are mechanisms to enable/disable functionality without deploying new code. Types: 1) Release toggles - control unfinished features, remove after launch, 2) Experiment toggles - A/B testing, multivariate tests, 3) Ops toggles - operational controls (circuit breakers), 4) Permission toggles - feature access by user/group. Benefits: decouple deployment from release, safe experimentation, gradual rollouts (canary, percentage-based), instant rollback, testing in production. Implementation: flag evaluation in code (if feature enabled), central flag management, targeting rules (user segments, percentages). Best practices: short-lived flags (remove after full rollout), flag naming conventions, test both paths, audit flag usage, document flag purpose. Tools: LaunchDarkly, Split, Unleash, ConfigCat, custom solutions. Technical debt: old flags are dead code; schedule removal. Trunk-based development relies heavily on feature flags to keep main branch deployable.",
                "context": "Development practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is trunk-based development?",
                "ground_truth": "Trunk-based development is a source control strategy where developers integrate small, frequent changes directly to main branch (trunk), avoiding long-lived feature branches. Practices: commit directly to trunk or use short-lived branches (<1 day), continuous integration, feature flags for incomplete work, code review before/after merge, always-green trunk. Benefits: reduced merge conflicts, faster feedback, continuous integration, simpler workflow, forces small batches. Enabling practices: comprehensive automated tests, feature flags, code review, pair programming, observability. Comparison to GitFlow: GitFlow uses multiple long-lived branches (develop, release, feature); trunk-based is simpler, faster, but requires more discipline. Trunk-based supports: continuous deployment, DevOps practices, high-performing teams (per DORA research). Challenges: requires mature testing, discipline for small commits, feature flags management. Start with short-lived branches if team isn't ready for direct trunk commits.",
                "context": "Version control practices",
                "verified": True,
                "created_by": "expert"
            },
            
            # More Refactoring Techniques
            {
                "question": "What is the Extract Method refactoring?",
                "ground_truth": "Extract Method takes a code fragment and turns it into a method with a name explaining its purpose. When to use: method is too long, code needs explanation (comment → method name), same code appears in multiple places. Steps: 1) Create new method named for what it does, 2) Copy extracted code to new method, 3) Replace old code with method call, 4) Pass needed variables as parameters, 5) Handle return values and local variables. Benefits: shorter methods, readable code, reusable logic, easier testing, single responsibility. Example: extracting validation logic from a long method into validateOrder(), calculateTotal(), notifyCustomer(). Considerations: don't extract too small (one-line methods rarely help), name reveals intention, watch for feature envy (method uses mostly other object's data). Inverse: Inline Method - when method body is as clear as its name. IDEs automate this refactoring safely.",
                "context": "Refactoring techniques",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Replace Conditional with Polymorphism refactoring?",
                "ground_truth": "Replace Conditional with Polymorphism converts conditional logic (switch/if-else based on type) into polymorphic method calls on subclasses. When to use: switch statements based on type code, same conditional structure repeated across methods, adding new type requires modifying multiple places. Steps: 1) Create class hierarchy for the type code, 2) Move conditional branches into overridden methods in each subclass, 3) Replace conditionals with polymorphic calls. Before: if (bird.type == 'European') {...} else if (bird.type == 'African') {...}. After: bird.getSpeed() where European/African birds override getSpeed(). Benefits: easier to add new types (just add class), eliminates duplicate conditional logic, follows Open/Closed Principle. Trade-offs: more classes, overkill for simple conditionals. Alternative: Strategy pattern when behavior should be swappable at runtime. Related: Replace Type Code with Subclasses, Replace Type Code with State/Strategy.",
                "context": "Refactoring techniques",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Introduce Parameter Object refactoring?",
                "ground_truth": "Introduce Parameter Object replaces a group of parameters that naturally go together with a single object that encapsulates them. When to use: multiple methods have the same parameter group, data clump code smell, parameter lists are long. Steps: 1) Create class for the parameter group, 2) Add fields for each parameter, 3) Update method signatures to take new object, 4) Update all callers, 5) Consider moving behavior to the parameter object. Before: createAppointment(startDate, endDate, description, location, attendees). After: createAppointment(appointmentDetails). Benefits: shorter parameter lists, data clumps become explicit concepts, can move related behavior to new object, easier to add new parameters. Common examples: DateRange (start, end), Money (amount, currency), Address (street, city, zip, country), Coordinates (x, y). Related: Preserve Whole Object (pass object instead of extracting its parts). The parameter object often becomes a Value Object in DDD terms.",
                "context": "Refactoring techniques",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Move Method refactoring?",
                "ground_truth": "Move Method transfers a method to the class it uses most (or is most used by), improving cohesion and reducing coupling. When to use: feature envy (method uses more features of another class), method doesn't fit current class's responsibility, related methods scattered across classes. Steps: 1) Identify target class, 2) Copy method to target class, 3) Turn old method into delegating method or remove, 4) Update all references, 5) Adjust for any needed parameters (former host may become parameter). Signs a method should move: uses many fields/methods from another class, changes together with another class, natural fit elsewhere. Benefits: improved cohesion, reduced coupling, clearer responsibilities. Related: Move Field, Extract Class (when moving multiple members). Consider: sometimes the data should move to the method's class instead. Feature Envy is strong signal for this refactoring. IDE support makes this safe and easy.",
                "context": "Refactoring techniques",
                "verified": True,
                "created_by": "expert"
            },
            
            # Additional Design Concepts
            {
                "question": "What is separation of concerns?",
                "ground_truth": "Separation of Concerns (SoC) is a design principle for dividing a program into distinct sections, each addressing a separate concern (a set of related functionality). Examples: MVC separates model, view, controller; layered architecture separates presentation, business, data; CSS separates styling from HTML structure. Benefits: easier maintenance (change one concern without affecting others), better testability (test concerns independently), improved readability (focused code), parallel development (different teams on different concerns), reusability (concerns can be reused). Implementation: modules/classes per concern, layered architecture, aspect-oriented programming for cross-cutting concerns, microservices for operational separation. Cross-cutting concerns (logging, security, caching) don't fit cleanly - handle with AOP, middleware, decorators. Anti-patterns: God class (mixed concerns), UI code with business logic, data access scattered everywhere. SoC is foundational to maintainable software; enables Single Responsibility Principle.",
                "context": "Design principles",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is a software architecture decision record (ADR)?",
                "ground_truth": "An Architecture Decision Record (ADR) is a document capturing an important architectural decision along with its context and consequences. Structure: Title, Date, Status (proposed/accepted/deprecated/superseded), Context (what is the issue), Decision (what we decided), Consequences (results, trade-offs). Benefits: preserves decision rationale (why, not just what), helps new team members understand choices, prevents revisiting settled decisions, creates institutional memory. When to write: significant architectural decisions, technology choices, design pattern selections, integration approaches. Best practices: store in repository with code, link related ADRs, review periodically, mark deprecated/superseded, keep concise. Tools: Markdown files, tools like adr-tools, log4brains. Example: 'ADR-001: Use PostgreSQL for primary database' - context, alternatives considered, decision, trade-offs. Part of documentation as code philosophy. Promotes lightweight but sufficient documentation.",
                "context": "Architecture practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Conway's Law?",
                "ground_truth": "Conway's Law states that organizations design systems that mirror their communication structures. Original quote: 'Any organization that designs a system will produce a design whose structure is a copy of the organization's communication structure.' Implications: team boundaries become system boundaries, siloed teams create siloed systems, cross-functional teams create integrated systems. Inverse Conway Maneuver: structure teams to achieve desired architecture. Examples: if frontend/backend/database are separate teams, you get layered architecture; if teams own features end-to-end, you get more modular systems. In microservices: one team per service works well; shared service across teams creates coordination overhead. Team Topologies framework leverages Conway's Law: stream-aligned teams, platform teams, enabling teams, complicated subsystem teams. Recognize: architecture and organization must evolve together. When restructuring systems, consider team restructuring. Conway's Law is inevitable - work with it, not against it.",
                "context": "Software organization",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is technical spike in agile development?",
                "ground_truth": "A technical spike is a time-boxed investigation to explore a technical question, reduce uncertainty, or prove feasibility before committing to a user story. Purpose: answer technical questions, evaluate technologies, prototype solutions, estimate effort for complex work. Types: 1) Technical spike - research technical approach, 2) Functional spike - explore user requirements. Process: define question to answer, time-box strictly (typically 1-2 days), document findings, present to team, inform estimation. Output: knowledge, not production code (though prototypes may inform implementation). Examples: can we integrate with payment gateway X?, how do we migrate legacy data?, what's the performance of approach A vs B? When to use: significant technical uncertainty, new technology evaluation, complex estimation, risk reduction. Not for: avoiding commitment, gold-plating, bypassing normal process. Spike stories are part of backlog, typically not pointed (or separate spike point budget). After spike, create actual stories with better estimates.",
                "context": "Agile practices",
                "verified": True,
                "created_by": "expert"
            },
            
            # Error Handling Patterns
            {
                "question": "What are error handling best practices?",
                "ground_truth": "Error handling best practices ensure robust, maintainable code. Principles: 1) Fail fast - detect errors early, fail immediately, 2) Be specific - catch specific exceptions, not generic Exception, 3) Handle at appropriate level - where you can do something useful, 4) Don't swallow exceptions - at minimum log them, 5) Provide context - meaningful error messages. Patterns: 1) Return error codes (Go style) - explicit handling, no exceptions, 2) Exceptions - for exceptional conditions, not control flow, 3) Result types (Rust, functional) - return Success or Failure, force handling, 4) Null Object - return neutral object instead of null. Clean code: avoid returning null, throw only checked exceptions caller can handle, don't use exceptions for flow control, wrap third-party exceptions. Logging: log with context (what failed, relevant data), appropriate level (error vs warning), structured logging for searchability. User messages vs logs: user messages are friendly; logs are detailed and technical.",
                "context": "Code quality",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Retry pattern?",
                "ground_truth": "The Retry pattern handles transient failures by automatically re-attempting failed operations. Use for: transient failures (network timeouts, temporary unavailability, rate limiting). Not for: permanent failures (invalid credentials, resource not found). Strategies: 1) Fixed delay - wait constant time between retries, 2) Exponential backoff - double wait time each retry (1s, 2s, 4s, 8s), 3) Jitter - add randomness to prevent thundering herd, 4) Linear backoff - increase by constant amount. Configuration: maximum retries, delay algorithm, retryable exceptions. Implementation: wrap operation in retry loop, detect retryable failures, apply delay strategy. Libraries: Polly (.NET), Resilience4j (Java), tenacity (Python). Combine with Circuit Breaker: retries for transient failures, circuit breaker for sustained failures. Considerations: idempotency (retried operation should be safe to repeat), timeout budget (total time limit), which errors to retry. Example: retry HTTP 503 with exponential backoff, max 3 attempts, 30 second total timeout.",
                "context": "Resilience pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Timeout pattern?",
                "ground_truth": "The Timeout pattern limits how long an operation can take, preventing indefinite waiting and resource exhaustion. Implementation levels: 1) Connection timeout - time to establish connection, 2) Read/socket timeout - time waiting for data, 3) Request timeout - total time for entire request, 4) Business operation timeout - encompassing all steps. Benefits: prevents resource exhaustion (threads stuck waiting), maintains responsiveness, enables graceful degradation, improves system stability. Configuration: set reasonable timeouts for all external calls, consider normal and peak times, shorter for user-facing paths. Error handling: timeout exceptions should trigger fallback behavior, logging, possibly retry. Propagation: request timeout should decrease through call chain (downstream gets remaining time). Libraries: HTTP clients have timeout configs, CompletableFuture.orTimeout() (Java), asyncio.wait_for() (Python). Related: Circuit Breaker opens when timeouts frequent. Common mistake: no timeout = system hangs when dependency unavailable. Default to explicit timeouts everywhere.",
                "context": "Resilience pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is graceful degradation?",
                "ground_truth": "Graceful degradation is a design approach where a system continues operating with reduced functionality when some components fail, rather than failing completely. Examples: 1) Show cached data when database unavailable, 2) Disable recommendations but continue showing products, 3) Queue requests when processing system is down, 4) Show default values when personalization fails. Implementation: identify critical vs optional features, implement fallbacks for optional features, use feature flags, monitor degraded state. Patterns: Circuit Breaker (return fallback when open), Cache (serve stale data), Queue (buffer requests), Default values (static fallback). Related: fail-safe design (system enters safe state on failure), fault tolerance (system handles faults without user impact). Trade-offs: degraded experience vs no experience, complexity of fallback paths. Testing: simulate failures to verify degradation works (chaos engineering). Design principle: identify what's essential, protect essential functions, gracefully reduce non-essential. User communication: inform users of limited functionality.",
                "context": "Resilience design",
                "verified": True,
                "created_by": "expert"
            },
            
            # Messaging Patterns
            {
                "question": "What is the difference between message queue and publish-subscribe?",
                "ground_truth": "Message Queue (Point-to-Point): one producer sends message, one consumer receives it. Message is consumed by exactly one consumer. Use for: task distribution, work queues, load balancing across workers. Examples: job processing, order processing. Technologies: RabbitMQ queues, AWS SQS, Azure Queue Storage. Publish-Subscribe (Pub/Sub): publisher sends message to topic, all subscribers receive copy. Message is broadcast to all interested parties. Use for: event notification, broadcasting, system integration. Examples: stock price updates, event-driven architecture. Technologies: Kafka topics, RabbitMQ exchanges/bindings, AWS SNS, Google Pub/Sub. Key differences: consumer count (one vs many), message handling (consumed once vs broadcast), coupling (producer may know consumer vs complete decoupling). Combined patterns: publish to topic → queue per subscriber (fan-out). Choose based on: should multiple systems react (pub/sub) or one system process (queue)?",
                "context": "Messaging patterns",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is message ordering and how to handle it?",
                "ground_truth": "Message ordering ensures messages are processed in the order they were sent. Challenges in distributed systems: multiple producers, multiple consumers, network delays, retries, partitioning. Ordering guarantees: 1) No ordering (parallel processing, highest throughput), 2) Per-key/partition ordering (messages with same key in order), 3) Global ordering (all messages in order, limited scalability). Kafka approach: ordered within partition, partition key determines placement. SQS: standard queues best-effort ordering, FIFO queues strict per message group. Handling strategies: 1) Use per-entity ordering key (user_id, order_id), 2) Include sequence numbers, detect/reorder gaps, 3) Design for idempotency (reprocessing is safe), 4) Accept eventual consistency. Trade-offs: strict ordering limits parallelism and throughput. Design questions: does order matter for correctness? per-entity or global? can you handle out-of-order? Many systems work correctly with eventual consistency; evaluate actual requirements.",
                "context": "Messaging patterns",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is a dead letter queue?",
                "ground_truth": "A Dead Letter Queue (DLQ) is a special queue where messages that cannot be processed successfully are sent for later analysis and handling. When messages go to DLQ: processing failures after max retries, message format errors, processing timeout, explicit rejection. Benefits: prevents poison messages (bad messages blocking queue), preserves failed messages for debugging, enables manual review and reprocessing, keeps main queue flowing. Implementation: configure max delivery attempts, specify DLQ destination, set message metadata (original queue, error reason, attempt count, timestamp). Monitoring: alert on DLQ depth, investigate patterns in failed messages. Handling DLQ messages: fix consumer bug and reprocess, fix message data and resubmit, discard if truly invalid. Technologies: all major message brokers support DLQ (RabbitMQ dead letter exchanges, SQS DLQ, Kafka DLQ patterns). Related: poison message handling. DLQ is essential for production messaging systems - without it, bad messages can halt processing.",
                "context": "Messaging patterns",
                "verified": True,
                "created_by": "expert"
            },
            
            # More Modern Practices
            {
                "question": "What is GitOps?",
                "ground_truth": "GitOps is an operational framework using Git as the single source of truth for declarative infrastructure and applications. Principles: 1) Declarative (desired state, not procedures), 2) Versioned and immutable (Git history), 3) Pulled automatically (agents sync from Git), 4) Continuously reconciled (agents ensure actual matches desired). Workflow: developer pushes to Git → automation syncs to cluster → cluster state matches Git. Benefits: auditability (Git history), rollback (git revert), consistency, security (no direct cluster access needed), developer experience (familiar Git workflow). Components: Git repository with manifests, GitOps operator (ArgoCD, Flux), automated deployment pipeline. Push vs Pull: traditional CI/CD pushes changes; GitOps operators pull changes. Scope: infrastructure, Kubernetes manifests, application config, environment configuration. Part of larger DevOps movement; specifically suited for Kubernetes but applicable broadly. Enables self-service, standardization, compliance.",
                "context": "DevOps practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is observability in software systems?",
                "ground_truth": "Observability is the ability to understand a system's internal state by examining its outputs. Three pillars: 1) Logs - timestamped records of discrete events (what happened when), 2) Metrics - numeric measurements over time (counters, gauges, histograms), 3) Traces - request flow across services (distributed tracing). Logs provide detail and context; metrics show trends and aggregates; traces show request paths. Modern addition: events, profiles. Key practices: structured logging (JSON), metric aggregation, correlation IDs across services, sampling for high-volume data. Tools: Prometheus/Grafana (metrics), ELK/Loki (logs), Jaeger/Zipkin (traces), Datadog/New Relic (all-in-one). Observability vs monitoring: monitoring alerts when things break; observability helps understand why. Design for observability: instrument code, propagate context, emit meaningful signals. Use for: debugging production issues, performance optimization, capacity planning, understanding system behavior. Essential for microservices and distributed systems.",
                "context": "Operations practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is Site Reliability Engineering (SRE)?",
                "ground_truth": "Site Reliability Engineering (SRE), originated at Google, applies software engineering principles to operations problems. Key concepts: 1) SLI (Service Level Indicator) - metric measuring service behavior (latency, availability), 2) SLO (Service Level Objective) - target value for SLI (99.9% availability), 3) SLA (Service Level Agreement) - contract with consequences for missing SLO, 4) Error Budget - allowed unreliability (100% - SLO), enables release velocity vs reliability balance. Practices: eliminate toil through automation, measure everything, blameless postmortems, capacity planning, on-call rotations, runbooks. Philosophy: operations as software problem, 50% ops/50% dev for SREs, reliability is a feature. Comparison to DevOps: DevOps is culture/philosophy; SRE is implementation with specific practices. Error budget policy: when budget depleted, focus on reliability over features. Tools: monitoring, alerting, automation, incident management. SRE enables sustainable velocity by explicitly balancing reliability with change.",
                "context": "Operations practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What are the DORA metrics?",
                "ground_truth": "DORA metrics are four key indicators of software delivery performance, identified by the DevOps Research and Assessment team through research. The metrics: 1) Deployment Frequency - how often code deploys to production (elite: multiple times per day), 2) Lead Time for Changes - time from commit to production (elite: less than one hour), 3) Change Failure Rate - percentage of deployments causing failure requiring remediation (elite: 0-15%), 4) Time to Restore Service - time to recover from failure (elite: less than one hour). High performers excel at all four; speed and stability reinforce each other. Improvement practices: continuous integration, trunk-based development, automated testing, continuous delivery, monitoring, blameless culture. Measurement: instrument deployment pipeline, track incidents, analyze trends. Use for: assessing DevOps maturity, focusing improvement efforts, demonstrating value of practices. Research shows high DORA performers have higher organizational performance. Metrics drive behavior - use thoughtfully.",
                "context": "DevOps metrics",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is semantic versioning?",
                "ground_truth": "Semantic Versioning (SemVer) is a versioning scheme using three numbers: MAJOR.MINOR.PATCH (e.g., 2.4.1). Rules: increment MAJOR for incompatible API changes, MINOR for backward-compatible new features, PATCH for backward-compatible bug fixes. Pre-release versions: 1.0.0-alpha, 1.0.0-beta.2. Build metadata: 1.0.0+build.123. Benefits: communicate change impact, safe dependency updates (minor/patch should not break), clear release expectations. Guidelines: 0.x.x indicates development (unstable), 1.0.0 is public API declaration, avoid breaking changes when possible. Dependency ranges: ^1.2.3 (compatible with 1.x.x), ~1.2.3 (compatible with 1.2.x), 1.2.3 (exact). Challenges: breaking changes in dependencies, transitive dependency conflicts, not always followed correctly. Best practices: document changes in CHANGELOG, automate version bumps from commit messages (conventional commits), run compatibility tests. Used by npm, Maven, NuGet, most package managers. Enables predictable dependency management.",
                "context": "Software versioning",
                "verified": True,
                "created_by": "expert"
            },
            
            # ============================================
            # FINAL BATCH - REACHING 200+ GROUND TRUTHS
            # ============================================
            
            # Additional Architectural Concepts
            {
                "question": "What is the Twelve-Factor App methodology?",
                "ground_truth": "The Twelve-Factor App is a methodology for building modern, scalable, cloud-native applications. The factors: 1) Codebase - one codebase in version control, many deploys, 2) Dependencies - explicitly declare and isolate dependencies, 3) Config - store config in environment variables, 4) Backing Services - treat backing services as attached resources, 5) Build/Release/Run - strictly separate build and run stages, 6) Processes - execute app as stateless processes, 7) Port Binding - export services via port binding, 8) Concurrency - scale out via the process model, 9) Disposability - maximize robustness with fast startup and graceful shutdown, 10) Dev/Prod Parity - keep development and production as similar as possible, 11) Logs - treat logs as event streams, 12) Admin Processes - run admin tasks as one-off processes. Benefits: portability, scalability, deployment agility. Foundation for containerized and serverless applications.",
                "context": "Cloud-native architecture",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Backend for Frontend (BFF) pattern?",
                "ground_truth": "Backend for Frontend (BFF) is a pattern where separate backend services are created for each frontend type (web, mobile, desktop). Each BFF: tailored to specific frontend needs, aggregates calls to downstream services, handles authentication for that client type, optimizes data format and payload size. Benefits: optimized APIs per client (mobile needs differ from web), simpler frontends (BFF handles complexity), independent evolution of client experiences, security isolation per client type. Implementation: one BFF service per major client type, BFF calls underlying microservices, GraphQL can serve as BFF layer. Trade-offs: multiple backends to maintain, potential code duplication across BFFs, need to prevent BFF becoming monolith. Alternative: single API with client-specific endpoints or GraphQL for flexible queries. BFF particularly useful when: clients have very different needs, multiple teams own different frontends, performance optimization is critical per client.",
                "context": "API architecture pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is eventual consistency?",
                "ground_truth": "Eventual consistency is a consistency model where, given enough time without new updates, all replicas will converge to the same value. Unlike strong consistency (immediate), updates propagate asynchronously. Characteristics: temporary inconsistency is acceptable, system prioritizes availability and partition tolerance, suitable for high-scale distributed systems. Implementation patterns: read-your-writes (client sees own updates), monotonic reads (no going back in time), causal consistency (respects cause-effect). Conflict resolution: last-write-wins (timestamp-based), merge functions (CRDTs), application-level resolution. Use cases: shopping carts, social media likes, analytics counters, caching layers. Not suitable for: financial transactions, inventory with strict limits, anything requiring immediate consistency. Design considerations: set appropriate consistency windows, handle stale reads gracefully, make operations idempotent. Example: DNS propagation, social media follower counts. Part of BASE (Basically Available, Soft state, Eventually consistent) model.",
                "context": "Distributed systems",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the difference between stateful and stateless architecture?",
                "ground_truth": "Stateless architecture: each request contains all information needed to process it; server doesn't store client state between requests. Benefits: horizontal scalability (any server can handle any request), simpler failover, easier load balancing, better cacheability. Implementation: pass state in requests (tokens, session IDs), store state externally (database, Redis). Stateful architecture: server maintains client state between requests; client bound to specific server. Benefits: faster operations (state in memory), simpler client logic, lower per-request overhead. Drawbacks: sticky sessions required, scaling complexity, failover loses state. Examples: Stateless - REST APIs, serverless functions, microservices; Stateful - WebSocket connections, gaming servers, trading systems. Hybrid approaches: mostly stateless with external state store, session affinity when needed. Modern trend: favor stateless for web applications; use stateful where necessary (real-time, performance-critical). Container orchestration (Kubernetes) handles both with StatefulSets for stateful workloads.",
                "context": "Architecture design",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is service discovery in microservices?",
                "ground_truth": "Service discovery enables services to find and communicate with each other without hardcoded locations. Problem: in dynamic environments (containers, cloud), service instances change frequently. Components: Service Registry (central database of service instances), Service Provider (registers on startup, deregisters on shutdown), Service Consumer (queries registry to find providers). Patterns: 1) Client-side discovery - client queries registry, chooses instance, makes request (Netflix Eureka), 2) Server-side discovery - client contacts router/load balancer, which queries registry and forwards (AWS ALB, Kubernetes Services). Health checks: registry removes unhealthy instances. Technologies: Consul, Eureka, etcd, Kubernetes DNS, AWS Cloud Map. Self-registration vs third-party: services register themselves or orchestrator registers them. Benefits: dynamic scaling, automatic failover, location transparency. Kubernetes approach: Services provide stable DNS names, kube-proxy handles routing to pods.",
                "context": "Microservices infrastructure",
                "verified": True,
                "created_by": "expert"
            },
            
            # More Design Patterns
            {
                "question": "What is the Null Object pattern?",
                "ground_truth": "The Null Object pattern provides an object with neutral behavior as a substitute for null, eliminating null checks. Instead of returning null, return a special 'null object' that implements the expected interface but does nothing or returns neutral values. Example: instead of null for a missing logger, return NullLogger that has log() method doing nothing. Benefits: eliminates null checks, prevents NullPointerExceptions, cleaner code, follows Tell Don't Ask. Implementation: create class implementing interface with do-nothing methods, return sensible defaults. Use cases: missing optional dependencies, unknown states, default behaviors. Related: Optional/Maybe types (wrap potentially null values), Special Case pattern (broader - any special case object). Comparison with Optional: Optional makes absence explicit; Null Object hides it behind neutral behavior. Choose based on: should caller know about absence? Null Object when caller shouldn't care; Optional when they should. Also called Active Nothing pattern.",
                "context": "Behavioral design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Object Pool pattern?",
                "ground_truth": "Object Pool pattern manages a set of reusable objects, providing them on request and returning them to the pool when done. Used when: object creation is expensive (database connections, threads, large objects), objects are frequently created and destroyed, fixed number of resources. Components: Pool (manages available/in-use objects), Reusable (objects being pooled), Client (requests and releases objects). Operations: acquire (get object from pool or wait), release (return to pool), create (initialize pool), destroy (cleanup). Benefits: reduced object creation overhead, controlled resource usage, improved performance. Considerations: pool sizing (too small = waiting, too large = wasted resources), object resetting (clear state before reuse), thread safety, leak detection (objects not returned). Examples: connection pools (HikariCP), thread pools (ExecutorService), game object pools. Modern alternatives: object pooling less critical with efficient GC, but still valuable for expensive resources like connections.",
                "context": "Creational design pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Double-Checked Locking pattern?",
                "ground_truth": "Double-Checked Locking is a pattern to reduce synchronization overhead when implementing lazy initialization in multithreaded environments. Standard implementation: check if instance exists (without lock), if not acquire lock, check again (double-check), create if still null. Purpose: avoid locking every time, only lock during initialization. Java implementation requires volatile keyword to prevent instruction reordering. Example: singleton lazy initialization. Problems: broken in some languages/compilers without memory barriers, complex and error-prone. Modern alternatives: static holder idiom (Java - uses class loading guarantees), enum singleton (Java), Lazy<T> (C#), std::call_once (C++). Best practice: use language/framework-provided lazy initialization rather than implementing manually. If needed, ensure proper memory barriers/volatile. The pattern demonstrates the complexity of concurrent programming and why higher-level abstractions are preferred.",
                "context": "Concurrency pattern",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the Service Locator pattern?",
                "ground_truth": "Service Locator is a pattern providing a central registry where clients can look up dependencies. Components: Service Locator (registry with get(serviceName) method), Service (interface), Service Provider (concrete implementation). Usage: ServiceLocator.get('UserRepository') returns implementation. Benefits: decouples clients from concrete implementations, centralized configuration, lazy loading possible. Criticisms: considered anti-pattern by many due to: hidden dependencies (not visible in constructor), harder testing (need to configure locator), runtime errors vs compile-time (missing service), global state. Comparison with Dependency Injection: DI pushes dependencies to client (explicit); Service Locator has client pull dependencies (implicit). DI is generally preferred: makes dependencies explicit, compile-time safety, better testability. Use cases where Service Locator might fit: plugin systems, legacy code migration, dynamic service resolution. If using, consider scoped locators to limit access. Most modern frameworks prefer DI containers.",
                "context": "Design pattern",
                "verified": True,
                "created_by": "expert"
            },
            
            # Software Quality and Metrics
            {
                "question": "What is cyclomatic complexity?",
                "ground_truth": "Cyclomatic complexity is a quantitative measure of code complexity based on the number of linearly independent paths through source code. Calculation: count decision points (if, while, for, case, catch, &&, ||) and add 1. Alternatively: E - N + 2P where E=edges, N=nodes, P=connected components. Interpretation: 1-10 simple, 11-20 moderate, 21-50 high risk, 50+ untestable. Uses: identify complex code needing refactoring, estimate testing effort (need at least as many tests as complexity), code review focus. Limitations: doesn't measure all complexity types, nested loops vs sequential ifs score same, doesn't consider cognitive complexity. Reduction strategies: Extract Method (break into smaller functions), Replace Conditional with Polymorphism, simplify boolean expressions. Tools: SonarQube, CodeClimate, IDE plugins. Related metrics: cognitive complexity (weights nesting), Halstead complexity (operands/operators). Target: keep methods under 10 complexity. High complexity correlates with bugs and maintenance difficulty.",
                "context": "Code metrics",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is software entropy?",
                "ground_truth": "Software entropy refers to the tendency of software systems to become increasingly disordered and difficult to maintain over time. Causes: quick fixes over proper solutions, changing requirements, knowledge loss, lack of refactoring, accumulated technical debt, inconsistent coding standards. Manifestations: code becomes harder to understand, changes take longer, bug fixes introduce new bugs, onboarding takes longer, fear of changing code. Prevention: continuous refactoring, code reviews, automated testing, documentation, coding standards, regular maintenance sprints, boy scout rule (leave code better than found). Second Law of Thermodynamics analogy: without energy input (maintenance effort), disorder increases. Broken Windows Theory: if small problems aren't fixed, bigger problems are tolerated. Metrics: increasing code churn, bug rates, lead time. Management: explicitly allocate time for reducing entropy, balance feature work with maintenance. Software entropy is inevitable but can be managed through disciplined engineering practices.",
                "context": "Software quality",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is software architecture fitness functions?",
                "ground_truth": "Fitness functions are automated tests that verify architectural characteristics and design decisions remain intact as code evolves. Inspired by evolutionary architecture. Types: 1) Atomic (single characteristic - latency test), 2) Holistic (multiple characteristics - security audit), 3) Triggered (run on events - pre-commit), 4) Continuous (always running - production monitoring). Examples: dependency direction tests (ArchUnit, NDepend), performance benchmarks, security scanners, accessibility tests, documentation coverage. Benefits: prevent architecture erosion, automate architecture governance, enable evolutionary architecture, catch violations early. Implementation: static analysis (code structure), dynamic analysis (runtime behavior), external probes (production monitoring). Tools: ArchUnit (Java), NDepend (.NET), custom CI checks, observability tools. Part of CI/CD pipeline: fail build on architecture violations. Fitness functions make implicit architecture rules explicit and automated. Enable teams to evolve architecture confidently knowing guardrails catch violations.",
                "context": "Architecture governance",
                "verified": True,
                "created_by": "expert"
            },
            
            # More API and Integration
            {
                "question": "What is webhook?",
                "ground_truth": "Webhooks are user-defined HTTP callbacks triggered by specific events in a source system. When event occurs, source makes HTTP POST request to configured URL with event payload. Push model vs polling: webhooks push data instantly; polling requires periodic requests. Components: provider (sends webhooks), consumer (receives at endpoint), payload (event data). Benefits: real-time notifications, reduced polling overhead, event-driven integration. Implementation considerations: endpoint security (signature verification, HMAC), retry logic (handle transient failures), idempotency (same event may arrive multiple times), payload validation. Consumer best practices: respond quickly (200 OK), process asynchronously (queue for later), verify signatures, handle retries. Common uses: payment notifications, CI/CD triggers, chat integrations, sync between systems. Example: GitHub webhook on push → triggers CI build. Alternative: message queues for more reliable delivery. Webhook payloads should include event type, timestamp, relevant data.",
                "context": "Integration patterns",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is API throttling?",
                "ground_truth": "API throttling limits request rates to protect services from overload and ensure fair usage. Strategies: 1) Rate limiting - fixed requests per time window (100 requests/minute), 2) Throttling - slow down excessive requests rather than reject, 3) Concurrent request limit - max simultaneous requests, 4) Quota - total requests per period (10,000/day). Algorithms: Fixed Window (simple but bursty at boundaries), Sliding Window (smoother), Token Bucket (allows bursts up to bucket size), Leaky Bucket (constant rate output). Scope: per user/API key, per IP, per endpoint, global. Response: HTTP 429 Too Many Requests, include Retry-After header, X-RateLimit-* headers (limit, remaining, reset). Implementation: Redis for distributed rate limiting, API Gateway level, application level. Benefits: prevent abuse, ensure availability, support tiered pricing, protect downstream services. Client handling: implement backoff, respect Retry-After, cache when possible. Different limits for different tiers (free vs paid).",
                "context": "API design",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is HATEOAS?",
                "ground_truth": "HATEOAS (Hypermedia as the Engine of Application State) is a REST constraint where API responses include hypermedia links indicating available actions and related resources. Instead of hardcoded URLs, clients discover navigation through links in responses. Example: GET /orders/123 returns order data plus links: self, cancel, payment, customer. Benefits: self-documenting API, client doesn't need hardcoded URLs, server can change URLs without breaking clients, discoverability, enables API evolution. Implementation: include _links or links section in responses, use standard formats (HAL, JSON-LD, SIREN). Levels of REST: Level 0 (single URI, one method), Level 1 (resources), Level 2 (HTTP verbs), Level 3 (hypermedia/HATEOAS). Challenges: more complex responses, client must parse links, less commonly implemented. Richardson Maturity Model places HATEOAS at highest REST maturity. Useful for: long-lived APIs, public APIs, APIs expected to evolve. Many REST APIs don't implement full HATEOAS.",
                "context": "REST API design",
                "verified": True,
                "created_by": "expert"
            },
            
            # More Testing
            {
                "question": "What is smoke testing?",
                "ground_truth": "Smoke testing is a preliminary test to verify basic functionality works before deeper testing. Origin: hardware testing - if it smokes, it fails. Also called build verification testing or sanity testing. Characteristics: broad but shallow coverage, tests critical paths, quick to execute, run early in testing cycle, blocks further testing if fails. Purpose: catch major failures quickly, verify build is stable enough for detailed testing, save time by not testing obviously broken builds. Examples: application starts, login works, main page loads, database connects, key workflow completes. Automation: typically automated in CI/CD pipeline, run after each build/deployment. Relationship to other tests: smoke tests verify build is worth testing; regression tests verify detailed functionality. Scope: 10-20 critical test cases, few minutes execution. If smoke test fails: fix before further testing; don't waste resources on detailed tests. Essential for: continuous integration, deployment verification, quick feedback.",
                "context": "Testing types",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is regression testing?",
                "ground_truth": "Regression testing verifies that previously working functionality still works after code changes. Purpose: catch unintended side effects of changes, ensure bug fixes don't break other features, maintain system stability. When to perform: after bug fixes, new feature development, code refactoring, environment changes, integration with external systems. Types: 1) Corrective (no specification changes, rerun existing tests), 2) Progressive (specifications change, update tests accordingly), 3) Complete (run all tests), 4) Selective (run subset based on changes). Test selection strategies: risk-based (test high-risk areas), dependency analysis (test affected modules), history-based (tests that found bugs before). Automation: essential for efficient regression testing, maintain test suite, update as system evolves. Challenges: test suite growth, execution time, test maintenance, flaky tests. Best practices: prioritize tests, parallelize execution, integrate in CI/CD, review and prune test suite regularly. Coverage: critical paths, high-risk areas, recently changed code.",
                "context": "Testing types",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is acceptance testing?",
                "ground_truth": "Acceptance testing verifies that software meets business requirements and is acceptable for delivery to end users. Types: 1) User Acceptance Testing (UAT) - end users verify business scenarios, 2) Business Acceptance Testing (BAT) - business stakeholders verify requirements, 3) Contract Acceptance Testing - verify contractual requirements, 4) Regulatory Acceptance Testing - compliance verification. Characteristics: tests from user perspective, uses business language, validates complete workflows, final testing phase before release. Process: define acceptance criteria with stakeholders, create test scenarios from requirements, execute in production-like environment, get stakeholder sign-off. Automation: BDD frameworks (Cucumber, SpecFlow) automate acceptance tests, Given-When-Then format. Acceptance Criteria: specific, measurable conditions that must be met. Example: 'Given a logged-in user, When they submit an order, Then order confirmation is displayed and email is sent.' Relationship: complements but doesn't replace system testing; focuses on 'does it do what users need?' vs 'does it work correctly?'",
                "context": "Testing types",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is load testing vs stress testing?",
                "ground_truth": "Load Testing evaluates system performance under expected load conditions. Goals: verify response times, throughput, resource usage under normal and peak expected load. Example: test e-commerce site with 1000 concurrent users (expected peak). Helps with: capacity planning, identifying bottlenecks, SLA verification, performance baseline. Stress Testing pushes system beyond normal capacity to find breaking points. Goals: determine maximum capacity, observe failure behavior, test recovery, identify failure modes. Example: keep adding users until system fails. Helps with: understanding limits, disaster planning, finding weak points. Key differences: Load tests expected conditions; Stress tests extreme conditions. Load validates performance requirements; Stress finds breaking points. Load helps optimization; Stress helps failure planning. Related types: Spike testing (sudden load increase), Soak/Endurance testing (sustained load over time), Scalability testing (adding resources). Tools: JMeter, Gatling, k6, Locust. Both essential: know you can handle expected load AND know what happens when exceeded.",
                "context": "Performance testing",
                "verified": True,
                "created_by": "expert"
            },
            
            # Functional Programming Concepts for Design
            {
                "question": "What is immutability and why is it important?",
                "ground_truth": "Immutability means an object's state cannot be modified after creation; any 'change' creates a new object. Benefits: 1) Thread safety - no synchronization needed, no race conditions, 2) Predictability - object won't change unexpectedly, 3) Easier debugging - state is traceable, 4) Safe sharing - can pass references without copying, 5) Hashable - safe for hash-based collections, 6) Undo/history - keep old versions. Implementation: final/readonly fields, no setters, return new objects from 'mutating' operations, defensive copying. Examples: String in Java, Value Objects in DDD, React state, Redux stores. Patterns: Builder for creating immutable objects, copy-on-write for efficient updates. Trade-offs: more object allocations (mitigated by modern GC), may need more memory, unfamiliar paradigm. Structural sharing: efficient immutable collections share unchanged parts. Libraries: Immutable.js, Vavr (Java). Default to immutability; make mutable only when necessary. Core to functional programming but valuable in OOP too.",
                "context": "Programming concepts",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What are pure functions?",
                "ground_truth": "A pure function always produces the same output for the same input and has no side effects. Properties: 1) Deterministic - same inputs → same output, 2) No side effects - doesn't modify external state, no I/O, no mutations. Examples of impure: reading time, random numbers, database queries, modifying global variables, console output. Examples of pure: mathematical functions, string transformations, data transformations without mutation. Benefits: 1) Testable - no mocking needed, just verify input/output, 2) Cacheable/memoizable - results can be cached, 3) Parallelizable - no shared state concerns, 4) Predictable - easier to reason about, 5) Referential transparency - can replace call with result. Design implications: separate pure logic from side effects, push I/O to edges of system. Functional core, imperative shell pattern: pure domain logic, impure boundaries. Use pure functions for: business logic, transformations, calculations. Impurity is necessary but should be isolated and minimized.",
                "context": "Programming concepts",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is higher-order function?",
                "ground_truth": "A higher-order function either takes one or more functions as arguments or returns a function as its result (or both). Examples taking function arguments: map (apply function to each element), filter (keep elements matching predicate), reduce (accumulate using function), sort (compare using function). Examples returning functions: function factories, closures, decorators, currying. Benefits: abstraction over actions (not just data), code reuse, declarative style, composition. Common patterns: 1) Callbacks (function as argument for async completion), 2) Strategy pattern (swap algorithms via function parameters), 3) Decorators (wrap functions with additional behavior), 4) Currying (partial application for specialized functions). Languages: first-class functions required; supported in Python, JavaScript, Java 8+, C#, most modern languages. Example: numbers.filter(n => n > 0).map(n => n * 2) uses filter and map as higher-order functions. Enables functional programming paradigm and more expressive code.",
                "context": "Programming concepts",
                "verified": True,
                "created_by": "expert"
            },
            
            # More Security
            {
                "question": "What is input validation and sanitization?",
                "ground_truth": "Input validation verifies that input meets expected format, type, and constraints before processing. Sanitization cleans input by removing or encoding potentially dangerous content. Validation types: 1) Type checking (is it a number?), 2) Range checking (within bounds?), 3) Format validation (valid email pattern?), 4) Business rule validation (is date in future?). Validation approaches: whitelist (allow known good - preferred), blacklist (block known bad - less secure). Sanitization: HTML encoding (prevent XSS), SQL parameterization (prevent SQLi), removing special characters, truncating length. Best practices: validate on both client (UX) and server (security), fail closed (reject invalid), specific error messages (don't reveal internals), validate all sources (forms, APIs, headers, cookies). Defense in depth: validation is one layer; also use parameterized queries, encoding on output, CSP. Common pitfalls: only client-side validation, trusting internal data, incomplete validation. Libraries provide validation (Joi, Yup, Bean Validation) - use them rather than rolling own.",
                "context": "Security practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is encryption at rest vs in transit?",
                "ground_truth": "Encryption at rest protects stored data on disk/database. Purpose: protect data if storage is compromised, comply with regulations. Implementation: database encryption (TDE), file system encryption, encrypted backups, disk encryption (BitLocker, LUKS). Key management: store keys separately from encrypted data, use key management services (AWS KMS, HashiCorp Vault). Encryption in transit protects data while moving across networks. Purpose: prevent eavesdropping, man-in-the-middle attacks. Implementation: TLS/HTTPS for web traffic, encrypted database connections (SSL/TLS), VPNs for network traffic, encrypted API calls. Configuration: enforce TLS 1.2+, strong cipher suites, valid certificates. Both are essential: at rest protects stored data; in transit protects data in motion. Regulatory requirements (GDPR, HIPAA, PCI-DSS) often mandate both. Additional: encrypt sensitive fields (PII) even within encrypted database, end-to-end encryption for highest security. Performance consideration: encryption adds overhead; use efficient algorithms, hardware acceleration.",
                "context": "Security practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is secret management?",
                "ground_truth": "Secret management is the practice of securely storing, accessing, and managing sensitive data like passwords, API keys, tokens, and certificates. Problems with poor practices: secrets in code/version control, shared credentials, no rotation, no audit trail. Best practices: 1) Never commit secrets to code, 2) Use dedicated secret management tools, 3) Rotate secrets regularly, 4) Audit access, 5) Least privilege access, 6) Different secrets per environment. Tools: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, Google Secret Manager, Kubernetes Secrets. Features: centralized storage, encryption, access control, audit logging, secret rotation, dynamic secrets. Implementation: inject secrets at runtime (environment variables, files), don't log secrets, use short-lived credentials when possible. Local development: .env files (gitignored), local secret stores. CI/CD: pipeline secret management, masked outputs. Rotation: automate where possible, have process for compromise. Secret sprawl: track where secrets are used, minimize secret count.",
                "context": "Security practices",
                "verified": True,
                "created_by": "expert"
            },
            
            # More Database
            {
                "question": "What is a database connection pool?",
                "ground_truth": "A database connection pool maintains a cache of database connections for reuse, avoiding the overhead of creating new connections for each query. How it works: pool initializes with min connections, requests borrow connections, connections returned to pool after use, pool creates new connections up to max if needed. Configuration: minimum connections, maximum connections, connection timeout (wait time if pool exhausted), idle timeout (remove unused connections), validation query (check connection health). Benefits: reduced latency (reuse established connections), controlled resource usage, connection sharing efficiency, protection against connection storms. Problems it solves: connection creation overhead (TCP handshake, authentication), database connection limits, resource exhaustion. Best practices: size pool appropriately (too small = waiting, too large = wasted resources), monitor pool metrics, handle connection leaks, use validation. Technologies: HikariCP (Java, fastest), c3p0, DBCP, built into ORMs. Sizing guidance: depends on workload; start conservative, monitor, adjust.",
                "context": "Database infrastructure",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is database migration?",
                "ground_truth": "Database migration is the process of evolving database schema in a controlled, versioned manner. Purpose: track schema changes, apply consistently across environments, rollback capability, team collaboration on schema. How it works: migrations are versioned scripts (001_create_users.sql, 002_add_email.sql), migration tool tracks applied migrations, applies pending migrations in order. Tools: Flyway, Liquibase (Java), Alembic (Python), Entity Framework Migrations (.NET), Django migrations, Knex (Node.js). Best practices: 1) One change per migration, 2) Migrations are immutable (don't edit applied), 3) Backward compatible when possible (add nullable first, then populate, then make required), 4) Test migrations, 5) Version control with code, 6) Automate in CI/CD. Rollback: not always possible (data loss operations), write down migrations when feasible. Zero-downtime: expand-contract pattern (add new, migrate data, remove old). Seed data: separate from schema migrations. Coordinate with application deployments.",
                "context": "Database management",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is ORM (Object-Relational Mapping)?",
                "ground_truth": "ORM is a technique that maps objects in code to relational database tables, abstracting database operations. Features: 1) Entity mapping (class → table), 2) Query abstraction (method calls → SQL), 3) Change tracking (detect modifications), 4) Lazy/eager loading (fetch related data), 5) Connection management, 6) Transaction support. Benefits: reduced boilerplate SQL, database portability, type safety, productivity, consistent patterns. Drawbacks: performance overhead, abstraction leakage (need to understand SQL anyway), complex queries difficult, learning curve. Popular ORMs: Hibernate/JPA (Java), Entity Framework (.NET), Django ORM, SQLAlchemy (Python), ActiveRecord (Ruby), Prisma (Node.js). N+1 problem: lazy loading causes excessive queries; solve with eager loading. Impedance mismatch: OOP and relational models don't map perfectly. Best practices: understand generated SQL, use appropriate fetch strategies, don't fight the ORM (use raw SQL when needed). Alternative: micro-ORMs (Dapper), query builders - less abstraction, more control.",
                "context": "Data access",
                "verified": True,
                "created_by": "expert"
            },
            
            # Agile and Process
            {
                "question": "What is Definition of Done in Agile?",
                "ground_truth": "Definition of Done (DoD) is a shared understanding of what it means for work to be complete. A checklist ensuring consistent quality and completeness. Typical items: code complete, code reviewed, tests written and passing, documentation updated, deployed to staging, no critical bugs, meets acceptance criteria, product owner acceptance. Purposes: 1) Shared understanding of complete, 2) Quality gate, 3) Transparency, 4) Reduces rework, 5) Builds trust. Levels: task-level, story-level, sprint-level, release-level. Evolution: DoD often becomes stricter as team matures. Created by: team together (developers, testers, PO input). Different from acceptance criteria: DoD is generic checklist for all work; acceptance criteria are specific to a story. Refinement: review and update periodically. Anti-patterns: too vague, ignored, too long, not visible. Done vs Done-Done: if there's qualifier, real DoD isn't being followed. Enforce: work isn't complete until DoD met, visible on board.",
                "context": "Agile practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is story points in Agile estimation?",
                "ground_truth": "Story points are a relative measure of effort, complexity, and uncertainty for completing a user story. Not time: comparing stories to each other, not estimating hours. Fibonacci sequence common: 1, 2, 3, 5, 8, 13, 21 (larger gaps for larger uncertainty). Process: team estimates together (Planning Poker), discuss differences, converge on estimate. Factors considered: complexity (how hard?), effort (how much work?), uncertainty (unknowns?). Benefits: abstract from individual speed, focus on relative size, velocity emerges naturally, promotes team discussion. Velocity: story points completed per sprint, used for capacity planning. Refinement: break large stories (>13) into smaller ones. Anti-patterns: converting to hours, comparing team velocities, individual estimates, management pressure on velocity. Alternatives: T-shirt sizing (S, M, L, XL), #NoEstimates (focus on flow, count stories). Story points work best with stable team, consistent sprint length, meaningful velocity history.",
                "context": "Agile practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is technical refinement in Agile?",
                "ground_truth": "Technical refinement (also technical grooming) is the process of breaking down user stories into technical tasks, identifying technical risks, and ensuring stories are implementation-ready. Activities: 1) Architecture discussion, 2) Technical approach agreement, 3) Identify dependencies, 4) Risk identification, 5) Spike needs, 6) Technical acceptance criteria, 7) Task breakdown. When: before or during regular refinement, with technical focus. Participants: development team, optionally architect; PO for clarification. Outputs: technical notes on story, tasks, spikes if needed, refined estimates, identified blockers. Benefits: reduces surprises during sprint, surfaces technical concerns early, improves estimates, enables parallelization. Relationship to refinement: complements product refinement; focuses on how vs what. Sign of need: stories consistently more complex than expected, technical surprises during sprint, conflicting approaches in team. Time-box: don't over-analyze; enough to be confident in starting. Document decisions for future reference.",
                "context": "Agile practices",
                "verified": True,
                "created_by": "expert"
            },
            
            # Additional Concepts
            {
                "question": "What is Technical Spike?",
                "ground_truth": "A technical spike is a time-boxed investigation to explore a technical question, reduce uncertainty, or prove feasibility before committing to a user story. Purpose: answer technical questions, evaluate technologies, prototype solutions, estimate effort for complex work. Types: 1) Technical spike - research technical approach, 2) Functional spike - explore user requirements. Process: define question to answer, time-box strictly (typically 1-2 days), document findings, present to team, inform estimation. Output: knowledge, not production code (though prototypes may inform implementation). Examples: can we integrate with payment gateway X?, how do we migrate legacy data?, what's the performance of approach A vs B? When to use: significant technical uncertainty, new technology evaluation, complex estimation, risk reduction. Not for: avoiding commitment, gold-plating, bypassing normal process. Spike stories are part of backlog, typically not pointed (or separate spike point budget). After spike, create actual stories with better estimates.",
                "context": "Agile practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is mob programming?",
                "ground_truth": "Mob programming extends pair programming to the whole team working together on the same thing, at the same time, on the same computer. Roles rotate frequently: Driver (types, follows instructions), Navigator (guides the driver), Mob (rest of team, contributes ideas). Rotation: typically 10-15 minutes per driver. Benefits: continuous code review, whole team knowledge, fast decision-making, eliminates work in progress, real-time knowledge transfer, high-quality code, no handoffs. Challenges: perceived inefficiency (all on one task), personality dynamics, remote coordination, meeting fatigue. When effective: complex problems, establishing patterns, onboarding, critical code, learning new technology. Not for: independent simple tasks, routine work. Remote mobbing: screen sharing, collaborative IDEs, timer tools. Variations: work on multiple tasks with multiple mobs. Research: teams report higher quality, faster overall delivery despite appearance of inefficiency. Try: start with one session/week to evaluate fit.",
                "context": "Development practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is technical leadership?",
                "ground_truth": "Technical leadership involves guiding technical direction, mentoring developers, and ensuring technical excellence while balancing business needs. Responsibilities: 1) Technical vision and strategy, 2) Architecture decisions, 3) Code quality standards, 4) Mentoring and growing team, 5) Cross-team technical coordination, 6) Technical risk management, 7) Stakeholder communication. Skills needed: deep technical expertise, communication, influence without authority, strategic thinking, teaching ability, decision-making under uncertainty. Leadership styles: hands-on (still coding), hands-off (enabling others), hybrid. Balance: technical depth vs breadth, individual contribution vs team leverage, short-term vs long-term. Common challenges: letting go of doing everything, delegating effectively, staying technical while leading, managing up. Tech Lead vs Architect: often overlapping; tech lead more team-focused, architect more system-focused. Growth path: individual contributor → tech lead → principal engineer/architect. Servant leadership: remove obstacles, enable team success.",
                "context": "Software engineering career",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is evolutionary architecture?",
                "ground_truth": "Evolutionary architecture supports guided, incremental change across multiple dimensions. Key principle: instead of big upfront design, architecture evolves as requirements and understanding emerge. Enablers: 1) Fitness functions - automated architectural tests, 2) Appropriate coupling - loosely coupled components, 3) Last responsible moment - defer decisions, 4) Small incremental changes. Guided evolution: not random change; fitness functions ensure architectural characteristics are maintained. Multiple dimensions: technical (performance, scalability), domain (business capability), data (schemas, storage). Practices: continuous delivery, trunk-based development, microservices (enable independent evolution), database evolution (migrations). Contrast with: emergent architecture (no guidance) and big design upfront (rigid). When appropriate: uncertain requirements, long-lived systems, learning domain. Team requirements: discipline, technical maturity, comprehensive testing. Book: 'Building Evolutionary Architectures' by Ford, Parsons, Kua. Fitness functions are key mechanism - make architecture constraints executable and automated.",
                "context": "Architecture practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is defensive programming?",
                "ground_truth": "Defensive programming is a practice of anticipating and guarding against potential errors, invalid inputs, and unexpected conditions. Techniques: 1) Input validation - validate all external inputs, 2) Assertions - verify assumptions in code, 3) Error handling - graceful handling of failures, 4) Fail fast - detect errors early, 5) Null checks - guard against null references, 6) Bounds checking - verify array/collection access, 7) Defensive copying - protect internal state, 8) Contract checking - preconditions, postconditions, invariants. Benefits: more robust code, easier debugging (errors surface close to cause), self-documenting (assertions show expectations), prevents security vulnerabilities. Balance: don't over-defend (impacts performance, clutters code); focus on boundaries (public APIs, user input, external systems). Related: Design by Contract (formal preconditions/postconditions), Fail Fast principle. Modern alternatives: type systems, Option/Result types, static analysis. Defensive internally vs boundaries: trust internal code more (within bounds), defend at system boundaries strictly.",
                "context": "Code quality practices",
                "verified": True,
                "created_by": "expert"
            },
            {
                "question": "What is the strangler pattern for legacy migration?",
                "ground_truth": "The Strangler Fig pattern incrementally replaces a legacy system by gradually building new functionality around it until the old system can be decommissioned. Named after strangler fig trees that grow around host trees. Steps: 1) Identify components to migrate, 2) Build new implementation alongside legacy, 3) Route traffic gradually to new system (using facade/proxy), 4) Remove legacy components as they become unused. Benefits: reduced risk (incremental migration), continuous delivery (don't wait for big-bang), learning from production. Implementation: API Gateway or facade routes requests; feature flags control traffic split. Anti-Corruption Layer translates between systems during transition. Example: migrating monolith to microservices - extract OrderService first, route order-related traffic to new service while other features stay in monolith. Eventually, entire monolith is replaced. Timeline: often takes months to years. Success factors: clear boundaries, comprehensive testing, monitoring, organizational patience. Alternative to risky big-bang rewrites.",
                "context": "Migration patterns",
                "verified": True,
                "created_by": "expert"
            }
        ]

        created_count = 0
        updated_count = 0
        
        for gt_data in ground_truths:
            # Check if ground truth already exists
            existing = GroundTruth.objects.filter(
                question=gt_data['question']
            ).first()
            
            if existing:
                # Update existing
                existing.ground_truth = gt_data['ground_truth']
                existing.context = gt_data['context']
                existing.verified = gt_data['verified']
                existing.created_by = gt_data['created_by']
                existing.verified_at = timezone.now() if gt_data['verified'] else None
                existing.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated: {gt_data['question'][:50]}..."))
            else:
                # Create new
                GroundTruth.objects.create(
                    question=gt_data['question'],
                    ground_truth=gt_data['ground_truth'],
                    context=gt_data.get('context', ''),
                    verified=gt_data['verified'],
                    created_by=gt_data['created_by'],
                    verified_at=timezone.now() if gt_data['verified'] else None
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {gt_data['question'][:50]}..."))

        self.stdout.write(self.style.SUCCESS(
            f'\nGround truth population completed!\n'
            f'Created: {created_count}\n'
            f'Updated: {updated_count}\n'
            f'Total: {created_count + updated_count}'
        ))
