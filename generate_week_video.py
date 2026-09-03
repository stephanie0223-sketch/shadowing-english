"""每週 Shadowing 動畫影片生成器
用法: 更新 WEEK / TITLE / DIALOGUE / KEY_SENTENCES 後執行 python generate_week_video.py
輸出: videos/W{N}_{title}.mp4
內容: 品牌畫面 + 對話動畫字幕 + 片尾 8 句 shadowing 練習(每句後留 10 秒)
品牌色: 森林綠 #5d9b76
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip, concatenate_audioclips
from moviepy.audio.AudioClip import AudioArrayClip
import os, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT = r"C:\Users\user\OneDrive\文件\Claude\Projects\生活英文Podcast練習shadowing"
HERE = os.path.dirname(os.path.abspath(__file__))
WEEK = 12
TITLE = "Hiking, Camping, Cycling & SUP"
OUT = os.path.join(HERE, "videos", f"W{WEEK}_" + TITLE.replace(" ", "_").replace("&", "and") + ".mp4")

W, H = 1280, 720
TEAL = (93, 155, 118)   # 淺森林綠 #5d9b76
BG = (246, 250, 247)
LIGHT = (227, 239, 231)
MIA_C = (212, 83, 126)
LEO_C = (24, 95, 165)
DARK = (42, 42, 42)
PRACTICE_SILENCE = 10  # 每句練習留白秒數

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

def font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", name), size)

# ========== 音訊時間軸 ==========
pod = AudioFileClip(os.path.join(PROJECT, "audio", f"W{WEEK}", f"W{WEEK}_full.mp3"))
trans = AudioFileClip(os.path.join(PROJECT, "assets", "shadow_transition.mp3"))
sent_clips = [AudioFileClip(os.path.join(PROJECT, "audio", f"W{WEEK}", f"W{WEEK}_S{i+1}.mp3")) for i in range(8)]
FPS_A = 44100
silence = AudioArrayClip(np.zeros((FPS_A * PRACTICE_SILENCE, 2)), fps=FPS_A)

gap = AudioArrayClip(np.zeros((FPS_A * 3, 2)), fps=FPS_A)  # 對話結束後停 3 秒
segments = [pod, gap, trans]
for c in sent_clips:
    segments += [c, silence]
full_audio = concatenate_audioclips(segments)
DUR = full_audio.duration

# 時間軸標記
POD_END = pod.duration
TRANS_END = POD_END + 3 + trans.duration
shadow_marks = []  # (listen_start, listen_end, practice_end) per sentence
t = TRANS_END
for c in sent_clips:
    shadow_marks.append((t, t + c.duration, t + c.duration + PRACTICE_SILENCE))
    t += c.duration + PRACTICE_SILENCE

# 對話段逐句時間（比例估算）
chars = [len(x) + 14 for _, x in DIALOGUE]
total_chars = sum(chars)
starts, acc = [], 0.0
for c in chars:
    starts.append(acc)
    acc += POD_END * c / total_chars
starts.append(POD_END)

def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if draw.textlength(test, font=fnt) <= maxw:
            cur = test
        else:
            lines.append(cur)
            cur = w_
    if cur: lines.append(cur)
    return lines

def base_canvas(subtitle_note=None):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 86], fill=TEAL)
    d.text((40, 43), "Shadowing English", font=font(36, True), fill=(255, 255, 255), anchor="lm")
    d.text((W - 40, 43), "Stephanie's English Lab", font=font(24), fill=LIGHT, anchor="rm")
    d.text((W // 2, 132), f"W{WEEK} · {TITLE}", font=font(40, True), fill=TEAL, anchor="mm")
    return img, d

def draw_avatar(d, cx, cy, r, color, active, bob):
    y = cy - (bob if active else 0)
    if active:
        d.ellipse([cx - r - 14, y - r - 14, cx + r + 14, y + r + 14], outline=color, width=6)
    d.ellipse([cx - r, y - r, cx + r, y + r], fill=color)
    er = 7 if active else 5
    d.ellipse([cx - r // 2.5 - er, y - 14 - er, cx - r // 2.5 + er, y - 14 + er], fill=(255, 255, 255))
    d.ellipse([cx + r // 2.5 - er, y - 14 - er, cx + r // 2.5 + er, y - 14 + er], fill=(255, 255, 255))
    d.arc([cx - 30, y + 2, cx + 30, y + 44], 20, 160, fill=(255, 255, 255), width=6)

def dialogue_frame(i, phase):
    img, d = base_canvas()
    spk, text = DIALOGUE[i]
    bob = 12 if phase else 0
    draw_avatar(d, 320, 330, 105, MIA_C, spk == "Mia", bob)
    draw_avatar(d, W - 320, 330, 105, LEO_C, spk == "Leo", bob)
    color = MIA_C if spk == "Mia" else LEO_C
    f_sub = font(38, True)
    lines = wrap(d, text, f_sub, W - 300)
    box_h = 44 + len(lines) * 52
    top = H - 110 - box_h
    d.rounded_rectangle([120, top, W - 120, top + box_h], radius=22, fill=(255, 255, 255), outline=color, width=4)
    for li, ln in enumerate(lines):
        d.text((W // 2, top + 46 + li * 52), ln, font=f_sub, fill=DARK, anchor="mm")
    d.rectangle([0, H - 14, int(W * (starts[i] / DUR)), H], fill=TEAL)
    return np.array(img)

def transition_frame(phase):
    img, d = base_canvas()
    f = font(52, True)
    d.text((W // 2, 340), "Now, let's shadow these sentences!", font=f, fill=TEAL, anchor="mm")
    d.text((W // 2, 420), "Listen, and repeat during the pause", font=font(32), fill=(120, 120, 120), anchor="mm")
    d.rectangle([0, H - 14, int(W * (POD_END / DUR)), H], fill=TEAL)
    return np.array(img)

def shadow_frame(idx, mode, countdown=None):
    """mode: 'listen' or 'practice'"""
    img, d = base_canvas()
    spk, text = KEY_SENTENCES[idx]
    color = MIA_C if spk == "Mia" else LEO_C
    d.text((W // 2, 200), f"Sentence {idx + 1} / 8", font=font(34, True), fill=(150, 150, 150), anchor="mm")
    f_sub = font(44, True)
    lines = wrap(d, text, f_sub, W - 260)
    y0 = 320 - (len(lines) - 1) * 30
    box_h = 70 + len(lines) * 60
    d.rounded_rectangle([100, y0 - 55, W - 100, y0 - 55 + box_h], radius=24, fill=(255, 255, 255), outline=color, width=5)
    for li, ln in enumerate(lines):
        d.text((W // 2, y0 + li * 60), ln, font=f_sub, fill=DARK, anchor="mm")
    if mode == "listen":
        d.text((W // 2, 560), "Listen...", font=font(40, True), fill=color, anchor="mm")
    else:
        d.text((W // 2, 545), "Your turn! Say it out loud!", font=font(42, True), fill=TEAL, anchor="mm")
        # 倒數條
        frac = countdown / PRACTICE_SILENCE
        d.rounded_rectangle([340, 600, W - 340, 626], radius=13, fill=LIGHT)
        d.rounded_rectangle([340, 600, 340 + int((W - 680) * frac), 626], radius=13, fill=TEAL)
    mark = shadow_marks[idx]
    d.rectangle([0, H - 14, int(W * (mark[0] / DUR)), H], fill=TEAL)
    return np.array(img)

print("預先渲染畫面...")
frames = {}
for i in range(len(DIALOGUE)):
    frames[("d", i, 0)] = dialogue_frame(i, 0)
    frames[("d", i, 1)] = dialogue_frame(i, 1)
frames[("t", 0, 0)] = transition_frame(0)
for i in range(8):
    frames[("l", i, 0)] = shadow_frame(i, "listen")
    for s in range(PRACTICE_SILENCE + 1):
        frames[("p", i, s)] = shadow_frame(i, "practice", countdown=PRACTICE_SILENCE - s)

def line_at(t):
    for i in range(len(DIALOGUE)):
        if starts[i] <= t < starts[i + 1]:
            return i
    return len(DIALOGUE) - 1

def make_frame(t):
    if t < POD_END:
        i = line_at(t)
        return frames[("d", i, int(t * 2.2) % 2)]
    if t < TRANS_END:
        return frames[("t", 0, 0)]
    for idx, (ls, le, pe) in enumerate(shadow_marks):
        if t < le:
            return frames[("l", idx, 0)]
        if t < pe:
            sec = min(int(t - le), PRACTICE_SILENCE)
            return frames[("p", idx, sec)]
    return frames[("p", 7, PRACTICE_SILENCE)]

print("合成影片...")
video = VideoClip(make_frame, duration=DUR).with_audio(full_audio).with_fps(12)
video.write_videofile(OUT, codec="libx264", audio_codec="aac", preset="faster", logger=None)
print("完成:", OUT, f"{os.path.getsize(OUT)/1024/1024:.1f} MB, 總長 {DUR/60:.1f} 分鐘")
