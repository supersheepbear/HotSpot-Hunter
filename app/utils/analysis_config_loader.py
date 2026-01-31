# coding=utf-8
"""
分析配置加载器

从 config/analysis_config.yaml 加载AI分析和推送相关配置
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List


def load_analysis_config() -> Dict[str, Any]:
    """
    加载分析配置
    
    Returns:
        配置字典，包含：
        - max_analyze_per_run: 每次最多分析多少条新闻
        - batch_size: 批量分析的批次大小
        - push_importance_levels: 推送的重要性级别列表
        - max_push_per_run: 每次最多推送多少条新闻
    """
    # 默认配置
    default_config = {
        "max_analyze_per_run": 100,
        "batch_size": 20,
        "push_importance_levels": ["critical", "high"],
        "max_push_per_run": 50,
    }
    
    # 配置文件路径
    config_path = Path(__file__).parent.parent.parent / "config" / "analysis_config.yaml"
    
    if not config_path.exists():
        print(f"[配置] 分析配置文件不存在: {config_path}，使用默认配置")
        return default_config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config:
            print(f"[配置] 分析配置文件为空，使用默认配置")
            return default_config
        
        # 合并配置
        result = {}
        
        # 分析配置
        analysis_config = config.get("analysis", {})
        result["max_analyze_per_run"] = analysis_config.get("max_analyze_per_run", default_config["max_analyze_per_run"])
        result["batch_size"] = analysis_config.get("batch_size", default_config["batch_size"])
        
        # 推送配置
        push_config = config.get("push", {})
        result["push_importance_levels"] = push_config.get("importance_levels", default_config["push_importance_levels"])
        result["max_push_per_run"] = push_config.get("max_push_per_run", default_config["max_push_per_run"])
        
        # 验证配置
        if result["max_analyze_per_run"] <= 0:
            print(f"[配置警告] max_analyze_per_run 必须大于0，使用默认值: {default_config['max_analyze_per_run']}")
            result["max_analyze_per_run"] = default_config["max_analyze_per_run"]
        
        if result["batch_size"] <= 0:
            print(f"[配置警告] batch_size 必须大于0，使用默认值: {default_config['batch_size']}")
            result["batch_size"] = default_config["batch_size"]
        
        if result["max_push_per_run"] <= 0:
            print(f"[配置警告] max_push_per_run 必须大于0，使用默认值: {default_config['max_push_per_run']}")
            result["max_push_per_run"] = default_config["max_push_per_run"]
        
        # 验证重要性级别
        valid_levels = ["critical", "high", "medium", "low"]
        if not result["push_importance_levels"]:
            print(f"[配置警告] push_importance_levels 为空，使用默认值: {default_config['push_importance_levels']}")
            result["push_importance_levels"] = default_config["push_importance_levels"]
        else:
            # 过滤无效的级别
            result["push_importance_levels"] = [
                level for level in result["push_importance_levels"]
                if level in valid_levels
            ]
            if not result["push_importance_levels"]:
                print(f"[配置警告] push_importance_levels 中没有有效的级别，使用默认值: {default_config['push_importance_levels']}")
                result["push_importance_levels"] = default_config["push_importance_levels"]
        
        print(f"[配置] 已加载分析配置: max_analyze={result['max_analyze_per_run']}, batch_size={result['batch_size']}, "
              f"push_levels={result['push_importance_levels']}, max_push={result['max_push_per_run']}")
        
        return result
        
    except Exception as e:
        print(f"[配置错误] 加载分析配置失败: {e}，使用默认配置")
        return default_config
