"""
Writer Agent

An agent that processes Discord content into categorized sections and generates summaries
based on provided style guides and newsletter context.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, ValidationError
from mirascope.core import openai, prompt_template
from mirascope.integrations.tenacity import collect_errors
from tenacity import retry, wait_exponential
from base import OpenAIAgent
from tools.discord_reader import DiscordContentReader
import asyncio

class WriterBase(OpenAIAgent):
    class ContentOutput(BaseModel):
        """Structure for categorized content output"""
        categories: List[Dict[str, Any]] = []
        
    class NewsletterConfig(BaseModel):
        """Configuration for newsletter style and context"""
        name: str
        description: str
        audience: str
        tone: str
        style_guide: str
        section_preferences: Optional[Dict[str, str]] = None
        custom_instructions: Optional[str] = None

    newsletter_config: NewsletterConfig

    def __init__(
        self,
        newsletter_config: Optional[NewsletterConfig] = None
    ):
        """Initialize writer with newsletter configuration."""
        config = newsletter_config or self.get_default_config()
        super().__init__(newsletter_config=config)

    @staticmethod
    def get_default_config() -> 'WriterBase.NewsletterConfig':
        """Provide default newsletter configuration."""
        return WriterBase.NewsletterConfig(
            name="Tech Newsletter",
            description="A curated newsletter covering the latest in technology",
            audience="Tech professionals and enthusiasts",
            tone="Professional yet accessible",
            style_guide="Keep summaries concise and highlight practical implications",
        )

    @staticmethod
    def parse_content_output(response: Union[Dict[str, Any], 'WriterBase.ContentOutput']) -> str:
        """Parse the structured content output into a string format"""
        print("\nDebug - Raw response type:", type(response))
        print("\nDebug - Raw response:", response)
        
        # Convert Pydantic model to dict if needed
        if hasattr(response, 'model_dump'):
            response_dict = response.model_dump()
        elif hasattr(response, 'dict'):
            response_dict = response.dict()
        else:
            response_dict = response if isinstance(response, dict) else {}
            
        print("\nDebug - Converted response:", response_dict)
            
        categories = response_dict.get('categories', [])
        if not categories:
            print("\nDebug - No categories found")
            return "No content categorized"
            
        formatted_categories = []
        for category in categories:
            items = category.get('items', [])
            formatted_items = [
                f"\n  - {item.get('summary', 'No summary')} ({item.get('links', ['No link'])[0]})"
                for item in items
            ]
            formatted_categories.append(
                f"\n{category.get('name', 'Uncategorized')}:{''.join(formatted_items)}"
            )
        result = "\n".join(formatted_categories)
        print("\nDebug - Formatted result:", result)
        return result or "No content categorized"

    def process_discord_content(self, messages: List[Dict[str, Any]]) -> str:
        """Format Discord messages for LLM processing."""
        formatted_entries = []
        for msg in messages:
            entry_parts = []
            if msg['content']:
                entry_parts.append(f"Content: {msg['content']}")
            for embed in msg['embeds']:
                if 'title' in embed:
                    entry_parts.append(f"Title: {embed['title']}")
                if 'description' in embed:
                    entry_parts.append(f"Description: {embed['description']}")
                if 'url' in embed:
                    entry_parts.append(f"URL: {embed['url']}")
            formatted_entries.append("\n".join(entry_parts))
        return "\n\n---\n\n".join(formatted_entries)

    @property
    def _format_section_preferences(self) -> str:
        """Format section preferences for the prompt."""
        if not self.newsletter_config.section_preferences:
            return "Use your judgment to create appropriate sections."
        
        return "\n".join([
            f"- {section}: {description}"
            for section, description in 
            self.newsletter_config.section_preferences.items()
        ])

    @property
    def _format_custom_instructions(self) -> str:
        """Format custom instructions for the prompt."""
        return self.newsletter_config.custom_instructions or "N/A"

class Writer(WriterBase):
    @openai.call(
        "gpt-4o-mini",
        response_model=WriterBase.ContentOutput,
        output_parser=WriterBase.parse_content_output,
        stream=False,
        json_mode=True
    )
    @prompt_template(
        """
        SYSTEM:
        You are a professional content curator and writer for {self.newsletter_config.name}.
        Your task is to categorize and summarize the following content.
        
        IMPORTANT: You must respond with a JSON object that has a "categories" array, like this:
        {{
            "categories": [
                {{
                    "name": "Developments",
                    "items": [
                        {{
                            "order": 1,
                            "original_content": "Microsoft released a neat Python library...",
                            "summary": "Microsoft has launched a new Python library for LLM-powered multi-agent simulations...",
                            "links": ["https://x.com/omarsar0/status/1857063448674263354"]
                        }}
                    ]
                }}
            ]
        }}

        NEWSLETTER CONTEXT:
        Description: {self.newsletter_config.description}
        Target Audience: {self.newsletter_config.audience}
        Tone: {self.newsletter_config.tone}
        Style: {self.newsletter_config.style_guide}
        
        SECTION PREFERENCES:
        {self._format_section_preferences}
        
        ADDITIONAL INSTRUCTIONS:
        {self._format_custom_instructions}
        
        USER: Analyze and categorize this content into the JSON format specified above:
        {content}
        """
    )
    def _step(
        self, 
        content: str, 
        *, 
        errors: List[ValidationError] | None = None
    ) -> Dict[str, Any]:
        """Process content into categorized sections."""
        print("\nProcessing with gpt-4o-mini...")
        # Return empty dict to let the OpenAI decorator handle the response
        return {}

    def run(self, prompt: str) -> Dict[str, Any]:
        """Run the agent and return the response directly."""
        print("\nDebug - Starting run with prompt:", prompt[:100], "...")
        try:
            response = self._step(prompt)
            print("\nDebug - Got response:", response)
            return response
        except Exception as e:
            print(f"\nError during run: {str(e)}")
            raise

    async def process_content(
        self,
        token: str,
        channel_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """Process Discord content into categorized sections."""
        try:
            print("FETCHING CONTENT...")
            messages = await DiscordContentReader.fetch_recent_content(
                token=token,
                channel_id=channel_id,
                days=days
            )
            
            if not messages:
                print("No messages found in the specified timeframe")
                return {"categories": []}
            
            print(f"PROCESSING {len(messages)} MESSAGES...")
            formatted_content = self.process_discord_content(messages)
            
            print("CATEGORIZING AND WRITING...")
            result = self.run(formatted_content)
            print("Response received!")
            return result
            
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            # Re-raise the exception after logging
            raise
        finally:
            # Cleanup any remaining connections
            await asyncio.sleep(0)  # Allow event loop to process pending closures

if __name__ == "__main__":
    import os
    import json
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
    
    async def main():
        try:
            # Example newsletter configuration
            config = WriterBase.NewsletterConfig(
                name="Improbable Automata",
                description="Field notes from the AI frontier (hallucinations may vary)",
                audience="founders, small business owners, and tech professionals interested in using AI to augment their work",
                tone="Hitchhiker's Guide to the Galaxy",
                style_guide="Washed-up up LessWrong blogger finding a new voice as a tech columnist with a subtle but classy taste for memes",
                section_preferences={
                    "Field Notes": "The overall theme of the newsletter, the biggest updates and developments in AI and my thoughts about them",
                    "Developments": "Commentary on AI news, research, and advancements",
                    "Augmented Community": "Updates on AI community stuff, new open source projects, jobs, meetups, and online discussions"
                },
                custom_instructions="We love a concise newsletter, but good personalities are hard to find"
            )
            
            writer = Writer(newsletter_config=config)
            
            print("\n=== Processing Multiple Content Examples ===")
            
            # Create sample messages for testing
            test_messages = [
                {
                    'content': 'https://x.com/omarsar0/status/1857063448674263354\n\nMicrosoft released a neat Python library to run LLM-powered multi-agent simulations of people with personalities, interests, and goals.',
                    'embeds': [{
                        'title': 'elvis (@omarsar0) on X',
                        'description': 'Microsoft released a neat Python library to run LLM-powered multi-agent simulations of people with personalities, interests, and goals.',
                        'url': 'https://twitter.com/omarsar0/status/1857063448674263354'
                    }]
                },
                {
                    'content': 'https://x.com/karpathy/status/1857090026776281404\n\nAndrej Karpathy shares insights on training your own LLM from scratch - fascinating thread on the challenges and opportunities.',
                    'embeds': [{
                        'title': 'Andrej Karpathy (@karpathy) on X',
                        'description': 'Training your own LLM from scratch - a thread on what it takes and what to watch out for.',
                        'url': 'https://twitter.com/karpathy/status/1857090026776281404'
                    }]
                },
                {
                    'content': 'Just launched our new open source project for AI agents! Check it out at github.com/coolproject',
                    'embeds': []
                }
            ]
            
            print("\nInput Content:")
            for msg in test_messages:
                print(f"\nContent: {msg['content']}")
                for embed in msg['embeds']:
                    print(f"Title: {embed.get('title', 'No title')}")
            
            # Format messages
            formatted_content = writer.process_discord_content(test_messages)
            
            print("\nProcessing content...")
            print("This may take 15-30 seconds for GPT-4 to process...")
            result = writer.run(formatted_content)
            
            print("\nFormatted Result:")
            print(json.dumps(result, indent=2))

        except Exception as e:
            print(f"\nError occurred: {str(e)}")
            raise

    asyncio.run(main()) 