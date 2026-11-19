"""NVIDIA NIM model metadata and reasoning payload adapters."""

MODELS = {
    "deepseek-ai/deepseek-v4.1-flash": {
        "title": "DeepSeek V4.1 Flash",
        "subtitle": "Ultra-rápido · Comandos e SO",
        "image": True,
        "reasoning": {"off": 0, "low": 25, "medium": 60, "high": 100},
        "parameter": "reasoning_effort",
    },
    "minimaxai/minimax-m3.1-flash": {
        "title": "MiniMax M3.1 Flash",
        "subtitle": "Agente · Visão e Automação",
        "image": True,
        "reasoning": {"off": None, "low": "low", "medium": "medium", "high": "high"},
        "parameter": "reasoning_effort",
    },
    "nvidia/nemotron-3.5-super-vl-120b-a12b": {
        "title": "NVIDIA Nemotron 3.5 Super VL",
        "subtitle": "Multimodal · Leve e Estável",
        "image": True,
        "reasoning": {"off": "none", "low": "low", "medium": "low", "high": "high"},
        "parameter": "reasoning_effort",
    },
    "mistralai/mistral-large-4-1t-a52b": {
        "title": "Mistral Large 4",
        "subtitle": "Equilibrado · Tarefas Gerais",
        "image": True,
        "reasoning": {"off": "none", "low": "high", "medium": "high", "high": "high"},
        "parameter": "reasoning_effort",
    },
    "moonshotai/kimi-k3.1-pro": {
        "title": "Kimi K3.1 Pro",
        "subtitle": "Força Bruta · Contexto 1M",
        "image": True,
        "reasoning": {"off": None, "low": "low", "medium": "medium", "high": "high"},
        "parameter": "reasoning_effort",
    },
}

DEFAULT_MODEL = "deepseek-ai/deepseek-v4.1-flash"
REASONING_LEVELS = ("off", "low", "medium", "high")
IMAGE_MODELS = frozenset(model_id for model_id, data in MODELS.items() if data["image"])


class ModelRegistryError(ValueError):
    pass


def model_metadata(model_id):
    try:
        return MODELS[model_id]
    except (KeyError, TypeError) as error:
        raise ModelRegistryError("Selecione um modelo NVIDIA listado no assistente.") from error


def request_options(model_id, reasoning_level):
    model = model_metadata(model_id)
    if reasoning_level not in REASONING_LEVELS:
        raise ModelRegistryError("Selecione um nível de raciocínio válido.")
    value = model["reasoning"][reasoning_level]
    if value is None:
        return {}
    return {model["parameter"]: value}


def fallback_instruction(reasoning_level):
    if reasoning_level == "off":
        return "Responda de forma direta e breve, sem etapas intermediárias."
    if reasoning_level == "low":
        return "Analise o contexto e responda com os passos essenciais."
    if reasoning_level == "medium":
        return "Confira os pontos importantes e explique a conclusão com clareza."
    return "Analise cuidadosamente os impactos e apresente conclusões e passos úteis, sem expor raciocínio interno."
