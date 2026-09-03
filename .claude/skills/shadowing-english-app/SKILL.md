---
name: shadowing-english-app
description: 維護和擴充 Shadowing English 生活英語跟讀練習 web app。當使用者提到「shadowing app」、「跟讀網站」、「跟讀練習」、「shadowing english」、「加新的一週」、「新增週次」、「修 shadowing bug」、「更新學生名單」、「音檔問題」、「teacher dashboard」、「教師後台」、「成績」、「Firebase 問題」、「登入問題」，或任何與這個口說跟讀 web app 的開發、維護、除錯、擴充相關的請求，都應觸發此 skill。即使使用者只說「網站壞了」或「加第十週」，只要是指這個 shadowing 專案，就用此 skill。
---

# Shadowing English App — 完整專案指南

本 skill 涵蓋 Stephanie's English Lab Shadowing English 口說跟讀練習 web app 的所有技術細節，供 Claude Code 維護和擴充使用。

---

## 1. 專案概覽

**產品名稱**: Shadowing English 生活英語跟讀練習
**目標用戶**: 台灣高中生 (B1-B2 程度)
**教學目的**: 透過精選生活主題對話的 shadowing 跟讀練習，訓練學生的語調韻律和口說能力
**部署位置**: GitHub Pages (`stephanie0223-sketch.github.io/shadowing-english/`)
**GitHub Repo**: `stephanie0223-sketch/shadowing-english`

### 雙系統架構

此 app 是「系統二：Shadowing 口說系統」，與「系統一：Podcast 聽力系統」共用同一主題和慣用語：

- **系統一 (Podcast)**: Claude 寫 script → ElevenLabs Text-to-Dialogue 生成雙聲 podcast → 上架 Spotify → 附測驗連結
- **系統二 (Shadowing, 本 app)**: 從同一 script 精選 8 句含慣用語/語調特色的句子 → ElevenLabs 生成音檔 → 學生聽一句錄一句 → AI 評分

**注意：自 W10 起已不再使用 NotebookLM**（品質不穩定像抽獎）。全部改用 Claude 寫 script + ElevenLabs 配音的全自動流程，見「7. 常見維護任務 → 新增一週（W10+ 自動化流程）」。
**W1-W9 的完整 podcast 維持 NotebookLM 版本不重做**（Stephanie 2026-09 決定：學生已聽過、對話較即興自然）；只有跟讀/字彙音檔是 ElevenLabs。

---

## 2. 技術架構

### 單一檔案 React 應用

整個 app 是 **一個 `index.html` 檔案** (~3200 行)，包含所有 React 元件、樣式、邏輯。

**CDN 依賴 (在 `<head>` 中載入):**

```html
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.sheetjs.com/xlsx-0.20.0/package/dist/xlsx.full.min.js"></script>
<script src="https://aka.ms/csspeech/jsbrowserpackageraw"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore-compat.js"></script>
```

**所有 React code 在 `<script type="text/babel" data-type="module">` 內。**

### Firebase 設定

```javascript
const firebaseConfig = {
    apiKey: "AIzaSyC8MzjG2IO1j-2j0yyaGMwZfu_MMFsI_1M",
    authDomain: "stephanies-english-lab.firebaseapp.com",
    projectId: "stephanies-english-lab",
    storageBucket: "stephanies-english-lab.firebasestorage.app",
    messagingSenderId: "206793170448",
    appId: "1:206793170448:web:b2d88b37df5b45adc0b495"
};
```

- **Firebase Auth**: Google 登入 (`signInWithPopup`)
- **Firestore Collections**:
  - `scores` — 學生成績 (docId: `{userId}_week{weekId}_s{sentenceIdx}`)
  - `settings` — 週次開放設定 (doc: `weekLocks`)
  - `studentBindings` — Google 帳號與學生姓名的綁定

### Azure Speech SDK

```javascript
const AZURE_SPEECH_KEY = '2r698XaKOD9BPIT5h1f70BOlHxrPzUn54QpM5OgnwyBiOTaZ4kJrJQQJ99CDAC3pKaRXJ3w3AAAYACOGkLfX';
const AZURE_SPEECH_REGION = 'eastasia';
```

用於 Pronunciation Assessment（發音評估），評分維度：
- **accuracy** (準確度) 30%
- **completeness** (完整度) 30%
- **prosody** (語調韻律) 40%

計分公式: `total = accuracy * 0.3 + completeness * 0.3 + prosody * 0.4 - lateDay * 5`

### ElevenLabs TTS

```
API_KEY: sk_558bbc35f1541d293966060323f25427ddb5086498d69e57
男聲 (Leo):  TxGEqnHWrfWFTfGW9XjX  (Josh 內建聲，年輕美式；原 l4Coq669 其實是女聲已棄用)
女聲 (Mia):  DODLEQrClDo8wCz460ld
字彙發音:    DODLEQrClDo8wCz460ld  (generate_vocab_audio.py, 輸出 W{N}_V{id}.mp3)
跟讀單句 Model: eleven_turbo_v2
完整 podcast Model: eleven_v3 (Text-to-Dialogue API, /v1/text-to-dialogue)
```

- 每句跟讀音檔由 ElevenLabs 生成，**不使用瀏覽器 TTS**（已廢棄，語調太機械化）
- W10 起跟讀音檔**依角色配音**（該句是誰講的就用誰的聲音），W1-W9 為單一聲音
- 完整 podcast 用 Text-to-Dialogue API 一次生成整段雙人對話，銜接自然
- **響度標準化**（Stephanie 聽感校正，2026-09 定案）：
  - Mia 單句／字彙音檔 → -16 LUFS
  - **Leo(Josh) 單句 → -12 LUFS**（Josh 聽感較遠較小聲，比 Mia 加 4dB 才平衡；-14 仍不夠，兩輪校正定案）
  - 完整 podcast → `dynaudnorm=f=150:g=11:m=12` 先拉平檔內兩位講者音量差，再 loudnorm -15（整檔 loudnorm 無法平衡檔內的講者差異）
  - 都內建在 `normalize_loudness()`，生成時自動套用

---

## 3. 檔案結構

```
shadowing-english/
├── index.html                 # 主 app（唯一的程式碼檔案）
├── generate_week_audio.py     # ★每週音檔 pipeline：雙聲 podcast + 8 句跟讀（含響度標準化）
├── generate_vocab_audio.py    # ★字彙發音 pipeline：解析 index.html 自動生成 W{N}_V{id}.mp3
├── generate_week_video.py     # ★每週動畫影片生成器（輸出到 videos/，不 commit）
├── assets/
│   └── shadow_transition.mp3  # 影片共用過場口白 "Now, let's shadow these sentences..."
├── videos/                    # 影片輸出（.gitignore 排除）
├── audio/
│   ├── W1/ ... W9/            # W{N}_S1-8.mp3（跟讀）+ W{N}_V{id}.mp3（字彙發音）
│   └── W10/ W11/ ...          # W10 起另含 W{N}_full.mp3（ElevenLabs 完整 podcast）
├── W1/ ... W9/                # W{N}_full.m4a：NotebookLM podcast，**Stephanie 決定保留不重做**（app 仍引用）
├── archive/                   # 封存區（gitignore）：NotebookLM docx/原始檔備份、舊原型、legacy 工具
└── .claude/skills/shadowing-english-app/   # 本 skill（隨 repo 版控）
```

**音檔路徑函式:**
```javascript
function getSentenceAudioSrc(weekId, sentenceNum) {
    return `audio/W${weekId}/W${weekId}_S${sentenceNum}.mp3`;
}
```

**重要**: 跟讀/字彙音檔存放在 `audio/W{n}/`；完整 podcast W1-W9 在根目錄 `W{n}/*.m4a`、W10+ 在 `audio/W{n}/W{n}_full.mp3`。

---

## 4. 元件架構

### 登入系統

- **LoginScreen**: 學生 Google 登入 + 教師密碼登入
- 教師密碼: `teacher2026`
- 學生登入流程: Google Auth → 選班級 → 選姓名 → 綁定到 Firestore `studentBindings`
- 已綁定的帳號自動跳過選擇步驟
- **重整保持登入**: App mount 時自動恢復 session——學生走 `auth.onAuthStateChanged` + binding 查詢；教師用 localStorage `teacherLoggedIn` flag（登出時清除）。恢復期間顯示「🔄 載入中...」

### 學生端 (StudentPortal)

- **LessonTab（本週課程）**: Podcast 完整音檔播放器（標題顯示「Week N: 主題」，有 0.75x/1x/1.25x 速度）＋ 對話內容（目標語塊藍色標示）＋ 字彙表 ＋ 理解測驗
  - 完整 podcast 路徑：W1-W9 是 `W{N}/W{N}_full.m4a`（NotebookLM 時期），**W10+ 是 `audio/W{N}/W{N}_full.mp3`**（ElevenLabs），程式碼用 `weekId >= 10` 判斷
  - 字彙表每個片語有 🔊 播放按鈕 → `audio/W{N}/W{N}_V{id}.mp3`
- **週次選擇器**: 「本週課程」「跟讀練習」上方有 W1-WN 按鈕；鎖定的週次顯示 🔒 且不可點。**鎖定狀態只在頁面載入時讀取**，教師解鎖後學生要重整才看得到
- **DialogueTab**: 完整對話文本 + 理解測驗（選擇題）
- **PracticeTab**: 核心跟讀練習
  - 流程: ready → listening(播放音檔) → canRecord → recording(錄音) → recorded(回放) → submitted(AI評分)
  - 8 句精選句，每句有 speaker、vocab、tag、tip
  - AI 即時評分：逐字發音分析 + 語調韻律回饋（分 5 級詳細建議）
  - 麥克風: 一次性取得權限，保持 stream 持續

### 教師端 (TeacherPortal)

- **TeacherStatusTab**: 繳交狀態板（🟢已交/🟡遲交/⚪未交/🔒鎖定）+ 週次開放控制
- **TeacherScoresTab**: 成績管理（即時同步 `onSnapshot`）+ Excel 匯出 + 點擊查看學生詳細逐句成績
  - 成績表每格顯示：總分 + **三項指標小字（音=accuracy 藍／完=completeness 綠／調=prosody 粉）** + 完成句數
- **TeacherAnalyticsTab**: 班級平均分數長條圖

**即時同步**: 教師端使用 `listenAllScores()` 函式（Firestore `onSnapshot`），學生交卷時教師端自動更新，不需手動重整。

### PDF 成績單

使用 `html2pdf.js` 生成（支援中文字），標籤雙語顯示（"Student 學生："等）。

---

## 5. 課程資料結構 (COURSE_DATA)

新增週次只需在 `COURSE_DATA` 物件中加入資料，程式碼完全不需動。

```javascript
const COURSE_DATA = {
    1: {
        title: 'Daily Routines',        // 主題名稱
        vocabulary: [                     // 單字片語列表
            { id: 1, phrase: 'sleep in', ipa: '/sliːp ɪn/', zh: '睡懶覺', example: '...' },
            // ...
        ],
        dialogue: `...`,                  // 完整對話文本（多行字串）
        comprehensionQuestions: [          // 理解測驗（3 題選擇題）
            { id: 1, question: '...', options: [...], explanation: '...', correctIndex: 0 },
        ],
        keySentences: [                   // 8 句跟讀精選句
            {
                speaker: 'Night Owl',
                text: "I just pulled an all-nighter. Kind of feel like a zombie now.",
                vocab: 'pull an all-nighter',
                tag: '🔵 關鍵片語',
                tip: '注意 "pulled‿an" 的連音...'
            },
            // ... 共 8 句
        ],
    },
    // Week 2, 3, ... 同樣結構
};
```

### 現有週次

| Week | Title | 句數 |
|------|-------|------|
| 1 | Daily Routines | 8 |
| 2 | Dating | 8 |
| 3 | Friendship | 8 |
| 4 | Playing Basketball | 8 |
| 5 | Cooking | 8 |
| 6 | Outdoor Activities | 8 |
| 7 | Airport English | 8 |
| 8 | Homestay English | 8 |
| 9 | Screen Time | 8 |
| 10 | Ordering at a Café | 8 |
| 11 | MBTI & Personality | 8 |
| 12 | Hiking, Camping, Cycling & SUP | 8 |

**27 週完整規劃**（含 Semester 2-3 待製作主題清單）見 `references/current-weeks.md`。

---

## 6. 班級與學生名單 (CLASSES)

```javascript
const CLASSES = {
    '電機二忠': [
        { id: 1, name: '王正緯' }, { id: 2, name: '王浩棠' }, ...
        // 36 位學生（原「電機一忠」，2026-09 升級改名）
    ],
    '電機適性分組': [
        // 20 位真實學生（電機一忠10位＋電機一孝10位）+ 第21位「老師測試」
        // 完整名單見 references/student-roster.md
    ]
};
```

改班級名稱時注意：Firestore `studentBindings` 和 `scores` 裡存的 `className` 也要一起 migration（學生登入靠 uid 不受影響，但教師端成績篩選會對不上）。做法：在 index.html 加一次性 migration script（比對 settings/migration doc 防重跑），跑完後移除。

---

## 7. 常見維護任務

### 新增一週（W10+ 自動化流程，不再使用 NotebookLM）

完整流程約 10 分鐘，Stephanie 只負責過目和試聽：

1. **Claude 寫 script**：兩角色對話（Mia 女／Leo 男），30-38 句短對話、約 1.5-2 分鐘
   - B1 難度、每句 12 字內、目標片語 8-12 個全數自然融入
   - 8 句 key sentences 事先設計好（5-15 字、含片語、語調特徵明顯：連音/選擇疑問/強調重音/誇張情緒）
   - 給 Stephanie 過目，逐句修改直到定稿
2. **跑 `generate_week_audio.py`**：更新腳本裡的 `WEEK`、`DIALOGUE`、`KEY_SENTENCES` 後執行
   - 完整 podcast：Text-to-Dialogue API 雙聲一次生成 → `audio/W{N}/W{N}_full.mp3`（給 Spotify 用）
   - 8 句跟讀：逐句 TTS（依 speaker 選聲音）→ `audio/W{N}/W{N}_S1.mp3` ~ `S8.mp3`
   - 自動跳過已存在 >1KB 的檔案；失敗重跑即可
3. **跑 `generate_vocab_audio.py`**：自動從 index.html 解析新週次的 vocabulary，生成片語發音音檔 → `audio/W{N}/W{N}_V{id}.mp3`（女聲 Mia；要先完成步驟 4 的 COURSE_DATA 才解析得到）
4. **更新 `COURSE_DATA`**：新增 entry（title、vocabulary 12 個含 IPA、dialogue、comprehensionQuestions 3 題、keySentences 8 句含語調提示）
   - `WEEKS` 陣列是自動衍生的，不用手動加
5. **Git commit + push** → GitHub Pages 自動部署
6. **產動畫影片**（固定步驟）：更新 `generate_week_video.py` 的 `WEEK`/`TITLE`/`DIALOGUE`/`KEY_SENTENCES` 後執行 → `videos/W{N}_*.mp4`，用 SendUserFile 傳給 Stephanie。完整規格見「11. 每週動畫影片生成」
7. **Stephanie 驗收**：用「老師測試」帳號（電機適性分組 #21，Google 帳號 stephanie0223@gmail.com 已綁定）登入試聽；新週次預設 🔒 鎖定（unlockedWeeks 存 Firestore），教師端確認後手動解鎖
   - **提醒她強制重整**（Ctrl+Shift+R）：部署後瀏覽器常快取舊頁面/舊音檔，同檔名的音檔重新生成後尤其容易聽到舊版

已定案的 27 週主題規劃見 `references/current-weeks.md`。

### Legacy 音檔工具

W1-W9 時期的 `audio_generator.html`（瀏覽器批量工具）和 `generate_audio.py`（單聲音腳本）已移至 `archive/`，不再使用。

**ElevenLabs 音檔 voice_settings:**
```json
{
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.3,
    "use_speaker_boost": true
}
```

### 更新學生名單

修改 `CLASSES` 物件即可。每個學生需要 `{ id: 座號, name: '姓名' }`。

### Firestore 安全規則

目前使用開放規則（開發/教學用途）：
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

**注意**: 如果之前設了到期日規則（如 `request.time < timestamp.date(...)`），過期後會導致登入失敗，錯誤訊息為 `Missing or insufficient permissions`。需到 Firebase Console → Firestore → 規則 更新。

### GitHub Pages 授權網域

Firebase Auth Google 登入需要在 Firebase Console → Authentication → Settings → Authorized domains 加入 `stephanie0223-sketch.github.io`。

---

## 8. 已知問題與解決方案

| 問題 | 原因 | 解決方式 |
|------|------|----------|
| 登入失敗 "Missing or insufficient permissions" | Firestore 安全規則過期 | 更新規則為 `allow read, write: if true;` |
| 音檔播放失敗 | 0 byte 檔案或路徑錯誤 | 重新生成音檔，確認 >1KB |
| PDF 中文亂碼 | jsPDF 不支援 CJK | 使用 html2pdf.js |
| audio_generator.html "Failed to fetch" | CORS 限制 file:// | 必須從 https:// 執行 |
| "Site Not Found" | Firebase Hosting 沒部署 | app 在 GitHub Pages，不是 Firebase Hosting |
| 教師成績不同步 | 使用一次性 get() | 改用 onSnapshot 即時監聽 |
| 部署後看不到新功能/聽到舊音檔 | 瀏覽器快取（GitHub Pages 部署本身約 1-2 分鐘） | Ctrl+Shift+R 強制重整；先 curl 線上檔案確認已部署再判斷 |
| 週次按鈕點不了 | 該週鎖定，或頁面在解鎖前載入（鎖定狀態只在載入時讀一次） | 教師端解鎖後重整頁面 |
| Voice ID 聲音性別不對 | ElevenLabs voice 名稱看不出性別（l4Coq669 "Hope" 其實是女聲） | 先生成試聽檔給 Stephanie 確認再正式使用；內建男聲備選：Josh TxGEqnHWrfWFTfGW9XjX、Liam TX3LPaxmHKxFdv7VOQHJ、Chris iP95p4xoKVk53GoZ742B |
| API key 無法列出 voices (401) | key 只有 TTS 權限 | 直接用內建 premade voice ID 測試即可 |

---

## 9. 部署流程

1. 修改 `index.html`
2. 如有新音檔，放入對應 `audio/W{N}/` 資料夾
3. Git commit & push 到 `stephanie0223-sketch/shadowing-english` 的 main branch
4. GitHub Pages 自動部署

---

## 10. Script 撰寫規範（Claude 每週寫對話 script 時遵守）

> **NotebookLM 已於 W10 起廢棄**（生成品質不穩定）。現在由 Claude 直接寫 script，再用 ElevenLabs 配音。以下規範改編自原 NotebookLM prompt，是寫 script 時的標準：

1. **長度**: 約 1.5-2 分鐘，30-38 句短對話，兩位角色（Mia 女／Leo 男，或依主題換名字但保持一女一男）
2. **對話流暢**: 每句都要回應上一句；單一主線：共同經驗 → 提問 → 分享習慣 → 給建議 → 鼓勵收尾；避免同一小主題連續太多 turn（顯得不自然，Stephanie 會抓）
3. **難度**: B1、每句 12 字內、不用 4 音節以上的字、不用學術用語
4. **目標片語**: 8-12 個全數自然融入，每個片語所在句子的情境要清楚好記
5. **語speaking風格**: 縮寫（I'm, gotta, wanna）、自然反應（"No way!", "Wait, seriously?"）、discourse markers（Well, Actually, I mean）
6. **語調特徵（最重要）**: 連音（grab‿a）、至少 2 個 Wh-/選擇疑問句、至少 1 個驚訝反應、至少 1 個鼓勵語句、強調重音（"So you DO like..."）、情緒多變
7. **8 句 key sentences 事先設計**: 5-15 字、獨立可理解；寫 script 時就規劃好哪 8 句，不是事後撿
   - **Prosody 優先（Stephanie 2026-09 明確要求）**: 挑語調豐富的句子（感嘆、重複強調、不敢置信問句、選擇疑問 ↗↘、回聲問句＋轉折、慌張感），**不挑語調平淡的公式句**（如 "I always say half sugar, less ice" 這種口訣句）——平淡但重要的片語放字彙表用 🔊 學發音即可
   - 一句可以不含目標片語，只要語調練習價值高（vocab 設 null）
   - **Mia / Leo 各約 4 句**，男女聲平均，學生可選擇模仿的角色
8. **有趣**: 包含一個笑點；結尾輕鬆（如 "Next time it's on me!"）
9. **禁止**: "Welcome to..." 開頭、解釋文法、教科書腔、中文
10. **產出後**: 先給 Stephanie 過目，逐句修改到定稿才生成音檔；她常見的修改包括增加主題相關實用句（如點餐的客製化說法）、刪掉不自然的 turn

---

## 11. 每週動畫影片生成（generate_week_video.py）

每週教材可產一支動畫練習影片（給 YouTube／課堂播放）。W11 起為固定步驟。

### 影片結構（總長約 3.5-4 分鐘）

1. **對話段**：完整 podcast 播放，畫面為品牌頂欄＋週次標題＋兩個卡通頭像（**不顯示 Mia/Leo 名字**，只用顏色區分：粉=女、藍=男）；說話者頭像跳動＋外圈高亮；底部白框逐句字幕（時間依句子字元數比例估算）；底部森林綠進度條
2. **停 3 秒**（Stephanie 要求：過場不能跟內容黏在一起）
3. **過場**：播 `assets/shadow_transition.mp3`（"Now, let's shadow these sentences. Listen, and repeat during the pause."，Mia 女聲，可重複使用不用重生成）；畫面純文字置中，**不放 emoji**
4. **Shadowing 練習段**：8 句逐句進行——
   - 播句子（畫面：Sentence N / 8＋白框句子＋"Listen..."）
   - **留 10 秒空白**讓學生開口練習（畫面："Your turn! Say it out loud!"＋倒數進度條）
   - 練習段用真實音檔長度計時，字幕完全同步

### 操作步驟

1. 更新 `generate_week_video.py` 頂部的 `WEEK`、`TITLE`、`DIALOGUE`、`KEY_SENTENCES`（跟 `generate_week_audio.py` 內容一致）
2. `python generate_week_video.py` → 輸出 `videos/W{N}_{Title}.mp4`（720p、~3.5MB）
3. `videos/` 已 gitignore，影片用 SendUserFile 直接傳給 Stephanie，不進 repo

### 設計規範

- **品牌色：森林綠 #5d9b76**（RGB 93,155,118；Stephanie 2026-09 定案）；背景 #f6faf7、淺色點綴 #e3efe7
- 字型用 Windows Arial／Arial Bold；**絕不放 emoji**（Arial 不支援會變空方框，🎯🔊🎤 都踩過雷）
- 依賴：`pip install moviepy imageio-ffmpeg pillow numpy`（moviepy 2.x API：`with_audio`/`with_fps`）
- 影片中 8 句文字若有修改（如拿掉 "Ha!"），app 的 keySentences 和跟讀音檔**必須同步改**，Azure 評分才對得上

---

## 12. 重要注意事項

- **不要使用瀏覽器 TTS**: 所有音檔必須來自 ElevenLabs，`speechSynthesis` 已完全移除
- **單一檔案架構**: 所有程式碼都在 index.html 中，不要拆成多個檔案
- **即時同步**: 教師端三個 tab 都使用 `listenAllScores()` + `onSnapshot`，配合 `useEffect` cleanup
- **音檔驗證**: 生成後必須確認 >1KB，0 byte 檔案無法播放
- **Firebase Hosting vs GitHub Pages**: 網站部署在 GitHub Pages，不是 Firebase Hosting
