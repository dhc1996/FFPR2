# -*- coding: utf-8 -*-
"""
配置文件模块
用于管理视频剪辑的各种参数配置
"""

import os
import json

class Config(object):
    """配置管理类"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "video": {
                "supported_formats": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
                "default_output_width": 1920,
                "default_output_height": 1080,
                "default_fps": 30,
                "default_crf": 23,
                "default_preset": "medium"
            },
            "audio": {
                "remove_audio": True,
                "audio_codec": "aac",
                "audio_bitrate": "128k"
            },
            "processing": {
                "min_segment_duration": 1.0,
                "max_segments_per_video": 10,
                "random_seed": None,
                "temp_folder": "temp"
            },
            "ffmpeg": {
                "path": "ffmpeg",
                "ffprobe_path": "ffprobe",
                "log_level": "error"
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # 合并默认配置和用户配置
                merged_config = self.default_config.copy()
                self._merge_dict(merged_config, config)
                return merged_config
            except Exception as e:
                print(u"加载配置文件失败，使用默认配置: {}".format(str(e)))
        
        return self.default_config
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(u"配置已保存到: {}".format(self.config_file))
        except Exception as e:
            print(u"保存配置文件失败: {}".format(str(e)))
    
    def _merge_dict(self, base, update):
        """递归合并字典"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dict(base[key], value)
            else:
                base[key] = value
    
    def get(self, *keys):
        """获取配置值"""
        result = self.config
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return None
        return result
    
    def set(self, value, *keys):
        """设置配置值"""
        if not keys:
            return False
        
        current = self.config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return True
    
    def reset_to_default(self):
        """重置为默认配置"""
        self.config = self.default_config.copy()
        self.save_config()


def create_default_config():
    """创建默认配置文件"""
    config = Config()
    config.save_config()
    return config
