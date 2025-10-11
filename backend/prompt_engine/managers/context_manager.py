from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
# Import UserExpertise enum
from prompt_engine.templates.base_template import UserExpertise


class ContextManager:
    """Manages conversation context and history with topic change detection"""

    def __init__(self, max_history_length: int = 10):
        self.max_history_length = max_history_length
        # Initialize conversations with a default expertise level
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
            ]
        }

    def _initialize_session(self, session_id: str):
        """Initializes a new session with default values, including user_expertise."""
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                'messages': [],
                'created_at': datetime.now(),
                'last_updated': datetime.now(),
                'current_topic': None,
                'user_expertise': UserExpertise.INTERMEDIATE  # Default initial expertise
            }

    def add_message(self, session_id: str, sender: str, text: str, metadata: Optional[Dict] = None):
        """Add a message to the conversation history."""
        self._initialize_session(session_id)
        
        # Determine the current topic based on the message's intent metadata
        current_topic = None
        if metadata and 'intent' in metadata and 'topic' in metadata['intent']:
            current_topic = metadata['intent']['topic']
        
        # Update current topic for the session
        if current_topic:
            self.conversations[session_id]['current_topic'] = current_topic
        
        message = {
            'sender': sender,
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata if metadata is not None else {}
        }
        self.conversations[session_id]['messages'].append(message)
        self.conversations[session_id]['last_updated'] = datetime.now()

        # Trim history if it exceeds max_history_length
        if len(self.conversations[session_id]['messages']) > self.max_history_length:
            self.conversations[session_id]['messages'] = \
                self.conversations[session_id]['messages'][-self.max_history_length:]

    def get_history(self, session_id: str) -> List[Dict]:
        """Retrieve conversation history for a session."""
        self._initialize_session(session_id)
        return self.conversations[session_id]['messages']

    def get_current_topic(self, session_id: str) -> Optional[str]:
        """Get the current dominant topic of the conversation."""
        self._initialize_session(session_id)
        return self.conversations[session_id].get('current_topic')

    def get_conversation_summary(self, session_id: str) -> Dict:
        """Get a summary of a specific conversation."""
        self._initialize_session(session_id)
        conversation = self.conversations[session_id]
        return {
            'session_id': session_id,
            'created_at': conversation['created_at'].isoformat(),
            'last_updated': conversation['last_updated'].isoformat(),
            'total_messages': len(conversation['messages'])
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
    
    def get_user_expertise(self, session_id: str) -> UserExpertise:
        """Retrieve the current user expertise level for a session."""
        self._initialize_session(session_id)
        return self.conversations[session_id].get('user_expertise', UserExpertise.INTERMEDIATE) # Default if not set

    def set_user_expertise(self, session_id: str, expertise: UserExpertise):
        """Set or update the user expertise level for a session."""
        self._initialize_session(session_id)
        self.conversations[session_id]['user_expertise'] = expertise

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
            self.clear_session(session_id)