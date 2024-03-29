from pathlib import Path

from pydantic import BaseModel, model_validator, field_validator, ConfigDict
from pydantic_core.core_schema import ValidationInfo

from .model_to_yaml_interface import get_model_mapping_and_path, check_model_overlap, check_yaml_path, \
    update_yaml_from_model, generate_yaml_from_model


class YamlConfigurableModel(BaseModel):
    """
    An enhanced version of the Pydantic BaseModel that supports saving and loading model configurations as YAML files. 

    The ConfigurableModel provides automatic validation of fields, as well as serialization and deserialization to and
    from YAML. This functionality is especially useful in managing complex configurations and ensuring type correctness.

    The class uses an inner `YamlConfig` class to set up a mapping between model fields and YAML files.

    Inner class:
        YamlConfig: An inner class specifying YAML file path (YAML_PATH) and a mapping dictionary 
                    between YAML files and model fields (MODEL_MAPPING).

    Example usage:
    ```
    class ModelConfig(BaseModel):
        vectorizer: str = 'tfidf'
        classifier: str = 'bdt'
    
    
    class PreprocessingConfig(BaseModel):
        remove_stop_words: bool = True
    
    
    class MyConfig(YamlConfigurableModel):
        model: ModelConfig = ModelConfig()
        preprocessing: PreprocessingConfig = PreprocessingConfig()
    
        class YamlConfig:
            YAML_PATH = Path('/path/to/yaml')
            MODEL_MAPPING = {
                'ml_config': ['model', 'preprocessing'],
            }


    cfg = MyConfig()
    ```
    """
    model_config = ConfigDict(
        validate_default=True,
    )

    class YamlConfig:
        YAML_PATH: Path | str
        MODEL_MAPPING: dict[str, list[str]]

    @model_validator(mode="before")
    def check_yaml_path(cls, values):
        yaml_path = cls.YamlConfig.YAML_PATH
        if not isinstance(yaml_path, Path):
            cls.YamlConfig.YAML_PATH = Path(yaml_path)
        return values

    @field_validator("*", mode='before')
    def load_or_generate_model_config(cls, v, info: ValidationInfo):
        yaml_path, model_mapping = get_model_mapping_and_path(cls)

        if yaml_path is not None:
            check_model_overlap(info, model_mapping)

            for yaml_file, models in model_mapping.items():
                if info.field_name in models:
                    model_class = cls.model_fields[info.field_name].get_default()
                    yaml_file_path = check_yaml_path(yaml_file, yaml_path)
                    if not yaml_file_path.is_file():
                        generate_yaml_from_model(info, model_class, yaml_file_path)
                    return update_yaml_from_model(info, model_class, models, yaml_file_path)
        return v
