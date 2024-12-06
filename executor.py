import os
from dotenv import load_dotenv; load_dotenv()
from mirascope.integrations.tenacity import collect_errors
from mirascope.core import openai, prompt_template
from pydantic import BaseModel, ValidationError
from tenacity import retry, wait_exponential
from base import OpenAIAgent
from agents.researcher import Researcher


class AgentExecutorBase(OpenAIAgent):
    researcher: Researcher = Researcher()
    num_paragraphs: int = 4

    class InitialDraft(BaseModel):
        draft: str
        critique: str

    @staticmethod
    def parse_initial_draft(response: InitialDraft) -> str:
        return f"Draft: {response.draft}\nCritique: {response.critique}"

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10),
        after=collect_errors(ValidationError),
    )
    @openai.call(
        "gpt-4o-mini", response_model=InitialDraft, output_parser=parse_initial_draft
    )
    @prompt_template(
        """
        SYSTEM:
        Your task is to write the initial draft for a blog post based on the information
        provided to you by the researcher, which will be a summary of the information
        they found on the internet.

        Along with the draft, you will also write a critique of your own work. This
        critique is crucial for improving the quality of the draft in subsequent
        iterations. Ensure that the critique is thoughtful, constructive, and specific.
        It should strike the right balance between comprehensive and concise feedback.

        If for any reason you deem that the research is insufficient or unclear, you can
        request that additional research be conducted by the researcher. Make sure that
        your request is specific, clear, and concise.

        MESSAGES: {self.history}
        USER:
        {previous_errors}
        {prompt}
        """
    )
    def _write_initial_draft(
        self, prompt: str, *, errors: list[ValidationError] | None = None
    ) -> openai.OpenAIDynamicConfig:
        """Writes the initial draft of a blog post along with a self-critique.

        Args:
            prompt: The user prompt to guide the writing process. The content of this
                prompt is directly responsible for the quality of the blog post, so it
                is crucial that the prompt be clear and concise.

        Returns:
            The initial draft of the blog post along with a self-critique.
        """
        return {
            "computed_fields": {
                "previous_errors": f"Previous Errors: {errors}" if errors else None
            }
        }
