# Krea 2 长提示词速查笔记

> 整理时间：2026-11-24　｜　来源：Krea 官方 prompting.md、Comfy 官方工作流、Ambience AI 实测、krea2-wildcards 实测库

---

## 0. 一句话原则

官方原话：**"Long detailed prompts yield best results."**（长而详细的提示词效果最好）

但「长」不等于「堆词」。判据只有一个：**每一句都要对应画面上一个能被渲染出来的事实**。如果一句话你说不清它会让哪个像素发生变化，删掉它。

官方 16 条示例里，没有一条出现 `beautiful` / `8k` / `masterpiece` / `best quality`。

---

## 1. 九段骨架（按顺序填，不会写成形容词列表）

| 段 | 写什么 | 示例词 |
|---|---|---|
| ① 介质/工艺 | 这张图是用什么"做"出来的 | `35mm film photograph` / `gouache painting on textured paper` / `cel animation` / `risograph print` / `3D render` |
| ② 主体外形 | 年龄、发型、眼睛、服装单品、表情 | `short choppy platinum blonde bob with heavy bangs` / `amber eyes` / `structured black top with architectural bust detail` |
| ③ 动作/接触 | 手上在做什么、和什么接触 | `hands wet with slip, throwing a bowl on a kick wheel` / `index finger delicately touching a subtle smile` |
| ④ 环境陈设 | 具体物件，不写"氛围感" | `slab of wet volcanic basalt` / `silhouetted utility poles with power lines` |
| ⑤ 光线 | 方向 + 软硬 + 色温 + 光源是什么 | `harsh chiaroscuro side-lighting` / `soft backlight through fog` / `raking light` / `glow from a CRT television` |
| ⑥ 质感材质 | 皮肤/毛/纸/vinyl/水珠 | `visible clay dust on her forearms` / `smooth vinyl texture` / `grainy ink texture` / `condensation droplets` |
| ⑦ 构图 | 景别 + 机位 + 景深 | `extreme low-angle close-up` / `medium close-up shot` / `shallow depth of field` / `high-angle wide perspective` |
| ⑧ 色彩 | 点名 2–3 个颜色 | `muted green and amber palette` / `ink black, bone white, and ochre` / `limited palette: fluorescent pink and navy` |
| ⑨ 背景 | 必须明确写出 | `solid vibrant blue background` / `solid striking crimson red` / `creamy bokeh` / `empty platform` |

**长度参考**（非官方，来自实测）：5–20 词探索方向 → 30–80 词可控人像/产品/场景 → 80–140 词复杂多人与密集环境 → 超过约 300 词基本不再增加信息量，反而开始自相矛盾。

---

## 2. 官方 16 条长提示词（原话，可直接复制）

来源：`krea-ai/krea-2/docs/prompting.md`，全部为 Turbo 2K 出图。

**1｜极简反例（说明短也能出图）**
```
immense rocket launch exhaust as seen from extremely close up
```

**2｜3D 潮玩（逗号堆叠式，每个逗号一个变量）**
```
3D rendered matte black designer toy figure, stylized round anthropomorphic shape, backward black baseball cap, oversized gold-rimmed aviator sunglasses, white traditional line-art tattoos of tiger and bird on torso, black studded belt with gold buckle, smooth vinyl texture, studio lighting, solid vibrant blue background, high contrast minimal composition
```

**3｜实验拼贴**
```
vintage analog collage, central irregularly shaped snowy mountain range with a section featuring distinct wavy edges, structured within a 12x16 grid of square tiles, composition fragments the subject by alternating tiles with solid azure blue background squares, thin white grid lines, grainy paper texture, retro aesthetic of mid-century print, vibrant cyan and warm neutral tones, experimental layout, tactile quality, high-contrast graphic composition
```

**4｜动漫特写**
```
close-up anime portrait of a young woman, large amber-brown eyes with intricate sparkling reflections, index finger delicately touching a subtle smile, messy dark blue hair with loose strands crossing her face, white and navy school uniform, bright high-key lighting, luminous shadows with cool blue undertones, detailed digital painting, dynamic tilted framing, shallow depth of field on hand
```

**5｜Ligne claire 平涂风景（段落叙事式范本）**
```
A minimalist flat-color illustration of a person wading through expansive shallow ocean waves beneath a pale peach sky. The dark-skinned figure, wearing an orange swim cap, light blue top, and bright green shorts, steps carefully through knee-deep water. The ocean is rendered in muted mint green with delicate, thin black linework detailing the continuous ripples and gentle whitecaps. Soft pinkish-peach reflections echo the sky on the water's surface. A dark, jagged rock rests in the lower left foreground near a pale grey shoreline. The horizon features a solid purplish-blue landmass and a stylized, layered yellow and blue cloud. The high-angle wide perspective emphasizes the vast negative space of the water, utilizing a clean ligne claire drawing aesthetic with a subtle paper texture.
```

**6｜点彩风景**
```
A tiny figure and a small white dog sit side-by-side in the deep green shadow of a massive tree on a sloping grassy hill. The enormous tree canopy dominates the upper composition, textured with thousands of stippled, light blue and yellow dabs representing leaves. A sharp diagonal line divides the vibrant, sunlit yellow-green grass in the foreground from the dark shade sheltering the pair. The stylized, painterly landscape features flattened perspective, visible brushstrokes, and intense color contrast.
```

**7｜高对比人像（红底打法）**
```
A close-up portrait of a young East Asian woman with straight black hair, loose strands sweeping across her fair skin, and an intense gaze. She wears a light grey collared shirt with a black tie. A vibrant bouquet of pink and orange lilies with lush green leaves sits in the blurred right foreground. The background is a solid, striking crimson red. Soft, directional studio lighting highlights her facial features, creating a high-contrast composition with a shallow depth of field.
```

**8｜微距动物**
```
A tiny, russet-brown harvest mouse clings to a slender diagonal branch amid vibrant green lobed leaves and small round buds. The mouse has soft textured fur, glossy black eyes, a pink nose, fine whiskers, and delicate pink paws firmly gripping the wood. In this macro photograph, an extremely shallow depth of field sharply focuses on the animal's face. The deep green background dissolves into a smooth, creamy bokeh, illuminated by soft, diffused natural lighting that highlights the intricate details of the fur and foliage.
```

**9｜动态数字绘画**
```
A dynamic digital painting of a joyful girl in a sailor uniform stretching her arms high against a solid vibrant blue background. She has short dark windblown hair, amber eyes, and a bright smile. She wears a white shirt, striped blue collar, flowing red neckerchief, and a billowing blue pleated skirt. Expressive thick brushstrokes and bold shading emphasize energetic motion.
```

**10｜海岸公路**
```
stylized digital painting of a dark convertible on a winding coastal cliff road, high-angle perspective, blocky painterly brushstrokes, golden hour sunlight hitting rocky orange terrain and green vegetation, flock of white abstract birds flying in foreground, blinding bright sun reflection on vast ocean, vibrant warm color palette, sharp graphic shadows
```

**11｜巨像遗迹**
```
An extreme low-angle close-up captures a colossal, weathered stone and bronze guardian towering in a dark, cavernous ruin. The foreground is dominated by a massive circular shield, deeply engraved with intricate spiral motifs, geometric borders, and a central star emblem. To the right, a massive gauntlet grips a textured staff. Cinematic shafts of light pierce the dusty gloom, highlighting the rough, aged textures of the ancient armor while the background fades into deep shadows through a shallow depth of field.
```

**12｜丛林挂毯**
```
A stylized jungle illustration densely packed with oversized flora and surreal characters, rendered with smooth geometric shapes and granular stippled shading. Two pale figures with flowing, star-speckled black hair navigate the lush environment in blue garments. On the left, a figure grasps a vine as a white, long-beaked bird perches on their outstretched hand. On the right, the second figure reclines beside a sleek, pinkish-orange fox. The dense surroundings feature sweeping green stalks and colossal blooms in brilliant golden yellow, coral pink, and deep red. A second white bird emerges from the lower foliage. The vibrant composition forms a seamless tapestry, utilizing rich colors and volumetric grain to create a dreamlike, textured depth.
```

**13｜复古未来金属**
```
A surreal retro-futuristic space scene features liquid chrome forming an abstract face merging with a glowing planetary horizon. The foreground is dominated by swirling, highly reflective metallic fluid that distorts into a stylized, melting facial profile with deep shadows and bright silver highlights. This undulating chrome form rests against the curved, atmospheric edge of a massive planet bathed in a soft electric blue and purple glow. Above the primary planet, a smaller eclipsed celestial sphere sits in the upper center, crowned by a sharp, cross-shaped starburst flare. Two additional radiant flares burst from the left and right edges of the horizon. Set against a deep black starfield, the artwork employs a vintage 1980s airbrush aesthetic with smooth gradients, ethereal lighting, and high-contrast metallic rendering.
```

**14｜金属丝带面部特写**
```
An extreme close-up portrait featuring pale, freckled skin and a single blue eye wrapped in reflective metallic gold ribbons. Thin gold strips crisscross diagonally over the cheek and forehead, casting sharp, hard shadows onto the face. Strands of copper hair frame the top edge while the left ear softly blurs out of focus. Harsh, direct lighting highlights intricate skin pores and bright golden reflections, isolating the brightly lit features against a pitch-black background in a bold, high-contrast macro editorial style.
```

**15｜小丑（最长的一条，看它怎么把"戏剧性"拆成可渲染项）**
```
Stylized digital painting of a menacing jester figure rendered with bold, expressive brushstrokes and a vibrant, almost psychedelic color palette against a pitch-black background. Dynamic low-angle perspective forces a dramatic, imposing composition as the character leans forward, one leg raised high. The jester wears a classic multi-pointed hat with bells, a ruffled collar, puffed sleeves, harlequin-patterned shorts in muted gold and dark brown, and striped tights in alternating shades of purple, blue, and chartreuse. A heavily textured, flowing cape billows outward to the left, decorated with abstract, fluid patterns of saturated purples, greens, and iridescent hues resembling oil slicks or marbled paper. The figure's face is completely obscured, appearing as a smooth, faceless, pale mauve mask with a single, glowing bright white point of light in the center. In its right hand, clad in a grey-blue gauntlet, the jester grips a massive, ornate sword with a wide, glowing, ethereal white blade, its crossguard intricately sculpted. Lighting is dramatic and theatrical, casting strong shadows and highlighting the painterly texture, giving the artwork a dark fantasy, surreal aesthetic reminiscent of concept art.
```

**16｜时尚大片（最像"可直接改主体"的模板）**
```
high-fashion editorial portrait of a young East Asian woman, short choppy platinum blonde bob with heavy bangs, looking over her bare shoulder to the right, lips playfully pursed, wearing a structured black top with an architectural protruding bust detail and thin straps, delicate gold hoop earrings, arm bent with hand resting on hip, warm skin tones, solid striking crimson red background, soft directional studio lighting, cinematic color palette, medium close-up shot
```

**17｜1990s 赛璐璐群像**
```
1990s vintage anime style cel animation, densely packed crowd of teenagers in summer uniforms, central boy with short black hair raising a clenched right fist, squinting one eye with a determined expression, wearing a white short-sleeve shirt and solid green necktie, surrounding students looking in various directions, girls in white sailor blouses with green striped collars and neckerchiefs, light blue skirts and trousers, tightly framed medium shot, flat shading, soft muted retro.
```

**18｜逆光动漫**
```
young woman looking over her right shoulder, anime-style illustration, messy black hair blowing dynamically in the wind, striking green eyes, subtle neutral expression, oversized white button-down collared shirt with soft blue shadows, vibrant deep blue sky background, bright fluffy white cumulus clouds, silhouetted utility poles with power lines, low angle portrait, cinematic sunlight, crisp cel-shaded aesthetic
```

**19｜胶片人像（"情绪"写成光与颗粒）**
```
extreme close-up of a woman's face partially obscured by tousled dark brown hair, soft parted lips, smooth skin on lower cheek and jawline, stray hair strands falling loosely across the nose, deep moody shadows enveloping the left frame, cinematic warm lighting, delicate highlights on the mouth, muted earthy color palette, sepia-toned warmth, intimate portrait photography, macro lens, shallow depth of field, distinct film grain texture, vintage atmospheric aesthetic
```

---

## 3. 段落式 vs 逗号式：怎么选

- **段落式**（示例 5、8、11、15）：适合叙事性强、有空间层次的画面。一句写一件事，主语明确，不会糊成一片。
- **逗号式**（示例 2、10、16、17）：适合风格化、电商、人像快改。好处是**一次只改一个逗号**就能做控制变量实验。
- 官方说两者它都读得懂，整段连贯描述和逗号清单效果一样。

---

## 4. 参数速查

| 项 | 值 |
|---|---|
| Krea 2 Turbo | ~4 秒，1K（本地可到 2K），2 点数，可批量 4 张，最多 4 张风格参考 |
| Krea 2 Medium | ~2 分钟，30 点数，更精细，无原生 3:4（会回落 4:5） |
| Krea 2 Large | 写实最强，避免"AI 塑料光泽" |
| Creativity | `raw` 不扩写 / `low` 贴字面 / `medium` 默认 / `high` 大幅补风格氛围 |
| 滑杆组合 | 图标/简洁设计：Complexity −60、Movement≈0；电影/时尚/角色：Intensity +60、Movement +30 |
| 本地采样（官方 Comfy 模板） | Turbo 8 步；cfg 1；euler；simple；1MP≈1344×768 |
| 社区常用 | 10 步；Moss 单采 50 步 + cfg 3.5；LoRA 权重 0.6–0.8 |
| 二次采样重绘强度 | 0.2 默认（保结构）→ 0.35（毛发/木纹更实）→ 再高画面开始变样 |
| 放大 | 4K 是"重画细节"而不是拉伸，先定图再开，比较费时 |
| 增强节点 | 强度 1.5 治发灰发平；胶片颗粒/锐化默认关 |

---

## 5. 官方扩写系统提示词（原文，拿去喂给任意 LLM）

官方仓库有 `expansion.txt`，Comfy 官方工作流里内置的版本如下，可直接当 system prompt：

```
You are an expert prompt engineer for text-to-image models. Your task is to expand the user's prompt into a highly effective image-generation prompt.

Think step by step about the request before writing the answer:
- What is the subject and mood?
- What visual styles, mediums, and lighting options would fit? Consider two or three alternatives and pick the one that best serves the caption.
- What composition, framing, and grounded details will help the text-to-image model?

Then output a single expanded prompt paragraph.

Follow these rules strictly:
1. Faithfulness First: Preserve all original subjects, actions, colors, and spatial relationships. Do not add new objects, props, characters, or animals unless the user clearly implies them.
2. Practical T2I Structure: Write a prompt that a text-to-image model can parse cleanly. Group subjects with their own attributes and actions. Use grounded phrasing for poses, interactions, and spatial layout.
3. Style Planning Stays Internal: Use your internal reasoning to choose style, medium, framing, and lighting. Do not emit planning tags or wrappers in the visible answer body.
4. Text Rendering: If the user requests visible text, quotes, labels, or typography, specify the exact text clearly and wrap requested words in quotes.
5. Avoid Over-Specification: Do not invent highly specific clothing, colors, materials, or scene details unless the input supports them.
6. Structure: Write one cohesive paragraph after the thinking block. No bullets, JSON, or markdown.
7. Respect Existing Detail: If the user's prompt is already detailed, lightly polish and finalize rather than heavily expanding — preserve their phrasing and direction.
8. Respect the Human Form: Treat depictions of people with dignity. Assume clothing covers genitals and intimate anatomy.
9. Preserve User Medium: When the user explicitly requests a medium (e.g. "photo of", "illustration of", "sketch of", "3D render of"), honor it. Do not pivot to a different medium to avoid difficulty — match the user's stated intent.

User's Input:
```

要点：**Faithfulness First（不改意图）+ Style Planning Stays Internal（风格只在内部推理里定，不写进正文）**。这两条就是"扩写不跑题"的关键。

---

## 6. 六个槽位模板（社区实测提炼）

1. `[medium] of [subject]` —— 整张画面换成某种画法
2. `[subject], raking light across [the surface]` —— 让材质显形（斜射光是最复用的光照短语）
3. `[subject], [what the light does], never [the name of the lamp]` —— 只写光的可见效果，不写灯具名（别写 softbox / ring light / window）
4. `Re-render this [subject] as [medium]: [what the medium looks like]` —— 图生图换画法，强度 0.50–0.60
5. `[subject] reading exactly "[the string]"` —— 画面里要出字，就把每个字符写全并加引号
6. `[subject], limited palette: [name each colour]` —— 限定配色，直接点色名

---

## 7. 踩坑清单

- **没有负面提示词**，你说"不要"的东西，名词照样会被画出来 → 改写成正面描述（`shallow depth of field` 而不是 `background not sharp`）。
- **背景没写就崩一半**，背景是模型自由度最大的地方。
- **3:4 在 Medium 上会变 4:5**。
- **大段文字必糊**：海报标题、UI 文案交给 GPT Image 2 / Nano Banana Pro。
- **"photorealistic" 单独用会落进平庸的图库感**，改写成 `35mm film photograph, fine grain` / `disposable camera flash`。
- **扩写和反推同时开，只认反推的词**（工作流逻辑）。
- **图生视频前先定图**，别边放大边改提示词。

---

## 8. 资源

| 资源 | 链接 |
|---|---|
| 官方 prompting.md（16 条示例 + expansion.txt） | https://github.com/krea-ai/krea-2/blob/main/docs/prompting.md |
| 官方中文文档（Medium/Large/Turbo + 滑杆） | https://www.krea.ai/docs/cn/user-guide/features/krea-2 |
| Comfy 官方工作流（含扩写系统提示词，可下载 JSON） | https://comfy.org/hub/workflows/krea-2-text-to-image-11657ed32877/ |
| ComfyUI 官方中文教程（含 2K 设置、LoRA 选择器说明） | https://docs.comfy.org/zh/tutorials/image/krea/krea-2 |
| 514 条实测提示词库（每条带图 + seed + 一键复制） | https://github.com/sjh9714/krea2-wildcards ｜ https://sjh9714.github.io/krea2-wildcards/ |
| 475 条 + 65 条失败案例及原因（61 类别，MIT） | https://github.com/sjh9714/awesome-krea-2 |
| Ambience AI 实测指南（五属性栈 + 风格手册） | https://www.ambienceai.com/tutorials/krea-2-prompting-guide |
| AI Reiter（长度分段与故障排查） | https://aireiter.com/blog/krea-2-prompting-guide |
| 斜杠中年（极简提示词 6 维度实测） | https://www.wesleychong.com/articles |
| 双采极清生图流（B站 黑鹤001 原版，JSON 可下） | https://www.9ll.uk/posts/ai/comfyui-wrokflow/krea2-seedvr2-upscale/ |
| RunningHub 上的 Krea2 四套工作流（双采/风格迁移/深度控制） | https://www.runninghub.cn/post/2075110170283298818 |
