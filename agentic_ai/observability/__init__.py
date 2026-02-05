# Copyright (c) Microsoft. All rights reserved.

"""
Observability module for Agent Framework applications.

This module provides easy-to-use telemetry setup for:
- Traces (spans for agent/tool execution)
- Logs (structured logging with context)
- Metrics (token usage, latency, etc.)

Quick Start:
    from observability import setup_observability, get_tracer
    
    # Initialize once at startup
    setup_observability()
    
    # Use tracer for custom spans
    with get_tracer().start_as_current_span("my-operation"):
        # Your code here
        pass
"""

from .setup import (
    setup_observability,
    get_tracer,
    get_trace_id,
)

__all__ = [
    "setup_observability",
    "get_tracer",
    "get_trace_id",
]
