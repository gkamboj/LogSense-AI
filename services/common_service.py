from config.configuration import configs
from services import openai_service as ois
from services import sap_ai_service as sas


def get_active_ai_service():
    service = None
    if configs['sapAI.active']:
        service = sas
    elif configs['openai.active']:
        service = ois
    return service


def get_llm():
    service = get_active_ai_service()
    return service.get_llm() if service else None
