from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

class ContextManager:
    """Manages conversation context and history with topic change detection"""
    
    def __init__(self, max_history_length: int = 10):
        self.max_history_length = max_history_length
        self.conversations = {}  # Store by session_id
        
        # Software design topic keywords for detection
        self.topic_keywords = {
            'design_patterns': [
            'observer', 'factory', 'singleton', 'strategy', 'composite', 'adapter',
            'decorator', 'command', 'template method', 'proxy', 'builder',
            'state', 'mediator', 'memento', 'bridge', 'flyweight', 'interpreter',
            'chain of responsibility'
            ],

            'solid_principles': [
                'single responsibility', 'open closed', 'liskov',
                'interface segregation', 'dependency inversion',
                'srp', 'ocp', 'lsp', 'isp', 'dip'
            ],

            'architecture': [
                'mvc', 'microservices', 'layered', 'event-driven', 'client-server',
                'monolith', 'service-oriented', 'soa', 'n-tier', 'hexagonal', 'clean architecture'
            ],

            'ddd': [
                'bounded context', 'aggregate', 'entity', 'value object', 'repository',
                'domain service', 'ubiquitous language', 'domain event', 'factory'
            ],

            'quality': [
                'maintainability', 'scalability', 'testability', 'performance',
                'security', 'availability', 'reliability', 'extensibility', 'modifiability',
                'usability', 'fault tolerance'
            ],

            'code_structure': [
                'class', 'interface', 'module', 'component', 'package',
                'method', 'inheritance', 'composition', 'abstraction', 'encapsulation'
            ]
        }
        
    def detect_topic(self, content: str) -> Optional[str]:
        """Detect topic from message content using keyword matching"""
        content_lower = content.lower()
        
        topic_scores = {}
        for topic, keywords in self.topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            # Return topic with highest score
            return max(topic_scores, key=topic_scores.get)
        return None
    
    def detect_topic_change(self, session_id: str, new_content: str) -> bool:
        """Detect if the conversation topic has changed"""
        if session_id not in self.conversations:
            return False
        
        messages = self.conversations[session_id]['messages']
        if len(messages) < 2:  # Need at least 2 messages to detect change
            return False
        
        # Get current topic from new content
        new_topic = self.detect_topic(new_content)
        if not new_topic:
            return False
        
        # Check last few messages for previous topics
        recent_messages = messages[-3:]  # Check last 3 messages
        previous_topics = []
        
        for msg in recent_messages:
            if msg['role'] == 'user':
                topic = self.detect_topic(msg['content'])
                if topic:
                    previous_topics.append(topic)
        
        # Topic changed if new topic is different from recent topics
        return new_topic not in previous_topics if previous_topics else False
    
    def get_topic_transition_keywords(self) -> List[str]:
        """Keywords that indicate explicit topic changes"""
        return [
            "let's talk about", "now about", "switch to", "change topic",
            "different question", "new topic", "moving on to", "what about"
        ]
    
    def detect_explicit_topic_change(self, content: str) -> bool:
        """Detect explicit topic change signals in user input"""
        content_lower = content.lower()
        transition_keywords = self.get_topic_transition_keywords()
        
        return any(keyword in content_lower for keyword in transition_keywords)
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None):
        """Add a message to the conversation history with automatic topic detection"""
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                'messages': [],
                'created_at': datetime.now(),
                'last_updated': datetime.now(),
                'current_topic': None,
                'topic_changes': []
            }
        
        # Detect topic and topic changes
        detected_topic = self.detect_topic(content) if role == 'user' else None
        topic_changed = False
        explicit_change = False
        
        if role == 'user':
            topic_changed = self.detect_topic_change(session_id, content)
            explicit_change = self.detect_explicit_topic_change(content)
            
            if detected_topic and (topic_changed or explicit_change):
                # Record topic change
                self.conversations[session_id]['topic_changes'].append({
                    'from_topic': self.conversations[session_id]['current_topic'],
                    'to_topic': detected_topic,
                    'timestamp': datetime.now().isoformat(),
                    'explicit': explicit_change
                })
                self.conversations[session_id]['current_topic'] = detected_topic
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add detected topic to metadata
        if detected_topic:
            if 'intent' not in metadata:
                metadata['intent'] = {}
            metadata['intent']['topic'] = detected_topic
            metadata['intent']['topic_changed'] = topic_changed
            metadata['intent']['explicit_topic_change'] = explicit_change
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata
        }
        
        self.conversations[session_id]['messages'].append(message)
        self.conversations[session_id]['last_updated'] = datetime.now()
        
        # Trim history if it exceeds max length
        if len(self.conversations[session_id]['messages']) > self.max_history_length:
            self.conversations[session_id]['messages'] = \
                self.conversations[session_id]['messages'][-self.max_history_length:]
    
    def should_clear_context_for_topic_change(self, session_id: str) -> bool:
        """Determine if context should be cleared due to topic change"""
        if session_id not in self.conversations:
            return False
        
        messages = self.conversations[session_id]['messages']
        if not messages:
            return False
        
        last_message = messages[-1]
        metadata = last_message.get('metadata', {})
        intent = metadata.get('intent', {})
        
        # Clear context if explicit topic change or significant topic shift
        return (intent.get('explicit_topic_change', False) or 
                intent.get('topic_changed', False))
    
    def get_context_with_topic_awareness(self, session_id: str, include_last_n: int = 5) -> Dict:
        """Get conversation context with topic change awareness"""
        base_context = self.get_context(session_id, include_last_n)
        
        if session_id in self.conversations:
            conversation = self.conversations[session_id]
            base_context.update({
                'current_topic': conversation.get('current_topic'),
                'topic_changes': conversation.get('topic_changes', []),
                'should_clear_context': self.should_clear_context_for_topic_change(session_id)
            })
        
        return base_context
    
    def clear_context_on_topic_change(self, session_id: str):
        """Clear conversation context when topic changes significantly"""
        if session_id in self.conversations:
            # Keep only the last message (the new topic starter)
            last_message = self.conversations[session_id]['messages'][-1:]
            self.conversations[session_id]['messages'] = last_message
    
    def load_from_database(self, session_id: str, max_messages: int = 10):
        """Load conversation history from database for session persistence across requests"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from core.models import Message, Conversation
            
            logger.info(f"🔄 load_from_database called for session_id: {session_id}")
            
            # Check if conversation exists in database
            conversation = Conversation.objects.filter(id=session_id).first()
            if not conversation:
                logger.warning(f"⚠️ No conversation found in DB for session_id: {session_id}")
                return
            
            logger.info(f"✅ Found conversation in DB: {conversation.title}")
            
            # Load recent messages from database
            messages = Message.objects.filter(
                conversation=conversation
            ).order_by('-created_at')[:max_messages]
            
            logger.info(f"📊 Found {messages.count()} messages in DB for this conversation")
            
            # Initialize session if not exists
            if session_id not in self.conversations:
                self.conversations[session_id] = {
                    'messages': [],
                    'created_at': conversation.created_at,
                    'last_updated': datetime.now()
                }
            
            # Add messages in chronological order (oldest first)
            loaded_count = 0
            for message in reversed(messages):
                msg_dict = {
                    'role': 'user' if message.sender == 'user' else 'assistant',
                    'content': message.content,
                    'timestamp': message.created_at,
                    'metadata': message.metadata or {}
                }
                
                # Avoid duplicates
                if not any(m['content'] == msg_dict['content'] and m['timestamp'] == msg_dict['timestamp'] 
                          for m in self.conversations[session_id]['messages']):
                    self.conversations[session_id]['messages'].append(msg_dict)
                    loaded_count += 1
                    logger.debug(f"  Loaded {message.sender}: {message.content[:50]}...")
            
            logger.info(f"✅ Loaded {loaded_count} messages into context manager")
            
        except Exception as e:
            logger.error(f"❌ Error loading context from database: {e}", exc_info=True)
    
    def get_context(self, session_id: str, include_last_n: int = 5) -> Dict:
        """Get conversation context for a session (auto-loads from DB if not in memory)"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Auto-load from database if session not in memory
        if session_id not in self.conversations:
            logger.info(f"🔄 Session {session_id} not in memory, loading from database...")
            self.load_from_database(session_id)
            if session_id in self.conversations:
                logger.info(f"✅ Loaded {len(self.conversations[session_id]['messages'])} messages from database")
            else:
                logger.warning(f"⚠️ No conversation found in database for session {session_id}")
        else:
            logger.info(f"✅ Session {session_id} already in memory with {len(self.conversations[session_id]['messages'])} messages")
        
        if session_id not in self.conversations:
            return {'previous_messages': [], 'session_info': {}}
        
        conversation = self.conversations[session_id]
        recent_messages = conversation['messages'][-include_last_n:] if include_last_n else conversation['messages']
        
        return {
            'previous_messages': recent_messages,
            'session_info': {
                'created_at': conversation['created_at'].isoformat(),
                'last_updated': conversation['last_updated'].isoformat(),
                'total_messages': len(conversation['messages'])
            }
        }
    
    def get_topic_context(self, session_id: str) -> List[str]:
        """Extract topics discussed in the conversation"""
        if session_id not in self.conversations:
            return []
        
        topics = []
        for message in self.conversations[session_id]['messages']:
            if message.get('metadata', {}).get('intent', {}).get('topic'):
                topic = message['metadata']['intent']['topic']
                if topic not in topics:
                    topics.append(topic)
        
        return topics
    
    def clear_session(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove old conversation sessions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        for session_id, conversation in self.conversations.items():
            if conversation['last_updated'] < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.conversations[session_id]