"""
自動化生成一週的 Shadowing 音檔（雙聲 podcast + 8 句跟讀）
使用方式: python generate_week_audio.py
- 完整 podcast: audio/W{N}/W{N}_full.mp3 (兩個 voice 對話)
- 跟讀音檔:    audio/W{N}/W{N}_S1.mp3 ~ S8.mp3 (依句子的 speaker 配音)
已存在且 >1KB 的檔案自動跳過。
"""

import requests
import os
import time
import sys
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_KEY = "sk_558bbc35f1541d293966060323f25427ddb5086498d69e57"

VOICES = {
    "Mia": "DODLEQrClDo8wCz460ld",   # 女聲
    "Leo": "TxGEqnHWrfWFTfGW9XjX",   # 男聲 Josh（年輕美式，2026-09 選定）
}

VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.3,
    "use_speaker_boost": True
}

HEADERS = {"xi-api-key": API_KEY, "Content-Type": "application/json"}

# ============================================================
# Week 12: Hiking, Camping, Cycling & SUP
# ============================================================
WEEK = 12

DIALOGUE = [
    ("Mia", "Leo! You're walking so slowly today. What happened?"),
    ("Leo", "Don't laugh. I'm sore all over. My legs are dead."),
    ("Mia", "Wait, seriously? What did you do this weekend?"),
    ("Leo", "We went camping in Hualien. Two days, three activities."),
    ("Mia", "Three? Okay, tell me everything."),
    ("Leo", "Day one, we cycled to the campsite. Forty kilometers!"),
    ("Mia", "Forty?! On a bike? That's crazy."),
    ("Leo", "Yeah. Pedaling uphill was the worst part."),
    ("Mia", "I bet you worked up a sweat."),
    ("Leo", "My shirt was soaked. Totally soaked."),
    ("Mia", "Okay, then what? Did you pitch a tent?"),
    ("Leo", "Yep. It fell down twice, though."),
    ("Mia", "Ha! Classic. Camping looks easy on YouTube."),
    ("Leo", "Right? But the campfire made everything better."),
    ("Mia", "Oh, I love campfires. Did you cook over it?"),
    ("Leo", "We grilled sausages and made hot chocolate."),
    ("Mia", "Okay, now I'm jealous. What about day two?"),
    ("Leo", "Stand-up paddleboarding. SUP. Ever tried it?"),
    ("Mia", "No way. Isn't that super hard?"),
    ("Leo", "The hardest part is keeping your balance."),
    ("Mia", "Did you fall in?"),
    ("Leo", "I wiped out five times. Five!"),
    ("Mia", "Ha! I would pay to see that."),
    ("Leo", "The water was freezing, by the way."),
    ("Mia", "So... was it fun or just painful?"),
    ("Leo", "Honestly? Both. But mostly fun."),
    ("Mia", "What was the best moment?"),
    ("Leo", "We got up early to catch the sunrise. Unreal."),
    ("Mia", "Okay, that sounds amazing. I want to go."),
    ("Leo", "You should! But remember to travel light."),
    ("Mia", "Why? What did you bring?"),
    ("Leo", "A huge bag. My sleeping bag alone weighed a ton."),
    ("Mia", "Noted. Small bag, big memories, right?"),
    ("Leo", "Exactly. So... are you in for next month?"),
    ("Mia", "I'm game! But I'm NOT doing forty kilometers."),
    ("Leo", "Deal. Twenty, and ice cream after."),
]

KEY_SENTENCES = [
    ("Leo", "Don't laugh. I'm sore all over. My legs are dead."),
    ("Mia", "Forty?! On a bike? That's crazy."),
    ("Mia", "I bet you worked up a sweat."),
    ("Leo", "The hardest part is keeping your balance."),
    ("Leo", "I wiped out five times. Five!"),
    ("Mia", "So... was it fun or just painful?"),
    ("Leo", "We got up early to catch the sunrise. Unreal."),
    ("Mia", "I'm game! But I'm NOT doing forty kilometers."),
]

WEEK_DIR = os.path.join("audio", f"W{WEEK}")


def file_ok(path):
    return os.path.exists(path) and os.path.getsize(path) > 1000


def normalize_loudness(path, target=-16, dynamic=False):
    """統一響度，消除不同 voice 的音量/距離感差異。
    - Leo(Josh) 單句用 target=-14（聽感較遠，比 Mia 加 2dB）
    - 完整 podcast 用 dynamic=True：dynaudnorm 先拉平檔內兩位講者的音量差"""
    try:
        import imageio_ffmpeg, subprocess
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        tmp = path + '.norm.mp3'
        af = f'loudnorm=I={target}:TP=-1.5:LRA=11'
        if dynamic:
            af = 'dynaudnorm=f=250:g=15:m=8,' + af
        r = subprocess.run([ff, '-y', '-i', path, '-af', af, '-b:a', '160k', tmp],
                           capture_output=True, text=True)
        if r.returncode == 0 and os.path.getsize(tmp) > 1000:
            os.replace(tmp, path)
            return True
        if os.path.exists(tmp):
            os.remove(tmp)
    except Exception as e:
        print(f"  ⚠️ 響度標準化失敗（保留原檔）: {e}")
    return False


def tts_line(text, voice_id, output_path):
    """單句 TTS (eleven_turbo_v2)；Leo 聲音響度目標 -14（比 Mia 大 2dB，Stephanie 聽感校正）"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    data = {"text": text, "model_id": "eleven_turbo_v2", "voice_settings": VOICE_SETTINGS}
    try:
        r = requests.post(url, json=data, headers={**HEADERS, "Accept": "audio/mpeg"}, timeout=60)
    except Exception as e:
        print(f"  ❌ 網路錯誤: {e}")
        return False
    if r.status_code == 200 and len(r.content) > 1000:
        with open(output_path, 'wb') as f:
            f.write(r.content)
        normalize_loudness(output_path, target=-14 if voice_id == VOICES["Leo"] else -16)
        return True
    print(f"  ❌ {r.status_code}: {r.text[:150]}")
    return False


def try_text_to_dialogue(output_path):
    """優先嘗試 Text-to-Dialogue API (eleven_v3) — 一次生成整段對話，銜接最自然"""
    url = "https://api.elevenlabs.io/v1/text-to-dialogue"
    inputs = [{"text": text, "voice_id": VOICES[spk]} for spk, text in DIALOGUE]
    data = {"inputs": inputs, "model_id": "eleven_v3"}
    print("🎙️  嘗試 Text-to-Dialogue API 生成完整 podcast...")
    try:
        r = requests.post(url, json=data, headers={**HEADERS, "Accept": "audio/mpeg"}, timeout=300)
    except Exception as e:
        print(f"  ⚠️ 網路錯誤: {e}")
        return False
    if r.status_code == 200 and len(r.content) > 10000:
        with open(output_path, 'wb') as f:
            f.write(r.content)
        normalize_loudness(output_path, dynamic=True)
        print(f"  ✅ 完整 podcast 完成 ({len(r.content)/1024:.0f} KB)")
        return True
    print(f"  ⚠️ Text-to-Dialogue 不可用 ({r.status_code}): {r.text[:200]}")
    return False


def fallback_podcast(output_path):
    """退回方案: 逐句 TTS 後串接 mp3"""
    print("🎙️  改用逐句生成 + 串接...")
    tmp_dir = os.path.join(WEEK_DIR, "_lines")
    os.makedirs(tmp_dir, exist_ok=True)
    parts = []
    for i, (spk, text) in enumerate(DIALOGUE, 1):
        p = os.path.join(tmp_dir, f"line{i:02d}.mp3")
        if not file_ok(p):
            print(f"  🔊 line {i:02d} [{spk}] {text[:40]}...")
            if not tts_line(text, VOICES[spk], p):
                print(f"  ❌ line {i} 失敗，中止 podcast 串接")
                return False
            time.sleep(0.6)
        parts.append(p)
    with open(output_path, 'wb') as out:
        for p in parts:
            with open(p, 'rb') as f:
                out.write(f.read())
    print(f"  ✅ 串接完成 ({os.path.getsize(output_path)/1024:.0f} KB)")
    return True


def main():
    os.makedirs(WEEK_DIR, exist_ok=True)

    # 1. 完整 podcast
    full_path = os.path.join(WEEK_DIR, f"W{WEEK}_full.mp3")
    if file_ok(full_path):
        print(f"⏭️  {full_path} 已存在，跳過")
    else:
        if not try_text_to_dialogue(full_path):
            fallback_podcast(full_path)

    # 2. 8 句跟讀音檔
    print(f"\n🔊 生成 8 句跟讀音檔...")
    done = failed = 0
    for i, (spk, text) in enumerate(KEY_SENTENCES, 1):
        path = os.path.join(WEEK_DIR, f"W{WEEK}_S{i}.mp3")
        if file_ok(path):
            print(f"  ⏭️  W{WEEK}_S{i}.mp3 已存在，跳過")
            done += 1
            continue
        print(f"  🔊 S{i} [{spk}] {text[:45]}")
        if tts_line(text, VOICES[spk], path):
            done += 1
            print(f"  ✅ W{WEEK}_S{i}.mp3 ({os.path.getsize(path)/1024:.1f} KB)")
        else:
            failed += 1
        time.sleep(0.8)

    print(f"\n🎉 跟讀音檔: {done}/8 完成，{failed} 失敗")
    if failed:
        print("⚠️  再跑一次腳本重試失敗的檔案")


if __name__ == "__main__":
    main()
