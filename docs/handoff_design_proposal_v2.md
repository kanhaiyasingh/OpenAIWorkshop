# Proposal: Lazy Intent Classification for Handoff Workflows

## The Key Idea

I'd like to propose an alternative handoff pattern that uses lazy intent classification—only triggered when a specialist agent signals they can't help—rather than having a coordinator mediate every turn.

The core insight: specialists know their own boundaries through their system prompt and signal when they're out of scope. The system then classifies intent and routes to the appropriate specialist.

## How It Works

**Each specialist has boundary instructions in their prompt:**

```
You are the Billing Specialist for Contoso support.

Your expertise: subscriptions, invoices, payments, account adjustments.

IMPORTANT: If the user asks about anything outside your domain, 
respond with this EXACT phrase:
"This is outside my area. Let me connect you with the right specialist."

Otherwise, handle billing questions directly using your tools.
```

**When the system detects this phrase in a response:**
1. Extract the original user request
2. Run intent classification to determine the correct domain
3. Route conversation to the new specialist
4. Transfer relevant context (configurable: N turns or full history)

**Otherwise, the specialist communicates directly with the user.** No intermediary, no overhead. Classification only happens when needed (first message or handoff signal).

## Why This Scales

The critical advantage here is scalability. Each specialist only needs to know their own boundaries—not the capabilities of other specialists. When you add a new specialist, you just define their domain and tools. No need to update coordination logic or make other specialists aware of the new addition. This makes the system scalable to a large number of specialist agents without growing complexity.

Other benefits:
- No coordinator overhead on every turn
- Fewer LLM API calls (around 40% reduction in my testing)
- Specialists stream directly to users for natural conversation flow
- Lower latency since most interactions bypass classification


## Flow Comparison

Current pattern (coordinator-mediated):
```
User: "I can't log in"
  → Coordinator analyzes → Routes to Security
  → Security responds → Coordinator
  → Coordinator requests user input
User: "What's my bill?"
  → Coordinator analyzes → Routes to Billing
```
Every turn goes through coordinator.

Proposed pattern (lazy classification):
```
User: "I can't log in"
  → [Classify once] → Security Specialist
  → Security ↔ User (direct)
User: "What's my bill?"
  → Security: "This is outside my area. Let me connect you..."
  → [Detect phrase] → [Classify] → Billing Specialist
  → Billing ↔ User (direct)
```
Classification only on entry and handoff signals.

## When to Use Each?

Coordinator-mediated works well for:
- Complex routing rules requiring centralized control
- Multi-tier specialist-to-specialist handoffs
- Strong governance/audit requirements
- Human-in-the-loop approval workflows

Lazy classification works well for:
- Customer support with clear domain specialists
- Low latency and natural conversation prioritized
- Specialists that can self-identify boundaries via prompts
- Token efficiency matters

## Implementation Question

Should this be added as an optional mode to HandoffBuilder?

```python
workflow = (
    HandoffBuilder(participants=[billing, security, products])
    .coordinator("billing")  # Starting agent
    .with_routing_mode("lazy_classification")  # vs "coordinator_mediated"
    .with_handoff_phrase("This is outside my area")  # Configurable
    .with_context_transfer(turns=3)  # How much history on handoff
    .build()
)
```

Or should it be a separate builder class altogether?

## Real Results and Reference Implementation

I've implemented this pattern for customer support with 3 domain specialists and seen:
- Around 40% reduction in LLM API calls vs coordinator-mediated
- Sub-second response times (direct streaming)
- Reliable handoffs using prompt-based boundary recognition
- Easy to scale (specialists don't need to know about each other)

For reference, here is my implementation which does not use the workflow framework:
[OpenAIWorkshop/agentic_ai/agents/agent_framework/multi_agent/HANDOFF_README.md](https://github.com/microsoft/OpenAIWorkshop/blob/main/agentic_ai/agents/agent_framework/multi_agent/HANDOFF_README.md)

## Discussion

Would love feedback on:
1. Should this be integrated into HandoffBuilder or kept separate?
2. Is "lazy_classification" a clear name for this mode?
3. Should the handoff phrase be standardized or configurable?
4. Any concerns about relying on prompt-based boundary recognition?

The key advantage is simplicity. Most of the time, specialists just talk directly to users. No third-party monitoring system needed. Adding new specialists doesn't require updating coordination logic—just define their domain and boundaries.

What do you think? Does this resonate with use cases you're working on?

