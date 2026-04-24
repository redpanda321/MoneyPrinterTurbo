import asyncio
import os
import re
from datetime import datetime
from typing import Union
from xml.sax.saxutils import unescape

import edge_tts
import requests
from edge_tts import SubMaker, submaker
from edge_tts.submaker import mktimestamp
from loguru import logger
from moviepy.video.tools import subtitles
from moviepy.audio.io.AudioFileClip import AudioFileClip

from app.config import config
from app.utils import utils


def get_siliconflow_voices() -> list[str]:
    """
    获取硅基流动的声音列表

    Returns:
        声音列表，格式为 ["siliconflow:FunAudioLLM/CosyVoice2-0.5B:alex", ...]
    """
    # 硅基流动的声音列表和对应的性别（用于显示）
    voices_with_gender = [
        ("FunAudioLLM/CosyVoice2-0.5B", "alex", "Male"),
        ("FunAudioLLM/CosyVoice2-0.5B", "anna", "Female"),
        ("FunAudioLLM/CosyVoice2-0.5B", "bella", "Female"),
        ("FunAudioLLM/CosyVoice2-0.5B", "benjamin", "Male"),
        ("FunAudioLLM/CosyVoice2-0.5B", "charles", "Male"),
        ("FunAudioLLM/CosyVoice2-0.5B", "claire", "Female"),
        ("FunAudioLLM/CosyVoice2-0.5B", "david", "Male"),
        ("FunAudioLLM/CosyVoice2-0.5B", "diana", "Female"),
    ]

    # 添加siliconflow:前缀，并格式化为显示名称
    return [
        f"siliconflow:{model}:{voice}-{gender}"
        for model, voice, gender in voices_with_gender
    ]


def get_gemini_voices() -> list[str]:
    """
    获取Gemini TTS的声音列表
    
    Returns:
        声音列表，格式为 ["gemini:Zephyr-Female", "gemini:Puck-Male", ...]
    """
    # Gemini TTS支持的语音列表
    voices_with_gender = [
        ("Zephyr", "Female"),
        ("Puck", "Male"), 
        ("Charon", "Male"),
        ("Kore", "Female"),
        ("Fenrir", "Male"),
        ("Aoede", "Female"),
        ("Thalia", "Female"),
        ("Sage", "Male"),
        ("Echo", "Female"),
        ("Harmony", "Female"),
        ("Lux", "Female"),
        ("Nova", "Female"),
        ("Vale", "Male"),
        ("Orion", "Male"),
        ("Atlas", "Male"),
    ]
    
    # 添加gemini:前缀，并格式化为显示名称
    return [
        f"gemini:{voice}-{gender}"
        for voice, gender in voices_with_gender
    ]


def get_all_azure_voices(filter_locals=None) -> list[str]:
    azure_voices_str = """
Name: af-ZA-AdriNeural
Gender: Female

Name: af-ZA-WillemNeural
Gender: Male

Name: am-ET-AmehaNeural
Gender: Male

Name: am-ET-MekdesNeural
Gender: Female

Name: ar-AE-FatimaNeural
Gender: Female

Name: ar-AE-HamdanNeural
Gender: Male

Name: ar-BH-AliNeural
Gender: Male

Name: ar-BH-LailaNeural
Gender: Female

Name: ar-DZ-AminaNeural
Gender: Female

Name: ar-DZ-IsmaelNeural
Gender: Male

Name: ar-EG-SalmaNeural
Gender: Female

Name: ar-EG-ShakirNeural
Gender: Male

Name: ar-IQ-BasselNeural
Gender: Male

Name: ar-IQ-RanaNeural
Gender: Female

Name: ar-JO-SanaNeural
Gender: Female

Name: ar-JO-TaimNeural
Gender: Male

Name: ar-KW-FahedNeural
Gender: Male

Name: ar-KW-NouraNeural
Gender: Female

Name: ar-LB-LaylaNeural
Gender: Female

Name: ar-LB-RamiNeural
Gender: Male

Name: ar-LY-ImanNeural
Gender: Female

Name: ar-LY-OmarNeural
Gender: Male

Name: ar-MA-JamalNeural
Gender: Male

Name: ar-MA-MounaNeural
Gender: Female

Name: ar-OM-AbdullahNeural
Gender: Male

Name: ar-OM-AyshaNeural
Gender: Female

Name: ar-QA-AmalNeural
Gender: Female

Name: ar-QA-MoazNeural
Gender: Male

Name: ar-SA-HamedNeural
Gender: Male

Name: ar-SA-ZariyahNeural
Gender: Female

Name: ar-SY-AmanyNeural
Gender: Female

Name: ar-SY-LaithNeural
Gender: Male

Name: ar-TN-HediNeural
Gender: Male

Name: ar-TN-ReemNeural
Gender: Female

Name: ar-YE-MaryamNeural
Gender: Female

Name: ar-YE-SalehNeural
Gender: Male

Name: az-AZ-BabekNeural
Gender: Male

Name: az-AZ-BanuNeural
Gender: Female

Name: bg-BG-BorislavNeural
Gender: Male

Name: bg-BG-KalinaNeural
Gender: Female

Name: bn-BD-NabanitaNeural
Gender: Female

Name: bn-BD-PradeepNeural
Gender: Male

Name: bn-IN-BashkarNeural
Gender: Male

Name: bn-IN-TanishaaNeural
Gender: Female

Name: bs-BA-GoranNeural
Gender: Male

Name: bs-BA-VesnaNeural
Gender: Female

Name: ca-ES-EnricNeural
Gender: Male

Name: ca-ES-JoanaNeural
Gender: Female

Name: cs-CZ-AntoninNeural
Gender: Male

Name: cs-CZ-VlastaNeural
Gender: Female

Name: cy-GB-AledNeural
Gender: Male

Name: cy-GB-NiaNeural
Gender: Female

Name: da-DK-ChristelNeural
Gender: Female

Name: da-DK-JeppeNeural
Gender: Male

Name: de-AT-IngridNeural
Gender: Female

Name: de-AT-JonasNeural
Gender: Male

Name: de-CH-JanNeural
Gender: Male

Name: de-CH-LeniNeural
Gender: Female

Name: de-DE-AmalaNeural
Gender: Female

Name: de-DE-ConradNeural
Gender: Male

Name: de-DE-FlorianMultilingualNeural
Gender: Male

Name: de-DE-KatjaNeural
Gender: Female

Name: de-DE-KillianNeural
Gender: Male

Name: de-DE-SeraphinaMultilingualNeural
Gender: Female

Name: el-GR-AthinaNeural
Gender: Female

Name: el-GR-NestorasNeural
Gender: Male

Name: en-AU-NatashaNeural
Gender: Female

Name: en-AU-WilliamNeural
Gender: Male

Name: en-CA-ClaraNeural
Gender: Female

Name: en-CA-LiamNeural
Gender: Male

Name: en-GB-LibbyNeural
Gender: Female

Name: en-GB-MaisieNeural
Gender: Female

Name: en-GB-RyanNeural
Gender: Male

Name: en-GB-SoniaNeural
Gender: Female

Name: en-GB-ThomasNeural
Gender: Male

Name: en-HK-SamNeural
Gender: Male

Name: en-HK-YanNeural
Gender: Female

Name: en-IE-ConnorNeural
Gender: Male

Name: en-IE-EmilyNeural
Gender: Female

Name: en-IN-NeerjaExpressiveNeural
Gender: Female

Name: en-IN-NeerjaNeural
Gender: Female

Name: en-IN-PrabhatNeural
Gender: Male

Name: en-KE-AsiliaNeural
Gender: Female

Name: en-KE-ChilembaNeural
Gender: Male

Name: en-NG-AbeoNeural
Gender: Male

Name: en-NG-EzinneNeural
Gender: Female

Name: en-NZ-MitchellNeural
Gender: Male

Name: en-NZ-MollyNeural
Gender: Female

Name: en-PH-JamesNeural
Gender: Male

Name: en-PH-RosaNeural
Gender: Female

Name: en-SG-LunaNeural
Gender: Female

Name: en-SG-WayneNeural
Gender: Male

Name: en-TZ-ElimuNeural
Gender: Male

Name: en-TZ-ImaniNeural
Gender: Female

Name: en-US-AnaNeural
Gender: Female

Name: en-US-AndrewMultilingualNeural
Gender: Male

Name: en-US-AndrewNeural
Gender: Male

Name: en-US-AriaNeural
Gender: Female

Name: en-US-AvaMultilingualNeural
Gender: Female

Name: en-US-AvaNeural
Gender: Female

Name: en-US-BrianMultilingualNeural
Gender: Male

Name: en-US-BrianNeural
Gender: Male

Name: en-US-ChristopherNeural
Gender: Male

Name: en-US-EmmaMultilingualNeural
Gender: Female

Name: en-US-EmmaNeural
Gender: Female

Name: en-US-EricNeural
Gender: Male

Name: en-US-GuyNeural
Gender: Male

Name: en-US-JennyNeural
Gender: Female

Name: en-US-MichelleNeural
Gender: Female

Name: en-US-RogerNeural
Gender: Male

Name: en-US-SteffanNeural
Gender: Male

Name: en-ZA-LeahNeural
Gender: Female

Name: en-ZA-LukeNeural
Gender: Male

Name: es-AR-ElenaNeural
Gender: Female

Name: es-AR-TomasNeural
Gender: Male

Name: es-BO-MarceloNeural
Gender: Male

Name: es-BO-SofiaNeural
Gender: Female

Name: es-CL-CatalinaNeural
Gender: Female

Name: es-CL-LorenzoNeural
Gender: Male

Name: es-CO-GonzaloNeural
Gender: Male

Name: es-CO-SalomeNeural
Gender: Female

Name: es-CR-JuanNeural
Gender: Male

Name: es-CR-MariaNeural
Gender: Female

Name: es-CU-BelkysNeural
Gender: Female

Name: es-CU-ManuelNeural
Gender: Male

Name: es-DO-EmilioNeural
Gender: Male

Name: es-DO-RamonaNeural
Gender: Female

Name: es-EC-AndreaNeural
Gender: Female

Name: es-EC-LuisNeural
Gender: Male

Name: es-ES-AlvaroNeural
Gender: Male

Name: es-ES-ElviraNeural
Gender: Female

Name: es-ES-XimenaNeural
Gender: Female

Name: es-GQ-JavierNeural
Gender: Male

Name: es-GQ-TeresaNeural
Gender: Female

Name: es-GT-AndresNeural
Gender: Male

Name: es-GT-MartaNeural
Gender: Female

Name: es-HN-CarlosNeural
Gender: Male

Name: es-HN-KarlaNeural
Gender: Female

Name: es-MX-DaliaNeural
Gender: Female

Name: es-MX-JorgeNeural
Gender: Male

Name: es-NI-FedericoNeural
Gender: Male

Name: es-NI-YolandaNeural
Gender: Female

Name: es-PA-MargaritaNeural
Gender: Female

Name: es-PA-RobertoNeural
Gender: Male

Name: es-PE-AlexNeural
Gender: Male

Name: es-PE-CamilaNeural
Gender: Female

Name: es-PR-KarinaNeural
Gender: Female

Name: es-PR-VictorNeural
Gender: Male

Name: es-PY-MarioNeural
Gender: Male

Name: es-PY-TaniaNeural
Gender: Female

Name: es-SV-LorenaNeural
Gender: Female

Name: es-SV-RodrigoNeural
Gender: Male

Name: es-US-AlonsoNeural
Gender: Male

Name: es-US-PalomaNeural
Gender: Female

Name: es-UY-MateoNeural
Gender: Male

Name: es-UY-ValentinaNeural
Gender: Female

Name: es-VE-PaolaNeural
Gender: Female

Name: es-VE-SebastianNeural
Gender: Male

Name: et-EE-AnuNeural
Gender: Female

Name: et-EE-KertNeural
Gender: Male

Name: fa-IR-DilaraNeural
Gender: Female

Name: fa-IR-FaridNeural
Gender: Male

Name: fi-FI-HarriNeural
Gender: Male

Name: fi-FI-NooraNeural
Gender: Female

Name: fil-PH-AngeloNeural
Gender: Male

Name: fil-PH-BlessicaNeural
Gender: Female

Name: fr-BE-CharlineNeural
Gender: Female

Name: fr-BE-GerardNeural
Gender: Male

Name: fr-CA-AntoineNeural
Gender: Male

Name: fr-CA-JeanNeural
Gender: Male

Name: fr-CA-SylvieNeural
Gender: Female

Name: fr-CA-ThierryNeural
Gender: Male

Name: fr-CH-ArianeNeural
Gender: Female

Name: fr-CH-FabriceNeural
Gender: Male

Name: fr-FR-DeniseNeural
Gender: Female

Name: fr-FR-EloiseNeural
Gender: Female

Name: fr-FR-HenriNeural
Gender: Male

Name: fr-FR-RemyMultilingualNeural
Gender: Male

Name: fr-FR-VivienneMultilingualNeural
Gender: Female

Name: ga-IE-ColmNeural
Gender: Male

Name: ga-IE-OrlaNeural
Gender: Female

Name: gl-ES-RoiNeural
Gender: Male

Name: gl-ES-SabelaNeural
Gender: Female

Name: gu-IN-DhwaniNeural
Gender: Female

Name: gu-IN-NiranjanNeural
Gender: Male

Name: he-IL-AvriNeural
Gender: Male

Name: he-IL-HilaNeural
Gender: Female

Name: hi-IN-MadhurNeural
Gender: Male

Name: hi-IN-SwaraNeural
Gender: Female

Name: hr-HR-GabrijelaNeural
Gender: Female

Name: hr-HR-SreckoNeural
Gender: Male

Name: hu-HU-NoemiNeural
Gender: Female

Name: hu-HU-TamasNeural
Gender: Male

Name: id-ID-ArdiNeural
Gender: Male

Name: id-ID-GadisNeural
Gender: Female

Name: is-IS-GudrunNeural
Gender: Female

Name: is-IS-GunnarNeural
Gender: Male

Name: it-IT-DiegoNeural
Gender: Male

Name: it-IT-ElsaNeural
Gender: Female

Name: it-IT-GiuseppeMultilingualNeural
Gender: Male

Name: it-IT-IsabellaNeural
Gender: Female

Name: iu-Cans-CA-SiqiniqNeural
Gender: Female

Name: iu-Cans-CA-TaqqiqNeural
Gender: Male

Name: iu-Latn-CA-SiqiniqNeural
Gender: Female

Name: iu-Latn-CA-TaqqiqNeural
Gender: Male

Name: ja-JP-KeitaNeural
Gender: Male

Name: ja-JP-NanamiNeural
Gender: Female

Name: jv-ID-DimasNeural
Gender: Male

Name: jv-ID-SitiNeural
Gender: Female

Name: ka-GE-EkaNeural
Gender: Female

Name: ka-GE-GiorgiNeural
Gender: Male

Name: kk-KZ-AigulNeural
Gender: Female

Name: kk-KZ-DauletNeural
Gender: Male

Name: km-KH-PisethNeural
Gender: Male

Name: km-KH-SreymomNeural
Gender: Female

Name: kn-IN-GaganNeural
Gender: Male

Name: kn-IN-SapnaNeural
Gender: Female

Name: ko-KR-HyunsuMultilingualNeural
Gender: Male

Name: ko-KR-InJoonNeural
Gender: Male

Name: ko-KR-SunHiNeural
Gender: Female

Name: lo-LA-ChanthavongNeural
Gender: Male

Name: lo-LA-KeomanyNeural
Gender: Female

Name: lt-LT-LeonasNeural
Gender: Male

Name: lt-LT-OnaNeural
Gender: Female

Name: lv-LV-EveritaNeural
Gender: Female

Name: lv-LV-NilsNeural
Gender: Male

Name: mk-MK-AleksandarNeural
Gender: Male

Name: mk-MK-MarijaNeural
Gender: Female

Name: ml-IN-MidhunNeural
Gender: Male

Name: ml-IN-SobhanaNeural
Gender: Female

Name: mn-MN-BataaNeural
Gender: Male

Name: mn-MN-YesuiNeural
Gender: Female

Name: mr-IN-AarohiNeural
Gender: Female

Name: mr-IN-ManoharNeural
Gender: Male

Name: ms-MY-OsmanNeural
Gender: Male

Name: ms-MY-YasminNeural
Gender: Female

Name: mt-MT-GraceNeural
Gender: Female

Name: mt-MT-JosephNeural
Gender: Male

Name: my-MM-NilarNeural
Gender: Female

Name: my-MM-ThihaNeural
Gender: Male

Name: nb-NO-FinnNeural
Gender: Male

Name: nb-NO-PernilleNeural
Gender: Female

Name: ne-NP-HemkalaNeural
Gender: Female

Name: ne-NP-SagarNeural
Gender: Male

Name: nl-BE-ArnaudNeural
Gender: Male

Name: nl-BE-DenaNeural
Gender: Female

Name: nl-NL-ColetteNeural
Gender: Female

Name: nl-NL-FennaNeural
Gender: Female

Name: nl-NL-MaartenNeural
Gender: Male

Name: pl-PL-MarekNeural
Gender: Male

Name: pl-PL-ZofiaNeural
Gender: Female

Name: ps-AF-GulNawazNeural
Gender: Male

Name: ps-AF-LatifaNeural
Gender: Female

Name: pt-BR-AntonioNeural
Gender: Male

Name: pt-BR-FranciscaNeural
Gender: Female

Name: pt-BR-ThalitaMultilingualNeural
Gender: Female

Name: pt-PT-DuarteNeural
Gender: Male

Name: pt-PT-RaquelNeural
Gender: Female

Name: ro-RO-AlinaNeural
Gender: Female

Name: ro-RO-EmilNeural
Gender: Male

Name: ru-RU-DmitryNeural
Gender: Male

Name: ru-RU-SvetlanaNeural
Gender: Female

Name: si-LK-SameeraNeural
Gender: Male

Name: si-LK-ThiliniNeural
Gender: Female

Name: sk-SK-LukasNeural
Gender: Male

Name: sk-SK-ViktoriaNeural
Gender: Female

Name: sl-SI-PetraNeural
Gender: Female

Name: sl-SI-RokNeural
Gender: Male

Name: so-SO-MuuseNeural
Gender: Male

Name: so-SO-UbaxNeural
Gender: Female

Name: sq-AL-AnilaNeural
Gender: Female

Name: sq-AL-IlirNeural
Gender: Male

Name: sr-RS-NicholasNeural
Gender: Male

Name: sr-RS-SophieNeural
Gender: Female

Name: su-ID-JajangNeural
Gender: Male

Name: su-ID-TutiNeural
Gender: Female

Name: sv-SE-MattiasNeural
Gender: Male

Name: sv-SE-SofieNeural
Gender: Female

Name: sw-KE-RafikiNeural
Gender: Male

Name: sw-KE-ZuriNeural
Gender: Female

Name: sw-TZ-DaudiNeural
Gender: Male

Name: sw-TZ-RehemaNeural
Gender: Female

Name: ta-IN-PallaviNeural
Gender: Female

Name: ta-IN-ValluvarNeural
Gender: Male

Name: ta-LK-KumarNeural
Gender: Male

Name: ta-LK-SaranyaNeural
Gender: Female

Name: ta-MY-KaniNeural
Gender: Female

Name: ta-MY-SuryaNeural
Gender: Male

Name: ta-SG-AnbuNeural
Gender: Male

Name: ta-SG-VenbaNeural
Gender: Female

Name: te-IN-MohanNeural
Gender: Male

Name: te-IN-ShrutiNeural
Gender: Female

Name: th-TH-NiwatNeural
Gender: Male

Name: th-TH-PremwadeeNeural
Gender: Female

Name: tr-TR-AhmetNeural
Gender: Male

Name: tr-TR-EmelNeural
Gender: Female

Name: uk-UA-OstapNeural
Gender: Male

Name: uk-UA-PolinaNeural
Gender: Female

Name: ur-IN-GulNeural
Gender: Female

Name: ur-IN-SalmanNeural
Gender: Male

Name: ur-PK-AsadNeural
Gender: Male

Name: ur-PK-UzmaNeural
Gender: Female

Name: uz-UZ-MadinaNeural
Gender: Female

Name: uz-UZ-SardorNeural
Gender: Male

Name: vi-VN-HoaiMyNeural
Gender: Female

Name: vi-VN-NamMinhNeural
Gender: Male

Name: zh-CN-XiaoxiaoNeural
Gender: Female

Name: zh-CN-XiaoyiNeural
Gender: Female

Name: zh-CN-YunjianNeural
Gender: Male

Name: zh-CN-YunxiNeural
Gender: Male

Name: zh-CN-YunxiaNeural
Gender: Male

Name: zh-CN-YunyangNeural
Gender: Male

Name: zh-CN-liaoning-XiaobeiNeural
Gender: Female

Name: zh-CN-shaanxi-XiaoniNeural
Gender: Female

Name: zh-HK-HiuGaaiNeural
Gender: Female

Name: zh-HK-HiuMaanNeural
Gender: Female

Name: zh-HK-WanLungNeural
Gender: Male

Name: zh-TW-HsiaoChenNeural
Gender: Female

Name: zh-TW-HsiaoYuNeural
Gender: Female

Name: zh-TW-YunJheNeural
Gender: Male

Name: zu-ZA-ThandoNeural
Gender: Female

Name: zu-ZA-ThembaNeural
Gender: Male


Name: en-US-AvaMultilingualNeural-V2
Gender: Female

Name: en-US-AndrewMultilingualNeural-V2
Gender: Male

Name: en-US-EmmaMultilingualNeural-V2
Gender: Female

Name: en-US-BrianMultilingualNeural-V2
Gender: Male

Name: de-DE-FlorianMultilingualNeural-V2
Gender: Male

Name: de-DE-SeraphinaMultilingualNeural-V2
Gender: Female

Name: fr-FR-RemyMultilingualNeural-V2
Gender: Male

Name: fr-FR-VivienneMultilingualNeural-V2
Gender: Female

Name: zh-CN-XiaoxiaoMultilingualNeural-V2
Gender: Female
    """.strip()
    voices = []
    # 定义正则表达式模式，用于匹配 Name 和 Gender 行
    pattern = re.compile(r"Name:\s*(.+)\s*Gender:\s*(.+)\s*", re.MULTILINE)
    # 使用正则表达式查找所有匹配项
    matches = pattern.findall(azure_voices_str)

    for name, gender in matches:
        # 应用过滤条件
        if filter_locals and any(
            name.lower().startswith(fl.lower()) for fl in filter_locals
        ):
            voices.append(f"{name}-{gender}")
        elif not filter_locals:
            voices.append(f"{name}-{gender}")

    voices.sort()
    return voices


def parse_voice_name(name: str):
    # zh-CN-XiaoyiNeural-Female
    # zh-CN-YunxiNeural-Male
    # zh-CN-XiaoxiaoMultilingualNeural-V2-Female
    name = name.replace("-Female", "").replace("-Male", "").strip()
    return name


def is_azure_v2_voice(voice_name: str):
    voice_name = parse_voice_name(voice_name)
    if voice_name.endswith("-V2"):
        return voice_name.replace("-V2", "").strip()
    return ""


def get_tiktok_voices() -> list[str]:
    """
    获取TikTok TTS的声音列表

    Returns:
        声音列表，格式为 ["tiktok:en_us_001-English US Female 1", ...]
    """
    voices = {
        # Disney / Character
        "en_us_ghostface": "Ghost Face",
        "en_us_chewbacca": "Chewbacca",
        "en_us_c3po": "C3PO",
        "en_us_stitch": "Stitch",
        "en_us_stormtrooper": "Stormtrooper",
        "en_us_rocket": "Rocket",
        # English
        "en_au_001": "English AU Female",
        "en_au_002": "English AU Male",
        "en_uk_001": "English UK Male 1",
        "en_uk_003": "English UK Male 2",
        "en_us_001": "English US Female 1",
        "en_us_002": "English US Female 2",
        "en_us_006": "English US Male 1",
        "en_us_007": "English US Male 2",
        "en_us_009": "English US Male 3",
        "en_us_010": "English US Male 4",
        # Europe
        "fr_001": "French Male 1",
        "fr_002": "French Male 2",
        "de_001": "German Female",
        "de_002": "German Male",
        "es_002": "Spanish Male",
        # Americas
        "es_mx_002": "Spanish MX Male",
        "br_001": "Portuguese BR Female 1",
        "br_003": "Portuguese BR Female 2",
        "br_004": "Portuguese BR Female 3",
        "br_005": "Portuguese BR Male",
        # Asia
        "id_001": "Indonesian Female",
        "jp_001": "Japanese Female 1",
        "jp_003": "Japanese Female 2",
        "jp_005": "Japanese Female 3",
        "jp_006": "Japanese Male",
        "kr_002": "Korean Male 1",
        "kr_003": "Korean Female",
        "kr_004": "Korean Male 2",
        # Singing
        "en_female_f08_salut_damour": "Alto",
        "en_male_m03_lobby": "Tenor",
        "en_female_f08_warmy_breeze": "Warmy Breeze",
        "en_male_m03_sunshine_soon": "Sunshine Soon",
        # Other
        "en_male_narration": "Narrator",
        "en_male_funny": "Wacky",
        "en_female_emotional": "Peaceful",
    }
    return [f"tiktok:{vid}-{label}" for vid, label in voices.items()]


def is_tiktok_voice(voice_name: str):
    """检查是否是TikTok TTS的声音"""
    return voice_name.startswith("tiktok:")


def get_ali_voices() -> list[str]:
    """
    获取阿里云NLS TTS的声音列表

    Returns:
        声音列表，格式为 ["ali:xiaoyun-中文女声", ...]
    """
    voices = {
        # 中文女声
        "xiaoyun": "中文女声-小云",
        "xiaogang": "中文男声-小刚",
        "ruoxi": "中文女声-若兮",
        "siqi": "中文女声-思琪",
        "sijia": "中文女声-思佳",
        "sicheng": "中文男声-思诚",
        "aiqi": "中文女声-艾琪",
        "aijia": "中文女声-艾佳",
        "aichu": "中文女声-艾楚",
        "aida": "中文男声-艾达",
        "ninger": "中文女声-宁儿",
        "ruilin": "中文女声-瑞琳",
        "siyue": "中文女声-思悦",
        "aiya": "中文女声-艾雅",
        "aimei": "中文女声-艾美",
        "aiyu": "中文女声-艾雨",
        "aiyue": "中文女声-艾悦",
        "aijing": "中文女声-艾婧",
        "xiaomei": "中文女声-小美",
        "aina": "中文女声-艾娜",
        "yina": "中文女声-伊娜",
        "sijing": "中文女声-思婧",
        "sitong": "中文童声-童童",
        "xiaobei": "中文女声-小北",
        "aitong": "中文童声-艾彤",
        "aiwei": "中文男声-艾威",
        "aibao": "中文男声-艾宝",
        # 英文
        "harry": "English Male",
        "abby": "English Female",
        "andy": "English Male 2",
        "eric": "English Male 3",
        "emily": "English Female 2",
        "luna": "English Female 3",
        # 日韩
        "tomoka": "Japanese Female",
        "tomoya": "Japanese Male",
        "yoomi": "Korean Female",
    }
    return [f"ali:{vid}-{label}" for vid, label in voices.items()]


def is_ali_voice(voice_name: str):
    """检查是否是阿里云NLS TTS的声音"""
    return voice_name.startswith("ali:")


def get_tencent_voices() -> list[str]:
    """
    获取腾讯云TTS的声音列表

    Returns:
        声音列表，格式为 ["tencent:1001-智瑜", ...]
    """
    voices = {
        "1001": "智瑜-中文女声",
        "1002": "智聆-中文女声",
        "1003": "智美-中文女声",
        "1004": "智云-中文男声",
        "1005": "智莉-中文女声",
        "1007": "智娜-中文女声",
        "1008": "智琪-中文女声",
        "1009": "智芸-中文女声",
        "1010": "智华-中文男声",
        "1017": "智蓉-中文女声",
        "1018": "智靖-中文男声",
        "1050": "WeJack-English Male",
        "1051": "WeRose-English Female",
    }
    return [f"tencent:{vid}-{label}" for vid, label in voices.items()]


def is_tencent_voice(voice_name: str):
    """检查是否是腾讯云TTS的声音"""
    return voice_name.startswith("tencent:")


def get_chattts_voices() -> list[str]:
    """获取ChatTTS声音列表"""
    return ["chattts:default-ChatTTS Default"]


def is_chattts_voice(voice_name: str):
    """检查是否是ChatTTS的声音"""
    return voice_name.startswith("chattts:")


def get_gptsovits_voices() -> list[str]:
    """获取GPT-SoVITS声音列表"""
    return ["gptsovits:default-GPT-SoVITS Default"]


def is_gptsovits_voice(voice_name: str):
    """检查是否是GPT-SoVITS的声音"""
    return voice_name.startswith("gptsovits:")


def get_cosyvoice_voices() -> list[str]:
    """获取CosyVoice声音列表"""
    voices = [
        "中文女", "中文男", "日语男", "粤语女",
        "英文女", "英文男", "韩语女",
    ]
    return [f"cosyvoice:{v}-CosyVoice {v}" for v in voices]


def is_cosyvoice_voice(voice_name: str):
    """检查是否是CosyVoice的声音"""
    return voice_name.startswith("cosyvoice:")


def is_siliconflow_voice(voice_name: str):
    """检查是否是硅基流动的声音"""
    return voice_name.startswith("siliconflow:")


def is_gemini_voice(voice_name: str):
    """检查是否是Gemini TTS的声音"""
    return voice_name.startswith("gemini:")


def tts(
    text: str,
    voice_name: str,
    voice_rate: float,
    voice_file: str,
    voice_volume: float = 1.0,
) -> Union[SubMaker, None]:
    if is_azure_v2_voice(voice_name):
        return azure_tts_v2(text, voice_name, voice_file)
    elif is_tiktok_voice(voice_name):
        # 格式: tiktok:voice_id-Label
        parts = voice_name.split(":")
        if len(parts) >= 2:
            voice_id = parts[1].split("-")[0]
            return tiktok_tts(text, voice_id, voice_rate, voice_file, voice_volume)
        else:
            logger.error(f"Invalid tiktok voice name format: {voice_name}")
            return None
    elif is_ali_voice(voice_name):
        # 格式: ali:voice_id-Label
        parts = voice_name.split(":")
        if len(parts) >= 2:
            voice_id = parts[1].split("-")[0]
            return ali_tts(text, voice_id, voice_rate, voice_file, voice_volume)
        else:
            logger.error(f"Invalid ali voice name format: {voice_name}")
            return None
    elif is_tencent_voice(voice_name):
        # 格式: tencent:voice_type-Label
        parts = voice_name.split(":")
        if len(parts) >= 2:
            voice_type = parts[1].split("-")[0]
            return tencent_tts(text, voice_type, voice_rate, voice_file, voice_volume)
        else:
            logger.error(f"Invalid tencent voice name format: {voice_name}")
            return None
    elif is_chattts_voice(voice_name):
        return chattts_tts(text, voice_file, voice_volume)
    elif is_gptsovits_voice(voice_name):
        return gptsovits_tts(text, voice_file, voice_volume)
    elif is_cosyvoice_voice(voice_name):
        # 格式: cosyvoice:voice_name-Label
        parts = voice_name.split(":")
        if len(parts) >= 2:
            voice = parts[1].split("-")[0]
            return cosyvoice_tts(text, voice, voice_file, voice_volume)
        else:
            logger.error(f"Invalid cosyvoice voice name format: {voice_name}")
            return None
    elif is_siliconflow_voice(voice_name):
        # 从voice_name中提取模型和声音
        # 格式: siliconflow:model:voice-Gender
        parts = voice_name.split(":")
        if len(parts) >= 3:
            model = parts[1]
            # 移除性别后缀，例如 "alex-Male" -> "alex"
            voice_with_gender = parts[2]
            voice = voice_with_gender.split("-")[0]
            # 构建完整的voice参数，格式为 "model:voice"
            full_voice = f"{model}:{voice}"
            return siliconflow_tts(
                text, model, full_voice, voice_rate, voice_file, voice_volume
            )
        else:
            logger.error(f"Invalid siliconflow voice name format: {voice_name}")
            return None
    elif is_gemini_voice(voice_name):
        # 从voice_name中提取声音名称
        # 格式: gemini:voice-Gender
        parts = voice_name.split(":")
        if len(parts) >= 2:
            # 移除性别后缀，例如 "Zephyr-Female" -> "Zephyr"
            voice_with_gender = parts[1]
            voice = voice_with_gender.split("-")[0]
            return gemini_tts(text, voice, voice_rate, voice_file, voice_volume)
        else:
            logger.error(f"Invalid gemini voice name format: {voice_name}")
            return None
    return azure_tts_v1(text, voice_name, voice_rate, voice_file)


def convert_rate_to_percent(rate: float) -> str:
    if rate == 1.0:
        return "+0%"
    percent = round((rate - 1.0) * 100)
    if percent > 0:
        return f"+{percent}%"
    else:
        return f"{percent}%"


def azure_tts_v1(
    text: str, voice_name: str, voice_rate: float, voice_file: str
) -> Union[SubMaker, None]:
    voice_name = parse_voice_name(voice_name)
    text = text.strip()
    rate_str = convert_rate_to_percent(voice_rate)
    for i in range(3):
        try:
            logger.info(f"start, voice name: {voice_name}, try: {i + 1}")

            async def _do() -> SubMaker:
                communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
                sub_maker = edge_tts.SubMaker()
                with open(voice_file, "wb") as file:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            file.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            sub_maker.create_sub(
                                (chunk["offset"], chunk["duration"]), chunk["text"]
                            )
                return sub_maker

            sub_maker = asyncio.run(_do())
            if not sub_maker or not sub_maker.subs:
                logger.warning("failed, sub_maker is None or sub_maker.subs is None")
                continue

            logger.info(f"completed, output file: {voice_file}")
            return sub_maker
        except Exception as e:
            logger.error(f"failed, error: {str(e)}")
    return None


def siliconflow_tts(
    text: str,
    model: str,
    voice: str,
    voice_rate: float,
    voice_file: str,
    voice_volume: float = 1.0,
) -> Union[SubMaker, None]:
    """
    使用硅基流动的API生成语音

    Args:
        text: 要转换为语音的文本
        model: 模型名称，如 "FunAudioLLM/CosyVoice2-0.5B"
        voice: 声音名称，如 "FunAudioLLM/CosyVoice2-0.5B:alex"
        voice_rate: 语音速度，范围[0.25, 4.0]
        voice_file: 输出的音频文件路径
        voice_volume: 语音音量，范围[0.6, 5.0]，需要转换为硅基流动的增益范围[-10, 10]

    Returns:
        SubMaker对象或None
    """
    text = text.strip()
    api_key = config.siliconflow.get("api_key", "")

    if not api_key:
        logger.error("SiliconFlow API key is not set")
        return None

    # 将voice_volume转换为硅基流动的增益范围
    # 默认voice_volume为1.0，对应gain为0
    gain = voice_volume - 1.0
    # 确保gain在[-10, 10]范围内
    gain = max(-10, min(10, gain))

    url = "https://api.siliconflow.cn/v1/audio/speech"

    payload = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": "mp3",
        "sample_rate": 32000,
        "stream": False,
        "speed": voice_rate,
        "gain": gain,
    }

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    for i in range(3):  # 尝试3次
        try:
            logger.info(
                f"start siliconflow tts, model: {model}, voice: {voice}, try: {i + 1}"
            )

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                # 保存音频文件
                with open(voice_file, "wb") as f:
                    f.write(response.content)

                # 创建一个空的SubMaker对象
                sub_maker = SubMaker()

                # 获取音频文件的实际长度
                try:
                    # 尝试使用moviepy获取音频长度
                    from moviepy import AudioFileClip

                    audio_clip = AudioFileClip(voice_file)
                    audio_duration = audio_clip.duration
                    audio_clip.close()

                    # 将音频长度转换为100纳秒单位（与edge_tts兼容）
                    audio_duration_100ns = int(audio_duration * 10000000)

                    # 使用文本分割来创建更准确的字幕
                    # 将文本按标点符号分割成句子
                    sentences = utils.split_string_by_punctuations(text)

                    if sentences:
                        # 计算每个句子的大致时长（按字符数比例分配）
                        total_chars = sum(len(s) for s in sentences)
                        char_duration = (
                            audio_duration_100ns / total_chars if total_chars > 0 else 0
                        )

                        current_offset = 0
                        for sentence in sentences:
                            if not sentence.strip():
                                continue

                            # 计算当前句子的时长
                            sentence_chars = len(sentence)
                            sentence_duration = int(sentence_chars * char_duration)

                            # 添加到SubMaker
                            sub_maker.subs.append(sentence)
                            sub_maker.offset.append(
                                (current_offset, current_offset + sentence_duration)
                            )

                            # 更新偏移量
                            current_offset += sentence_duration
                    else:
                        # 如果无法分割，则使用整个文本作为一个字幕
                        sub_maker.subs = [text]
                        sub_maker.offset = [(0, audio_duration_100ns)]

                except Exception as e:
                    logger.warning(f"Failed to create accurate subtitles: {str(e)}")
                    # 回退到简单的字幕
                    sub_maker.subs = [text]
                    # 使用音频文件的实际长度，如果无法获取，则假设为10秒
                    sub_maker.offset = [
                        (
                            0,
                            audio_duration_100ns
                            if "audio_duration_100ns" in locals()
                            else 10000000,
                        )
                    ]

                logger.success(f"siliconflow tts succeeded: {voice_file}")
                print("s", sub_maker.subs, sub_maker.offset)
                return sub_maker
            else:
                logger.error(
                    f"siliconflow tts failed with status code {response.status_code}: {response.text}"
                )
        except Exception as e:
            logger.error(f"siliconflow tts failed: {str(e)}")

    return None


def azure_tts_v2(text: str, voice_name: str, voice_file: str) -> Union[SubMaker, None]:
    voice_name = is_azure_v2_voice(voice_name)
    if not voice_name:
        logger.error(f"invalid voice name: {voice_name}")
        raise ValueError(f"invalid voice name: {voice_name}")
    text = text.strip()

    def _format_duration_to_offset(duration) -> int:
        if isinstance(duration, str):
            time_obj = datetime.strptime(duration, "%H:%M:%S.%f")
            milliseconds = (
                (time_obj.hour * 3600000)
                + (time_obj.minute * 60000)
                + (time_obj.second * 1000)
                + (time_obj.microsecond // 1000)
            )
            return milliseconds * 10000

        if isinstance(duration, int):
            return duration

        return 0

    for i in range(3):
        try:
            logger.info(f"start, voice name: {voice_name}, try: {i + 1}")

            import azure.cognitiveservices.speech as speechsdk

            sub_maker = SubMaker()

            def speech_synthesizer_word_boundary_cb(evt: speechsdk.SessionEventArgs):
                # print('WordBoundary event:')
                # print('\tBoundaryType: {}'.format(evt.boundary_type))
                # print('\tAudioOffset: {}ms'.format((evt.audio_offset + 5000)))
                # print('\tDuration: {}'.format(evt.duration))
                # print('\tText: {}'.format(evt.text))
                # print('\tTextOffset: {}'.format(evt.text_offset))
                # print('\tWordLength: {}'.format(evt.word_length))

                duration = _format_duration_to_offset(str(evt.duration))
                offset = _format_duration_to_offset(evt.audio_offset)
                sub_maker.subs.append(evt.text)
                sub_maker.offset.append((offset, offset + duration))

            # Creates an instance of a speech config with specified subscription key and service region.
            speech_key = config.azure.get("speech_key", "")
            service_region = config.azure.get("speech_region", "")
            if not speech_key or not service_region:
                logger.error("Azure speech key or region is not set")
                return None

            audio_config = speechsdk.audio.AudioOutputConfig(
                filename=voice_file, use_default_speaker=True
            )
            speech_config = speechsdk.SpeechConfig(
                subscription=speech_key, region=service_region
            )
            speech_config.speech_synthesis_voice_name = voice_name
            # speech_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceResponse_RequestSentenceBoundary,
            #                            value='true')
            speech_config.set_property(
                property_id=speechsdk.PropertyId.SpeechServiceResponse_RequestWordBoundary,
                value="true",
            )

            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
            )
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                audio_config=audio_config, speech_config=speech_config
            )
            speech_synthesizer.synthesis_word_boundary.connect(
                speech_synthesizer_word_boundary_cb
            )

            result = speech_synthesizer.speak_text_async(text).get()
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.success(f"azure v2 speech synthesis succeeded: {voice_file}")
                return sub_maker
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(
                    f"azure v2 speech synthesis canceled: {cancellation_details.reason}"
                )
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    logger.error(
                        f"azure v2 speech synthesis error: {cancellation_details.error_details}"
                    )
            logger.info(f"completed, output file: {voice_file}")
        except Exception as e:
            logger.error(f"failed, error: {str(e)}")
    return None


def ali_tts(
    text: str,
    voice: str,
    voice_rate: float,
    voice_file: str,
    voice_volume: float = 1.0,
) -> Union[SubMaker, None]:
    """
    使用阿里云NLS TTS生成语音

    需要配置: ali_access_key_id, ali_access_key_secret, ali_app_key
    使用REST API而非WebSocket，简化实现

    Returns:
        None（需要whisper生成字幕）
    """
    import base64
    import hmac
    import hashlib
    import uuid
    import time
    from urllib.parse import quote

    access_key_id = config.app.get("ali_access_key_id", "")
    access_key_secret = config.app.get("ali_access_key_secret", "")
    app_key = config.app.get("ali_app_key", "")

    if not access_key_id or not access_key_secret or not app_key:
        logger.error("Alibaba Cloud NLS: access_key_id, access_key_secret, or app_key not set")
        return None

    text = text.strip()
    if not text:
        return None

    # 获取Token
    def _get_token():
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        params = {
            "AccessKeyId": access_key_id,
            "Action": "CreateToken",
            "Format": "JSON",
            "RegionId": "cn-shanghai",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": str(uuid.uuid4()),
            "SignatureVersion": "1.0",
            "Timestamp": timestamp,
            "Version": "2019-02-28",
        }
        sorted_params = sorted(params.items())
        query_string = "&".join(f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in sorted_params)
        string_to_sign = f"GET&{quote('/', safe='')}&{quote(query_string, safe='')}"
        sign_key = (access_key_secret + "&").encode("utf-8")
        signature = base64.b64encode(
            hmac.new(sign_key, string_to_sign.encode("utf-8"), hashlib.sha1).digest()
        ).decode("utf-8")
        params["Signature"] = signature
        resp = requests.get("https://nls-meta.cn-shanghai.aliyuncs.com/", params=params, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        return result.get("Token", {}).get("Id", "")

    for attempt in range(3):
        try:
            logger.info(f"start ali tts, voice: {voice}, try: {attempt + 1}")
            token = _get_token()
            if not token:
                raise ValueError("Failed to obtain Alibaba Cloud NLS token")

            # 使用REST API
            url = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/tts"
            # 语速转换：voice_rate 1.0 = 正常, 映射到 [-500, 500]
            speech_rate = int((voice_rate - 1.0) * 500)
            speech_rate = max(-500, min(500, speech_rate))

            headers = {
                "Content-Type": "application/json",
                "X-NLS-Token": token,
            }
            payload = {
                "appkey": app_key,
                "text": text,
                "voice": voice,
                "format": "mp3",
                "sample_rate": 16000,
                "speech_rate": speech_rate,
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            content_type = resp.headers.get("Content-Type", "")
            if "audio" in content_type or resp.status_code == 200 and len(resp.content) > 1000:
                with open(voice_file, "wb") as f:
                    f.write(resp.content)
                logger.success(f"ali tts succeeded: {voice_file}")
                return None
            else:
                raise ValueError(f"Ali NLS returned error: {resp.text[:200]}")

        except Exception as e:
            logger.error(f"ali tts failed: {str(e)}")

    return None


def tencent_tts(
    text: str,
    voice_type: str,
    voice_rate: float,
    voice_file: str,
    voice_volume: float = 1.0,
) -> Union[SubMaker, None]:
    """
    使用腾讯云TTS生成语音

    需要配置: tencent_secret_id, tencent_secret_key
    使用REST API直接请求

    Returns:
        None（需要whisper生成字幕）
    """
    import base64 as b64
    import hmac
    import hashlib
    import json
    import time

    secret_id = config.app.get("tencent_secret_id", "")
    secret_key = config.app.get("tencent_secret_key", "")

    if not secret_id or not secret_key:
        logger.error("Tencent Cloud TTS: secret_id or secret_key not set")
        return None

    text = text.strip()
    if not text:
        return None

    # 语速转换：voice_rate 1.0 = 正常(0), 映射到 [-2, 6]的整数
    speed = max(-2, min(6, int((voice_rate - 1.0) * 5)))

    def _sign_request(payload_str: str, action: str):
        """生成腾讯云API v3签名"""
        service = "tts"
        host = "tts.tencentcloudapi.com"
        timestamp = int(time.time())
        date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))

        # CanonicalRequest
        canonical_request = (
            f"POST\n/\n\ncontent-type:application/json\nhost:{host}\n\n"
            f"content-type;host\n{hashlib.sha256(payload_str.encode('utf-8')).hexdigest()}"
        )
        # StringToSign
        credential_scope = f"{date}/{service}/tc3_request"
        string_to_sign = (
            f"TC3-HMAC-SHA256\n{timestamp}\n{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )
        # Signature
        def _hmac_sha256(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = _hmac_sha256(("TC3" + secret_key).encode("utf-8"), date)
        secret_service = _hmac_sha256(secret_date, service)
        secret_signing = _hmac_sha256(secret_service, "tc3_request")
        signature = hmac.new(
            secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        authorization = (
            f"TC3-HMAC-SHA256 Credential={secret_id}/{credential_scope}, "
            f"SignedHeaders=content-type;host, Signature={signature}"
        )
        return {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Host": host,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": "2019-08-23",
        }

    for attempt in range(3):
        try:
            logger.info(f"start tencent tts, voice: {voice_type}, try: {attempt + 1}")

            payload = {
                "Text": text,
                "SessionId": str(int(time.time() * 1000)),
                "VoiceType": int(voice_type),
                "Codec": "mp3",
                "Speed": speed,
                "Volume": max(0, min(10, int(voice_volume * 5))),
            }
            payload_str = json.dumps(payload)
            headers = _sign_request(payload_str, "TextToVoice")

            resp = requests.post(
                "https://tts.tencentcloudapi.com",
                headers=headers,
                data=payload_str,
                timeout=60,
            )
            result = resp.json()

            if "Response" in result and "Audio" in result["Response"]:
                audio_data = b64.b64decode(result["Response"]["Audio"])
                with open(voice_file, "wb") as f:
                    f.write(audio_data)
                logger.success(f"tencent tts succeeded: {voice_file}")
                return None
            else:
                error_msg = result.get("Response", {}).get("Error", {}).get("Message", "Unknown error")
                raise ValueError(f"Tencent TTS error: {error_msg}")

        except Exception as e:
            logger.error(f"tencent tts failed: {str(e)}")

    return None


def chattts_tts(
    text: str,
    voice_file: str,
    voice_volume: float = 1.0,
) -> Union[SubMaker, None]:
    """
    使用本地ChatTTS服务器生成语音

    需要配置: chattts_server (默认 http://127.0.0.1:8080)

    Returns:
        None（需要whisper生成字幕）
    """
    import zipfile
    import io

    server = config.app.get("chattts_server", "http://127.0.0.1:8080").rstrip("/")
    text = text.strip()
    if not text:
        return None

    for attempt in range(3):
        try:
            logger.info(f"start chattts tts, try: {attempt + 1}")

            payload = {
                "text": [text],
                "stream": False,
                "lang": None,
                "skip_refine_text": False,
                "refine_text_only": False,
                "use_decoder": True,
                "audio_seed": 42,
                "text_seed": 42,
                "do_text_normalization": True,
                "do_homophone_replacement": False,
            }
            resp = requests.post(
                f"{server}/generate_voice",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()

            # ChatTTS返回ZIP格式
            content_type = resp.headers.get("Content-Type", "")
            if "zip" in content_type or resp.content[:2] == b"PK":
                with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                    audio_files = [n for n in zf.namelist() if n.endswith((".mp3", ".wav"))]
                    if audio_files:
                        audio_data = zf.read(audio_files[0])
                        with open(voice_file, "wb") as f:
                            f.write(audio_data)
                        logger.success(f"chattts tts succeeded: {voice_file}")
                        return None
                    raise ValueError("No audio files found in ChatTTS ZIP response")
            else:
                # 直接是音频数据
                with open(voice_file, "wb") as f:
                    f.write(resp.content)
                logger.success(f"chattts tts succeeded: {voice_file}")
                return None

        except Exception as e:
            logger.error(f"chattts tts failed: {str(e)}")

    return None


def gptsovits_tts(
    text: str,
    voice_file: str,
    voice_volume: float = 1.0,
) -> Union[SubMaker, None]:
    """
    使用本地GPT-SoVITS服务器生成语音

    需要配置: gptsovits_server (默认 http://127.0.0.1:9880)

    Returns:
        None（需要whisper生成字幕）
    """
    server = config.app.get("gptsovits_server", "http://127.0.0.1:9880").rstrip("/")
    text = text.strip()
    if not text:
        return None

    for attempt in range(3):
        try:
            logger.info(f"start gptsovits tts, try: {attempt + 1}")

            payload = {
                "text": text,
                "text_language": "zh",
            }
            resp = requests.post(server, json=payload, timeout=120)
            resp.raise_for_status()

            with open(voice_file, "wb") as f:
                f.write(resp.content)
            logger.success(f"gptsovits tts succeeded: {voice_file}")
            return None

        except Exception as e:
            logger.error(f"gptsovits tts failed: {str(e)}")

    return None


def cosyvoice_tts(
    text: str,
    voice: str,
    voice_file: str,
    voice_volume: float = 1.0,
) -> Union[SubMaker, None]:
    """
    使用本地CosyVoice服务器生成语音

    需要配置: cosyvoice_server

    Returns:
        None（需要whisper生成字幕）
    """
    server = config.app.get("cosyvoice_server", "").rstrip("/")
    if not server:
        logger.error("CosyVoice server URL not configured")
        return None

    text = text.strip()
    if not text:
        return None

    for attempt in range(3):
        try:
            logger.info(f"start cosyvoice tts, voice: {voice}, try: {attempt + 1}")

            payload = {
                "mode": "sft",
                "tts_text": text,
                "sft_dropdown": voice,
            }
            resp = requests.post(f"{server}/text-tts", json=payload, timeout=120)
            resp.raise_for_status()

            with open(voice_file, "wb") as f:
                f.write(resp.content)
            logger.success(f"cosyvoice tts succeeded: {voice_file}")
            return None

        except Exception as e:
            logger.error(f"cosyvoice tts failed: {str(e)}")

    return None


def tiktok_tts(
    text: str,
    voice_id: str,
    voice_rate: float,
    voice_file: str,
    voice_volume: float = 1.0,
) -> Union[SubMaker, None]:
    """
    使用TikTok TTS生成语音（免费，无需API key）

    Args:
        text: 要转换为语音的文本
        voice_id: TikTok voice ID，如 "en_us_001"
        voice_rate: 语音速度（当前未使用，TikTok API不支持）
        voice_file: 输出的音频文件路径
        voice_volume: 语音音量（当前未使用）

    Returns:
        None（TikTok TTS不提供word-level时间戳，需要whisper生成字幕）
    """
    import base64

    TIKTOK_ENDPOINTS = [
        "https://tiktok-tts.weilnet.workers.dev/api/generation",
        "https://tiktoktts.com/api/tiktok-tts",
    ]
    CHUNK_LIMIT = 300

    def _split_text(s: str, limit: int) -> list[str]:
        """按词边界拆分文本，每段不超过limit字符"""
        words = s.split()
        chunks = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= limit:
                current += f" {word}" if current else word
            else:
                if current:
                    chunks.append(current)
                current = word
        if current:
            chunks.append(current)
        return chunks if chunks else [s[:limit]]

    def _call_endpoint(endpoint_url: str, chunk: str, voice: str) -> str:
        """调用TikTok TTS端点并返回base64音频数据"""
        headers = {"Content-Type": "application/json"}
        data = {"text": chunk, "voice": voice}
        resp = requests.post(endpoint_url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        # 两个端点的响应格式略有不同
        if "data" in result:
            return result["data"]
        elif "audioUrl" in result:
            # 第二个端点可能返回base64 data URI
            audio_str = result["audioUrl"]
            if "," in audio_str:
                return audio_str.split(",", 1)[1]
            return audio_str
        raise ValueError(f"Unexpected response format from {endpoint_url}")

    text = text.strip()
    if not text:
        logger.error("TikTok TTS: empty text")
        return None

    for attempt in range(3):
        try:
            logger.info(f"start tiktok tts, voice: {voice_id}, try: {attempt + 1}")

            # 选择可用的端点
            endpoint = None
            for ep in TIKTOK_ENDPOINTS:
                try:
                    base_url = ep.split("/api")[0] if "/api" in ep else ep
                    check = requests.get(base_url, timeout=10)
                    if check.status_code == 200:
                        endpoint = ep
                        break
                except Exception:
                    continue

            if not endpoint:
                logger.warning("No TikTok TTS endpoint available, retrying...")
                continue

            # 拆分文本并生成音频
            chunks = _split_text(text, CHUNK_LIMIT) if len(text) > CHUNK_LIMIT else [text]
            all_audio_b64 = []
            for chunk in chunks:
                b64_data = _call_endpoint(endpoint, chunk, voice_id)
                if not b64_data or b64_data == "error":
                    raise ValueError(f"TikTok TTS returned error for chunk: {chunk[:50]}...")
                all_audio_b64.append(b64_data)

            # 合并base64数据并写入文件
            combined_b64 = "".join(all_audio_b64)
            audio_bytes = base64.b64decode(combined_b64)
            with open(voice_file, "wb") as f:
                f.write(audio_bytes)

            logger.success(f"tiktok tts succeeded: {voice_file}")
            # 返回None：TikTok TTS不提供word-level时间戳
            # 需要使用whisper作为subtitle_provider来生成字幕
            return None

        except Exception as e:
            logger.error(f"tiktok tts failed: {str(e)}")

    return None


def gemini_tts(
    text: str,
    voice_name: str,
    voice_rate: float,
    voice_file: str,
    voice_volume: float = 1.0,
) -> Union[SubMaker, None]:
    """
    使用Google Gemini TTS生成语音
    
    Args:
        text: 要转换的文本
        voice_name: 语音名称，如 "Zephyr", "Puck" 等
        voice_rate: 语音速率（当前未使用）
        voice_file: 输出音频文件路径
        voice_volume: 音频音量（当前未使用）
        
    Returns:
        SubMaker对象或None
    """
    import base64
    import json
    import io
    from pydub import AudioSegment
    import google.generativeai as genai
    
    try:
        # 配置Gemini API
        api_key = config.app.get("gemini_api_key", "")
        if not api_key:
            logger.error("Gemini API key is not set")
            return None
            
        genai.configure(api_key=api_key)
        
        logger.info(f"start, voice name: {voice_name}, try: 1")
        
        # 使用Gemini TTS API
        model = genai.GenerativeModel("gemini-2.5-flash-preview-tts")
        
        generation_config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": voice_name
                    }
                }
            }
        }
        
        response = model.generate_content(
            contents=text,
            generation_config=generation_config
        )
        
        # 检查响应
        if not response.candidates or not response.candidates[0].content:
            logger.error("No audio content received from Gemini TTS")
            return None
            
        # 获取音频数据
        audio_data = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                audio_data = part.inline_data.data
                break
                
        if not audio_data:
            logger.error("No audio data found in response")
            return None
            
        # 音频数据已经是原始字节，不需要base64解码
        if isinstance(audio_data, str):
            # 如果是字符串，则需要base64解码
            audio_bytes = base64.b64decode(audio_data)
        else:
            # 如果已经是字节，直接使用
            audio_bytes = audio_data
        
        # 尝试不同的音频格式 - Gemini可能返回不同的格式
        audio_segment = None
        
        # Gemini返回Linear PCM格式，按照文档参数解析
        try:
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_bytes), 
                format="raw",
                frame_rate=24000,  # Gemini TTS默认采样率
                channels=1,        # 单声道
                sample_width=2     # 16-bit
            )
        except Exception as e:
            logger.error(f"Failed to load PCM audio: {e}")
            return None
        
        # 导出为MP3格式
        audio_segment.export(voice_file, format="mp3")
        
        logger.info(f"completed, output file: {voice_file}")
        
        # 创建SubMaker对象用于字幕
        sub_maker = SubMaker()
        audio_duration = len(audio_segment) / 1000.0  # 转换为秒
        
        # 将音频长度转换为100纳秒单位（与edge_tts兼容）
        audio_duration_100ns = int(audio_duration * 10000000)
        
        # 使用create_sub方法正确创建字幕项
        sub_maker.create_sub(
            (0, audio_duration_100ns), 
            text
        )
        
        return sub_maker
        
    except ImportError as e:
        logger.error(f"Missing required package for Gemini TTS: {str(e)}. Please install: pip install pydub")
        return None
    except Exception as e:
        logger.error(f"Gemini TTS failed, error: {str(e)}")
        return None


def _format_text(text: str) -> str:
    # text = text.replace("\n", " ")
    text = text.replace("[", " ")
    text = text.replace("]", " ")
    text = text.replace("(", " ")
    text = text.replace(")", " ")
    text = text.replace("{", " ")
    text = text.replace("}", " ")
    text = text.strip()
    return text


def create_subtitle(sub_maker: submaker.SubMaker, text: str, subtitle_file: str):
    """
    优化字幕文件
    1. 将字幕文件按照标点符号分割成多行
    2. 逐行匹配字幕文件中的文本
    3. 生成新的字幕文件
    """

    text = _format_text(text)

    def formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
        """
        1
        00:00:00,000 --> 00:00:02,360
        跑步是一项简单易行的运动
        """
        start_t = mktimestamp(start_time).replace(".", ",")
        end_t = mktimestamp(end_time).replace(".", ",")
        return f"{idx}\n{start_t} --> {end_t}\n{sub_text}\n"

    start_time = -1.0
    sub_items = []
    sub_index = 0

    script_lines = utils.split_string_by_punctuations(text)

    def match_line(_sub_line: str, _sub_index: int):
        if len(script_lines) <= _sub_index:
            return ""

        _line = script_lines[_sub_index]
        if _sub_line == _line:
            return script_lines[_sub_index].strip()

        _sub_line_ = re.sub(r"[^\w\s]", "", _sub_line)
        _line_ = re.sub(r"[^\w\s]", "", _line)
        if _sub_line_ == _line_:
            return _line_.strip()

        _sub_line_ = re.sub(r"\W+", "", _sub_line)
        _line_ = re.sub(r"\W+", "", _line)
        if _sub_line_ == _line_:
            return _line.strip()

        return ""

    sub_line = ""

    try:
        for _, (offset, sub) in enumerate(zip(sub_maker.offset, sub_maker.subs)):
            _start_time, end_time = offset
            if start_time < 0:
                start_time = _start_time

            sub = unescape(sub)
            sub_line += sub
            sub_text = match_line(sub_line, sub_index)
            if sub_text:
                sub_index += 1
                line = formatter(
                    idx=sub_index,
                    start_time=start_time,
                    end_time=end_time,
                    sub_text=sub_text,
                )
                sub_items.append(line)
                start_time = -1.0
                sub_line = ""

        if len(sub_items) == len(script_lines):
            with open(subtitle_file, "w", encoding="utf-8") as file:
                file.write("\n".join(sub_items) + "\n")
            try:
                sbs = subtitles.file_to_subtitles(subtitle_file, encoding="utf-8")
                duration = max([tb for ((ta, tb), txt) in sbs])
                logger.info(
                    f"completed, subtitle file created: {subtitle_file}, duration: {duration}"
                )
            except Exception as e:
                logger.error(f"failed, error: {str(e)}")
                os.remove(subtitle_file)
        else:
            logger.warning(
                f"failed, sub_items len: {len(sub_items)}, script_lines len: {len(script_lines)}"
            )

    except Exception as e:
        logger.error(f"failed, error: {str(e)}")


def _get_audio_duration_from_submaker(sub_maker: submaker.SubMaker):
    """
    获取音频时长
    """
    if not sub_maker.offset:
        return 0.0
    return sub_maker.offset[-1][1] / 10000000

def _get_audio_duration_from_mp3(mp3_file: str) -> float:
    """
    获取MP3音频时长
    """
    if not os.path.exists(mp3_file):
        logger.error(f"MP3 file does not exist: {mp3_file}")
        return 0.0

    try:
        # Use moviepy to get the duration of the MP3 file
        with AudioFileClip(mp3_file) as audio:
            return audio.duration  # Duration in seconds
    except Exception as e:
        logger.error(f"Failed to get audio duration from MP3: {str(e)}")
        return 0.0

def get_audio_duration( target: Union[str, submaker.SubMaker]) -> float:
    """
    获取音频时长
    如果是SubMaker对象，则从SubMaker中获取时长
    如果是MP3文件，则从MP3文件中获取时长
    """
    if isinstance(target, submaker.SubMaker):
        return _get_audio_duration_from_submaker(target)
    elif isinstance(target, str) and target.endswith(".mp3"):
        return _get_audio_duration_from_mp3(target)
    else:
        logger.error(f"Invalid target type: {type(target)}")
        return 0.0

if __name__ == "__main__":
    voice_name = "zh-CN-XiaoxiaoMultilingualNeural-V2-Female"
    voice_name = parse_voice_name(voice_name)
    voice_name = is_azure_v2_voice(voice_name)
    print(voice_name)

    voices = get_all_azure_voices()
    print(len(voices))

    async def _do():
        temp_dir = utils.storage_dir("temp")

        voice_names = [
            "zh-CN-XiaoxiaoMultilingualNeural",
            # 女性
            "zh-CN-XiaoxiaoNeural",
            "zh-CN-XiaoyiNeural",
            # 男性
            "zh-CN-YunyangNeural",
            "zh-CN-YunxiNeural",
        ]
        text = """
        静夜思是唐代诗人李白创作的一首五言古诗。这首诗描绘了诗人在寂静的夜晚，看到窗前的明月，不禁想起远方的家乡和亲人，表达了他对家乡和亲人的深深思念之情。全诗内容是：“床前明月光，疑是地上霜。举头望明月，低头思故乡。”在这短短的四句诗中，诗人通过“明月”和“思故乡”的意象，巧妙地表达了离乡背井人的孤独与哀愁。首句“床前明月光”设景立意，通过明亮的月光引出诗人的遐想；“疑是地上霜”增添了夜晚的寒冷感，加深了诗人的孤寂之情；“举头望明月”和“低头思故乡”则是情感的升华，展现了诗人内心深处的乡愁和对家的渴望。这首诗简洁明快，情感真挚，是中国古典诗歌中非常著名的一首，也深受后人喜爱和推崇。
            """

        text = """
        What is the meaning of life? This question has puzzled philosophers, scientists, and thinkers of all kinds for centuries. Throughout history, various cultures and individuals have come up with their interpretations and beliefs around the purpose of life. Some say it's to seek happiness and self-fulfillment, while others believe it's about contributing to the welfare of others and making a positive impact in the world. Despite the myriad of perspectives, one thing remains clear: the meaning of life is a deeply personal concept that varies from one person to another. It's an existential inquiry that encourages us to reflect on our values, desires, and the essence of our existence.
        """

        text = """
               预计未来3天深圳冷空气活动频繁，未来两天持续阴天有小雨，出门带好雨具；
               10-11日持续阴天有小雨，日温差小，气温在13-17℃之间，体感阴凉；
               12日天气短暂好转，早晚清凉；
                   """

        text = "[Opening scene: A sunny day in a suburban neighborhood. A young boy named Alex, around 8 years old, is playing in his front yard with his loyal dog, Buddy.]\n\n[Camera zooms in on Alex as he throws a ball for Buddy to fetch. Buddy excitedly runs after it and brings it back to Alex.]\n\nAlex: Good boy, Buddy! You're the best dog ever!\n\n[Buddy barks happily and wags his tail.]\n\n[As Alex and Buddy continue playing, a series of potential dangers loom nearby, such as a stray dog approaching, a ball rolling towards the street, and a suspicious-looking stranger walking by.]\n\nAlex: Uh oh, Buddy, look out!\n\n[Buddy senses the danger and immediately springs into action. He barks loudly at the stray dog, scaring it away. Then, he rushes to retrieve the ball before it reaches the street and gently nudges it back towards Alex. Finally, he stands protectively between Alex and the stranger, growling softly to warn them away.]\n\nAlex: Wow, Buddy, you're like my superhero!\n\n[Just as Alex and Buddy are about to head inside, they hear a loud crash from a nearby construction site. They rush over to investigate and find a pile of rubble blocking the path of a kitten trapped underneath.]\n\nAlex: Oh no, Buddy, we have to help!\n\n[Buddy barks in agreement and together they work to carefully move the rubble aside, allowing the kitten to escape unharmed. The kitten gratefully nuzzles against Buddy, who responds with a friendly lick.]\n\nAlex: We did it, Buddy! We saved the day again!\n\n[As Alex and Buddy walk home together, the sun begins to set, casting a warm glow over the neighborhood.]\n\nAlex: Thanks for always being there to watch over me, Buddy. You're not just my dog, you're my best friend.\n\n[Buddy barks happily and nuzzles against Alex as they disappear into the sunset, ready to face whatever adventures tomorrow may bring.]\n\n[End scene.]"

        text = "大家好，我是乔哥，一个想帮你把信用卡全部还清的家伙！\n今天我们要聊的是信用卡的取现功能。\n你是不是也曾经因为一时的资金紧张，而拿着信用卡到ATM机取现？如果是，那你得好好看看这个视频了。\n现在都2024年了，我以为现在不会再有人用信用卡取现功能了。前几天一个粉丝发来一张图片，取现1万。\n信用卡取现有三个弊端。\n一，信用卡取现功能代价可不小。会先收取一个取现手续费，比如这个粉丝，取现1万，按2.5%收取手续费，收取了250元。\n二，信用卡正常消费有最长56天的免息期，但取现不享受免息期。从取现那一天开始，每天按照万5收取利息，这个粉丝用了11天，收取了55元利息。\n三，频繁的取现行为，银行会认为你资金紧张，会被标记为高风险用户，影响你的综合评分和额度。\n那么，如果你资金紧张了，该怎么办呢？\n乔哥给你支一招，用破思机摩擦信用卡，只需要少量的手续费，而且还可以享受最长56天的免息期。\n最后，如果你对玩卡感兴趣，可以找乔哥领取一本《卡神秘籍》，用卡过程中遇到任何疑惑，也欢迎找乔哥交流。\n别忘了，关注乔哥，回复用卡技巧，免费领取《2024用卡技巧》，让我们一起成为用卡高手！"

        text = """
        2023全年业绩速览
公司全年累计实现营业收入1476.94亿元，同比增长19.01%，归母净利润747.34亿元，同比增长19.16%。EPS达到59.49元。第四季度单季，营业收入444.25亿元，同比增长20.26%，环比增长31.86%；归母净利润218.58亿元，同比增长19.33%，环比增长29.37%。这一阶段
的业绩表现不仅突显了公司的增长动力和盈利能力，也反映出公司在竞争激烈的市场环境中保持了良好的发展势头。
2023年Q4业绩速览
第四季度，营业收入贡献主要增长点；销售费用高增致盈利能力承压；税金同比上升27%，扰动净利率表现。
业绩解读
利润方面，2023全年贵州茅台，>归母净利润增速为19%，其中营业收入正贡献18%，营业成本正贡献百分之一，管理费用正贡献百分之一点四。(注：归母净利润增速值=营业收入增速+各科目贡献，展示贡献/拖累的前四名科目，且要求贡献值/净利润增速>15%)
"""
        text = "静夜思是唐代诗人李白创作的一首五言古诗。这首诗描绘了诗人在寂静的夜晚，看到窗前的明月，不禁想起远方的家乡和亲人"

        text = _format_text(text)
        lines = utils.split_string_by_punctuations(text)
        print(lines)

        for voice_name in voice_names:
            voice_file = f"{temp_dir}/tts-{voice_name}.mp3"
            subtitle_file = f"{temp_dir}/tts.mp3.srt"
            sub_maker = azure_tts_v2(
                text=text, voice_name=voice_name, voice_file=voice_file
            )
            create_subtitle(sub_maker=sub_maker, text=text, subtitle_file=subtitle_file)
            audio_duration = get_audio_duration(sub_maker)
            print(f"voice: {voice_name}, audio duration: {audio_duration}s")

    loop = asyncio.get_event_loop_policy().get_event_loop()
    try:
        loop.run_until_complete(_do())
    finally:
        loop.close()
