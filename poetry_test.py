from flask import Flask, render_template_string, jsonify, request
import random
import json
import os

app = Flask(__name__)

# ===== 数据加载 =====
def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

BASE = os.path.dirname(__file__)
tang_path = os.path.join(BASE, "data", "chinese-poetry-master", "全唐诗", "唐诗三百首.json")
song_path = os.path.join(BASE, "data", "chinese-poetry-master", "宋词", "宋词三百首.json")
yun_path = os.path.join(BASE, "zhonghua_xinyun.json")

try:
    tang_list = load_json(tang_path)
except:
    tang_list = [{"title": "示例诗", "author": "佚名", "paragraphs": ["山高月小", "水落石出"]}]

try:
    song_list = load_json(song_path)
except:
    song_list = [{"title": "示例词", "author": "佚名", "paragraphs": ["春风又绿江南岸", "明月何时照我还"]}]

# 加载韵部数据
try:
    yunbu_data = load_json(yun_path)
except Exception as e:
    print("韵部文件加载失败:", e)
    yunbu_data = {}

# ===== 悬浮搜索框组件 =====
floating_search_html = '''
<div id="floating-search" style="
    position: fixed;
    top: 20px;
    right: 20px;
    width: 300px;
    background: white;
    border: 2px solid #007BFF;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    padding: 15px;
    font-family: 'KaiTi', 'SimSun', serif;
    z-index: 1000;
    transition: transform 0.2s;
    display: none; /* 默认隐藏 */
">
    <div style="text-align: right; margin-bottom: 8px;">
        <span id="floating-search-close" style="
            color: #999;
            cursor: pointer;
            font-weight: bold;
            font-size: 1.2em;
        ">&times;</span>
    </div>
    <h3 style="margin: 0 0 10px 0; font-size: 1em; color: #333;">查韵部</h3>
    <input type="text" id="yun-input" maxlength="1" placeholder="输入一个字"
        style="
            width: 100%;
            padding: 8px;
            font-size: 1.1em;
            font-family: 'KaiTi', 'SimSun', serif;
            border: 1px solid #ccc;
            border-radius: 6px;
            box-sizing: border-box;
        "/>
    <div id="yun-result" style="
        margin-top: 10px;
        font-size: 0.95em;
        line-height: 1.5;
        color: #333;
        min-height: 20px;
        max-height: 200px;
        overflow-y: auto;
    "></div>
</div>

<!-- 打开浮动搜索的按钮 -->
<button id="open-floating-search" style="
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 10px 20px;
    background-color: #007BFF;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1em;
">打开查韵部</button>

<script>
// 获取元素
const floatingSearch = document.getElementById('floating-search');
const closeBtn = document.getElementById('floating-search-close');
const openBtn = document.getElementById('open-floating-search');

// 输入框逻辑
const input = document.getElementById('yun-input');
const result = document.getElementById('yun-result');

// 关闭按钮点击事件
closeBtn.onclick = () => {
    floatingSearch.style.display = 'none';
};

// 打开按钮点击事件
openBtn.onclick = () => {
    floatingSearch.style.display = 'block';
};

// 输入框监听
input.addEventListener('input', function() {
    const char = this.value.trim();
    if (char.length !== 1) {
        result.innerHTML = '';
        return;
    }

    fetch(`/api/search_yun?char=${encodeURIComponent(char)}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                result.innerHTML = `<span style="color: #e63946">${data.error}</span>`;
            } else {
                result.innerHTML = `
                    <strong style="color: #007BFF;">${data.yun}</strong><br>
                    ${data.zi.map(z => `<span style="margin: 2px 4px;">${z}</span>`).join('')}
                `;
            }
        })
        .catch(err => {
            result.innerHTML = '<span style="color: #e63946;">查询失败</span>';
            console.error(err);
        });
});
</script>
'''

# ===== 首页 HTML =====
html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>唐诗 / 宋词 随机展示</title>
    <style>
        body { 
            font-family: "KaiTi", "SimSun", serif; 
            text-align: center; 
            margin-top: 80px; 
            background-color: #f9f7f3;
        }
        #title { font-size: 2em; margin-bottom: 10px; color: #333; }
        #author { font-size: 1.2em; margin-bottom: 20px; color: gray; }
        #content { white-space: pre-line; font-size: 1.5em; line-height: 2em; }
        button { 
            font-size: 1.2em; 
            padding: 8px 16px; 
            margin: 10px; 
            cursor: pointer; 
            border: 2px solid #007BFF;
            border-radius: 8px;
            background: white;
            color: #007BFF;
        }
        button:hover { background: #007BFF; color: white; }
    </style>
</head>
<body>
    <h1>随机唐诗 / 宋词</h1>
    <button onclick="fetchPoem('tang')">唐诗</button>
    <button onclick="fetchPoem('song')">宋词</button>
    <button onclick="window.location.href='/compose/tang'">填诗</button>
    <button onclick="window.location.href='/compose/song'">填词</button>

    <div id="title"></div>
    <div id="author"></div>
    <div id="content">点击按钮以获取诗词</div>

    <script>
    function fetchPoem(type) {
        fetch('/poem/' + type)
        .then(resp => resp.json())
        .then(data => {
            document.getElementById('title').innerText = data.title;
            document.getElementById('author').innerText = data.author;
            document.getElementById('content').innerText = data.content;
        });
    }
    </script>
</body>
</html>
"""

# ===== 填诗选择页 =====
compose_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>选择诗歌体裁</title>
    <style>
        body { 
            font-family: "KaiTi", "SimSun", serif; 
            text-align: center; 
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
            min-height: 100vh;
        }
        h1 { color: #2c3e50; margin: 30px 0 20px; }
        .options {
            max-width: 500px;
            margin: 30px auto;
        }
        .option-btn {
            display: block;
            width: 100%;
            padding: 16px;
            margin: 10px 0;
            font-size: 1.4em;
            cursor: pointer;
            border: 2px solid #2c3e50;
            border-radius: 10px;
            background-color: white;
            color: #2c3e50;
            transition: all 0.3s;
            text-decoration: none;
        }
        .option-btn:hover {
            background-color: #2c3e50;
            color: white;
        }
        .back-btn {
            margin-top: 30px;
            padding: 10px 20px;
            font-size: 1em;
            color: #007BFF;
            border: 1px solid #007BFF;
            border-radius: 6px;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <h1>请选择要创作的诗歌体裁</h1>
    <div class="options">
        <a href="/compose/tang/wuyan-jueju" class="option-btn">五言绝句</a>
        <a href="/compose/tang/wuyan-lvshi" class="option-btn">五言律诗</a>
        <a href="/compose/tang/qiyan-jueju" class="option-btn">七言绝句</a>
        <a href="/compose/tang/qiyan-lvshi" class="option-btn">七言律诗</a>
    </div>
    <a href="javascript:window.history.back()" class="back-btn">← 返回</a>
</body>
</html>
"""


# ===== 五言律诗 =====
wuyan_lvshi_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>创作五言律诗</title>
    <style>
        body { 
            font-family: "KaiTi", "SimSun", serif; 
            text-align: center; 
            margin: 0;
            padding: 20px 10px;
            background-color: #f7f4ed;
            color: #333;
            min-height: 100vh;
        }
        h1 { 
            font-size: 1.8em; 
            color: #2c3e50; 
            margin: 20px 0;
        }
        .tone-select {
            font-size: 1em;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #aaa;
            background: white;
            margin-bottom: 20px;
            width: 90%;
            max-width: 300px;
        }
        .tone-unit.correct {
            color: #28a745 !important;
        }
        .tone-unit.wrong {
            color: #e63946 !important;
        }
        .title-input {
            width: 90%;
            max-width: 300px;
            padding: 12px;
            margin: 20px auto;
            font-size: 1.2em;
            font-family: "KaiTi", "SimSun", serif;
            border: 2px solid #ddd;
            border-radius: 8px;
            text-align: center;
            display: block;
        }
        .poem-form {
            max-width: 600px;
            margin: 20px auto;
            padding: 0 10px;
        }
        .line-group {
            margin-bottom: 15px;
        }
        .couplet-vertical {
            display: flex;
            flex-direction: column;
            gap: 10px;
            align-items: center;
        }
        .input-container {
            position: relative;
            width: 100%;
            max-width: 300px;
        }
        .input-container input {
            width: 100%;
            padding: 12px;
            font-size: 1.3em;
            font-family: "KaiTi", "SimSun", serif;
            border: 2px solid #ddd;
            border-radius: 8px;
            background: white;
            text-align: center;
        }
        .input-container input:focus {
            outline: none;
            border-color: #007BFF;
            box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
        }
        .tone-hint {
            margin-top: 6px;
            font-size: 0.9em;
            letter-spacing: 8px;
            user-select: none;
            display: flex;
            justify-content: center;
            gap: 6px;
        }
        .tone-unit {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            border: 1px solid currentColor;
            box-sizing: border-box;
        }
        .tone-unit.ping {
            border-width: 2px;
            background: transparent;
        }
        .tone-unit.ze {
            background: currentColor;
        }
        .tone-unit.blue {
            color: #007BFF !important;
        }
        .tone-unit.orange {
            color: #FF8000 !important;
        }
        .submit-btn {
            margin: 30px auto;
            padding: 12px 30px;
            font-size: 1.2em;
            background-color: #2c3e50;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .submit-btn:active {
            transform: translateY(1px);
        }
        .back-btn {
            display: inline-block;
            margin-top: 20px;
            padding: 8px 16px;
            font-size: 1em;
            color: #007BFF;
            border: 1px solid #007BFF;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
        }

        /* 移动端适配 */
        @media (max-width: 480px) {
            h1 { font-size: 1.5em; }
            .title-input, 
            .input-container input,
            .tone-select {
                max-width: 280px;
                font-size: 1.1em;
                padding: 10px;
            }
            .tone-hint { 
                gap: 4px;
                letter-spacing: normal;
            }
            .tone-unit {
                width: 10px;
                height: 10px;
            }
            .submit-btn { 
                font-size: 1.1em; 
                padding: 10px 20px; 
            }
        }
    </style>
</head>
<body>
    <h1>创作五言律诗</h1>
    <select class="tone-select" id="tone" onchange="updateTone(this.value)">
        <option value="">请选择平仄格式</option>
        <option value="pingqi_buru">平起首句不入韵式</option>
        <option value="pingqi_ru">平起首句入韵式</option>
        <option value="zeqi_buru">仄起首句不入韵式</option>
        <option value="zeqi_ru">仄起首句入韵式</option>
    </select>

    <input type="text" class="title-input" id="title" placeholder="请输入诗题">

    <form class="poem-form" onsubmit="alert('提交功能暂未实现'); return false;">
        <!-- 第一联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line1" placeholder="五言诗句">
                    <div class="tone-hint" id="hint1"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line2" placeholder="五言诗句">
                    <div class="tone-hint" id="hint2"></div>
                </div>
            </div>
        </div>

        <!-- 第二联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line3" placeholder="五言诗句">
                    <div class="tone-hint" id="hint3"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line4" placeholder="五言诗句">
                    <div class="tone-hint" id="hint4"></div>
                </div>
            </div>
        </div>

        <!-- 第三联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line5" placeholder="五言诗句">
                    <div class="tone-hint" id="hint5"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line6" placeholder="五言诗句">
                    <div class="tone-hint" id="hint6"></div>
                </div>
            </div>
        </div>

        <!-- 第四联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line7" placeholder="五言诗句">
                    <div class="tone-hint" id="hint7"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line8" placeholder="五言诗句">
                    <div class="tone-hint" id="hint8"></div>
                </div>
            </div>
        </div>

        <button type="submit" class="submit-btn">完成创作</button>
    </form>

    <a href="javascript:window.history.back()" class="back-btn">← 返回</a>

<script>
    // 声明 toneData，初始为空
    let toneData = {};

    const templates = {
        pingqi_buru: [
            "─ ─ ○ │ │", "│ │ │ ─ ─",
            "│ │ ─ ─ │", "─ ─ │ │ ─",
            "─ ─ ○ │ │", "│ │ │ ─ ─",
            "│ │ ─ ─ │", "─ ─ │ │ ─"
        ],
        pingqi_ru: [
            "─ ─ │ │ ─", "│ │ │ ─ ─",
            "│ │ ─ ─ │", "─ ─ │ │ ─",
            "─ ─ ○ │ │", "│ │ │ ─ ─",
            "│ │ ─ ─ │", "─ ─ │ │ ─"
        ],
        zeqi_buru: [
            "│ │ │ ─ ─", "─ ─ ○ │ │",
            "─ ─ │ │ ─", "│ │ │ ─ ─",
            "│ │ ○ ─ ─", "─ ─ │ │ ─",
            "─ ─ │ │ ─", "│ │ │ ─ ─"
        ],
        zeqi_ru: [
            "│ │ │ ─ ─", "─ ─ │ │ ─",
            "─ ─ │ │ ─", "│ │ │ ─ ─",
            "│ │ ○ ─ ─", "─ ─ │ │ ─",
            "─ ─ │ │ ─", "│ │ │ ─ ─"
        ]
    };

    const rhymePositions = {
        pingqi_buru: [1, 3, 5, 7],
        pingqi_ru:   [0, 1, 3, 5, 7],
        zeqi_buru:   [1, 3, 5, 7],
        zeqi_ru:     [0, 1, 3, 5, 7]
    };

    // 从 char_tones.json 加载音调数据
    fetch('/static/char_tones.json')
         .then(r => {
             if (!r.ok) throw new Error('无法加载 char_tones.json');
             return r.json();
         })
         .then(data => {
             toneData = data;
             console.log('音调数据加载成功', toneData);
             // 数据加载后，绑定输入事件
             setupInputListeners();
         })
         .catch(err => {
             console.error('加载音调数据失败:', err);
             alert('音调数据加载失败，请检查 char_tones.json 是否存在且格式正确。');
         });

    // 平仄判断函数
    function getToneClass(char) {
        const tone = toneData[char];
        if (tone === 1 || tone === 2) return 'ping';
        if (tone === 3 || tone === 4) return 'ze';
        return null; // 未知字
    }

    // 获取结果提示元素
    function getResultHintEl(lineNum) {
        let resultHint = document.getElementById(`result-hint-${lineNum}`);
        if (!resultHint) {
            resultHint = document.createElement('div');
            resultHint.id = `result-hint-${lineNum}`;
            resultHint.className = 'result-hint';
            resultHint.style.cssText = `
                margin-top: 4px;
                font-size: 0.9em;
                letter-spacing: 6px;
                display: flex;
                justify-content: center;
                gap: 6px;
            `;
            document.getElementById(`hint${lineNum}`).after(resultHint);
        }
        return resultHint;
    }

    // 校验单行平仄
    function validateLine(lineNum) {
        const input = document.getElementById(`line${lineNum}`);
        const value = input.value.trim();
        const resultHint = getResultHintEl(lineNum);
        resultHint.innerHTML = '';

        if (value.length !== 5) {
            input.style.borderColor = '#e63946';
            input.style.boxShadow = '0 0 5px rgba(230, 57, 70, 0.3)';
            resultHint.textContent = '需五字';
            resultHint.style.color = '#e63946';
            return;
        } else {
            input.style.borderColor = '#28a745';
            input.style.boxShadow = '0 0 5px rgba(40, 167, 69, 0.2)';
        }

        const format = document.getElementById('tone').value;
        const expectedPattern = templates[format]?.[lineNum - 1];
        if (!expectedPattern) {
            resultHint.textContent = '请选择格式';
            resultHint.style.color = '#666';
            return;
        }

        const expectedTones = expectedPattern.split(' ').filter(c => c);
        const userTones = [];

        for (let i = 0; i < 5; i++) {
            const char = value[i];
            const toneClass = getToneClass(char);
            userTones.push(toneClass);
        }

        userTones.forEach((t, idx) => {
            const expected = expectedTones[idx];
            const isCorrect =
                expected === '○' ||                    // 可平可仄 → 不论平仄都对
                (t === 'ping' && expected === '─') ||  // 必须平 → 只能平
                (t === 'ze' && expected === '│');      // 必须仄 → 只能仄

            const unit = document.createElement('span');
            unit.className = 'tone-unit';

            if (t === 'ping') {
                unit.classList.add('ping');
            } else if (t === 'ze') {
                unit.classList.add('ze');
            } else {
                unit.classList.add('ping');
                unit.style.color = '#999';
                unit.style.borderColor = '#999';
            }

            if (t === 'ping' || t === 'ze') {
                unit.classList.add(isCorrect ? 'correct' : 'wrong');
            }

            resultHint.appendChild(unit);
        });
    }

    // 更新平仄提示模板
    function updateTone(format) {
        const patternLines = templates[format] || Array(8).fill("");
        const rhymePos = rhymePositions[format] || [];

        for (let i = 1; i <= 8; i++) {
            const hintEl = document.getElementById(`hint${i}`);
            hintEl.innerHTML = '';

            const pattern = patternLines[i-1];
            if (!pattern) continue;

            const chars = pattern.split(' ').filter(c => c);
            const lineEndIndex = chars.length - 1;

            chars.forEach((char, index) => {
                const unit = document.createElement('span');
                unit.className = 'tone-unit';

                const isRhyme = rhymePos.includes(i-1) && index === lineEndIndex;
                const isOptional = char === '○';

                if (char === '─' || char === '○') {
                    unit.classList.add('ping');
                } else if (char === '│') {
                    unit.classList.add('ze');
                }

                if (isOptional) {
                    unit.classList.add('blue');
                }
                if (isRhyme) {
                    unit.classList.add('orange');
                }

                hintEl.appendChild(unit);
            });
        }

        // 重新校验所有已输入的行
        for (let i = 1; i <= 8; i++) {
            const input = document.getElementById(`line${i}`);
            if (input.value.trim()) {
                validateLine(i);
            }
        }
    }

    // 绑定输入框事件
    function setupInputListeners() {
        for (let i = 1; i <= 8; i++) {
            const input = document.getElementById(`line${i}`);
            input.addEventListener('blur', () => {
                if (Object.keys(toneData).length > 0) {
                    validateLine(i);
                }
            });
        }
    }

    // 初始化
    updateTone("");
</script>
</body>
</html>
"""

# ===== 五言绝句（带平仄提示）=====
wuyan_jueju_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>创作五言绝句</title>
    <style>
        body { 
            font-family: "KaiTi", "SimSun", serif; 
            text-align: center; 
            margin: 0;
            padding: 20px 10px;
            background-color: #f7f4ed;
            color: #333;
            min-height: 100vh;
        }
        h1 { 
            font-size: 1.8em; 
            color: #2c3e50; 
            margin: 20px 0;
        }
        .tone-select {
            font-size: 1em;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #aaa;
            background: white;
            margin-bottom: 20px;
            width: 90%;
            max-width: 300px;
        }
        .tone-unit.correct {
            color: #28a745 !important;
        }
        .tone-unit.wrong {
            color: #e63946 !important;
        }
        .title-input {
            width: 90%;
            max-width: 300px;
            padding: 12px;
            margin: 20px auto;
            font-size: 1.2em;
            font-family: "KaiTi", "SimSun", serif;
            border: 2px solid #ddd;
            border-radius: 8px;
            text-align: center;
            display: block;
        }
        .poem-form {
            max-width: 600px;
            margin: 20px auto;
            padding: 0 10px;
        }
        .line-group {
            margin-bottom: 15px;
        }
        .couplet-vertical {
            display: flex;
            flex-direction: column;
            gap: 10px;
            align-items: center;
        }
        .input-container {
            position: relative;
            width: 100%;
            max-width: 300px;
        }
        .input-container input {
            width: 100%;
            padding: 12px;
            font-size: 1.3em;
            font-family: "KaiTi", "SimSun", serif;
            border: 2px solid #ddd;
            border-radius: 8px;
            background: white;
            text-align: center;
        }
        .input-container input:focus {
            outline: none;
            border-color: #007BFF;
            box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
        }
        .tone-hint {
            margin-top: 6px;
            font-size: 0.9em;
            letter-spacing: 8px;
            user-select: none;
            display: flex;
            justify-content: center;
            gap: 6px;
        }
        .tone-unit {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            border: 1px solid currentColor;
            box-sizing: border-box;
        }
        .tone-unit.ping {
            border-width: 2px;
            background: transparent;
        }
        .tone-unit.ze {
            background: currentColor;
        }
        .tone-unit.blue {
            color: #007BFF !important;
        }
        .tone-unit.orange {
            color: #FF8000 !important;
        }
        .submit-btn {
            margin: 30px auto;
            padding: 12px 30px;
            font-size: 1.2em;
            background-color: #2c3e50;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .submit-btn:active {
            transform: translateY(1px);
        }
        .back-btn {
            display: inline-block;
            margin-top: 20px;
            padding: 8px 16px;
            font-size: 1em;
            color: #007BFF;
            border: 1px solid #007BFF;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
        }

        /* 移动端适配 */
        @media (max-width: 480px) {
            h1 { font-size: 1.5em; }
            .title-input, 
            .input-container input,
            .tone-select {
                max-width: 280px;
                font-size: 1.1em;
                padding: 10px;
            }
            .tone-hint { 
                gap: 4px;
                letter-spacing: normal;
            }
            .tone-unit {
                width: 10px;
                height: 10px;
            }
            .submit-btn { 
                font-size: 1.1em; 
                padding: 10px 20px; 
            }
        }
    </style>
</head>
<body>
    <h1>创作五言绝句</h1>
    <select class="tone-select" id="tone" onchange="updateTone(this.value)">
        <option value="">请选择平仄格式</option>
        <option value="zeqi_buru">仄起首句不入韵式</option>
        <option value="zeqi_ru">仄起首句入韵式</option>
        <option value="pingqi_buru">平起首句不入韵式</option>
        <option value="pingqi_ru">平起首句入韵式</option>
    </select>

    <input type="text" class="title-input" id="title" placeholder="请输入诗题">

    <form class="poem-form" onsubmit="alert('提交功能暂未实现'); return false;">
        <!-- 第一联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line1" placeholder="五言诗句">
                    <div class="tone-hint" id="hint1"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line2" placeholder="五言诗句">
                    <div class="tone-hint" id="hint2"></div>
                </div>
            </div>
        </div>

        <!-- 第二联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line3" placeholder="五言诗句">
                    <div class="tone-hint" id="hint3"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line4" placeholder="五言诗句">
                    <div class="tone-hint" id="hint4"></div>
                </div>
            </div>
        </div>

        <button type="submit" class="submit-btn">完成创作</button>
    </form>

    <a href="javascript:window.history.back()" class="back-btn">← 返回</a>

<script>
    // 声明 toneData，初始为空
    let toneData = {};

    const templates = {
        pingqi_buru: ["─ ─ ○ │ │", "│ │ │ ─ ─", "│ │ ─ ─ │", "─ ─ │ │ ─"],
        pingqi_ru:   ["─ ─ │ │ ─", "│ │ │ ─ ─", "│ │ ─ ─ │", "─ ─ │ │ ─"],
        zeqi_buru:   ["│ │ │ ─ ─", "─ ─ ○ │ │", "─ ─ │ │ ─", "│ │ │ ─ ─"],
        zeqi_ru:     ["│ │ │ ─ ─", "─ ─ │ │ ─", "─ ─ │ │ ─", "│ │ │ ─ ─"]
    };

    const rhymePositions = {
        pingqi_buru: [1, 3],
        pingqi_ru:   [0, 1, 3],
        zeqi_buru:   [1, 3],
        zeqi_ru:     [0, 1, 2, 3]
    };

    // 从 tone.json 加载音调数据
    fetch('/static/char_tones.json')
         .then(r => {
             if (!r.ok) throw new Error('无法加载 char_tones.json');
             return r.json();
         })
         .then(data => {
             toneData = data;
            console.log('音调数据加载成功', toneData);
             // 数据加载后，重新绑定事件或恢复功能
             setupInputListeners();
         })
         .catch(err => {
             console.error('加载音调数据失败:', err);
             alert('音调数据加载失败，请检查 char_tones.json 是否存在且格式正确。');
         });

    // 平仄判断函数
    function getToneClass(char) {
        const tone = toneData[char];
        if (tone === 1 || tone === 2) return 'ping';
        if (tone === 3 || tone === 4) return 'ze';
        return null; // 未知字
    }

    // 校验逻辑（与之前一致）
function validateLine(lineNum) {
    const input = document.getElementById(`line${lineNum}`);
    const value = input.value.trim();
    const resultHint = getResultHintEl(lineNum);
    resultHint.innerHTML = '';

    if (value.length !== 5) {
        input.style.borderColor = '#e63946';
        input.style.boxShadow = '0 0 5px rgba(230, 57, 70, 0.3)';
        resultHint.textContent = '需五字';
        resultHint.style.color = '#e63946';
        return;
    } else {
        input.style.borderColor = '#28a745';
        input.style.boxShadow = '0 0 5px rgba(40, 167, 69, 0.2)';
    }

    const format = document.getElementById('tone').value;
    const expectedPattern = templates[format]?.[lineNum - 1];
    if (!expectedPattern) {
        resultHint.textContent = '请选择格式';
        resultHint.style.color = '#666';
        return;
    }

    const expectedTones = expectedPattern.split(' ').filter(c => c);
    const userTones = [];

    for (let i = 0; i < 5; i++) {
        const char = value[i];
        const toneClass = getToneClass(char);
        userTones.push(toneClass);
    }

    userTones.forEach((t, idx) => {
        const expected = expectedTones[idx];
        const isCorrect =
            expected === '○' ||                    // 可平可仄 → 不论平仄都对
            (t === 'ping' && expected === '─') ||  // 必须平 → 只能平
            (t === 'ze' && expected === '│');      // 必须仄 → 只能仄

        const unit = document.createElement('span');
        unit.className = 'tone-unit';

        if (t === 'ping') {
            unit.classList.add('ping');
        } else if (t === 'ze') {
            unit.classList.add('ze');
        } else {
            unit.classList.add('ping');
            unit.style.color = '#999';
            unit.style.borderColor = '#999';
        }

        if (t === 'ping' || t === 'ze') {
            unit.classList.add(isCorrect ? 'correct' : 'wrong');
        }

        resultHint.appendChild(unit);
    });
}

    function getResultHintEl(lineNum) {
        let resultHint = document.getElementById(`result-hint-${lineNum}`);
        if (!resultHint) {
            resultHint = document.createElement('div');
            resultHint.id = `result-hint-${lineNum}`;
            resultHint.className = 'result-hint';
            resultHint.style.cssText = `
                margin-top: 4px;
                font-size: 0.9em;
                letter-spacing: 6px;
                display: flex;
                justify-content: center;
                gap: 6px;
            `;
            document.getElementById(`hint${lineNum}`).after(resultHint);
        }
        return resultHint;
    }

    function updateTone(format) {
        const patternLines = templates[format] || ["", "", "", ""];
        const rhymePos = rhymePositions[format] || [];

        for (let i = 1; i <= 4; i++) {
            const hintEl = document.getElementById(`hint${i}`);
            hintEl.innerHTML = '';

            const pattern = patternLines[i-1];
            if (!pattern) continue;

            const chars = pattern.split(' ').filter(c => c);
            const lineEndIndex = chars.length - 1;

            chars.forEach((char, index) => {
                const unit = document.createElement('span');
                unit.className = 'tone-unit';

                const isRhyme = rhymePos.includes(i-1) && index === lineEndIndex;
                const isOptional = char === '○';

                if (char === '─' || char === '○') {
                    unit.classList.add('ping');
                } else if (char === '│') {
                    unit.classList.add('ze');
                }

                if (isOptional) {
                    unit.classList.add('blue');
                }
                if (isRhyme) {
                    unit.classList.add('orange');
                }

                hintEl.appendChild(unit);
            });
        }

        for (let i = 1; i <= 4; i++) {
            const input = document.getElementById(`line${i}`);
            if (input.value.trim()) {
                validateLine(i);
            }
        }
    }

    // 绑定输入框事件（在数据加载完成后调用）
    function setupInputListeners() {
        for (let i = 1; i <= 4; i++) {
            const input = document.getElementById(`line${i}`);
            input.addEventListener('blur', () => {
                if (Object.keys(toneData).length > 0) { // 确保数据已加载
                    validateLine(i);
                }
            });
        }
    }

    // 初始化
    updateTone("");
</script>
</body>
</html>
"""


# ===== 七言绝句 =====
qiyan_jueju_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>创作七言绝句</title>
    <style>
        body { 
            font-family: "KaiTi", "SimSun", serif; 
            text-align: center; 
            margin: 0;
            padding: 20px 10px;
            background-color: #f7f4ed;
            color: #333;
            min-height: 100vh;
        }
        h1 { 
            font-size: 1.8em; 
            color: #2c3e50; 
            margin: 20px 0;
        }
        .tone-select {
            font-size: 1em;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #aaa;
            background: white;
            margin-bottom: 20px;
            width: 90%;
            max-width: 300px;
        }
        .tone-unit.correct {
            color: #28a745 !important;
        }
        .tone-unit.wrong {
            color: #e63946 !important;
        }
        .title-input {
            width: 90%;
            max-width: 300px;
            padding: 12px;
            margin: 20px auto;
            font-size: 1.2em;
            font-family: "KaiTi", "SimSun", serif;
            border: 2px solid #ddd;
            border-radius: 8px;
            text-align: center;
            display: block;
        }
        .poem-form {
            max-width: 600px;
            margin: 20px auto;
            padding: 0 10px;
        }
        .line-group {
            margin-bottom: 15px;
        }
        .couplet-vertical {
            display: flex;
            flex-direction: column;
            gap: 10px;
            align-items: center;
        }
        .input-container {
            position: relative;
            width: 100%;
            max-width: 300px;
        }
        .input-container input {
            width: 100%;
            padding: 12px;
            font-size: 1.3em;
            font-family: "KaiTi", "SimSun", serif;
            border: 2px solid #ddd;
            border-radius: 8px;
            background: white;
            text-align: center;
        }
        .input-container input:focus {
            outline: none;
            border-color: #007BFF;
            box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
        }
        .tone-hint {
            margin-top: 6px;
            font-size: 0.9em;
            letter-spacing: 8px;
            user-select: none;
            display: flex;
            justify-content: center;
            gap: 6px;
        }
        .tone-unit {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            border: 1px solid currentColor;
            box-sizing: border-box;
        }
        .tone-unit.ping {
            border-width: 2px;
            background: transparent;
        }
        .tone-unit.ze {
            background: currentColor;
        }
        .tone-unit.blue {
            color: #007BFF !important;
        }
        .tone-unit.orange {
            color: #FF8000 !important;
        }
        .submit-btn {
            margin: 30px auto;
            padding: 12px 30px;
            font-size: 1.2em;
            background-color: #2c3e50;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .submit-btn:active {
            transform: translateY(1px);
        }
        .back-btn {
            display: inline-block;
            margin-top: 20px;
            padding: 8px 16px;
            font-size: 1em;
            color: #007BFF;
            border: 1px solid #007BFF;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
        }

        @media (max-width: 480px) {
            h1 { font-size: 1.5em; }
            .title-input, 
            .input-container input,
            .tone-select {
                max-width: 280px;
                font-size: 1.1em;
                padding: 10px;
            }
            .tone-hint { 
                gap: 4px;
                letter-spacing: normal;
            }
            .tone-unit {
                width: 10px;
                height: 10px;
            }
            .submit-btn { 
                font-size: 1.1em; 
                padding: 10px 20px; 
            }
        }
    </style>
</head>
<body>
    <h1>创作七言绝句</h1>
    <select class="tone-select" id="tone" onchange="updateTone(this.value)">
        <option value="">请选择平仄格式</option>
        <option value="pingqi_buru">平起首句不入韵式</option>
        <option value="pingqi_ru">平起首句入韵式</option>
        <option value="zeqi_buru">仄起首句不入韵式</option>
        <option value="zeqi_ru">仄起首句入韵式</option>
    </select>

    <input type="text" class="title-input" id="title" placeholder="请输入诗题">

    <form class="poem-form" onsubmit="alert('提交功能暂未实现'); return false;">
        <!-- 第一联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line1" placeholder="七言诗句">
                    <div class="tone-hint" id="hint1"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line2" placeholder="七言诗句">
                    <div class="tone-hint" id="hint2"></div>
                </div>
            </div>
        </div>

        <!-- 第二联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line3" placeholder="七言诗句">
                    <div class="tone-hint" id="hint3"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line4" placeholder="七言诗句">
                    <div class="tone-hint" id="hint4"></div>
                </div>
            </div>
        </div>

        <button type="submit" class="submit-btn">完成创作</button>
    </form>

    <a href="javascript:window.history.back()" class="back-btn">← 返回</a>

    <script>
        // 声明 toneData，用于存储汉字音调
        let toneData = {};

        // 七言绝句平仄模板
        const templates = {
    pingqi_buru: [
        "─ ─ │ │ ─ ─ │",  // 平平仄仄平平仄
        "│ │ ─ ─ │ │ ─",  // 仄仄平平仄仄平
        "│ │ ─ ─ ─ │ │",  // 仄仄平平平仄仄
        "─ ─ │ │ │ ─ ─"   // 平平仄仄仄平平
    ],
    pingqi_ru: [
        "─ ─ │ │ │ ─ ─",  // 平平仄仄仄平平
        "│ │ ─ ─ │ │ ─",  // 仄仄平平仄仄平
        "│ │ ─ ─ ─ │ │",  // 仄仄平平平仄仄
        "─ ─ │ │ │ ─ ─"   // 平平仄仄仄平平
    ],
    zeqi_buru: [
        "│ │ ─ ─ │ │ ─",  // 仄仄平平仄仄平
        "─ ─ │ │ ─ ─ │",  // 平平仄仄平平仄
        "─ ─ │ │ ─ │ │",  // 平平仄仄平仄仄
        "│ │ ─ ─ │ │ ─"   // 仄仄平平仄仄平
    ],
    zeqi_ru: [
        "│ │ ─ ─ ─ │ │",  // 仄仄平平平仄仄
        "─ ─ │ │ │ ─ ─",  // 平平仄仄仄平平
        "─ ─ │ │ ─ │ │",  // 平平仄仄平仄仄
        "│ │ ─ ─ │ │ ─"   // 仄仄平平仄仄平
    ]
};

        // 押韵位置（行号索引 + 末字位置）
        const rhymePositions = {
            pingqi_buru: [1, 3],
            pingqi_ru:   [0, 1, 3],
            zeqi_buru:   [1, 3],
            zeqi_ru:     [0, 1, 3]
        };

        // 从 char_tones.json 加载音调数据
        fetch('/static/char_tones.json')
            .then(r => {
                if (!r.ok) throw new Error('无法加载 char_tones.json');
                return r.json();
            })
            .then(data => {
                toneData = data;
                console.log('音调数据加载成功', Object.keys(data).length + ' 个汉字');
                setupInputListeners(); // 数据加载成功后绑定输入事件
            })
            .catch(err => {
                console.error('加载音调数据失败:', err);
                alert('音调数据加载失败，请检查 /static/char_tones.json 是否存在且格式正确。');
            });

        // 获取单个字的平仄类型
        function getToneClass(char) {
            const tone = toneData[char];
            if (tone === 1 || tone === 2) return 'ping'; // 平声
            if (tone === 3 || tone === 4) return 'ze';  // 仄声
            return null; // 未知字
        }

        // 校验某一行诗句是否符合格式
        function validateLine(lineNum) {
            const input = document.getElementById(`line${lineNum}`);
            const value = input.value.trim();
            const resultHint = getResultHintEl(lineNum);
            resultHint.innerHTML = '';

            if (value.length !== 7) {
                input.style.borderColor = '#e63946';
                input.style.boxShadow = '0 0 5px rgba(230, 57, 70, 0.3)';
                resultHint.textContent = '需七字';
                resultHint.style.color = '#e63946';
                return;
            } else {
                input.style.borderColor = '#28a745';
                input.style.boxShadow = '0 0 5px rgba(40, 167, 69, 0.2)';
            }

            const format = document.getElementById('tone').value;
            const expectedPattern = templates[format]?.[lineNum - 1];
            if (!expectedPattern) {
                resultHint.textContent = '请选择格式';
                resultHint.style.color = '#666';
                return;
            }

            const expectedTones = expectedPattern.split(' ').filter(c => c);
            const userTones = [];

            for (let i = 0; i < 7; i++) {
                const char = value[i];
                const toneClass = getToneClass(char);
                userTones.push(toneClass);
            }

            userTones.forEach((t, idx) => {
                const expected = expectedTones[idx];
                const isCorrect =
                    expected === '○' ||                    // 可平可仄 → 正确
                    (t === 'ping' && expected === '─') ||  // 平对平
                    (t === 'ze' && expected === '│');      // 仄对仄

                const unit = document.createElement('span');
                unit.className = 'tone-unit';

                if (t === 'ping') {
                    unit.classList.add('ping');
                } else if (t === 'ze') {
                    unit.classList.add('ze');
                } else {
                    unit.classList.add('ping');
                    unit.style.color = '#999';
                    unit.style.borderColor = '#999';
                }

                if (t === 'ping' || t === 'ze') {
                    unit.classList.add(isCorrect ? 'correct' : 'wrong');
                }

                resultHint.appendChild(unit);
            });
        }

        // 获取或创建结果提示元素
        function getResultHintEl(lineNum) {
            let resultHint = document.getElementById(`result-hint-${lineNum}`);
            if (!resultHint) {
                resultHint = document.createElement('div');
                resultHint.id = `result-hint-${lineNum}`;
                resultHint.className = 'result-hint';
                resultHint.style.cssText = `
                    margin-top: 4px;
                    font-size: 0.9em;
                    letter-spacing: 6px;
                    display: flex;
                    justify-content: center;
                    gap: 6px;
                `;
                document.getElementById(`hint${lineNum}`).after(resultHint);
            }
            return resultHint;
        }

        // 更新平仄提示模板
        function updateTone(format) {
            const patternLines = templates[format] || ["", "", "", ""];
            const rhymePos = rhymePositions[format] || [];

            for (let i = 1; i <= 4; i++) {
                const hintEl = document.getElementById(`hint${i}`);
                hintEl.innerHTML = '';

                const pattern = patternLines[i-1];
                if (!pattern) continue;

                const chars = pattern.split(' ').filter(c => c);
                const lineEndIndex = chars.length - 1;

                chars.forEach((char, index) => {
                    const unit = document.createElement('span');
                    unit.className = 'tone-unit';

                    const isRhyme = rhymePos.includes(i-1) && index === lineEndIndex;
                    const isOptional = char === '○';

                    if (char === '─' || char === '○') {
                        unit.classList.add('ping');
                    } else if (char === '│') {
                        unit.classList.add('ze');
                    }

                    if (isOptional) {
                        unit.classList.add('blue');
                    }
                    if (isRhyme) {
                        unit.classList.add('orange');
                    }

                    hintEl.appendChild(unit);
                });
            }

            // 若已有输入内容，重新校验
            for (let i = 1; i <= 4; i++) {
                const input = document.getElementById(`line${i}`);
                if (input.value.trim()) {
                    validateLine(i);
                }
            }
        }

        // 绑定输入框的失焦事件用于校验
        function setupInputListeners() {
            for (let i = 1; i <= 4; i++) {
                const input = document.getElementById(`line${i}`);
                input.addEventListener('blur', () => {
                    if (Object.keys(toneData).length > 0) {
                        validateLine(i);
                    }
                });
            }
        }

        // 初始化
        updateTone("");
    </script>
</body>
</html>
"""


# ===== 七言律诗（你已粘贴，这里保留）=====
qiyan_lvshi_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>创作七言律诗</title>
    <style>
        body { 
            font-family: "KaiTi", "SimSun", serif; 
            text-align: center; 
            margin: 0;
            padding: 20px 10px;
            background-color: #f7f4ed;
            color: #333;
            min-height: 100vh;
        }
        h1 { 
            font-size: 1.8em; 
            color: #2c3e50; 
            margin: 20px 0;
        }
        .tone-select {
            font-size: 1em;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #aaa;
            background: white;
            margin-bottom: 20px;
            width: 90%;
            max-width: 300px;
        }
        .tone-unit.correct {
            color: #28a745 !important;
        }
        .tone-unit.wrong {
            color: #e63946 !important;
        }
        .title-input {
            width: 90%;
            max-width: 300px;
            padding: 12px;
            margin: 20px auto;
            font-size: 1.2em;
            font-family: "KaiTi", "SimSun", serif;
            border: 2px solid #ddd;
            border-radius: 8px;
            text-align: center;
            display: block;
        }
        .poem-form {
            max-width: 600px;
            margin: 20px auto;
            padding: 0 10px;
        }
        .line-group {
            margin-bottom: 15px;
        }
        .couplet-vertical {
            display: flex;
            flex-direction: column;
            gap: 10px;
            align-items: center;
        }
        .input-container {
            position: relative;
            width: 100%;
            max-width: 300px;
        }
        .input-container input {
            width: 100%;
            padding: 12px;
            font-size: 1.3em;
            font-family: "KaiTi", "SimSun", serif;
            border: 2px solid #ddd;
            border-radius: 8px;
            background: white;
            text-align: center;
        }
        .input-container input:focus {
            outline: none;
            border-color: #007BFF;
            box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
        }
        .tone-hint {
            margin-top: 6px;
            font-size: 0.9em;
            letter-spacing: 8px;
            user-select: none;
            display: flex;
            justify-content: center;
            gap: 6px;
        }
        .tone-unit {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            border: 1px solid currentColor;
            box-sizing: border-box;
        }
        .tone-unit.ping {
            border-width: 2px;
            background: transparent;
        }
        .tone-unit.ze {
            background: currentColor;
        }
        .tone-unit.blue {
            color: #007BFF !important;
        }
        .tone-unit.orange {
            color: #FF8000 !important;
        }
        .submit-btn {
            margin: 30px auto;
            padding: 12px 30px;
            font-size: 1.2em;
            background-color: #2c3e50;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .submit-btn:active {
            transform: translateY(1px);
        }
        .back-btn {
            display: inline-block;
            margin-top: 20px;
            padding: 8px 16px;
            font-size: 1em;
            color: #007BFF;
            border: 1px solid #007BFF;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
        }

        @media (max-width: 480px) {
            h1 { font-size: 1.5em; }
            .title-input, 
            .input-container input,
            .tone-select {
                max-width: 280px;
                font-size: 1.1em;
                padding: 10px;
            }
            .tone-hint { 
                gap: 4px;
                letter-spacing: normal;
            }
            .tone-unit {
                width: 10px;
                height: 10px;
            }
            .submit-btn { 
                font-size: 1.1em; 
                padding: 10px 20px; 
            }
        }
    </style>
</head>
<body>
    <h1>创作七言律诗</h1>
    <select class="tone-select" id="tone" onchange="updateTone(this.value)">
        <option value="">请选择平仄格式</option>
        <option value="pingqi_buru">平起首句不入韵式</option>
        <option value="pingqi_ru">平起首句入韵式</option>
        <option value="zeqi_buru">仄起首句不入韵式</option>
        <option value="zeqi_ru">仄起首句入韵式</option>
    </select>

    <input type="text" class="title-input" id="title" placeholder="请输入诗题">

    <form class="poem-form" onsubmit="alert('提交功能暂未实现'); return false;">
        <!-- 第一联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line1" placeholder="七言诗句">
                    <div class="tone-hint" id="hint1"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line2" placeholder="七言诗句">
                    <div class="tone-hint" id="hint2"></div>
                </div>
            </div>
        </div>

        <!-- 第二联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line3" placeholder="七言诗句">
                    <div class="tone-hint" id="hint3"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line4" placeholder="七言诗句">
                    <div class="tone-hint" id="hint4"></div>
                </div>
            </div>
        </div>

        <!-- 第三联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line5" placeholder="七言诗句">
                    <div class="tone-hint" id="hint5"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line6" placeholder="七言诗句">
                    <div class="tone-hint" id="hint6"></div>
                </div>
            </div>
        </div>

        <!-- 第四联 -->
        <div class="line-group">
            <div class="couplet-vertical">
                <div class="input-container">
                    <input type="text" id="line7" placeholder="七言诗句">
                    <div class="tone-hint" id="hint7"></div>
                </div>
                <div class="input-container">
                    <input type="text" id="line8" placeholder="七言诗句">
                    <div class="tone-hint" id="hint8"></div>
                </div>
            </div>
        </div>

        <button type="submit" class="submit-btn">完成创作</button>
    </form>

    <a href="javascript:window.history.back()" class="back-btn">← 返回</a>

    <script>
        // 声明 toneData，用于存储汉字音调
        let toneData = {};

        // 七言律诗平仄模板（8句）
        const templates = {
            pingqi_buru: [
                "─ ─ │ │ ─ ─ │",  // 1
                "│ │ ─ ─ │ │ ─",  // 2
                "│ │ ─ ─ ─ │ │",  // 3
                "─ ─ │ │ │ ─ ─",  // 4
                "─ ─ │ │ ─ ─ │",  // 5
                "│ │ ─ ─ │ │ ─",  // 6
                "│ │ ─ ─ ─ │ │",  // 7
                "─ ─ │ │ │ ─ ─"   // 8
            ],
            pingqi_ru: [
                "─ ─ │ │ │ ─ ─",  // 1
                "│ │ ─ ─ │ │ ─",  // 2
                "│ │ ─ ─ ─ │ │",  // 3
                "─ ─ │ │ │ ─ ─",  // 4
                "─ ─ │ │ ─ ─ │",  // 5
                "│ │ ─ ─ │ │ ─",  // 6
                "│ │ ─ ─ ─ │ │",  // 7
                "─ ─ │ │ │ ─ ─"   // 8
            ],
            zeqi_buru: [
                "│ │ ─ ─ │ │ ─",  // 1
                "─ ─ │ │ ─ ─ │",  // 2
                "─ ─ │ │ │ ─ ─",  // 3
                "│ │ ─ ─ │ │ ─",  // 4
                "│ │ ─ ─ ─ │ │",  // 5
                "─ ─ │ │ │ ─ ─",  // 6
                "─ ─ │ │ ─ ─ │",  // 7
                "│ │ ─ ─ │ │ ─"   // 8
            ],
            zeqi_ru: [
                "│ │ ─ ─ ─ │ │",  // 1
                "─ ─ │ │ │ ─ ─",  // 2
                "─ ─ │ │ ─ ─ │",  // 3
                "│ │ ─ ─ │ │ ─",  // 4
                "│ │ ─ ─ ─ │ │",  // 5
                "─ ─ │ │ │ ─ ─",  // 6
                "─ ─ │ │ ─ ─ │",  // 7
                "│ │ ─ ─ │ │ ─"   // 8
            ]
        };

        // 押韵位置（行号索引 + 末字位置）
        const rhymePositions = {
            pingqi_buru: [1, 3, 5, 7],
            pingqi_ru:   [0, 1, 3, 5, 7],
            zeqi_buru:   [1, 3, 5, 7],
            zeqi_ru:     [0, 1, 3, 5, 7]
        };

        // 从 char_tones.json 加载音调数据
        fetch('/static/char_tones.json')
            .then(r => {
                if (!r.ok) throw new Error('无法加载 char_tones.json');
                return r.json();
            })
            .then(data => {
                toneData = data;
                console.log('音调数据加载成功', Object.keys(data).length + ' 个汉字');
                setupInputListeners(); // 数据加载成功后绑定输入事件
            })
            .catch(err => {
                console.error('加载音调数据失败:', err);
                alert('音调数据加载失败，请检查 /static/char_tones.json 是否存在且格式正确。');
            });

        // 获取单个字的平仄类型
        function getToneClass(char) {
            const tone = toneData[char];
            if (tone === 1 || tone === 2) return 'ping'; // 平声
            if (tone === 3 || tone === 4) return 'ze';  // 仄声
            return null; // 未知字
        }

        // 校验某一行诗句是否符合格式
        function validateLine(lineNum) {
            const input = document.getElementById(`line${lineNum}`);
            const value = input.value.trim();
            const resultHint = getResultHintEl(lineNum);
            resultHint.innerHTML = '';

            if (value.length !== 7) {
                input.style.borderColor = '#e63946';
                input.style.boxShadow = '0 0 5px rgba(230, 57, 70, 0.3)';
                resultHint.textContent = '需七字';
                resultHint.style.color = '#e63946';
                return;
            } else {
                input.style.borderColor = '#28a745';
                input.style.boxShadow = '0 0 5px rgba(40, 167, 69, 0.2)';
            }

            const format = document.getElementById('tone').value;
            const expectedPattern = templates[format]?.[lineNum - 1];
            if (!expectedPattern) {
                resultHint.textContent = '请选择格式';
                resultHint.style.color = '#666';
                return;
            }

            const expectedTones = expectedPattern.split(' ').filter(c => c);
            const userTones = [];

            for (let i = 0; i < 7; i++) {
                const char = value[i];
                const toneClass = getToneClass(char);
                userTones.push(toneClass);
            }

            userTones.forEach((t, idx) => {
                const expected = expectedTones[idx];
                const isCorrect =
                    expected === '○' ||                    // 可平可仄 → 正确
                    (t === 'ping' && expected === '─') ||  // 平对平
                    (t === 'ze' && expected === '│');      // 仄对仄

                const unit = document.createElement('span');
                unit.className = 'tone-unit';

                if (t === 'ping') {
                    unit.classList.add('ping');
                } else if (t === 'ze') {
                    unit.classList.add('ze');
                } else {
                    unit.classList.add('ping');
                    unit.style.color = '#999';
                    unit.style.borderColor = '#999';
                }

                if (t === 'ping' || t === 'ze') {
                    unit.classList.add(isCorrect ? 'correct' : 'wrong');
                }

                resultHint.appendChild(unit);
            });
        }

        // 获取或创建结果提示元素
        function getResultHintEl(lineNum) {
            let resultHint = document.getElementById(`result-hint-${lineNum}`);
            if (!resultHint) {
                resultHint = document.createElement('div');
                resultHint.id = `result-hint-${lineNum}`;
                resultHint.className = 'result-hint';
                resultHint.style.cssText = `
                    margin-top: 4px;
                    font-size: 0.9em;
                    letter-spacing: 6px;
                    display: flex;
                    justify-content: center;
                    gap: 6px;
                `;
                document.getElementById(`hint${lineNum}`).after(resultHint);
            }
            return resultHint;
        }

        // 更新平仄提示模板
        function updateTone(format) {
            const patternLines = templates[format] || Array(8).fill("");
            const rhymePos = rhymePositions[format] || [];

            for (let i = 1; i <= 8; i++) {
                const hintEl = document.getElementById(`hint${i}`);
                hintEl.innerHTML = '';

                const pattern = patternLines[i-1];
                if (!pattern) continue;

                const chars = pattern.split(' ').filter(c => c);
                const lineEndIndex = chars.length - 1;

                chars.forEach((char, index) => {
                    const unit = document.createElement('span');
                    unit.className = 'tone-unit';

                    const isRhyme = rhymePos.includes(i-1) && index === lineEndIndex;
                    const isOptional = char === '○';

                    if (char === '─' || char === '○') {
                        unit.classList.add('ping');
                    } else if (char === '│') {
                        unit.classList.add('ze');
                    }

                    if (isOptional) {
                        unit.classList.add('blue');
                    }
                    if (isRhyme) {
                        unit.classList.add('orange');
                    }

                    hintEl.appendChild(unit);
                });
            }

            // 若已有输入内容，重新校验
            for (let i = 1; i <= 8; i++) {
                const input = document.getElementById(`line${i}`);
                if (input.value.trim()) {
                    validateLine(i);
                }
            }
        }

        // 绑定输入框的失焦事件用于校验
        function setupInputListeners() {
            for (let i = 1; i <= 8; i++) {
                const input = document.getElementById(`line${i}`);
                input.addEventListener('blur', () => {
                    if (Object.keys(toneData).length > 0) {
                        validateLine(i);
                    }
                });
            }
        }

        // 初始化
        updateTone("");
    </script>
</body>
</html>
"""


# ===== 路由 =====
@app.route("/")
def index():
    return render_template_string(html)

@app.route("/compose/<ptype>")
def compose(ptype):
    if ptype == "tang":
        return render_template_string(compose_html  + floating_search_html)
    elif ptype == "song":
        return "<h1>填词功能暂未开放</h1><p><a href='javascript:window.history.back()' class='back-btn'>← 返回</a></p>"
    else:
        return "<h1>未知类型</h1><p><a href='javascript:window.history.back()' class='back-btn'>← 返回</a></p>", 400

@app.route("/compose/tang/wuyan-jueju")
def compose_wuyan_jueju():
    return render_template_string(wuyan_jueju_html + floating_search_html)

@app.route("/compose/tang/wuyan-lvshi")
def compose_wuyan_lvshi():
    return render_template_string(wuyan_lvshi_html + floating_search_html)

@app.route("/compose/tang/qiyan-jueju")
def compose_qiyan_jueju():
    return render_template_string(qiyan_jueju_html + floating_search_html)

@app.route("/compose/tang/qiyan-lvshi")
def compose_qiyan_lvshi():
    return render_template_string(qiyan_lvshi_html + floating_search_html)

@app.route("/api/search_yun")
def search_yun():
    char = request.args.get("char", "").strip()
    if not char:
        return jsonify({"error": "请输入一个汉字"}), 400

    result = []
    found_yun = None

    # 遍历所有韵部，查找该字
    for yun_name, data in yunbu_data.items():
        if char in data.get("zi", []):
            result = data["zi"]
            found_yun = yun_name
            break

    if not result:
        return jsonify({"error": f"未找到汉字 '{char}' 所在的韵部", "result": []})

    return jsonify({
        "char": char,
        "yun": found_yun,
        "zi": result
    })

@app.route("/poem/<ptype>")
def poem(ptype):
    if ptype == "tang":
        poem = random.choice(tang_list)
    elif ptype == "song":
        poem = random.choice(song_list)
    else:
        return jsonify({"title": "", "author": "", "content": "未知类别"})

    paragraphs = poem.get("paragraphs", [])
    content = "\n".join(paragraphs)
    return jsonify({
        "title": poem.get("title", ""),
        "author": poem.get("author", ""),
        "content": content
    })


# ===== 启动 =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)