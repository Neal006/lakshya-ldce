"""
llm.py — Provider-agnostic LLM client (Groq / OpenAI-compatible).
LangSmith observability via RunTree.post() + RunTree.patch() — appears instantly in dashboard.
"""

import os
import time
import logging
import json
from datetime import datetime, timezone
from openai import OpenAI

logger = logging.getLogger("genai.llm")


# ─── LangSmith Bootstrap ─────────────────────────────────────────────

def _bootstrap_langsmith() -> dict | None:
    """Set the 4 LangSmith env vars and return config dict, or None if disabled."""
    try:
        from config import config
        if not (config.LANGCHAIN_TRACING and config.LANGCHAIN_API_KEY):
            logger.info("LangSmith tracing disabled — set LANGCHAIN_TRACING_V2=true + LANGCHAIN_API_KEY")
            return None

        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"]     = config.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"]     = config.LANGCHAIN_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"]    = config.LANGCHAIN_ENDPOINT

        logger.info(f"LangSmith tracing ready — project: {config.LANGCHAIN_PROJECT}")
        return {
            "project":  config.LANGCHAIN_PROJECT,
            "api_key":  config.LANGCHAIN_API_KEY,
            "endpoint": config.LANGCHAIN_ENDPOINT,
        }
    except Exception as e:
        logger.warning(f"LangSmith bootstrap failed: {e}")
        return None


_LS = _bootstrap_langsmith()


# ─── LangSmith Run Logger ────────────────────────────────────────────

def _ls_log_run(
    name:       str,
    inputs:     dict,
    outputs:    dict,
    start_time: datetime,
    end_time:   datetime,
    error:      str | None = None,
) -> None:
    """
    Log a completed LLM run to LangSmith using RunTree.post() + RunTree.patch().
    This is the same code path the SDK uses internally — runs appear in the
    dashboard instantly with full inputs, outputs, and token counts.
    """
    if not _LS:
        return
    try:
        from langsmith.run_trees import RunTree

        rt = RunTree(
            name         = name,
            run_type     = "llm",
            inputs       = inputs,
            start_time   = start_time,
            project_name = _LS["project"],
        )
        rt.post()                                       # create run (start)
        rt.end(outputs=outputs, end_time=end_time)      # set outputs + end_time
        if error:
            rt.error = error
        rt.patch()                                      # close run (appears in dashboard)

        # Force-flush the underlying client buffer so traces appear immediately
        # (default buffer timeout is 5000ms — won't flush in long-running server)
        client = getattr(rt, "client", None)
        if client is not None:
            flush = getattr(client, "_flush_run_ops_buffer", None)
            if flush is not None:
                flush()

    except Exception as e:
        logger.warning(f"LangSmith log failed: {e}")


# ─── LLM Client ──────────────────────────────────────────────────────

class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model  = model
        logger.info(
            f"LLMClient ready | model={model} | "
            f"tracing={'on → LangSmith' if _LS else 'off (local log only)'}"
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt:   str,
        temperature:   float = 0.25,
        max_tokens:    int   = 2048,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
        start_dt = datetime.now(timezone.utc)
        start_ts = time.time()

        try:
            response = self.client.chat.completions.create(
                model       = self.model,
                messages    = messages,
                temperature = temperature,
                max_tokens  = max_tokens,
            )
            content  = response.choices[0].message.content
            latency  = round((time.time() - start_ts) * 1000)
            end_dt   = datetime.now(timezone.utc)
            usage    = {
                "prompt_tokens":     getattr(response.usage, "prompt_tokens",     0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                "total_tokens":      getattr(response.usage, "total_tokens",      0),
            }

            # ── Log to LangSmith ────────────────────────────────────
            _ls_log_run(
                name       = "complaint-resolution-llm",
                inputs     = {"messages": messages, "model": self.model, "temperature": temperature},
                outputs    = {"text": content, "usage": usage},
                start_time = start_dt,
                end_time   = end_dt,
            )

            logger.info(json.dumps({
                "event":      "llm_call",
                "model":      self.model,
                "latency_ms": latency,
                "tokens":     usage,
                "langsmith":  _LS is not None,
                "status":     "success",
            }))
            return content

        except Exception as e:
            _ls_log_run(
                name       = "complaint-resolution-llm",
                inputs     = {"messages": messages, "model": self.model, "temperature": temperature},
                outputs    = {},
                start_time = start_dt,
                end_time   = datetime.now(timezone.utc),
                error      = str(e),
            )
            logger.error(json.dumps({
                "event":      "llm_call",
                "model":      self.model,
                "latency_ms": round((time.time() - start_ts) * 1000),
                "status":     "error",
                "error":      str(e),
            }))
            raise

    def health_check(self) -> bool:
        try:
            self.generate("Say OK.", "test", max_tokens=5)
            return True
        except Exception:
            return False
