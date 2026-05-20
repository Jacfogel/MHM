# ai/conversational_context/__init__.py

"""
Natural-language context assembly for comprehensive conversational AI prompts.

Split from ai/response_generator.py so prompt orchestration stays separate from
engagement post-processing. Prefer adding new context phrasing in context_phraser.py
rather than growing response_generator.py. Analytics belong in ai.context_builder.
"""

from ai.conversational_context.assembly import (
    assemble_comprehensive_messages,
    build_context_parts,
)

__all__ = [
    "assemble_comprehensive_messages",
    "build_context_parts",
]
