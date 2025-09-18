from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv
from configurations.config import config

load_dotenv()

# To create the instance of Any LangChain Model
# def get_llm_instance(
#     temperature: float = 0.7,
#     **kwargs
# ):
#     """
#     Initialize and return a LangChain chat model instance for any provider,
#     and allowing temperature and other parameters to be set.

#     Args:
#         temperature (float, optional): Sampling temperature for the model. Defaults to 0.7.
#         **kwargs: Additional optional parameters to pass to the model constructor.

#     Returns:
#         An instance of the chat model.
#     """

#     # Initialize the chat model with temperature and any other kwargs
#     model = init_chat_model(
#         config.MODEL_NAME,
#         model_provider=config.MODEL_PROVIDER,
#         temperature=temperature,
#         **kwargs
#     )
#     return model

# To create the instance of AIMl Model
def get_llm_instance(
    temperature: float = 0.7,
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

    # Initialize the chat model with temperature and any other kwargs
    from langchain_aimlapi import AimlapiLLM

    model = AimlapiLLM(
        model=config.MODEL_NAME,
        temperature=temperature,
        api_key=config.AIML_API_KEY,
        **kwargs
    )
    return model


def get_llm_instance_with_tools(
    temperature: float = 0.7,
    tools: list = [],
    **kwargs
):
    llm = get_llm_instance(temperature, **kwargs)
    return llm.bind_tools(tools)
