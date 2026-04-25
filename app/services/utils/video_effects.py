import random
import subprocess
from typing import List

from moviepy import Clip, ColorClip, CompositeVideoClip, vfx


# FadeIn
def fadein_transition(clip: Clip, t: float) -> Clip:
    return clip.with_effects([vfx.FadeIn(t)])


# FadeOut
def fadeout_transition(clip: Clip, t: float) -> Clip:
    return clip.with_effects([vfx.FadeOut(t)])


# SlideIn
def slidein_transition(clip: Clip, t: float, side: str) -> Clip:
    width, height = clip.size

    # MoviePy 内置 SlideIn 在当前这条处理链里对全屏素材不稳定，
    # 会出现“逻辑上应用了转场，但画面几乎看不出变化”的情况。
    # 这里改成显式黑底 + 位移动画，保证转场效果可见且行为可控。
    def position(current_time: float):
        progress = min(max(current_time / max(t, 0.001), 0), 1)

        if side == "left":
            return (-width + width * progress, 0)
        if side == "right":
            return (width - width * progress, 0)
        if side == "top":
            return (0, -height + height * progress)
        if side == "bottom":
            return (0, height - height * progress)
        return (0, 0)

    background = ColorClip(size=(width, height), color=(0, 0, 0)).with_duration(
        clip.duration
    )
    moving_clip = clip.with_position(position)
    return CompositeVideoClip([background, moving_clip], size=(width, height)).with_duration(
        clip.duration
    )


# SlideOut
def slideout_transition(clip: Clip, t: float, side: str) -> Clip:
    width, height = clip.size
    transition_start = max(clip.duration - t, 0)

    # SlideOut 同样改成显式位移，保证片段末尾能稳定滑出画面。
    def position(current_time: float):
        if current_time <= transition_start:
            return (0, 0)

        progress = min(
            max((current_time - transition_start) / max(t, 0.001), 0), 1
        )

        if side == "left":
            return (-width * progress, 0)
        if side == "right":
            return (width * progress, 0)
        if side == "top":
            return (0, -height * progress)
        if side == "bottom":
            return (0, height * progress)
        return (0, 0)

    background = ColorClip(size=(width, height), color=(0, 0, 0)).with_duration(
        clip.duration
    )
    moving_clip = clip.with_position(position)
    return CompositeVideoClip([background, moving_clip], size=(width, height)).with_duration(
        clip.duration
    )


# ffmpeg xfade effect names
XFADE_EFFECTS = [
    'fade', 'smoothleft', 'smoothright', 'smoothup', 'smoothdown',
    'circlecrop', 'rectcrop', 'circleclose', 'circleopen',
    'horzclose', 'horzopen', 'vertclose', 'vertopen',
    'diagbl', 'diagbr', 'diagtl', 'diagtr',
    'hlslice', 'hrslice', 'vuslice', 'vdslice',
    'dissolve', 'pixelize', 'radial', 'hblur',
    'wipetl', 'wipetr', 'wipebl', 'wipebr', 'zoomin',
    'hlwind', 'hrwind', 'vuwind', 'vdwind',
    'coverleft', 'coverright', 'covertop', 'coverbottom',
    'revealleft', 'revealright', 'revealup', 'revealdown',
]


def combine_clips_with_xfade(
    clip_paths: List[str],
    output_path: str,
    effect: str = "fade",
    duration: float = 1.0,
    ffmpeg_cmd: str = "ffmpeg",
) -> bool:
    """
    使用ffmpeg xfade filter将多个视频片段合并，带过渡效果。

    Args:
        clip_paths: 输入视频文件路径列表
        output_path: 输出视频文件路径
        effect: xfade效果名称 (如 'fade', 'dissolve', 'wipeleft')
        duration: 过渡时长（秒）
        ffmpeg_cmd: ffmpeg可执行文件路径

    Returns:
        True 如果成功，否则 False
    """
    if len(clip_paths) < 2:
        return False

    if effect == "shuffle":
        # 每个连接点随机选择不同的xfade效果
        effects = [random.choice(XFADE_EFFECTS) for _ in range(len(clip_paths) - 1)]
    else:
        effects = [effect] * (len(clip_paths) - 1)

    # 获取每个片段的时长
    clip_durations = []
    for path in clip_paths:
        try:
            result = subprocess.run(
                [ffmpeg_cmd, "-i", path, "-f", "null", "-"],
                capture_output=True, text=True, timeout=30,
            )
            # 从ffmpeg输出中解析时长
            for line in result.stderr.split("\n"):
                if "Duration:" in line:
                    time_str = line.split("Duration:")[1].split(",")[0].strip()
                    parts = time_str.split(":")
                    dur = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                    clip_durations.append(dur)
                    break
            else:
                clip_durations.append(5.0)  # 默认5秒
        except Exception:
            clip_durations.append(5.0)

    # 构建ffmpeg命令
    # 使用逐步合并方式：先合并前两个，再逐个添加
    # 这比构建复杂的filter_complex更可靠

    current_input = clip_paths[0]
    current_duration = clip_durations[0]

    for i in range(1, len(clip_paths)):
        next_input = clip_paths[i]
        next_duration = clip_durations[i] if i < len(clip_durations) else 5.0
        xfade_effect = effects[i - 1]
        offset = max(0, current_duration - duration)

        if i < len(clip_paths) - 1:
            temp_output = output_path.replace(".mp4", f"_xfade_temp_{i}.mp4")
        else:
            temp_output = output_path

        cmd = [
            ffmpeg_cmd, "-y",
            "-i", current_input,
            "-i", next_input,
            "-filter_complex",
            f"[0:v][1:v]xfade=transition={xfade_effect}:duration={duration}:offset={offset}[v]",
            "-map", "[v]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-an",  # 音频后续处理
            temp_output,
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=120, check=True)
        except subprocess.CalledProcessError as e:
            from loguru import logger
            logger.error(f"xfade merge failed at step {i}: {e.stderr[:500] if e.stderr else 'unknown error'}")
            return False

        # 更新当前合并结果的时长
        current_duration = offset + next_duration
        # 清理中间临时文件
        if i > 1:
            import os
            prev_temp = output_path.replace(".mp4", f"_xfade_temp_{i-1}.mp4")
            if os.path.exists(prev_temp):
                os.remove(prev_temp)
        current_input = temp_output

    return True
