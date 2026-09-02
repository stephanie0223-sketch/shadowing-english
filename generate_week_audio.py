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
    "Leo": "l4Coq6695JDX9xtLqXDE",   # 男聲（原本跟讀用的聲音）
}

VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.3,
    "use_speaker_boost": True
}

HEADERS = {"xi-api-key": API_KEY, "Content-Type": "application/json"}

# ============================================================
# Week 10: Ordering at a Cafe
# ============================================================
WEEK = 10

DIALOGUE = [
    ("Mia", "Finally! I've been dying to grab a coffee all day."),
    ("Leo", "Honestly, I never come to cafés. The menu scares me."),
    ("Mia", "Wait, seriously? Okay, don't worry. I've got you."),
    ("Leo", "There are like fifty drinks up there. Fifty!"),
    ("Mia", "Ha! I just get my usual. A large iced matcha latte."),
    ("Leo", "Your usual? Wow, you sound like a regular."),
    ("Mia", "I'm here every day. And I always say half sugar, less ice."),
    ("Leo", "Whoa, you can change all that stuff?"),
    ("Mia", "Sure! Sugar level, ice, size. Whatever you want."),
    ("Leo", "Cool. So, what do you recommend? What's the signature drink here?"),
    ("Mia", "The honey latte. It's the house special. But it's pretty sweet."),
    ("Leo", "Hmm, no thanks. I need something super strong. I stayed up late gaming."),
    ("Mia", "Then go for an Americano. Hot or iced?"),
    ("Leo", "Iced, for sure. It's so hot today."),
    ("Mia", "You can make it a double. Two espresso shots."),
    ("Leo", "Perfect. But hmm, maybe milk would be nice."),
    ("Mia", "Then get a latte instead. It's coffee plus milk."),
    ("Leo", "But milk makes my stomach hurt a little."),
    ("Mia", "No problem. Just ask for a dairy-free option, like oat milk."),
    ("Leo", "Oh, they can do that? That's actually great."),
    ("Mia", "What about food? The chocolate cake here is amazing."),
    ("Leo", "Sure! I'm kind of hungry anyway."),
    ("Mia", "Get the sauce on the side. The cake stays crispy that way."),
    ("Leo", "You're clearly a café expert. Oh no, it's our turn!"),
    ("Mia", "Watch me first. Hi! Can I have a large iced matcha latte, half sugar, less ice?"),
    ("Leo", "Okay, my turn. Um... I'll have a small iced latte, no sugar, with oat milk."),
    ("Mia", "Look at you! You sound like a pro already."),
    ("Leo", "Wait, for here or to go? She's asking me."),
    ("Mia", "For here, obviously. We've got cake to eat."),
    ("Leo", "Right! For here, please."),
    ("Mia", "And put your wallet away. Let me treat you today."),
    ("Leo", "What? No way. You don't have to."),
    ("Mia", "You can treat me next time. Deal?"),
    ("Leo", "Deal. Next time it's on me!"),
]

KEY_SENTENCES = [
    ("Mia", "Finally! I've been dying to grab a coffee all day."),
    ("Mia", "I just get my usual. A large iced matcha latte."),
    ("Mia", "I always say half sugar, less ice."),
    ("Mia", "Then go for an Americano. Hot or iced?"),
    ("Mia", "You can make it a double. Two espresso shots."),
    ("Mia", "Can I have a large iced matcha latte, half sugar, less ice?"),
    ("Leo", "I'll have a small iced latte, no sugar, with oat milk."),
    ("Leo", "Wait, for here or to go? She's asking me."),
]

WEEK_DIR = os.path.join("audio", f"W{WEEK}")


def file_ok(path):
    return os.path.exists(path) and os.path.getsize(path) > 1000


def tts_line(text, voice_id, output_path):
    """單句 TTS (eleven_turbo_v2)"""
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
