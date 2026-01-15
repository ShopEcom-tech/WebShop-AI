# 🚀 WebShop-AI Agent System - Major Enhancement Plan

## 📊 Current System Analysis

### What exists:
- Basic MARIE agent with simple prompt
- LangGraph orchestrator (basic routing)
- Claude/Gemini LLM router

### What's Missing (Critical):
| Feature | Impact | Priority |
|---------|--------|----------|
| **OCaml Debugger** | Trace agent execution | 🔴 HIGH |
| **RAG System** | Knowledge retrieval | 🔴 HIGH |
| **Agent Tools** | Web search, calculators | 🔴 HIGH |
| **Memory System** | Long-term memory (Redis) | 🔴 HIGH |
| **Observability** | OpenTelemetry tracing | 🟡 MED |
| **Sentiment Analysis** | Detect user emotions | 🟡 MED |
| **Multi-Agent Collab** | Agents working together | 🟡 MED |
| **Guardrails** | Safety filters | 🔴 HIGH |

---

## 🔧 Enhancements to Implement

### 1. 🐫 OCaml Agent Debugger/Tracer
Build a step-by-step tracer in OCaml for debugging agent execution.

```ocaml
(* ocaml-debugger/src/tracer.ml *)
type trace_event = {
  timestamp: float;
  agent: string;
  action: string;
  input: string;
  output: string option;
  duration_ms: int;
}

type trace_session = {
  session_id: string;
  events: trace_event list;
  start_time: float;
  end_time: float option;
}
```

**Features:**
- Real-time step tracing
- Execution graph visualization
- Performance profiling
- Error detection

---

### 2. 🧠 RAG System (Retrieval Augmented Generation)
Use Qdrant for vector search over Web Shop knowledge.

```python
# src/rag/retriever.py
class KnowledgeRetriever:
    def __init__(self, qdrant_client):
        self.client = qdrant_client
        self.collection = "webshop_knowledge"
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        # Embed query
        embedding = await self.embed(query)
        # Search Qdrant
        results = await self.client.search(
            collection_name=self.collection,
            query_vector=embedding,
            limit=top_k
        )
        return results
```

**Knowledge Base:**
- FAQ (50+ questions)
- Services détaillés
- Exemples de projets
- Politique de remboursement
- Témoignages clients

---

### 3. 🛠️ Agent Tools

| Tool | Description | Agent |
|------|-------------|-------|
| `WebSearch` | Search the web | All |
| `Calculator` | Math operations | LUCAS |
| `PDFGenerator` | Create PDFs | LUCAS |
| `EmailSender` | Send emails | EMMA |
| `CalendarChecker` | Check availability | MARIE |
| `PriceCalculator` | Calculate quotes | LUCAS |
| `SocialPoster` | Post to socials | JOHN |
| `ImageGenerator` | Create images | JOHN |

```python
# src/tools/web_search.py
class WebSearchTool:
    name = "web_search"
    description = "Search the web for information"
    
    async def run(self, query: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query},
                headers={"X-Subscription-Token": API_KEY}
            )
        return self._format_results(response.json())
```

---

### 4. 💾 Advanced Memory System

```python
# src/memory/long_term.py
class LongTermMemory:
    """Redis-based long-term memory for agents"""
    
    async def remember(self, session_id: str, key: str, value: Any):
        """Store a memory"""
        await self.redis.hset(f"memory:{session_id}", key, json.dumps(value))
    
    async def recall(self, session_id: str, key: str) -> Any:
        """Retrieve a memory"""
        data = await self.redis.hget(f"memory:{session_id}", key)
        return json.loads(data) if data else None
    
    async def get_user_profile(self, user_id: str) -> UserProfile:
        """Get aggregated user information"""
        # Combine conversation history, preferences, past interactions
        ...
```

**Memory Types:**
- **Short-term**: Current conversation
- **Long-term**: User preferences, past purchases
- **Episodic**: Specific past interactions
- **Semantic**: General knowledge

---

### 5. 📊 OpenTelemetry Observability

```python
# src/observability/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

tracer = trace.get_tracer("webshop-ai")

class TracedAgent:
    async def process(self, state: AgentState) -> str:
        with tracer.start_as_current_span(
            f"agent.{self.name}.process",
            attributes={
                "agent.name": self.name,
                "session.id": state.session_id,
                "input.length": len(state.user_input)
            }
        ) as span:
            try:
                result = await self._do_process(state)
                span.set_attribute("output.length", len(result))
                return result
            except Exception as e:
                span.record_exception(e)
                raise
```

**Metrics:**
- Response time (p50, p95, p99)
- Token usage per request
- Error rate by agent
- Escalation rate
- User satisfaction score

---

### 6. 🛡️ Safety Guardrails

```python
# src/guardrails/safety.py
class SafetyGuardrails:
    def __init__(self):
        self.blocked_patterns = [...]
        self.sensitive_topics = [...]
    
    async def check_input(self, text: str) -> SafetyResult:
        """Check user input for safety issues"""
        # PII detection
        # Harmful content detection
        # Injection attempts
        ...
    
    async def check_output(self, text: str) -> SafetyResult:
        """Validate agent output before sending"""
        # Ensure no hallucinated prices
        # No competitor mentions
        # Appropriate tone
        ...
```

---

### 7. 😊 Sentiment & Intent Analysis

```python
# src/analysis/sentiment.py
class SentimentAnalyzer:
    def analyze(self, text: str) -> SentimentResult:
        return SentimentResult(
            sentiment="positive|neutral|negative|frustrated",
            confidence=0.95,
            emotions=["happy", "curious"],
            intent="asking_price|requesting_info|complaining"
        )
```

**Used for:**
- Adjust tone of response
- Trigger escalation if frustrated
- Track satisfaction over time

---

### 8. 🤝 Multi-Agent Collaboration

```python
# src/orchestrator/collaboration.py
class MultiAgentTask:
    """Task that requires multiple agents working together"""
    
    async def execute(self, request: str):
        # 1. HUGO generates content
        content = await self.agents["hugo"].generate(request)
        
        # 2. JOHN formats for social media
        social_post = await self.agents["john"].adapt(content, platform="linkedin")
        
        # 3. EMMA sends as email
        await self.agents["emma"].send(recipient, social_post)
        
        return {"content": content, "post": social_post}
```

---

## 📁 New File Structure

```
python-agents/
├── src/
│   ├── agents/
│   │   ├── base.py          # Enhanced base agent
│   │   ├── marie_support.py # MARIE v2.0
│   │   └── ...
│   ├── orchestrator/
│   │   ├── engine.py        # Enhanced orchestrator
│   │   └── collaboration.py # Multi-agent tasks
│   ├── rag/
│   │   ├── retriever.py     # Vector search
│   │   ├── embedder.py      # Text embeddings
│   │   └── indexer.py       # Knowledge indexing
│   ├── tools/
│   │   ├── base.py          # Tool interface
│   │   ├── web_search.py
│   │   ├── calculator.py
│   │   ├── pdf_generator.py
│   │   └── calendar.py
│   ├── memory/
│   │   ├── short_term.py    # Session memory
│   │   ├── long_term.py     # Redis persistence
│   │   └── semantic.py      # Vector memory
│   ├── guardrails/
│   │   ├── safety.py        # Content safety
│   │   └── validators.py    # Output validation
│   ├── analysis/
│   │   ├── sentiment.py     # Sentiment analysis
│   │   └── intent.py        # Intent detection
│   └── observability/
│       ├── tracing.py       # OpenTelemetry
│       └── metrics.py       # Prometheus
│
├── ocaml-debugger/           # OCaml tracer
│   ├── dune-project
│   ├── src/
│   │   ├── tracer.ml
│   │   ├── visualizer.ml
│   │   └── profiler.ml
│   └── bin/
│       └── main.ml
│
└── data/
    └── knowledge/
        ├── faq.json
        ├── services.json
        ├── testimonials.json
        └── projects.json
```

---

## ⏱️ Implementation Order

1. **OCaml Debugger** (now)
2. **Enhanced Memory System** (now)
3. **Agent Tools** (now)
4. **RAG System** (next)
5. **Sentiment Analysis** (next)
6. **Guardrails** (next)
7. **OpenTelemetry** (later)
8. **Multi-Agent Collab** (later)

---

## ✅ Ready to Implement

Proceeding with:
1. OCaml Debugger/Tracer
2. Enhanced MARIE agent with tools
3. Memory system (Redis)
4. RAG with Qdrant
