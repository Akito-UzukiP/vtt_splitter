import os
import shutil
import soundfile as sf
import numpy as np
import librosa

#根据src中的vtt，切割对应的wav，并保存到dst中。dst中，每个wav一个文件夹，同时有一个all.wav文件，包含所有的wav
def parse_milliseconds(timestamp:str):
    """ 将时间戳转换为毫秒
    :param timestamp: 时间戳，格式为hh:mm:ss.sss
    :return: 毫秒, int
    """
    # 将时间戳转换为毫秒
    hours, minutes, seconds = timestamp.split(':')
    seconds, milliseconds = seconds.split('.')
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)
    
    total_milliseconds = hours * 60 * 60 * 1000
    total_milliseconds += minutes * 60 * 1000
    total_milliseconds += seconds * 1000
    total_milliseconds += milliseconds
    
    return total_milliseconds
def parse_vtt(filename:str):
    """ 解析VTT文件
    :param filename: VTT文件名, 绝对路径,str
    :return: 解析后的VTT文件内容, list, 每个元素是一个元组，包含开始时间，结束时间和文本
    """
    with open(filename, 'r', encoding='UTF-8') as file:
        lines = file.readlines()
    
    # 移除文件开头的WEBVTT行和空行
    lines = [line for line in lines if not line.startswith('WEBVTT')]
    
    segments = []
    buffer = []
    for line in lines:
        if line.strip():  # 如果行不为空，则添加到缓冲区
            buffer.append(line.strip())
        else:  # 如果遇到空行，则处理缓冲区中的内容
            if buffer:
                # 假设第一行是时间戳，其余是文本
                timestamp = buffer[1]
                start_time, end_time = timestamp.split(' --> ')
                start_mili = parse_milliseconds(start_time)
                end_mili = parse_milliseconds(end_time)
                text = ' '.join(buffer[2:])
                segments.append((start_mili, end_mili, text))
                buffer = []  # 清空缓冲区以处理下一个块
                
    # 处理可能存在的最后一个段落
    if buffer:
        timestamp = buffer[1]
        start_time, end_time = timestamp.split(' --> ')
        start_mili = parse_milliseconds(start_time)
        end_mili = parse_milliseconds(end_time)
        text = ' '.join(buffer[2:])
        segments.append((start_mili, end_mili, text))
    
    return segments

def split_wav(start_mili:int, end_mili:int,  input_audio):
    """ 切割WAV文件
    :param start_mili: 开始时间, int
    :param end_mili: 结束时间, int
    """
    # 判断mono还是stereo
    if input_audio.ndim == 1:
        output_audio = input_audio[start_mili:end_mili]
    else:
        output_audio = input_audio[:, start_mili:end_mili]
    return output_audio

def save_wav(output_audio, sr, output_filename:str):
    """ 保存WAV文件
    :param output_audio: 输出音频, numpy.ndarray
    :param sr: 采样率, int
    :param output_filename: 输出文件名, str
    """
    sf.write(output_filename, output_audio, sr)

def main(src:str, dst:str):
    wavs = os.listdir(src)
    for wav in wavs:
        # 读取音频
        input_audio, sr = librosa.load(os.path.join(src, wav), sr=None, mono=False)
        # 读取VTT文件
        if os.path.exists(os.path.join(src, wav.replace('.wav', '.vtt'))):
            segments = parse_vtt(os.path.join(src, wav.replace('.wav', '.vtt')))
        elif os.path.exists(os.path.join(src, wav+'.vtt')):
            segments = parse_vtt(os.path.join(src, wav+'.vtt'))
        else:
            print('no vtt file')
            continue
        # 创建输出文件夹
        output_folder = os.path.join(dst, wav.replace('.wav', ''))
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(os.path.join(dst, "all"), exist_ok=True)
        # 切割音频
        for i, segment in enumerate(segments):
            start_mili, end_mili, text = segment
            output_audio = split_wav(start_mili, end_mili, input_audio)
            output_filename = os.path.join(output_folder, f'{i}.wav')
            save_wav(output_audio, sr, output_filename)
            all_output_filename = os.path.join(dst, "all", f'{wav.replace(".wav","_")}{i}.wav')
            save_wav(output_audio, sr, all_output_filename)


if __name__ == "__main__":
    main('src','dst')