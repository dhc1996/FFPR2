# -*- coding: utf-8 -*-
"""
广告插入命令行界面
提供用户友好的广告插入功能
"""

import os
import sys
from config import Config
from ad_inserter import AdInserter
from utils import generate_timestamped_filename

def safe_input(prompt):
    """安全的输入函数，处理Python 2.7的编码问题"""
    try:
        if isinstance(prompt, unicode):
            prompt = prompt.encode('utf-8')
        return raw_input(prompt).decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        try:
            return raw_input(prompt)
        except:
            return ""
    except KeyboardInterrupt:
        raise
    except:
        return ""

class AdInserterCLI(object):
    """广告插入命令行界面"""
    
    def __init__(self):
        self.config = Config()
        self.ad_inserter = AdInserter(self.config)
    
    def print_banner(self):
        """打印程序横幅"""
        print(u"=" * 60)
        print(u"      视频广告插入工具 (Python 2.7.18 + FFmpeg)")
        print(u"=" * 60)
        print(u"功能特性:")
        print(u"  - 在指定时间和位置插入广告视频")
        print(u"  - 支持多种位置选择（四个角落+中心位置）")
        print(u"  - 可自定义广告大小和显示时长")
        print(u"  - 支持插入多个广告")
        print(u"  - 广告置顶显示，不被遮挡")
        print(u"=" * 60)
        print()
    
    def get_main_video_path(self):
        """获取主视频路径"""
        while True:
            path = safe_input(u"请输入主视频文件路径: ").strip().strip('"')
            if path and os.path.exists(path):
                # 验证是否为视频文件
                info = self.ad_inserter.get_video_info(path)
                if info:
                    print(u"✓ 主视频信息: {:.1f}秒, {}x{}".format(
                        info['duration'], info['width'], info['height']
                    ))
                    return path, info
                else:
                    print(u"错误：不是有效的视频文件")
            else:
                print(u"错误：文件不存在，请重新输入")
    
    def get_ad_video_path(self):
        """获取广告视频路径"""
        while True:
            path = safe_input(u"请输入广告视频文件路径: ").strip().strip('"')
            if path and os.path.exists(path):
                is_valid, duration = self.ad_inserter.validate_ad_video(path)
                if is_valid:
                    print(u"✓ 广告视频时长: {:.1f}秒".format(duration))
                    return path, duration
                else:
                    print(u"错误：{}".format(duration))
            else:
                print(u"错误：文件不存在，请重新输入")
    
    def get_ad_timing(self, main_duration, ad_duration):
        """获取广告时间配置"""
        print(u"\n时间配置:")
        
        # 开始时间
        while True:
            try:
                start_input = safe_input(u"广告开始时间（秒，0-{:.1f}）: ".format(main_duration)).strip()
                start_time = float(start_input)
                if 0 <= start_time < main_duration:
                    break
                print(u"开始时间必须在0到{:.1f}秒之间".format(main_duration))
            except ValueError:
                print(u"请输入有效的数字")
        
        # 显示时长
        max_duration = min(ad_duration, main_duration - start_time)
        while True:
            try:
                duration_input = safe_input(u"广告显示时长（秒，建议{:.1f}，最大{:.1f}）: ".format(
                    min(5.0, max_duration), max_duration
                )).strip()
                if not duration_input:
                    duration = min(5.0, max_duration)  # 默认5秒
                    break
                duration = float(duration_input)
                if 0 < duration <= max_duration:
                    break
                print(u"显示时长必须在0到{:.1f}秒之间".format(max_duration))
            except ValueError:
                print(u"请输入有效的数字")
        
        return start_time, duration
    
    def get_ad_position(self):
        """获取广告位置"""
        print(u"\n位置选择:")
        print(u"1. 右上角 (推荐)")
        print(u"2. 左上角")
        print(u"3. 右下角")
        print(u"4. 左下角")
        print(u"5. 中心位置")
        
        positions = {
            1: 'top-right',
            2: 'top-left', 
            3: 'bottom-right',
            4: 'bottom-left',
            5: 'center'
        }
        
        while True:
            try:
                choice = int(safe_input(u"请选择位置 (1-5，默认1): ").strip() or "1")
                if choice in positions:
                    position = positions[choice]
                    position_names = {
                        'top-right': u'右上角',
                        'top-left': u'左上角',
                        'bottom-right': u'右下角', 
                        'bottom-left': u'左下角',
                        'center': u'中心位置'
                    }
                    print(u"✓ 选择位置: {}".format(position_names[position]))
                    return position
                print(u"请输入1-5之间的数字")
            except ValueError:
                print(u"请输入有效的数字")
    
    def get_ad_scale(self):
        """获取广告缩放比例"""
        print(u"\n大小设置:")
        print(u"1. 小 (15%)")
        print(u"2. 中等 (25%) - 推荐")
        print(u"3. 大 (35%)")
        print(u"4. 自定义")
        
        scales = {1: 0.15, 2: 0.25, 3: 0.35}
        
        while True:
            try:
                choice = int(safe_input(u"请选择大小 (1-4，默认2): ").strip() or "2")
                if choice in scales:
                    scale = scales[choice]
                    print(u"✓ 广告大小: {:.0%}".format(scale))
                    return scale
                elif choice == 4:
                    # 自定义
                    while True:
                        try:
                            custom_input = safe_input(u"请输入缩放比例（10-50%，如: 20): ").strip()
                            custom_scale = float(custom_input) / 100.0
                            if 0.1 <= custom_scale <= 0.5:
                                print(u"✓ 自定义大小: {:.0%}".format(custom_scale))
                                return custom_scale
                            print(u"缩放比例必须在10%-50%之间")
                        except ValueError:
                            print(u"请输入有效的数字")
                print(u"请输入1-4之间的数字")
            except ValueError:
                print(u"请输入有效的数字")
    
    def get_output_path(self, main_video_path):
        """获取输出路径"""
        # 生成默认文件名（使用主视频文件夹名和时间戳）
        default_name = generate_timestamped_filename(main_video_path, "ad", "_with_ad")
        output_dir = self.config.get('video', 'default_output_dir') or 'output'
        
        output_name = safe_input(u"输出文件名（默认：{}）: ".format(default_name)).strip()
        if not output_name:
            output_name = default_name
        
        # 确保输出文件名有扩展名
        if not output_name.lower().endswith('.mp4'):
            output_name += '.mp4'
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_path = os.path.join(output_dir, output_name)
        return output_path
    
    def show_configuration(self, config):
        """显示配置信息"""
        print(u"\n" + u"=" * 50)
        print(u"广告插入配置")
        print(u"=" * 50)
        print(u"主视频: {}".format(os.path.basename(config['main_video'])))
        print(u"广告视频: {}".format(os.path.basename(config['ad_video'])))
        print(u"开始时间: {:.1f}秒".format(config['start_time']))
        print(u"显示时长: {:.1f}秒".format(config['duration']))
        print(u"显示位置: {}".format({
            'top-right': u'右上角',
            'top-left': u'左上角',
            'bottom-right': u'右下角',
            'bottom-left': u'左下角',
            'center': u'中心位置'
        }[config['position']]))
        print(u"广告大小: {:.0%}".format(config['scale']))
        print(u"输出文件: {}".format(config['output_path']))
        print(u"=" * 50)
        
        confirm = safe_input(u"\n确认开始处理？(Y/n): ").strip().lower()
        return confirm != 'n'
    
    def single_ad_mode(self):
        """单个广告插入模式"""
        print(u"=== 单个广告插入模式 ===")
        
        # 获取主视频
        main_video_path, main_info = self.get_main_video_path()
        
        # 获取广告视频
        ad_video_path, ad_duration = self.get_ad_video_path()
        
        # 获取时间配置
        start_time, duration = self.get_ad_timing(main_info['duration'], ad_duration)
        
        # 获取位置配置
        position = self.get_ad_position()
        
        # 获取大小配置
        scale = self.get_ad_scale()
        
        # 获取输出路径
        output_path = self.get_output_path(main_video_path)
        
        # 配置汇总
        config = {
            'main_video': main_video_path,
            'ad_video': ad_video_path,
            'start_time': start_time,
            'duration': duration,
            'position': position,
            'scale': scale,
            'output_path': output_path
        }
        
        # 显示配置并确认
        if not self.show_configuration(config):
            print(u"操作已取消")
            return
        
        # 执行广告插入
        success, result = self.ad_inserter.insert_ad_overlay(
            main_video_path, ad_video_path, output_path,
            start_time, duration, position, scale
        )
        
        if success:
            print(u"\n" + u"=" * 50)
            print(u"广告插入完成！")
            print(u"=" * 50)
            print(u"输出文件: {}".format(output_path))
            
            # 显示文件信息
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                print(u"文件大小: {:.2f} MB".format(file_size))
        else:
            print(u"\n广告插入失败:")
            print(result)
    
    def multiple_ads_mode(self):
        """多个广告插入模式"""
        print(u"=== 多个广告插入模式 ===")
        print(u"注意：多个广告会同时显示，请合理安排时间和位置避免重叠")
        
        # 获取主视频
        main_video_path, main_info = self.get_main_video_path()
        
        # 广告配置列表
        ad_configs = []
        
        while True:
            print(u"\n--- 添加广告 {} ---".format(len(ad_configs) + 1))
            
            # 获取广告视频
            ad_video_path, ad_duration = self.get_ad_video_path()
            
            # 获取时间配置
            start_time, duration = self.get_ad_timing(main_info['duration'], ad_duration)
            
            # 获取位置配置
            position = self.get_ad_position()
            
            # 获取大小配置
            scale = self.get_ad_scale()
            
            ad_configs.append({
                'path': ad_video_path,
                'start': start_time,
                'duration': duration,
                'position': position,
                'scale': scale
            })
            
            print(u"✓ 广告 {} 配置完成".format(len(ad_configs)))
            
            # 询问是否继续添加
            more = safe_input(u"是否添加更多广告？(Y/n): ").strip().lower()
            if more not in ['', 'y', 'yes']:
                break
        
        # 获取输出路径
        output_path = self.get_output_path(main_video_path)
        
        # 显示所有配置
        print(u"\n" + u"=" * 50)
        print(u"多广告插入配置")
        print(u"=" * 50)
        print(u"主视频: {}".format(os.path.basename(main_video_path)))
        print(u"广告数量: {}".format(len(ad_configs)))
        
        for i, config in enumerate(ad_configs, 1):
            print(u"广告 {}: {} ({:.1f}s-{:.1f}s)".format(
                i, os.path.basename(config['path']), 
                config['start'], config['start'] + config['duration']
            ))
        
        print(u"输出文件: {}".format(output_path))
        print(u"=" * 50)
        
        confirm = safe_input(u"\n确认开始处理？(Y/n): ").strip().lower()
        if confirm == 'n':
            print(u"操作已取消")
            return
        
        # 执行多广告插入
        success, result = self.ad_inserter.insert_multiple_ads(
            main_video_path, ad_configs, output_path
        )
        
        if success:
            print(u"\n" + u"=" * 50)
            print(u"多广告插入完成！")
            print(u"=" * 50)
            print(u"输出文件: {}".format(output_path))
        else:
            print(u"\n多广告插入失败:")
            print(result)
    
    def run(self):
        """运行主程序"""
        self.print_banner()
        
        # 检查FFmpeg
        try:
            import subprocess
            subprocess.check_output(['ffmpeg', '-version'], stderr=subprocess.STDOUT)
        except:
            print(u"错误：未找到FFmpeg，请确保已安装并添加到PATH环境变量")
            return
        
        try:
            print(u"请选择模式:")
            print(u"1. 插入单个广告")
            print(u"2. 插入多个广告")
            
            while True:
                try:
                    choice = int(safe_input(u"请选择 (1-2): ").strip())
                    if choice == 1:
                        self.single_ad_mode()
                        break
                    elif choice == 2:
                        self.multiple_ads_mode()
                        break
                    else:
                        print(u"请输入1或2")
                except ValueError:
                    print(u"请输入有效的数字")
        
        except KeyboardInterrupt:
            print(u"\n\n用户中断操作")
        except Exception as e:
            print(u"\n程序执行出错: {}".format(str(e)))
            import traceback
            traceback.print_exc()


def main():
    """主入口函数"""
    cli = AdInserterCLI()
    cli.run()


if __name__ == "__main__":
    main()
