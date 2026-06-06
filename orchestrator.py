import asyncio
import logging
from agents import Runner, trace, gen_trace_id

logger = logging.getLogger(__name__)

from models import (
    ResearchState, ResearchStatus,
    WebSearchPlan, WebSearchItem,
    SufficiencyEvaluation, ReportData,
    ClarificationPlan,
)
from clarification_agent import clarification_agent
from planner_agent import planner_agent
from evaluator_agent import evaluator_agent
from search_agent import search_agent
from writer_agent import writer_agent
from email_agent import email_agent

MAX_ROUNDS = 3


class ResearchOrchestrator:

    async def get_clarifications(self, query: str) -> ClarificationPlan:
        """Ask the clarification agent whether questions are needed."""
        result = await Runner.run(clarification_agent, f"Research query: {query}")
        return result.final_output_as(ClarificationPlan)

    async def run(self, state: ResearchState, send_email_after: bool = False):
        """
        Main research loop. Yields status strings for the UI to display.
        Mutates `state` in place so the caller can read the final report.
        """
        trace_id = gen_trace_id()
        with trace("Deep Research", trace_id=trace_id):
            yield f"🔍 Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            # ── Round loop ──────────────────────────────────────────────────
            while state.rounds_completed < MAX_ROUNDS:
                round_num = state.rounds_completed + 1
                yield f"📋 **Round {round_num}** — Planning searches..."
                state.status = ResearchStatus.PLANNING

                # Build the planner prompt, including gaps from previous evaluation
                gaps_context = ""
                if state.evaluation_history:
                    last_eval = state.evaluation_history[-1]
                    if last_eval.gaps:
                        gaps_context = (
                            "\n\nGaps identified in previous research round:\n"
                            + "\n".join(f"- {g}" for g in last_eval.gaps)
                            + "\n\nFocus new searches on filling these gaps."
                        )
                    if last_eval.suggested_queries:
                        gaps_context += (
                            "\n\nSuggested search queries:\n"
                            + "\n".join(f"- {q}" for q in last_eval.suggested_queries)
                        )

                planner_input = f"{state.enriched_query}{gaps_context}"
                plan_result = await Runner.run(planner_agent, planner_input)
                search_plan = plan_result.final_output_as(WebSearchPlan)

                yield f"🔎 Searching {len(search_plan.searches)} queries in parallel..."
                state.status = ResearchStatus.SEARCHING

                # Parallel searches
                round_results = await self._run_searches(search_plan.searches)
                state.search_results.extend(round_results)
                state.rounds_completed += 1

                yield f"✅ Round {round_num} complete — {len(round_results)} results gathered ({len(state.search_results)} total)"

                # ── Evaluate sufficiency ────────────────────────────────────
                yield f"🧠 Evaluating research sufficiency..."
                state.status = ResearchStatus.EVALUATING

                eval_input = (
                    f"Research query: {state.enriched_query}\n\n"
                    f"Research round completed: {state.rounds_completed} of {MAX_ROUNDS} max\n\n"
                    f"Accumulated search results:\n{state.search_results_summary}"
                )
                eval_result = await Runner.run(evaluator_agent, eval_input)
                evaluation = eval_result.final_output_as(SufficiencyEvaluation)
                state.evaluation_history.append(evaluation)

                coverage = evaluation.coverage_score
                depth = evaluation.depth_score
                yield (
                    f"📊 Coverage: {coverage}/10 | Depth: {depth}/10 — "
                    f"{'✅ Sufficient' if evaluation.is_sufficient else '⚠️ More research needed'}"
                )

                if evaluation.is_sufficient:
                    yield f"💡 {evaluation.reasoning}"
                    break

                if state.rounds_completed < MAX_ROUNDS:
                    yield f"🔄 Gaps found: {', '.join(evaluation.gaps[:3])}. Starting next round..."
                else:
                    yield f"⚠️ Max rounds reached. Proceeding with available research."
                    break

            # ── Write report (handoff pattern) ──────────────────────────────
            yield "✍️ Writing report..."
            state.status = ResearchStatus.WRITING

            writer_input = (
                f"{state.enriched_query}\n\n"
                f"Summarised search results ({state.rounds_completed} rounds):\n"
                f"{state.search_results_summary}"
            )
            write_result = await Runner.run(writer_agent, writer_input)
            state.report = write_result.final_output_as(ReportData)
            state.status = ResearchStatus.COMPLETE

            yield "📄 Report complete!"
            yield f"__REPORT__{state.report.markdown_report}"
            yield f"__SUMMARY__{state.report.short_summary}"
            yield f"__FOLLOWUP__{','.join(state.report.follow_up_questions)}"

            # ── Optional email handoff ───────────────────────────────────────
            if send_email_after:
                yield "📧 Sending email..."
                state.status = ResearchStatus.EMAILING
                try:
                    await Runner.run(email_agent, state.report.markdown_report)
                    yield "📬 Email sent!"
                except Exception as e:
                    yield f"⚠️ Email failed: {str(e)}"

    async def _run_searches(self, searches: list[WebSearchItem]) -> list[str]:
        """Run all searches in parallel, return non-None results."""
        tasks = [asyncio.create_task(self._single_search(item)) for item in searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
        return results

    async def _single_search(self, item: WebSearchItem) -> str | None:
        """Run one search, return summary string or None on failure."""
        prompt = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, prompt)
            return str(result.final_output)
        except Exception as e:
            logger.warning("Search failed for %r: %s", item.query, e)
            return None
