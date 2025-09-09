# -*- coding: utf-8 -*-
"""
字幕生成器模块
支持从文案文档生成SRT字幕文件并插入视频
"""

import os
import re
import time
import codecs
import subprocess
from utils import format_duration, safe_filename

class SubtitleGenerator(object):
    """字幕生成器类"""
    
    def __init__(self):
        self.supported_formats = ['.txt', '.docx', '.md', '.srt']
        self.subtitle_styles = {
            'default': {
                'font_size': 24,
                'font_color': 'white',
                'outline_color': 'black',
                'outline_width': 2,
                'position': 'bottom',
                'margin': 20
            },
            'large': {
                'font_size': 32,
                'font_color': 'white',
                'outline_color': 'black',
                'outline_width': 3,
                'position': 'bottom',
                'margin': 30
            },
            'small': {
                'font_size': 18,
                'font_color': 'white',
                'outline_color': 'black',
                'outline_width': 1,
                'position': 'bottom',
                'margin': 15
            }
        }
        
        # 字幕分割模式配置
        self.split_modes = {
            'auto': '自动模式（根据文本长度和标点符号智能分配时间）',
            'one_second': '按秒分割（每条字幕显示1秒）',
            'smart_split': '智能分割（按句子和语义分割，每条1秒）'
        }
    
    def read_text_document(self, doc_path, split_mode='smart_split', start_time=0.0, video_duration=None):
        """
        读取文案文档内容
        
        参数:
        - doc_path: 文档路径
        - split_mode: 分割模式 ('auto', 'one_second', 'smart_split')
        - start_time: 字幕开始时间（秒），默认为0
        - video_duration: 视频总长度（用于智能时间分配）
        """
        if not os.path.exists(doc_path):
            raise ValueError(u"文档文件不存在: {}".format(doc_path))
        
        ext = os.path.splitext(doc_path)[1].lower()
        
        if ext == '.txt':
            return self._read_txt_file(doc_path, split_mode, start_time, video_duration)
        elif ext == '.md':
            return self._read_markdown_file(doc_path, split_mode, start_time, video_duration)
        elif ext == '.docx':
            return self._read_docx_file(doc_path, split_mode, start_time, video_duration)
        elif ext == '.srt':
            return self._read_srt_file(doc_path)
        else:
            raise ValueError(u"不支持的文档格式: {}".format(ext))
    
    def _read_txt_file(self, file_path, split_mode='smart_split', start_time=0.0, video_duration=None):
        """读取TXT文件"""
        content = None
        encodings = ['utf-8', 'utf-16', 'gbk', 'gb2312', 'cp1252']
        
        for encoding in encodings:
            try:
                with codecs.open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if content is None:
            # 最后尝试系统默认编码
            try:
                with open(file_path, 'r') as f:
                    content = f.read().decode('utf-8', errors='ignore')
            except:
                raise ValueError(u"无法读取文件，请检查文件编码: {}".format(file_path))
        
        return self._parse_text_content(content, split_mode, start_time, video_duration)
    
    def _read_markdown_file(self, file_path, split_mode='smart_split', start_time=0.0, video_duration=None):
        """读取Markdown文件"""
        with codecs.open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除Markdown标记
        content = re.sub(r'#+\s*', '', content)  # 标题
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # 粗体
        content = re.sub(r'\*(.*?)\*', r'\1', content)  # 斜体
        content = re.sub(r'`(.*?)`', r'\1', content)  # 代码
        
        return self._parse_text_content(content, split_mode, start_time, video_duration)
    
    def _read_docx_file(self, file_path, split_mode='smart_split', start_time=0.0, video_duration=None):
        """读取DOCX文件（需要python-docx库）"""
        try:
            from docx import Document
            doc = Document(file_path)
            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            return self._parse_text_content(content, split_mode, start_time, video_duration)
        except ImportError:
            raise ValueError(u"读取DOCX文件需要安装python-docx库: pip install python-docx")
    
    def _read_srt_file(self, file_path):
        """读取现有的SRT字幕文件"""
        with codecs.open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析SRT格式
        subtitles = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                try:
                    # 解析时间戳
                    time_line = lines[1]
                    start_time, end_time = time_line.split(' --> ')
                    start_seconds = self._srt_time_to_seconds(start_time)
                    end_seconds = self._srt_time_to_seconds(end_time)
                    
                    # 获取字幕文本
                    text = '\n'.join(lines[2:])
                    
                    subtitles.append({
                        'start': start_seconds,
                        'end': end_seconds,
                        'text': text.strip()
                    })
                except:
                    continue
        
        return subtitles
    
    def _parse_text_content(self, content, split_mode='smart_split', start_time=0.0, video_duration=None):
        """解析文本内容为字幕片段"""
        # 清理文本
        content = content.strip()
        if not content:
            return []
        
        # 按行分割文本
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # 检查是否包含时间戳信息
        timestamped_lines = []
        normal_lines = []
        
        for line in lines:
            # 检查是否有时间戳格式 [00:00] 文本 或 0:00 文本
            time_match = re.match(r'^\[?(\d{1,2}):(\d{2})\]?\s*(.*)', line)
            if time_match:
                minutes = int(time_match.group(1))
                seconds = int(time_match.group(2))
                text = time_match.group(3).strip()
                if text:
                    timestamped_lines.append({
                        'start': minutes * 60 + seconds + start_time,  # 加上开始时间偏移
                        'text': text
                    })
            else:
                normal_lines.append(line)
        
        if timestamped_lines:
            return self._process_timestamped_lines(timestamped_lines)
        else:
            # 根据分割模式选择处理方法
            if split_mode == 'auto':
                return self._process_normal_lines(normal_lines, start_time)
            elif split_mode == 'one_second':
                return self._process_normal_lines_by_seconds(normal_lines, start_time, video_duration)
            elif split_mode == 'smart_split':
                return self._process_normal_lines_by_seconds(normal_lines, start_time, video_duration)
            else:
                return self._process_normal_lines_by_seconds(normal_lines, start_time, video_duration)
    
    def _process_timestamped_lines(self, timestamped_lines):
        """处理带时间戳的文本行"""
        subtitles = []
        
        for i, line in enumerate(timestamped_lines):
            start_time = line['start']
            
            # 确定结束时间
            if i + 1 < len(timestamped_lines):
                end_time = timestamped_lines[i + 1]['start']
            else:
                # 最后一行，默认显示5秒
                end_time = start_time + 5.0
            
            # 确保最小显示时间2秒
            if end_time - start_time < 2.0:
                end_time = start_time + 2.0
            
            subtitles.append({
                'start': start_time,
                'end': end_time,
                'text': line['text']
            })
        
        return subtitles
    
    def _process_normal_lines(self, lines, start_time=0.0):
        """处理普通文本行，自动分配时间"""
        if not lines:
            return []
        
        subtitles = []
        current_time = float(start_time)  # 从指定时间开始
        
        for line in lines:
            # 根据文本长度估算显示时间
            display_duration = max(3.0, len(line) * 0.1)  # 最少3秒，每个字符0.1秒
            display_duration = min(display_duration, 8.0)  # 最多8秒
            
            subtitles.append({
                'start': current_time,
                'end': current_time + display_duration,
                'text': line
            })
            
            current_time += display_duration + 0.5  # 字幕间隔0.5秒
        
        return subtitles
    
    def _process_normal_lines_by_seconds(self, lines, start_time=0.0, video_duration=None):
        """按每秒分割处理普通文本行，支持智能时间分配"""
        if not lines:
            return []
        
        # 将所有行合并为一个连续的文本
        full_text = ' '.join(lines)
        
        # 按标点符号和长度智能分割文本
        sentences = self._split_text_into_sentences(full_text)
        
        if not sentences:
            return []
        
        # 智能时间分配 - 根据文本长度动态调整
        subtitles = []
        current_time = float(start_time)  # 从指定时间开始
        
        if video_duration and video_duration > 0:
            # 计算每个句子的字符数和相对权重
            char_counts = [len(sentence.strip()) for sentence in sentences if sentence.strip()]
            total_chars = sum(char_counts)
            
            if total_chars > 0:
                # 基于正常阅读速度分配时间，不受视频长度限制
                print(u"智能时间分配：{:d}条字幕，总字符数{:d}，使用正常语速".format(
                    len(sentences), total_chars
                ))
                
                sentence_index = 0
                for sentence in sentences:
                    if sentence.strip():
                        char_count = len(sentence.strip())
                        
                        # 基于字符数计算正常阅读时间
                        # 正常阅读速度：每秒约6-8个中文字符
                        base_duration = char_count / 7.0  # 每秒7个字符的阅读速度
                        
                        # 设置合理的时间范围：
                        # - 最少1.5秒（让用户有时间阅读）
                        # - 最多8.0秒（避免显示过久）
                        min_duration = 1.5
                        if char_count <= 5:
                            min_duration = 1.5
                        elif char_count <= 10:
                            min_duration = 2.0
                        elif char_count <= 15:
                            min_duration = 2.5
                        else:
                            min_duration = 3.0
                        
                        subtitle_duration = max(min_duration, min(8.0, base_duration))
                        
                        print(u"  字幕{}: '{:.20s}...' ({:d}字符) -> {:.1f}秒".format(
                            sentence_index + 1, sentence.strip(), char_count, subtitle_duration
                        ))
                        
                        subtitles.append({
                            'start': current_time,
                            'end': current_time + subtitle_duration,
                            'text': sentence.strip()
                        })
                        current_time += subtitle_duration
                        sentence_index += 1
            else:
                # 备用方案：每个句子1.5秒
                for sentence in sentences:
                    if sentence.strip():
                        subtitles.append({
                            'start': current_time,
                            'end': current_time + 1.5,
                            'text': sentence.strip()
                        })
                        current_time += 1.5
        else:
            # 默认根据字符数计算时间
            for sentence in sentences:
                if sentence.strip():
                    char_count = len(sentence.strip())
                    # 每秒7个字符的正常阅读速度
                    subtitle_duration = max(1.5, char_count / 7.0)
                    subtitles.append({
                        'start': current_time,
                        'end': current_time + subtitle_duration,
                        'text': sentence.strip()
                    })
                    current_time += subtitle_duration
        
        return subtitles
    
    def _split_text_into_sentences(self, text):
        """将文本智能分割为句子片段"""
        # 确保文本是字符串
        if isinstance(text, bytes):
            text = text.decode('utf-8')
            
        # 定义标点符号（使用字符编码避免字面值问题）
        # 中文句号、感叹号、问号
        strong_delimiters = [u'\u3002', u'\uff01', u'\uff1f', u'.', u'!', u'?']
        # 中文逗号、顿号、分号等
        weak_delimiters = [u'\uff0c', u'\u3001', u'\uff1b', u',', u';']
        
        sentences = []
        current_sentence = u''
        
        for char in text:
            current_sentence += char
            if char in strong_delimiters:
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                    current_sentence = u''
        
        # 添加剩余的文本
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # 进一步处理过长的句子
        processed_sentences = []
        max_chars_per_second = 20  # 每秒最多显示20个字符
        
        for sentence in sentences:
            if len(sentence) <= max_chars_per_second:
                processed_sentences.append(sentence)
            else:
                # 按逗号、分号等弱分割符再次分割
                weak_delimiters_for_split = [u'\uff0c', u'\u3001', u'\uff1b', u',', u';']
                sub_parts = []
                current_part = u''
                
                for char in sentence:
                    current_part += char
                    if char in weak_delimiters_for_split and len(current_part) >= 10:
                        sub_parts.append(current_part.strip())
                        current_part = u''
                
                if current_part.strip():
                    sub_parts.append(current_part.strip())
                
                # 如果分割后的部分仍然太长，按字符数强制分割
                for part in sub_parts:
                    if len(part) <= max_chars_per_second:
                        processed_sentences.append(part)
                    else:
                        # 按空格分割单词，避免切断单词
                        words = part.split()
                        current_chunk = u''
                        
                        for word in words:
                            if len(current_chunk + u' ' + word) <= max_chars_per_second:
                                if current_chunk:
                                    current_chunk += u' ' + word
                                else:
                                    current_chunk = word
                            else:
                                if current_chunk:
                                    processed_sentences.append(current_chunk)
                                current_chunk = word
                        
                        if current_chunk:
                            processed_sentences.append(current_chunk)
        
        return processed_sentences
    
    def generate_srt_file(self, subtitles, output_path):
        """生成SRT字幕文件"""
        if not subtitles:
            raise ValueError(u"没有字幕内容可生成")
        
        srt_content = []
        
        for i, subtitle in enumerate(subtitles, 1):
            start_time = self._seconds_to_srt_time(subtitle['start'])
            end_time = self._seconds_to_srt_time(subtitle['end'])
            
            srt_content.append(str(i))
            srt_content.append("{} --> {}".format(start_time, end_time))
            srt_content.append(subtitle['text'])
            srt_content.append("")  # 空行分隔
        
        # 写入文件
        with codecs.open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))
        
        return output_path
    
    def _seconds_to_srt_time(self, seconds):
        """将秒数转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return "{:02d}:{:02d}:{:02d},{:03d}".format(hours, minutes, secs, milliseconds)
    
    def _srt_time_to_seconds(self, srt_time):
        """将SRT时间格式转换为秒数"""
        time_part, ms_part = srt_time.split(',')
        hours, minutes, seconds = map(int, time_part.split(':'))
        milliseconds = int(ms_part)
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        return total_seconds
    
    def create_subtitle_filter(self, srt_path, style='default'):
        """创建FFmpeg字幕过滤器"""
        if style not in self.subtitle_styles:
            style = 'default'
        
        style_config = self.subtitle_styles[style]
        
        # 使用简化的字幕过滤器，避免复杂的路径转义
        # 直接使用文件名，确保文件在当前工作目录
        import os
        srt_filename = os.path.basename(srt_path)
        
        # 构建字幕过滤器 - 使用简化版本
        subtitle_filter = "subtitles={}".format(srt_filename)
        
        return subtitle_filter
    
    def _color_to_hex(self, color_name):
        """将颜色名称转换为十六进制"""
        color_map = {
            'white': 'FFFFFF',
            'black': '000000',
            'red': '0000FF',
            'blue': 'FF0000',
            'green': '00FF00',
            'yellow': '00FFFF'
        }
        return color_map.get(color_name.lower(), 'FFFFFF')
    
    def preview_subtitles(self, subtitles, max_lines=10):
        """预览字幕内容"""
        if not subtitles:
            print(u"没有字幕内容")
            return
        
        print(u"=" * 60)
        print(u"字幕预览 (共{}条字幕)".format(len(subtitles)))
        print(u"=" * 60)
        
        for i, subtitle in enumerate(subtitles[:max_lines], 1):
            start_str = format_duration(subtitle['start'])
            end_str = format_duration(subtitle['end'])
            print(u"{}. [{} - {}] {}".format(i, start_str, end_str, subtitle['text']))
        
        if len(subtitles) > max_lines:
            print(u"... 还有{}条字幕".format(len(subtitles) - max_lines))
        
        print(u"=" * 60)
    
    def adjust_subtitle_timing(self, subtitles, video_duration, auto_fit=True):
        """调整字幕时间以适应视频长度"""
        if not subtitles:
            return subtitles
        
        last_subtitle_end = max(sub['end'] for sub in subtitles)
        
        if auto_fit and last_subtitle_end > video_duration:
            # 字幕时间超出视频长度，按比例压缩
            time_scale = video_duration / last_subtitle_end
            
            for subtitle in subtitles:
                subtitle['start'] *= time_scale
                subtitle['end'] *= time_scale
            
            print(u"字幕时间已按比例调整以适应视频长度")
        
        # 过滤掉超出视频时长的字幕
        filtered_subtitles = []
        for subtitle in subtitles:
            if subtitle['start'] < video_duration:
                # 如果字幕结束时间超出视频，截断到视频结束
                if subtitle['end'] > video_duration:
                    subtitle['end'] = video_duration
                filtered_subtitles.append(subtitle)
        
        return filtered_subtitles
    
    def validate_subtitles(self, subtitles):
        """验证字幕格式"""
        errors = []
        
        for i, subtitle in enumerate(subtitles, 1):
            # 检查必需字段
            if 'start' not in subtitle or 'end' not in subtitle or 'text' not in subtitle:
                errors.append(u"字幕 {} 缺少必需字段".format(i))
                continue
            
            # 检查时间有效性
            if subtitle['start'] < 0:
                errors.append(u"字幕 {} 开始时间为负数".format(i))
            
            if subtitle['end'] <= subtitle['start']:
                errors.append(u"字幕 {} 结束时间不能早于或等于开始时间".format(i))
            
            # 检查文本内容
            if not subtitle['text'].strip():
                errors.append(u"字幕 {} 文本内容为空".format(i))
        
        return errors
    
    def split_long_subtitles(self, subtitles, max_chars_per_line=30, max_lines=2):
        """分割过长的字幕"""
        processed_subtitles = []
        
        for subtitle in subtitles:
            text = subtitle['text'].strip()
            
            # 如果文本不长，直接添加
            if len(text) <= max_chars_per_line * max_lines:
                processed_subtitles.append(subtitle)
                continue
            
            # 分割长文本
            words = text.split()
            chunks = []
            current_chunk = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= max_chars_per_line * max_lines:
                    current_chunk.append(word)
                    current_length += len(word) + 1
                else:
                    if current_chunk:
                        chunks.append(' '.join(current_chunk))
                        current_chunk = [word]
                        current_length = len(word)
            
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            
            # 为每个片段创建字幕条目
            duration = subtitle['end'] - subtitle['start']
            chunk_duration = duration / len(chunks)
            
            for i, chunk in enumerate(chunks):
                new_subtitle = {
                    'start': subtitle['start'] + i * chunk_duration,
                    'end': subtitle['start'] + (i + 1) * chunk_duration,
                    'text': chunk
                }
                processed_subtitles.append(new_subtitle)
        
        return processed_subtitles
