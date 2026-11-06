"""The same three-agent research workflow written for CrewAI (needs an LLM: CrewAI calls one for every agent step).
Set GEMINI_API_KEY (CrewAI model "gemini/gemini-2.0-flash") or run Ollama ("ollama/qwen2.5:1.5b"), then:
    pip install crewai && python crew.py "vector databases in Python"
Without an LLM, use agents.py (LangGraph), which runs the identical roles with rule-based fallbacks."""
import os, sys
from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
import search_tools as T
@tool("GitHub search")
def github(query: str) -> str:
    """Search GitHub repositories sorted by stars."""
    return str(T.run("github_search", query))
@tool("PyPI package")
def pypi(name: str) -> str:
    """Facts about a Python package from PyPI."""
    return str(T.run("pypi_package", name))
@tool("Web search")
def web(query: str) -> str:
    """General web search (DuckDuckGo)."""
    return str(T.run("web_search", query))
LLM = os.environ.get("CREW_LLM", "gemini/gemini-2.0-flash" if os.environ.get("GEMINI_API_KEY") else "ollama/qwen2.5:1.5b")
searcher = Agent(role="Searcher", goal="Find 8-12 authoritative, current sources on {topic}", backstory="A meticulous research librarian.", tools=[github, pypi, web], llm=LLM, verbose=True)
summarizer = Agent(role="Summarizer", goal="Summarise each source in one sentence with its key facts", backstory="An analyst who never adds facts that aren't in the source.", llm=LLM)
writer = Agent(role="Writer", goal="Write a structured, cited research report on {topic}", backstory="A technical writer who cites every claim.", llm=LLM)
t1 = Task(description="Search for sources on {topic}. Return a numbered list with title, URL and the raw facts.", expected_output="Numbered list of sources with facts", agent=searcher)
t2 = Task(description="Summarise every source from the previous step.", expected_output="One summary per source, keeping the numbering", agent=summarizer, context=[t1])
t3 = Task(description="Write a markdown report: Overview, Key findings, Comparison table, Open questions, Sources. Cite as [n].", expected_output="Markdown report", agent=writer, context=[t2])
crew = Crew(agents=[searcher, summarizer, writer], tasks=[t1, t2, t3], process=Process.sequential)
if __name__ == "__main__": print(crew.kickoff(inputs={"topic": " ".join(sys.argv[1:]) or "vector databases in Python"}))
