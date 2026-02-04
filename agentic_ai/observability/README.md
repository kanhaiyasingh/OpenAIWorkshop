# Agent Observability with Application Insights

This module provides full observability for Agent Framework applications using Azure Application Insights and Grafana dashboards.

## Features

- **Traces**: Full span hierarchy for agent executions, tool calls, and LLM invocations
- **Logs**: Structured logging with trace context correlation
- **Metrics**: Token usage, latency, and custom metrics
- **Grafana Dashboards**: Pre-built dashboards for agent and workflow visualization

## Quick Start

### 1. Get your Application Insights Connection String

From Azure Portal:
1. Navigate to your Application Insights resource
2. Go to **Overview** → **Connection String**
3. Copy the full connection string

### 2. Configure Environment

Add to your `.env` file (in `agentic_ai/applications/`):

```bash
APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=xxx;IngestionEndpoint=https://xxx.in.applicationinsights.azure.com/;LiveEndpoint=https://xxx.livediagnostics.monitor.azure.com/"

# Optional: Enable sensitive data (prompts/responses) - DEV ONLY!
ENABLE_SENSITIVE_DATA=true

# Optional: Custom service name
OTEL_SERVICE_NAME="contoso-agent"
```

### 3. Install Dependencies

```bash
cd agentic_ai/applications
uv sync
```

### 4. Run the Sample

```bash
# Start MCP server first
cd mcp && uv run python mcp_service.py

# In another terminal, run the sample
cd agentic_ai/applications
uv run python ../observability/sample_agent_with_tracing.py
```

## Usage in Your Code

### Basic Setup

```python
from observability import setup_observability, get_tracer

# Initialize once at application startup
setup_observability(
    connection_string="InstrumentationKey=...",  # Or set APPLICATIONINSIGHTS_CONNECTION_STRING
    service_name="my-agent-app",
    enable_live_metrics=True,
    enable_sensitive_data=False,  # Set True only in dev!
)

# Use tracer for custom spans
tracer = get_tracer()
with tracer.start_as_current_span("my-operation"):
    # Your code here
    pass
```

### With Agents

```python
from observability import setup_observability, get_tracer, get_trace_id
from agent_framework import ChatAgent
from opentelemetry.trace import SpanKind

# Setup observability BEFORE creating agents
setup_observability()

tracer = get_tracer()

# Create a parent span for the session
with tracer.start_as_current_span("customer-session", kind=SpanKind.SERVER) as span:
    trace_id = get_trace_id()
    print(f"Trace ID: {trace_id}")
    
    # Add custom attributes
    span.set_attribute("customer.id", "12345")
    span.set_attribute("session.type", "support")
    
    # Run your agent - all tool calls and LLM invocations are traced automatically
    agent = ChatAgent(...)
    async for update in agent.run_stream(query, thread=thread):
        print(update.text, end="")
```

## Viewing Telemetry

### Azure Monitor Dashboards (Recommended)

Pre-built dashboards are available via Azure Monitor Workbooks - **no Grafana setup required!**

| Dashboard | URL | Description |
|-----------|-----|-------------|
| **Agent Overview** | https://aka.ms/amg/dash/af-agent | Agent execution, tool calls, token usage, response times |
| **Workflow Overview** | https://aka.ms/amg/dash/af-workflow | Workflow execution, step timing, fan-out/fan-in |

**To use:**
1. Click the dashboard link above
2. Select your **Subscription** and **Application Insights** resource from the dropdowns
3. View your live agent telemetry immediately!

![Agent Framework Dashboard](../docs/media/observability-dashboard.png)

### Azure Portal (Manual)

1. Go to Application Insights → **Transaction search**
2. Filter by Trace ID to see the full execution tree
3. Use **Live Metrics** for real-time monitoring

### KQL Queries

Use these queries in Application Insights → Logs:

**View all spans for recent traces:**
```kusto
dependencies
| where operation_Id in (dependencies
    | project operation_Id, timestamp
    | order by timestamp desc
    | summarize operations = make_set(operation_Id), timestamp = max(timestamp) by operation_Id
    | order by timestamp desc
    | project operation_Id
    | take 5)
| evaluate bag_unpack(customDimensions)
| extend tool_call_id = tostring(["gen_ai.tool.call.id"])
| project-keep timestamp, target, operation_Id, duration, gen_ai*
| order by timestamp asc
```

**Token usage by model:**
```kusto
customMetrics
| where name contains "gen_ai.client.token"
| summarize TotalTokens = sum(value) by name, bin(timestamp, 1h)
| render timechart
```

## What Gets Traced

The Agent Framework automatically captures:

| Span Type | Attributes |
|-----------|------------|
| **Agent Run** | `gen_ai.agent.name`, `gen_ai.agent.id` |
| **LLM Call** | `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens` |
| **Tool Call** | `gen_ai.tool.name`, `gen_ai.tool.call.id`, arguments, results |
| **MCP Tool** | `mcp.server.url`, `mcp.tool.name` |
| **Workflow** | `workflow.name`, `workflow.step`, fan-out/fan-in relationships |

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights connection string | Required |
| `ENABLE_SENSITIVE_DATA` | Include prompts/responses in traces | `false` |
| `OTEL_SERVICE_NAME` | Service name in telemetry | `agent_framework` |
| `OTEL_SERVICE_VERSION` | Service version | Package version |

## Troubleshooting

### No data in Application Insights

1. Verify connection string is correct
2. Check that `setup_observability()` returns `True`
3. Allow 2-5 minutes for data to appear in the portal
4. Check for firewall rules blocking outbound HTTPS

### Missing tool calls

Ensure you're using Agent Framework's MCP integration with `McpServerManager` which has built-in instrumentation.

### Sensitive data not appearing

Set `ENABLE_SENSITIVE_DATA=true` or pass `enable_sensitive_data=True` to `setup_observability()`.

> ⚠️ **Warning**: Never enable sensitive data in production as it may expose PII and confidential information.

## Related Documentation

- [Agent Framework Observability](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/observability)
- [Azure Monitor OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable)
- [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
