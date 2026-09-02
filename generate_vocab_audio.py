"""
批量生成字彙表片語發音音檔
自動從 index.html 解析所有週次的 vocabulary，用 ElevenLabs 生成
輸出: audio/W{N}/W{N}_V{id}.mp3
已存在且 >1KB 的檔案自動跳過，重跑即可補失敗的檔案。
"""

import requests
import os
import re
import time
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_KEY = "sk_558bbc35f1541d293966060323f25427ddb5086498d69e57"
VOICE_ID = "DODLEQrClDo8wCz460ld"  # Mia 女聲，教學發音清晰

TTS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
HEADERS = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": API_KEY}


def parse_vocab_from_html(path="index.html"):
    """解析 index.html 中每週的 vocabulary: {week: [(id, phrase), ...]}"""
    with open(path, encoding='utf-8') as f:
        src = f.read()
    # 只取 COURSE_DATA 區塊
    start = src.index('const COURSE_DATA')
    end = src.index('以下是程式碼')
    block = src[start:end]

    weeks = {}
    # 每週開頭: "            N: {"
    week_iter = list(re.finditer(r'^\s{12}(\d+): \{', block, re.M))
    for i, m in enumerate(week_iter):
        week_num = int(m.group(1))
        seg_end = week_iter[i + 1].start() if i + 1 < len(week_iter) else len(block)
        seg = block[m.start():seg_end]
        # vocabulary 到 dialogue 之間
        vm = re.search(r'vocabulary:\s*\[(.*?)\],\s*\n\s*dialogue', seg, re.S)
        if not vm:
            continue
        vocab_seg = vm.group(1)
        items = re.findall(r"id:\s*(\d+),\s*phrase:\s*(['\"])(.*?)\2", vocab_seg)
        weeks[week_num] = [(int(vid), phrase.replace("\\'", "'")) for vid, _, phrase in items]
    return weeks


def clean_for_tts(phrase):
    """把片語清理成適合唸的文字"""
    t = phrase.replace('...', '').strip()
    return t


def normalize_loudness(path):
    try:
        import imageio_ffmpeg, subprocess
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        tmp = path + '.norm.mp3'
        r = subprocess.run([ff, '-y', '-i', path, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-b:a', '160k', tmp],
                           capture_output=True, text=True)
        if r.returncode == 0 and os.path.getsize(tmp) > 1000:
            os.replace(tmp, path)
            return True
        if os.path.exists(tmp):
            os.remove(tmp)
    except Exception:
        pass
    return False


def generate(text, output_path):
    data = {
        "text": text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {"stability": 0.6, "similarity_boost": 0.75, "style": 0.2, "use_speaker_boost": True}
    }
    try:
        r = requests.post(TTS_URL, json=data, headers=HEADERS, timeout=30)
    except Exception as e:
        print(f"  ❌ 網路錯誤: {e}")
        return False
    if r.status_code == 200 and len(r.content) > 1000:
        with open(output_path, 'wb') as f:
            f.write(r.content)
        normalize_loudness(output_path)
        return True
    print(f"  ❌ {r.status_code}: {r.text[:120]}")
    return False


def main():
    weeks = parse_vocab_from_html()
    total = sum(len(v) for v in weeks.values())
    print(f"🎙️  解析到 {len(weeks)} 週共 {total} 個片語\n")
    done = failed = 0

    for week_num in sorted(weeks):
        week_dir = os.path.join("audio", f"W{week_num}")
        os.makedirs(week_dir, exist_ok=True)
        print(f"📂 W{week_num} ({len(weeks[week_num])} 個片語)")
        for vid, phrase in weeks[week_num]:
            path = os.path.join(week_dir, f"W{week_num}_V{vid}.mp3")
            if os.path.exists(path) and os.path.getsize(path) > 1000:
                done += 1
                continue
            text = clean_for_tts(phrase)
            print(f"  🔊 V{vid}: {text}")
            if generate(text, path):
                done += 1
            else:
                failed += 1
            time.sleep(0.7)
        print()

    print(f"🎉 完成 {done}/{total}，失敗 {failed}")
    if failed:
        print("⚠️  再跑一次補失敗的檔案")


if __name__ == "__main__":
    main()
