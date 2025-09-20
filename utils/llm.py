from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv
from configurations.config import config
from langchain_openai import ChatOpenAI

load_dotenv()

# To create the instance of AIMl Model
def get_llm_instance(
    temperature: float = 0.7,
    max_tokens: int = 1500,
    **kwargs
):
    """
    Initialize and return a LangChain chat model instance for any provider,
    and allowing temperature and other parameters to be set.

    Args:
        temperature (float, optional): Sampling temperature for the model. Defaults to 0.7.
        **kwargs: Additional optional parameters to pass to the model constructor.

    Returns:
        An instance of the chat model.
    """

    model = ChatOpenAI(
        model=config.MODEL_NAME,
        temperature=0,
        base_url="https://api.aimlapi.com/v1",
        api_key=config.AIML_API_KEY
    )
    return model


def get_llm_instance_with_tools(
    temperature: float = 0.7,
    tools: list = [],
    **kwargs
):
    llm = get_llm_instance(temperature, **kwargs)
    return llm.bind_tools(tools)
