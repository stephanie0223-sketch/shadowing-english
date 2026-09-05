# CLAUDE.md — Shadowing English 專案指南

> 完整技術細節在 `.claude/skills/shadowing-english-app/SKILL.md`（會自動觸發載入）。
> 本檔是快速導覽；兩邊如有出入，以 SKILL.md 為準並同步修正。

## 1. 這個專案在做什麼、目前進度

**Shadowing English 生活英語跟讀練習** — 給台灣高中生（B1-B2）的口說訓練 web app。
每週一個生活主題：聽 podcast 對話 → 學字彙（可點 🔊 聽發音）→ 理解測驗 → 跟讀 8 句精選句（錄音後 Azure AI 評分：發音 30%＋完整度 30%＋語調 40%）。

- 部署：GitHub Pages `stephanie0223-sketch.github.io/shadowing-english/`（repo: `stephanie0223-sketch/shadowing-english`，push main 即自動部署）
- **進度：W1-W12 完成**（共規劃 27 週，一學期 9 週 × 3 學期）。W13-W27 主題已定案，見 `.claude/skills/shadowing-english-app/references/current-weeks.md`
- 下一週：**W13 Showing Taiwan to Foreigners（介紹台灣）**
- 使用班級：電機二忠（36 人）、電機適性分組（20 人＋第 21 位「老師測試」= Stephanie 的測試帳號）

## 2. 已確定的決定與規範

### 技術選擇
- **單一檔案架構**：整個 app 就是一個 `index.html`（React 18 CDN + Babel + Tailwind CDN），不拆檔
- Firebase Auth（Google 登入）+ Firestore（成績/設定/綁定）；Azure Speech 評分；ElevenLabs 配音
- **不用瀏覽器 TTS**（已廢棄）；**不用 NotebookLM**（W10 起廢棄，改 Claude 寫 script + ElevenLabs）
- **W1-W9 的完整 podcast 保留 NotebookLM 版本不重做**（Stephanie 決定）

### 聲音與音訊（Stephanie 聽感校正定案）
- Mia 女聲 `DODLEQrClDo8wCz460ld`／Leo 男聲 Josh `TxGEqnHWrfWFTfGW9XjX`
- 響度：Mia 單句 -16 LUFS、**Leo 單句 -12 LUFS**（+4dB 才聽感平衡）；podcast 先 `dynaudnorm=f=150:g=11:m=12` 再 loudnorm -15
- 生成腳本已內建自動標準化，不需手動處理

### 命名慣例
- 跟讀句：`audio/W{N}/W{N}_S1~S8.mp3`；字彙發音：`W{N}_V{id}.mp3`；完整 podcast：W10+ `W{N}_full.mp3`、W1-W9 根目錄 `W{N}/W{N}_full.m4a`
- 影片：`videos/W{N}_{Title}.mp4`（gitignore，不進 repo）

### 教材風格
- Script：B1、每句 ≤12 字、30-38 句、片語 8-12 個全融入、有笑點；先給 Stephanie 過目再生成
- **8 句跟讀 Prosody 優先**：挑語調豐富句（感嘆/重複強調/回聲問句/選擇疑問/強調重音），不挑平淡公式句；Mia/Leo 各約 4 句
- 影片品牌色：**森林綠 #5d9b76**；影片內**禁用 emoji**（Arial 會變空方框）；不顯示角色名字；片尾 shadowing 練習段每句留 10 秒

## 3. 已知問題／未解決事項

- **瀏覽器快取**：部署後常看到舊頁面/聽到舊音檔 → 必提醒 Ctrl+Shift+R；判斷前先 curl 線上檔案確認
- **週次鎖定狀態只在頁面載入時讀取**：教師解鎖後學生要重整才看得到（可考慮改 onSnapshot）
- **影片對話段字幕是按句長比例估時**，個別句切換點可能差 0.5-1 秒（練習段是精準的）；未來可用語音辨識對時
- Firestore 安全規則是全開放（`allow read, write: if true`）——教學用途可接受，但 key 都在前端，勿存敏感資料
- Azure Speech 免費層 5 小時/月：兩班全用起來接近上限，超過會停止評分（F0）或計費（S0），開學後留意

## 4. 下一步（優先順序）

1. **W13: Showing Taiwan to Foreigners** — 說「做 W13」即啟動全自動 pipeline
2. 依序完成 Semester 2（W14 Night Market → W15 Public Transport → W16 Dieting & Working Out → W17 Social Media Drama → W18 Learning New Skills）
3. Semester 3（W19-W27）：主題清單見 current-weeks.md
4. （低優先）影片字幕精準對時；週次解鎖即時同步；學期正式開始前清除「老師測試」的測試成績

## 5. 重要檔案地圖

| 檔案/資料夾 | 負責什麼 |
|---|---|
| `index.html` | 整個 web app（COURSE_DATA 課程資料 + 全部 React 元件）。新增週次只動 COURSE_DATA |
| `generate_week_audio.py` | 每週音檔 pipeline：改 `WEEK`/`DIALOGUE`/`KEY_SENTENCES` 後執行 → 雙聲 podcast + 8 句跟讀（自動響度平衡） |
| `generate_vocab_audio.py` | 字彙發音：自動解析 index.html 的 vocabulary → `W{N}_V{id}.mp3`（先寫好 COURSE_DATA 再跑） |
| `generate_week_video.py` | 每週動畫影片：同步 `WEEK`/`TITLE`/`DIALOGUE`/`KEY_SENTENCES` 後執行 → `videos/` |
| `assets/shadow_transition.mp3` | 影片共用過場口白（不用重生成） |
| `audio/W{N}/` | 各週音檔（網站直接引用） |
| `W1/~W9/`（根目錄） | NotebookLM 時期完整 podcast m4a（app 仍引用，勿刪勿改） |
| `archive/` | 封存區（gitignore）：NotebookLM 文件/原始檔、舊原型、legacy 工具 |
| `.claude/skills/shadowing-english-app/` | 完整專案 skill：SKILL.md（技術+SOP）、current-weeks.md（27 週規劃+各週內容）、student-roster.md（學生名單） |

## 每週新增流程（速記）

1. Claude 寫 script → Stephanie 過目定稿
2. `generate_week_audio.py`（改週次資料後跑）
3. 更新 `index.html` COURSE_DATA
4. `generate_vocab_audio.py`
5. `generate_week_video.py` → SendUserFile 傳影片
6. git commit + push → 提醒強制重整 → Stephanie 用「老師測試」驗收 → 教師端解鎖
