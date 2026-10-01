"""Chat with TeachMate from the terminal (the Node API must be running).

Examples:
  python cli.py "Why did engagement drop?"
  python cli.py --lesson segmented-and-paged-memory-demo2 "What worked well in this lecture?"
  python cli.py            # interactive session; type 'exit' to quit
"""
import argparse
import asyncio
import logging
import sys
import textwrap

from app.analytics import EvidenceLog
from app.assistant import TeachMate
from app.tcherly_client import TcherlyClient, sign_in
from app.tools import ToolContext

DEFAULT_LESSON = "demonstration-of-java-programs-demo1"


def print_turn(turn, evidence: EvidenceLog, show_evidence: bool) -> None:
    print(f"\n--- TeachMate ({turn.model}) ---\n")
    print(turn.text)
    calls = ", ".join(f"{c['name']}({', '.join(f'{k}={v}' for k, v in c['args'].items())})" for c in turn.tool_calls) or "none"
    print(f"\n[tools used: {calls}]")
    unknown = [c for c in turn.cited if evidence.get(c) is None]
    print(f"[cited: {', '.join(turn.cited) or 'nothing'}" + (f"; UNKNOWN IDs: {', '.join(unknown)}" if unknown else "") + "]")
    g = turn.grounding
    print(
        f"[grounding: {'OK' if g.get('grounded') else 'ISSUES'}, score {g.get('score')}, {g.get('checked_numbers')} numbers checked"
        + (", answer was auto-repaired" if turn.repaired else "")
        + "]"
    )
    for proposal in turn.proposals:
        print(f"[proposed reflection: {proposal['topic']} (min {proposal['start_min']}-{proposal['end_min']}): {proposal['question']} | action: {proposal['action'] or '-'}]")
    if show_evidence:
        for evidence_id in turn.cited:
            item = evidence.get(evidence_id)
            if item:
                print(textwrap.fill(f"  {item.id}: {item.fact}", width=110, subsequent_indent="      "))


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question", nargs="*", help="question to ask (omit for interactive mode)")
    parser.add_argument("--lesson", default=DEFAULT_LESSON, help="lesson slug or _id")
    parser.add_argument("--email", default="demo.teacher@tcherly.local")
    parser.add_argument("--password", default="Demo@1234")
    parser.add_argument("--evidence", action="store_true", help="print the evidence items that were cited")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    token = await sign_in(args.email, args.password)
    client = TcherlyClient(token)
    ctx = ToolContext(client, args.lesson)
    assistant = TeachMate()
    history = None

    try:
        questions = [" ".join(args.question)] if args.question else None
        while True:
            if questions is not None:
                if not questions:
                    break
                question = questions.pop(0)
                print(f"\nTeacher: {question}")
            else:
                question = input("\nTeacher> ").strip()
                if question.lower() in {"exit", "quit"}:
                    break
                if not question:
                    continue
            turn = await assistant.reply(ctx, question, history)
            history = turn.history
            print_turn(turn, ctx.evidence, args.evidence)
    finally:
        await client.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
