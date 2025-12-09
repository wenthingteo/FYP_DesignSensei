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
