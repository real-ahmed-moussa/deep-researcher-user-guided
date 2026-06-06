# 📌 Deep Researcher: User-Guided

> An adaptive six-agent pipeline that clarifies your query, runs up to three rounds of parallel web searches, evaluates sufficiency, and delivers a structured report.

## 📖 Overview
 - Implements a six-agent research pipeline — Clarification → Planning → Search → Evaluation → Writing → Email — that converts a natural-language query into a 1,000+ word structured markdown report.
 - Extends a fixed workflow baseline by adding a pre-search clarification dialogue and a multi-round evaluation loop that adaptively fills research gaps identified between rounds, rather than always running a fixed sequence.
 - Built with the OpenAI Agents SDK (`openai-agents`), Gradio, and Python asyncio; runs locally by launching `deep_research.py` which opens a newspaper-styled browser UI.
 - An explicit sufficiency evaluator — coverage ≥ 7 AND depth ≥ 6, both scored 1–10 — governs early exit and caps the loop at three rounds to balance completeness against compute cost.

## 🏢 Business Impact
Researchers, analysts, and knowledge workers typically spend hours manually formulating search strategies, evaluating sources, and synthesizing findings into coherent documents. This pipeline eliminates that manual effort by automatically scoping ambiguous queries through a clarification dialogue, running five parallel web searches per round, and scoring information coverage and depth before committing to report writing. The result is a polished, structured report — optionally delivered by email — that reduces a multi-hour research task to a few minutes, enabling automated intelligence workflows for content teams, consultants, and analysts.

## 🚀 Features
✅ **Clarification Dialogue:** Before any search begins, a dedicated agent determines whether the query needs scoping and surfaces up to four targeted questions directly in the Gradio UI.  
✅ **Adaptive Multi-Round Search:** The orchestrator runs up to three search rounds, with the planner receiving explicit gap descriptions from the previous evaluator so follow-on queries fill holes rather than re-cover ground.  
✅ **Parallel Search Execution:** All five search queries within a round run concurrently via asyncio, so total round time equals the slowest single search rather than the sum of all five.  
✅ **Sufficiency Evaluation:** An evaluator agent scores coverage (1–10) and depth (1–10) after each round and triggers early exit when thresholds are met, avoiding unnecessary search iterations.  
✅ **Structured Markdown Report:** The writer agent produces a report with an executive summary, sectioned body, conclusions, and follow-up questions — all validated against a Pydantic schema before rendering.  
✅ **Email Delivery:** An optional email agent converts the markdown report to styled HTML and sends it via SendGrid, enabling fully hands-off report delivery to any recipient.  

## ⚙️ Tech Stack
| Technology                  | Purpose                                                                |
| --------------------------- | ---------------------------------------------------------------------- |
| `Python 3.12`               | Core runtime; asyncio drives concurrent search tasks within each round |
| `openai-agents`             | Agent SDK providing Runner, WebSearchTool, tracing, and function_tool  |
| `GPT-4o-mini`               | LLM powering all six agents via the Agents SDK                         |
| `Gradio`                    | Browser UI implementing the two-phase analyse → research workflow      |
| `Pydantic`                  | Enforces structured output schema for every agent response             |
| `SendGrid`                  | Converts the markdown report to styled HTML and delivers it by email   |
| `python-dotenv`             | Loads API keys and email config from `.env` at startup                 |

## 📂 Project Structure
<pre>
📦 Deep Researcher — User-Guided
 ┣ 📜 deep_research.py
 ┣ 📜 orchestrator.py
 ┣ 📜 models.py
 ┣ 📜 clarification_agent.py
 ┣ 📜 planner_agent.py
 ┣ 📜 search_agent.py
 ┣ 📜 evaluator_agent.py
 ┣ 📜 writer_agent.py
 ┣ 📜 email_agent.py
 ┣ 📜 LICENSE
 ┣ 📜 requirements.txt
 ┗ 📜 README.md
</pre>

> **Why one file per agent?** Each agent's instructions, model, and output type are co-located in its own module so any single agent can be inspected, swapped, or tested without touching the orchestration logic in `orchestrator.py`.

## 🛠️ Installation

1️⃣ **Clone the repository**
<pre>
git clone https://github.com/real-ahmed-moussa/deep-researcher-user-guided.git
cd deep-researcher-user-guided
</pre>

2️⃣ **Create a virtual environment and install dependencies**
<pre>
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
</pre>

3️⃣ **Configure environment variables**
<pre>
cp .env.example .env
# Edit .env and set:
#   OPENAI_API_KEY   — required; needs access to gpt-4o-mini and the Responses API
#   SENDGRID_API_KEY — required only if using the "Send report by email" option
#   EMAIL_FROM       — sender address for emailed reports
#   EMAIL_TO         — recipient address for emailed reports
</pre>

4️⃣ **Launch the application**
<pre>
python deep_research.py
</pre>

The Gradio UI opens in your browser automatically. Enter a research query, click **Analyse Query**, answer any clarifying questions that appear, then click **Start Research** to run the pipeline.

## 📊 Results
 - **Task:** End-to-end autonomous research pipeline combining user-guided query scoping, adaptive multi-round retrieval, sufficiency gating, and structured report generation.
 - **Report output:** Writer agent produces structured markdown reports of 1,000+ words covering executive summary, sectioned body, conclusions, and suggested follow-up questions.
 - **Search efficiency:** Five queries execute in parallel per round; the loop exits early as soon as coverage ≥ 7 AND depth ≥ 6, with a hard cap of three rounds.
 - **Quality gating:** Two-dimensional sufficiency scoring (coverage 1–10, depth 1–10) with explicit decision rules prevents over-searching while enforcing a minimum quality floor before writing begins.
 - **Full automation:** The complete flow — from query clarification to an emailed HTML report — requires zero manual intervention after the initial query is submitted.

## 📝 License
This project is shared for portfolio purposes only and may not be used for commercial purposes without permission.
