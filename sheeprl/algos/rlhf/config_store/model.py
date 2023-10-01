from dataclasses import dataclass
from enum import Enum
from typing import Optional

from hydra.core.config_store import ConfigStore
from omegaconf import II, MISSING


# Omegaconf does not support Literal String types
class FINETUNE_MODE(Enum):
    ALL = "all"
    LAST_LAYER = "last_layer"
    LORA = "lora"


@dataclass
class LibraryConfig:
    name: str = MISSING


@dataclass
class HuggingFaceConfig(LibraryConfig):
    name: str = "transformers"
    model_name: str = II("model.name")
    trust_remote_code: bool = False
    load_in_8bit: bool = False
    low_cpu_mem_usage: bool = False
    use_cache: bool = False


@dataclass
class LORAConfig:
    targets: str = MISSING
    rank: int = 16
    alpha: float = 16
    dropout: float = 0.0


@dataclass
class ModelConfig:
    name: str = MISSING
    embedding_dim_name: Optional[str] = None
    transformer_name: Optional[str] = None
    casual: bool = True
    freeze_transformer: bool = False
    disable_dropout: bool = False
    library_config: HuggingFaceConfig = HuggingFaceConfig()
    finetune_mode: FINETUNE_MODE = FINETUNE_MODE.ALL
    lora_config: Optional[LORAConfig] = None


@dataclass
class OPTConfig(ModelConfig):
    name: str = "facebook/opt-350m"
    embedding_dim_name: Optional[str] = "word_embed_proj_dim"
    lora_config: Optional[LORAConfig] = LORAConfig(targets="('q_proj','v_proj')")


@dataclass
class GPT2Config(ModelConfig):
    name: str = "gpt2-medium"
    embedding_dim_name: Optional[str] = "n_embd"
    lora_config: Optional[LORAConfig] = LORAConfig(targets="('c_attn',)")


@dataclass
class Phi1dot5Config(ModelConfig):
    name: str = "microsoft/phi-1_5"
    library_config: HuggingFaceConfig = HuggingFaceConfig(trust_remote_code=True)


def register_model_configs(cs: ConfigStore) -> None:
    cs.store(
        group="model",
        name="opt",
        node=OPTConfig,
    )
    cs.store(
        group="model",
        name="gpt2",
        node=GPT2Config,
    )
    cs.store(
        group="model",
        name="phi",
        node=Phi1dot5Config,
    )
