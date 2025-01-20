import logging
import os
from dataclasses import asdict, dataclass, field
from dataclasses import fields as dc_fields
from pathlib import Path
from typing import Self

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class BotConfig(object):
    bot_token: str = None
    bug_bounty_url: str = None
    user_id: int = None
    check_interval: int = 600  # seconds

    def __post_init__(self):
        if isinstance(self.user_id, str):
            self.user_id = int(self.user_id)

        if isinstance(self.check_interval, str):
            self.check_interval = int(self.check_interval)


@dataclass
class LoggingConfig(object):
    level: int = logging.INFO
    file_path: str | None = None
    syslog_enabled: bool = False

    def __post_init__(self):
        log_levels = logging.getLevelNamesMapping()

        if isinstance(self.level, int):
            if self.level not in [val for key, val in log_levels.items()]:
                self.level = logging.INFO

        if isinstance(self.level, str):
            self.level = log_levels.get(self.level, logging.INFO)


@dataclass
class Config(object):
    """
    Generalized Config class
    """
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    app: BotConfig = field(default_factory=BotConfig)

    def __post_init__(self):
        attrs = [(field.name, field.type) for field in dc_fields(self)]
        for attr_name, attr_type in attrs:
            if isinstance(getattr(self, attr_name), dict):
                setattr(self, attr_name, attr_type(**getattr(self, attr_name)))

    @classmethod
    def load(cls, cfg_path: str | os.PathLike | None = "config.yaml") -> Self:
        """
            Load config from config file
                or from environment variables
        """
        if cfg_path and Path(cfg_path).exists():
            return cls._load_config_file(cfg_path)
        else:
            return cls._load_env_configs()

    @classmethod
    def _load_config_file(cls, cfg_path: str | os.PathLike) -> Self:
        """
            Loads config from yaml file
        """
        config = {}
        with open(cfg_path) as path:
            yaml_conf = path.read()
            config = yaml.safe_load(yaml_conf)
        return cls(**config)

    @classmethod
    def _load_env_configs(cls) -> Self:
        """
            Loads config from environment variables
                sets default values if any var found
        """
        if Path(".env").exists:
            load_dotenv()

        env_items = dict(os.environ.items())

        config = asdict(cls())
        cfg_fields = [x.name for x in dc_fields(cls)]
        env_vars = filter(
            lambda x: x.split("__")[0].lower() in cfg_fields,
            env_items.keys()
        )
        for env_var in env_vars:
            vars = env_var.lower().split("__")
            cfg_instance = config
            while vars:
                var = vars.pop(0)
                if var in cfg_instance:
                    if isinstance(cfg_instance[var], dict):
                        cfg_instance = cfg_instance[var]
                    else:
                        cfg_instance[var] = env_items[env_var]
        return cls(**config)


# Cached if imported
settings = Config.load()
