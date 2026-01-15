"""
Advanced Memory System
Short-term, Long-term, and Semantic memory for agents
"""

import json
import hashlib
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class Memory:
    """A single memory item"""
    key: str
    value: Any
    memory_type: str  # "short_term", "long_term", "semantic"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    accessed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    access_count: int = 0
    importance: float = 0.5  # 0.0 = low, 1.0 = high
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Memory":
        return cls(**data)


class ShortTermMemory:
    """
    In-memory storage for current conversation.
    Limited capacity, automatically prunes oldest items.
    """
    
    def __init__(self, max_items: int = 50):
        self._storage: Dict[str, Dict[str, Memory]] = {}  # session_id -> memories
        self._max_items = max_items
    
    def store(self, session_id: str, key: str, value: Any, importance: float = 0.5) -> None:
        """Store a memory for the current session"""
        if session_id not in self._storage:
            self._storage[session_id] = {}
        
        memory = Memory(
            key=key,
            value=value,
            memory_type="short_term",
            importance=importance
        )
        self._storage[session_id][key] = memory
        
        # Prune if needed
        self._prune(session_id)
        logger.debug(f"Stored short-term memory: {key} for session {session_id}")
    
    def retrieve(self, session_id: str, key: str) -> Optional[Any]:
        """Retrieve a memory by key"""
        if session_id in self._storage and key in self._storage[session_id]:
            memory = self._storage[session_id][key]
            memory.accessed_at = datetime.utcnow().isoformat()
            memory.access_count += 1
            return memory.value
        return None
    
    def get_all(self, session_id: str) -> List[Memory]:
        """Get all memories for a session"""
        if session_id in self._storage:
            return list(self._storage[session_id].values())
        return []
    
    def clear(self, session_id: str) -> None:
        """Clear all memories for a session"""
        if session_id in self._storage:
            del self._storage[session_id]
    
    def _prune(self, session_id: str) -> None:
        """Remove least important memories when over capacity"""
        memories = self._storage.get(session_id, {})
        if len(memories) > self._max_items:
            # Sort by importance and access count
            sorted_keys = sorted(
                memories.keys(),
                key=lambda k: (memories[k].importance, memories[k].access_count)
            )
            # Remove least important
            for key in sorted_keys[:len(memories) - self._max_items]:
                del memories[key]


class LongTermMemory:
    """
    Redis-backed persistent memory.
    Survives across sessions, stores user preferences and history.
    """
    
    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._local_fallback: Dict[str, Dict[str, str]] = {}
        self._prefix = "webshop:memory:"
    
    async def store(
        self, 
        user_id: str, 
        key: str, 
        value: Any,
        importance: float = 0.5,
        ttl_days: int = 30
    ) -> None:
        """Store a persistent memory"""
        memory = Memory(
            key=key,
            value=value,
            memory_type="long_term",
            importance=importance
        )
        
        redis_key = f"{self._prefix}{user_id}:{key}"
        data = json.dumps(memory.to_dict())
        
        if self._redis:
            await self._redis.setex(redis_key, ttl_days * 86400, data)
        else:
            if user_id not in self._local_fallback:
                self._local_fallback[user_id] = {}
            self._local_fallback[user_id][key] = data
        
        logger.debug(f"Stored long-term memory: {key} for user {user_id}")
    
    async def retrieve(self, user_id: str, key: str) -> Optional[Any]:
        """Retrieve a persistent memory"""
        redis_key = f"{self._prefix}{user_id}:{key}"
        
        if self._redis:
            data = await self._redis.get(redis_key)
        else:
            data = self._local_fallback.get(user_id, {}).get(key)
        
        if data:
            memory = Memory.from_dict(json.loads(data))
            return memory.value
        return None
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get all stored information about a user"""
        profile = {
            "user_id": user_id,
            "preferences": {},
            "history": [],
            "metadata": {}
        }
        
        if self._redis:
            pattern = f"{self._prefix}{user_id}:*"
            keys = await self._redis.keys(pattern)
            for key in keys:
                data = await self._redis.get(key)
                if data:
                    memory = Memory.from_dict(json.loads(data))
                    short_key = key.replace(f"{self._prefix}{user_id}:", "")
                    profile["preferences"][short_key] = memory.value
        else:
            if user_id in self._local_fallback:
                for key, data in self._local_fallback[user_id].items():
                    memory = Memory.from_dict(json.loads(data))
                    profile["preferences"][key] = memory.value
        
        return profile
    
    async def delete(self, user_id: str, key: str) -> bool:
        """Delete a memory"""
        redis_key = f"{self._prefix}{user_id}:{key}"
        
        if self._redis:
            return await self._redis.delete(redis_key) > 0
        else:
            if user_id in self._local_fallback:
                if key in self._local_fallback[user_id]:
                    del self._local_fallback[user_id][key]
                    return True
        return False


class ConversationMemory:
    """
    Specialized memory for conversation history.
    Maintains context window and summarizes old messages.
    """
    
    def __init__(self, max_messages: int = 20):
        self._conversations: Dict[str, List[Dict]] = {}
        self._summaries: Dict[str, str] = {}
        self._max_messages = max_messages
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the conversation"""
        if session_id not in self._conversations:
            self._conversations[session_id] = []
        
        self._conversations[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Check if we need to summarize
        if len(self._conversations[session_id]) > self._max_messages:
            self._summarize_old_messages(session_id)
    
    def get_messages(self, session_id: str, last_n: int = 10) -> List[Dict]:
        """Get recent messages for context"""
        if session_id not in self._conversations:
            return []
        
        messages = self._conversations[session_id][-last_n:]
        
        # Prepend summary if exists
        if session_id in self._summaries:
            summary_message = {
                "role": "system",
                "content": f"Résumé de la conversation précédente: {self._summaries[session_id]}"
            }
            return [summary_message] + messages
        
        return messages
    
    def _summarize_old_messages(self, session_id: str) -> None:
        """Summarize old messages to save context space"""
        messages = self._conversations[session_id]
        old_messages = messages[:-10]  # Keep last 10
        
        if old_messages:
            # Create a simple summary (in production, use LLM)
            topics = set()
            for msg in old_messages:
                if "prix" in msg["content"].lower():
                    topics.add("tarifs")
                if "devis" in msg["content"].lower():
                    topics.add("devis")
                if "délai" in msg["content"].lower():
                    topics.add("délais")
            
            summary = f"Discussion sur: {', '.join(topics) if topics else 'divers sujets'}"
            self._summaries[session_id] = summary
            
            # Keep only recent messages
            self._conversations[session_id] = messages[-10:]
    
    def clear(self, session_id: str) -> None:
        """Clear conversation history"""
        if session_id in self._conversations:
            del self._conversations[session_id]
        if session_id in self._summaries:
            del self._summaries[session_id]


# Singleton instances
_short_term: Optional[ShortTermMemory] = None
_long_term: Optional[LongTermMemory] = None
_conversation: Optional[ConversationMemory] = None


def get_short_term_memory() -> ShortTermMemory:
    global _short_term
    if _short_term is None:
        _short_term = ShortTermMemory()
    return _short_term


def get_long_term_memory() -> LongTermMemory:
    global _long_term
    if _long_term is None:
        _long_term = LongTermMemory()
    return _long_term


def get_conversation_memory() -> ConversationMemory:
    global _conversation
    if _conversation is None:
        _conversation = ConversationMemory()
    return _conversation
