"""Slack client for sending messages."""

import os
import sys
from typing import Dict, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackClient:
    """Slack client for sending messages to channels."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize Slack client with bot token."""
        self.token = token or os.environ.get("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")
        
        self.client = WebClient(token=self.token)
        
        # Channel aliases mapping
        self.channel_aliases = {
            "alerts": "#alerts",
            "general": "#general", 
            "notifications": "#notifications",
            "dev": "#dev",
            "test": "#test"
        }
    
    def resolve_channel(self, channel_alias: str) -> str:
        """Resolve channel alias to actual channel name."""
        # If it starts with #, use as-is
        if channel_alias.startswith("#"):
            return channel_alias
        
        # If it starts with C (channel ID), use as-is
        if channel_alias.startswith("C"):
            return channel_alias
            
        # Look up alias
        if channel_alias in self.channel_aliases:
            return self.channel_aliases[channel_alias]
        
        # Default to treating as channel name
        return f"#{channel_alias}"
    
    def post_message(self, channel_alias: str, message: str, use_blocks: bool = False) -> bool:
        """Post message to Slack channel."""
        try:
            channel = self.resolve_channel(channel_alias)
            
            if use_blocks:
                # Use block-based rich formatting
                response = self.client.chat_postMessage(
                    channel=channel,
                    text=message,  # Fallback text for notifications
                    blocks=self._create_message_blocks(message),
                    username="Todo Bot"
                )
            else:
                # Use simple text message
                response = self.client.chat_postMessage(
                    channel=channel,
                    text=message,
                    username="Todo Bot"
                )
            
            if response["ok"]:
                print(f"✅ Message sent to {channel}")
                return True
            else:
                print(f"❌ Failed to send message: {response.get('error', 'Unknown error')}")
                return False
                
        except SlackApiError as e:
            error_code = e.response["error"]
            if error_code == "channel_not_found":
                print(f"❌ Channel '{channel}' not found")
            elif error_code == "not_in_channel":
                print(f"❌ Bot is not a member of channel '{channel}'")
            elif error_code == "invalid_auth":
                print("❌ Invalid Slack token")
            else:
                print(f"❌ Slack API error: {error_code}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return False
    
    def _create_message_blocks(self, message: str) -> list:
        """Create Slack block format from message text."""
        lines = message.split('\n')
        blocks = []
        
        # Find the header (first line with content)
        header_line = ""
        content_lines = []
        
        for line in lines:
            if line.strip() and not header_line:
                header_line = line.strip()
            elif line.strip():
                content_lines.append(line)
        
        # Add header block if we have one
        if header_line:
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_line.replace("*", "").replace("✅", "✅").replace("⚠️", "⚠️")
                }
            })
        
        # Add divider
        if header_line:
            blocks.append({"type": "divider"})
        
        # Process content into sections
        current_section = []
        section_content = []
        
        for line in content_lines:
            line = line.strip()
            if not line:
                continue
                
            # If line starts with emoji and asterisk, it's a section header
            if line and any(emoji in line for emoji in ["📈", "📊", "🕐", "📋", "🔍"]) and "*" in line:
                # Save previous section if exists
                if section_content:
                    current_section.append("\n".join(section_content))
                    section_content = []
                # Start new section
                current_section.append(line)
            else:
                # Add to current section content
                section_content.append(line)
        
        # Add final section
        if section_content:
            current_section.append("\n".join(section_content))
        
        # Create context block with all content
        if current_section:
            full_content = "\n\n".join(current_section)
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": full_content
                    }
                ]
            })
        
        return blocks
    
    def list_available_aliases(self) -> Dict[str, str]:
        """Get available channel aliases."""
        return self.channel_aliases.copy()