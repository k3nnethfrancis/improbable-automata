import requests
import inspect
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from mirascope.core import openai, prompt_template
from base import OpenAIAgent

class ResearcherBase(OpenAIAgent):
    max_results: int = 10

    def web_search(self, text: str) -> str:
        """Search the web for the given text.

        Args:
            text: The text to search for.

        Returns:
            The search results for the given text formatted as newline separated
            dictionaries with keys 'title', 'href', and 'body'.
        """
        try:
            results = DDGS(proxy=None).text(text, max_results=self.max_results)
            return "\n\n".join(
                [
                    inspect.cleandoc(
                        """
                        title: {title}
                        href: {href}
                        body: {body}
                        """
                    ).format(**result)
                    for result in results
                ]
            )
        except Exception as e:
            return f"{type(e)}: Failed to search the web for text"

class ResearcherBaseWithParser(ResearcherBase):
    def parse_webpage(self, link: str) -> str:
        """Parse the paragraphs of the webpage found at `link`.

        Args:
            link: The URL of the webpage.

        Returns:
            The parsed paragraphs of the webpage, separated by newlines.
        """
        try:
            response = requests.get(link)
            soup = BeautifulSoup(response.content, "html.parser")
            return "\n".join([p.text for p in soup.find_all("p")])
        except Exception as e:
            return f"{type(e)}: Failed to parse content from URL"
        
        
class ResearcherBaseWithStep(ResearcherBaseWithParser):
    @openai.call("gpt-4o-mini", stream=True)
    @prompt_template(
        """
        SYSTEM:
        Your task is to research a topic and summarize the information you find.
        This information will be given to a writer (user) to create a blog post.

        You have access to the following tools:
        - `web_search`: Search the web for information. Limit to max {self.max_results}
            results.
        - `parse_webpage`: Parse the content of a webpage.

        When calling the `web_search` tool, the `body` is simply the body of the search
        result. You MUST then call the `parse_webpage` tool to get the actual content
        of the webpage. It is up to you to determine which search results to parse.

        Once you have gathered all of the information you need, generate a writeup that
        strikes the right balance between brevity and completeness. The goal is to
        provide as much information to the writer as possible without overwhelming them.

        MESSAGES: {self.history}
        USER: {prompt}
        """
    )
    def _step(self, prompt: str) -> openai.OpenAIDynamicConfig:
        return {"tools": [self.web_search, self.parse_webpage]}
    
    
class Researcher(ResearcherBaseWithStep):
    def research(self, prompt: str) -> str:
        """Research a topic and summarize the information found.

        Args:
            prompt: The user prompt to guide the research. The content of this prompt
                is directly responsible for the quality of the research, so it is
                crucial that the prompt be clear and concise.

        Returns:
            The results of the research.
        """
        print("RESEARCHING...")
        result = self.run(prompt)
        print("RESEARCH COMPLETE!")
        return result