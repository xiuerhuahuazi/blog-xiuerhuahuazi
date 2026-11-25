# Krea2 双采工作流 · 实跑记录

> 2026-11-24　｜　全部在本机实测通过，出图见 `output/`

## 一、跑在哪儿

| 项 | 值 |
|---|---|
| 执行机 | `peer-mini`（M6 / 24GB 统一内存 / MPS） |
| 连接 | 雷雳网桥 `ssh peer`（192.0.2.10，示例地址，延迟 0.7ms） |
| ComfyUI | 0.45.6，已在跑，`127.0.0.1:8188` |
| 模型根 | `~/ComfyUI-Shared/models/` |
| 出图目录 | `~/ComfyUI-Shared/output/` |

## 二、三条链，全部实跑成功

### 链 1：冒烟测试（验证节点链路）
- 512×512，一采 4 步 → 潜空间放大 1.4× → 二采 1 步（denoise 0.5）
- 耗时 **约 70 秒**，产物 `output/krea_smoke_00001_.png`（720×720）

### 链 2：Krea2 纯双采（主交付）
`workflows/krea_double_api.json`

| 段 | 节点 | 参数 |
|---|---|---|
| 一采 | KSampler | 1024×1024，8 步，cfg 1，euler + simple，denoise 1.0 |
| 放大 | LatentUpscaleBy | bicubic，1.25×（→1280²） |
| 二采 | KSampler | 3 步，cfg 1，**denoise 0.45** |
| 输出 | VAEDecode + SaveImage | 1280×1280 |

- 耗时 **约 3 分 23 秒**（18:41:07 → 18:44:30）
- 产物 `output/krea_double_00001_.png`

### 链 3：MOSS 一采 → Krea2 二采（双模型双采）
分两次跑，中间用图片交接（避免两个模型同时占内存）：

| 段 | 文件 | 参数 | 耗时 |
|---|---|---|---|
| 一采（构图/内容） | `workflows/moss_chain_first_api.json` | MOSS SFT int8，768×768，20 步，cfg 2.5，`er_sde`/simple | 约 4 分 |
| 二采（质感/光影） | `workflows/krea2_second_pass_api.json` | Krea2 turbo int8，LoadImage → VAEEncode → 4 步，cfg 1，**denoise 0.45** | 约 2 分 |

- 中间交接：`cp output/moss_chain_00001_.png input/`，二采用 LoadImage 读它
- 产物 `output/moss_chain_00001_.png`（一采）、`output/moss_krea_double_00001_.png`（二采）

## 三、实测结论（这几条是真跑出来的）

1. **中文长提示词可用**。CLIP 是 qwen3vl_4b，我直接喂了 500 余字的分段中文（主体/动作/环境/光线/质感/构图/色板/背景/介质），出图完全对得上，没有出现"中文失效"。
2. **双采提速明显**。同样是 1024，8 步一采 + 3 步二采只要 3 分半，而之前带 LoRA 的 8 步单采花了 17 分钟——差别主要来自 LoRA 与内存压力，不是双采本身贵。
3. **二采的 denoise 是唯一起作用的旋钮**。0.45 保留了构图（人、窗、陶罐位置基本不动），只把皮肤毛孔、亚麻织纹、陶土哑光颗粒和暗部层次补了出来。
4. **MOSS 与 Krea2 的分工成立**。MOSS 一采给的是更"摆拍感"的商业人像，光比更大、构图更规整；Krea2 二采把画面拉回胶片写实，去掉了数码光泽，还按提示词把背景压成 solid umber。
5. **单模型双采 vs 双模型双采的区别**：前者二采是在自己的 latent 上重绘（构图几乎不变，细节增益）；后者是解码成像素、换 VAE 重新编码再画（构图继承但会重新解释，所以脸型/姿态会有轻微漂移）。

## 四、MJ 风格：LoRA 已就位，且实跑通过

两个 LoRA 从 `hf-mirror.com/RunningHubAI/rh-krea2-cc-mj-lora` 下完并校验（各 768 张量、大小与远端逐字节一致），落在对端 `~/ComfyUI-Shared/models/loras/`：

| 文件 | 大小 | 作用 |
|---|---|---|
| `krea2-Cc-MJ-风格滤镜.safetensors` | 342.9 MB | MJ 整体影调 / 色彩滤镜 |
| `krea2-Cc-MJ-影视柔光.safetensors` | 228.6 MB | 人物柔光、皮肤质感，史诗场景也吃 |

作者给的口径：**建议权重 0.8–1.2，没有触发词**（这一点和很多 LoRA 不同，别去找 trigger word）。

### MJ 版实跑参数

一采 1024²、8 步、denoise 1.0 → LatentUpscaleBy 1.25× → 二采 **2 步、denoise 0.40**；
两个 LoRA 串在 UNET 后：风格滤镜 0.85、影视柔光 0.90；seed 20261124（与主链同 prompt 同 seed，可直接对照）。
耗时约 4 分半（含两份 LoRA 加载），输出 `output/krea_mj_00001_.png` 1280×1280。

### 同 prompt 同 seed 的差异（这是 LoRA 真正改变了什么）

- 无 LoRA 主链：自然窗光、单一光源、肤色偏真实带颗粒，画面像"纪录式人像"，暗部保留很多。
- 挂 MJ LoRA：明显变成三灯布光——左窗主光 + 暖金轮廓光打在发丝 + 前景大光圈 bokeh 光斑，浅景深把背景陶罐压成奶油状虚化，皮肤被柔光处理过（少了毛孔，多了通透感），整体像商业海报。
- 结论：**LoRA 改的是影调与光型，不是构图**。人物姿态、窗、陶罐位置几乎一致，说明这套"一采定构图 + 二采加风格"的分工是成立的。

### 挂法（要复用到别的流时照这个接）

- `LoraLoaderModelOnly` 串在 UNETLoader 之后、喂给两个 KSampler；两个 LoRA 就串两层
- 触发词：无
- 权重：0.8–1.2，双 LoRA 同开时各取 0.85 / 0.90 比较稳；超过 1.2 皮肤会发蜡
- 二采 denoise 0.40 是这次的甜点区：0.3 风格不显，0.5 开始冲掉 LoRA 的柔光

这套骨架和你抖音看到的那份「Moss 一采 + Krea2 二采 + MJ LoRA + 缩放 2.0」是同一个东西，现在只差 SeedVR2 那一档 2× 放大（要第三方节点，没装）。

## 五、复跑命令

```bash
# 主链
scp workflows/krea_double_api.json peer:~/ComfyUI-Shared/workflows/
ssh peer '/usr/bin/python3 ~/run_workflow_test.py ~/ComfyUI-Shared/workflows/krea_double_api.json double'

# 双模型链（两段）
ssh peer '/usr/bin/python3 ~/run_workflow_test.py ~/ComfyUI-Shared/workflows/moss_chain_first_api.json moss1'
ssh peer 'cp ~/ComfyUI-Shared/output/moss_chain_00001_.png ~/ComfyUI-Shared/input/'
ssh peer '/usr/bin/python3 ~/run_workflow_test.py ~/ComfyUI-Shared/workflows/krea2_second_pass_api.json k2pass'
```

改参数不用手改 JSON，用本地 `build_krea2_double.py`：

```bash
python3 build_krea2_double.py --w 1024 --h 1216 --s1 8 --s2 4 --d2 0.5 --scale 1.5 --lora 0.7 --prefix krea_v2 --out krea_v2.json
```

## 六、文件清单

```
Krea2-长提示词速查笔记.md
Krea2-工作流拆解笔记.md
Krea2-工作流实跑记录.md        ← 本文
build_krea2_double.py          ← 参数化生成器
workflows/
  krea_double_api.json         ← 主链（Krea2 一采 + 放大 + 二采）
  krea_mj_api.json             ← MJ 双 LoRA 版（已实跑成功）
  moss_chain_first_api.json    ← 双模型链·一采
  krea2_second_pass_api.json   ← 双模型链·二采
  Krea2-双采极清生图流+SeedVR2放大.json  ← 参考原版（含 SeedVR2，需第三方节点）
  Krea2四视图.json
output/
  krea_smoke_00001_.png        ← 冒烟 720×720
  krea_double_00001_.png       ← 主图 1280×1280（无 LoRA）
  krea_mj_00001_.png           ← MJ 双 LoRA 1280×1280（同 prompt 同 seed 对照）
  moss_chain_00001_.png        ← MOSS 一采 768×768
  moss_krea_double_00001_.png  ← 双模型二采 768×768
```
