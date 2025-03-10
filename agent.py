from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, Controller
from browser_use import BrowserConfig
from dotenv import load_dotenv
import asyncio
from pydantic import BaseModel
import os

# Load environment variables if any
load_dotenv()

provider_address = os.getenv("PROVIDER_ADDRESS")
network = os.getenv("NETWORK", "flare")

class RewardEpochInfo(BaseModel):
    primary: float
    secondary: float

# Define the output format using Pydantic
class WebpageInfo(BaseModel):
    availability_6h: float
    availability_24h: float
    success_rate_6h: RewardEpochInfo
    success_rate_24h: RewardEpochInfo


async def get_provider_monitor_data(custom_provider_address=None):
    """
    Get monitoring data for a Flare FTSO provider.
    
    Args:
        custom_provider_address (str, optional): The provider's address. 
                                         If not provided, uses environment variable.
    
    Returns:
        WebpageInfo: Structured monitoring data including availability and success rates
    """
    # Use the provided address or fall back to the environment variable
    current_provider_address = custom_provider_address or provider_address
        
    if not current_provider_address:
        raise ValueError("Provider address not provided and PROVIDER_ADDRESS not set in environment")
    
    llm = ChatOpenAI(model="gpt-4o")
    
    # Configure the browser to run in headless mode
    browser_config = BrowserConfig(
        headless=True,
        disable_security=False
    )
    
    agent = Agent(
        task=f"""
          Navigate to 'https://{network}-systems-explorer.flare.network/providers/ftso/{current_provider_address}' and return availability and success rates.
          example:

          Availability
          Success Rate
          LAST 6 HOURS
          99.87 %
          LAST 6 HOURS
          48.80 % / 95.87 %
          LAST 24 HOURS
          99.45 %
          LAST 24 HOURS
          46.60 % / 95.85 %
          LAST 6 HOURS
          48.80 % / 95.87 %

          The output should be in the following format:
          {{
            "availability_6h": 90.87,
            "availability_24h": 99.45,
            "success_rate_6h": {{
              "primary": 48.80,
              "secondary": 95.87
            }},
            "success_rate_24h": {{
              "primary": 46.60,
              "secondary": 95.85
            }}
          }}
        """,
        llm=llm,
        browser=Browser(config=browser_config),
        controller=Controller(output_model=WebpageInfo)
    )
    
    # Run the agent
    try:
        history = await agent.run()
        result = history.final_result()
        
        if result:
            try:
                parsed_result = WebpageInfo.model_validate_json(result)
                return parsed_result
            except Exception as parse_error:
                raise Exception(f"Error parsing result: {parse_error}. Raw result: {result}")
        else:
            raise Exception("No result was returned from the agent")
    except Exception as e:
        raise Exception(f"An error occurred while getting provider data: {e}")


async def main():
    try:
        provider_data = await get_provider_monitor_data()
        
        print("\nScraping Results (structured):")
        print(f"Availability 6h: {provider_data.availability_6h}")
        print(f"Availability 24h: {provider_data.availability_24h}")
        print(f"Success Rate 6h: {provider_data.success_rate_6h}")
        print(f"Success Rate 24h: {provider_data.success_rate_24h}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 