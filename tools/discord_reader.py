"""
Discord Content Reader

A module for reading and processing content from Discord channels.
Designed to be used as a base component for autonomous agents.
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import discord
from discord import Intents

class DiscordContentReader:
    """A class to read and process content from Discord channels."""
    
    def __init__(self, token: str):
        """Initialize the Discord reader with necessary permissions.
        
        Args:
            token (str): Discord bot token for authentication
        """
        # Set up Discord client with required intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.messages = True
        
        self.client = discord.Client(intents=intents)
        self.token = token

    async def get_channel_content(
        self,
        channel_id: int,
        start_date: datetime,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch and process content from a Discord channel."""
        messages = []
        print(f"Getting content for channel {channel_id}")
        
        try:
            print("- Setting up on_ready event")
            ready_event = asyncio.Event()
            
            @self.client.event
            async def on_ready():
                try:
                    print("- Bot is ready")
                    channel = self.client.get_channel(channel_id)
                    if not channel:
                        print(f"Error: Could not access channel {channel_id}")
                        return

                    print(f"- Found channel: {channel.name}")
                    print("- Starting message fetch")
                    
                    async for message in channel.history(
                        limit=limit,
                        after=start_date,
                        oldest_first=True
                    ):
                        message_data = self._process_message(message)
                        messages.append(message_data)
                        if len(messages) % 10 == 0:
                            print(f"- Fetched {len(messages)} messages so far")
                    
                    print("- Message fetch complete")
                except Exception as e:
                    print(f"Error in on_ready: {str(e)}")
                    raise
                finally:
                    ready_event.set()
                    await self.client.close()  # Close client after fetching
            
            print("- Starting Discord client")
            try:
                await self.client.start(self.token)
            except Exception as e:
                print(f"Error starting client: {str(e)}")
                raise
            finally:
                await ready_event.wait()  # Wait for event before proceeding
            
        except Exception as e:
            print(f"Error in get_channel_content: {str(e)}")
            raise
        finally:
            print("- Cleanup: Checking client status")
            if not self.client.is_closed():
                print("- Cleanup: Closing client")
                await self.client.close()
            print("- Cleanup: Client closed")
        
        return messages

    def _process_message(self, message: discord.Message) -> Dict[str, Any]:
        """Process a Discord message into a structured format.
        
        Args:
            message (discord.Message): Raw Discord message object
            
        Returns:
            Dict[str, Any]: Structured message data
        """
        return {
            'content': message.content,
            'author': str(message.author),
            'author_id': str(message.author.id),
            'timestamp': message.created_at,
            'attachments': [att.url for att in message.attachments],
            'embeds': [embed.to_dict() for embed in message.embeds],
            'message_id': str(message.id),
            'is_pinned': message.pinned,
            'reference': str(message.reference) if message.reference else None,
        }

    @staticmethod
    async def fetch_recent_content(
        token: str,
        channel_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Convenience method to fetch recent content from a channel.
        
        Args:
            token (str): Discord bot token
            channel_id (int): Channel ID to read from
            days (int): Number of days of history to fetch
            
        Returns:
            List[Dict[str, Any]]: List of processed messages
        """
        reader = DiscordContentReader(token)
        start_date = datetime.now() - timedelta(days=days)
        return await reader.get_channel_content(channel_id, start_date)

    @staticmethod
    async def fetch_all_content(
        token: str,
        channel_id: int,
    ) -> List[Dict[str, Any]]:
        """Fetch all available content from a channel.
        
        Args:
            token (str): Discord bot token
            channel_id (int): Channel ID to read from
            
        Returns:
            List[Dict[str, Any]]: List of all messages
        """
        reader = DiscordContentReader(token)
        # Discord epoch timestamp (2015-01-01)
        discord_epoch = datetime(2015, 1, 1)
        return await reader.get_channel_content(channel_id, discord_epoch)

def get_available_channels(token: str) -> None:
    """Utility function to list all available channels.
    
    Args:
        token (str): Discord bot token
    """
    async def list_channels():
        reader = DiscordContentReader(token)
        
        @reader.client.event
        async def on_ready():
            print("\nAvailable Channels:")
            for guild in reader.client.guilds:
                print(f"\nServer: {guild.name}")
                for channel in guild.channels:
                    if isinstance(channel, discord.TextChannel):
                        print(f"- {channel.name} (ID: {channel.id})")
            await reader.client.close()
        
        await reader.client.start(token)
    
    asyncio.run(list_channels())

# Example usage
if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
    
    print(f"Using Channel ID: {CHANNEL_ID}")
    
    async def main():
        print("\n=== Discord Content Reader Demo ===")
        print("Initializing...")
        
        try:
            # Only test the weekly lookback
            print("\nAttempting to fetch last week's messages...")
            print("- Creating reader instance")
            reader = DiscordContentReader(TOKEN)
            
            print("- Setting start date")
            start_date = datetime.now() - timedelta(days=7)
            
            print("- Fetching messages")
            messages = await reader.get_channel_content(
                channel_id=CHANNEL_ID,
                start_date=start_date
            )
            
            print(f"\nSuccess! Fetched {len(messages)} messages")
            if messages:
                print("\nMost recent message:")
                print(messages[-1])
            else:
                print("\nNo messages found in the last 7 days")
            
        except Exception as e:
            print(f"\nError occurred: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            # Simplified cleanup
            if hasattr(reader, 'client') and not reader.client.is_closed():
                await reader.client.close()
    
    try:
        print("\nStarting main loop...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
    finally:
        print("Program terminated")