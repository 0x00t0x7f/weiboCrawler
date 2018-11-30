# -*- coding:utf-8 -*-

import os
import yaml


__all__ = ["configPools"]

normal_config = lambda path: yaml.load(open(path, "rt"))
config_path = os.path.join(os.getcwd(), "config.yaml")
configPools = type("configPools", (object,), normal_config(config_path))
