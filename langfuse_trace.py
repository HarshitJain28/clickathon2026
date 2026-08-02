"""Cross-process Langfuse trace propagation.

Every agent in this pipeline runs as its own OS process, and each one builds
its own Langfuse client. Left alone, that produces one disconnected trace per
process — so a single spec onboarding scatters across ~5+ unrelated traces
with no way to see the run end to end.

This module threads one trace through all of them. The orchestrator opens a
root span for the run and exports its ids into the environment; every child
process picks those ids up and attaches its own work as a child span of that
same trace. The result is a single Langfuse trace per run, with the
Instrumentation / Loader / Context / Analysis stages nested inside it.

Nothing here is required for an agent to work standalone: with no parent ids
in the environment (a direct CLI invocation), `attach_to_parent` is a no-op
and each script traces exactly as it did before.
"""

import os
from contextlib import ExitStack, contextmanager, nullcontext

from langfuse import propagate_attributes

TRACE_ID_ENV = "LANGFUSE_PIPELINE_TRACE_ID"
PARENT_SPAN_ID_ENV = "LANGFUSE_PIPELINE_PARENT_SPAN_ID"
TRACE_NAME_ENV = "LANGFUSE_PIPELINE_TRACE_NAME"
SESSION_ID_ENV = "LANGFUSE_PIPELINE_SESSION_ID"


def parent_trace_context():
    """The trace/span this process should attach to, or None if it's a
    standalone run with no orchestrating parent."""
    trace_id = os.environ.get(TRACE_ID_ENV)
    if not trace_id:
        return None
    return {
        "trace_id": trace_id,
        "parent_span_id": os.environ.get(PARENT_SPAN_ID_ENV) or None,
    }


def child_trace_env(span, base_env=None, trace_name=None, session_id=None):
    """Environment for a subprocess so its spans land under `span`.

    Returns a full copy of the environment (defaulting to os.environ) with the
    propagation ids set, ready to hand to subprocess.run(env=...).

    `trace_name`/`session_id` are carried through so every process asserts the
    same trace-level attributes — see attach_to_parent for why that matters.
    """
    env = dict(base_env if base_env is not None else os.environ)
    env[TRACE_ID_ENV] = span.trace_id
    env[PARENT_SPAN_ID_ENV] = span.id
    if trace_name:
        env[TRACE_NAME_ENV] = trace_name
    if session_id:
        env[SESSION_ID_ENV] = session_id
    return env


@contextmanager
def attach_to_parent(client, name, as_type="agent", **kwargs):
    """Run the enclosed block as a child span of the orchestrator's trace.

    Also re-asserts the run's trace_name/session_id. That's deliberate, not
    redundant: the trace's own name is last-write-wins across the processes
    writing to it, so if only the orchestrator set it, whichever agent
    flushed last would rename the whole trace after itself (observed: a run
    showing up as "context_agent"). Having every process assert the same
    values makes the outcome order-independent.

    Falls back to a plain no-op context when this process wasn't launched by
    the orchestrator, so standalone CLI runs keep their previous behaviour
    (their own root trace) rather than silently losing instrumentation.
    """
    trace_context = parent_trace_context()
    if trace_context is None:
        with nullcontext():
            yield None
        return

    with ExitStack() as stack:
        span = stack.enter_context(
            client.start_as_current_observation(
                name=name, as_type=as_type, trace_context=trace_context, **kwargs
            )
        )
        attrs = {}
        if os.environ.get(TRACE_NAME_ENV):
            attrs["trace_name"] = os.environ[TRACE_NAME_ENV]
        if os.environ.get(SESSION_ID_ENV):
            attrs["session_id"] = os.environ[SESSION_ID_ENV]
        if attrs:
            stack.enter_context(propagate_attributes(**attrs))
        yield span
