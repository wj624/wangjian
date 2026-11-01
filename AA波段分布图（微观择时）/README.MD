# AA波段分布图（微观择时）

> **Pine Script v6** · **主图叠加**指标
> 脚本声明：`indicator("Structural Leg Profiler + 异常量AVWAP (全场景实战终极版)", "波段分布图+AVWAP", overlay=true, max_boxes_count=500, max_lines_count=500, max_labels_count=500)`

---

## 一、这个指标解决什么问题

它是一个**主图一体化「波段结构 + 筹码分布 + 交易计划」作战台**。把五个原本需要来回切换的能力合并在同一张主图上：

| 能力 | 作用 |
|---|---|
| ① ATR ZigZag 波段识别 | 自动把行情切成一条条"腿"（leg） |
| ② 分段成交量分布（Volume Profile） | 每完成一条腿，就在该腿区间画出横向筹码柱 |
| ③ POC 控制点 | 标出该腿成交最密集的价格 |
| ④ 异常量气泡 + AVWAP | 以放量为锚点的动态资金成本线 |
| ⑤ 双模交易计划引擎 | 自动给出入场 / 止盈 / 止损并输出到右下看板 |

**解决的核心问题**：支撑阻力在哪、量能是否异常、当下该左侧接还是右侧追、这笔单子盈亏比多少——全部在一个主图 + 一个看板里给出答案。

> 📌 **与本仓库其他脚本的关系**：`BBB/集合RSI及MFI云图的筹码分布` 是本脚本的**增强版**（在相同引擎之上追加了 RSI / MFI 自适应云图模块）。两者共用同一套波段切分与 AVWAP 逻辑。

---

## 二、快速上手

### 第 1 步：加载

Pine 编辑器 → 新建指标 → 粘贴本目录同名代码文件 → 添加到图表。因为是 `overlay=true`，会直接叠在 K 线上。

### 第 2 步：选择品种与周期

| 项目 | 建议 |
|---|---|
| 品种 | **必须有真实成交量**的量品种：期货主力连续、加密货币、美股个股 |
| 周期 | 15m / 1H / 4H / 日线 |
| `ltfSelect` | 日线波段建议选 **15** 或 **30** |

> ⚠️ **外汇 / CFD 的 tick 量或完全没有成交量的品种会严重失真**，筹码分布与 Delta 全部失去意义。

### 第 3 步：选交易模式

设置面板 **`交易模式 (核心开关)`**：

- **`左侧抄底 (逆势震荡)`**（默认）——适合价格在两个 POC 之间来回的**震荡行情**
- **`右侧突破 (顺势跟踪)`**——适合**趋势行情**，依赖 AVWAP 生命线

---

## 三、核心计算逻辑（代码说明）

### 3.1 底层 LTF 数据获取

```pine
[ltfOpens, ltfHighs, ltfLows, ltfCloses, ltfVolumes] =
     request.security_lower_tf(syminfo.tickerid, ltfSelect, [open, high, low, close, volume])
```

- `ltfSelect` 可选 `"1" / "5" / "15" / "30"`（分钟），默认 **30**
- 每根底层 K 线封装为 `LTFBar` 对象存入 `ltfHistory` 数组

**买卖量拆分**（按收盘价在振幅中的相对位置线性切分）：

```pine
float rng     = math.max(h - l, syminfo.mintick)
float buyVol  = v * (c - l) / rng
float sellVol = v * (h - c) / rng
```

**零量兜底**：`v = na(rawV) or rawV == 0 ? 1.0 : rawV`

### 3.2 ATR ZigZag 波段切分

```pine
float globalAtr     = ta.atr(atrPeriod)        // 默认 ATR(5)
float revAmount     = nz(globalAtr, syminfo.mintick * 10) * swingMult   // ×2.5
```

标准 ATR 反转逻辑：
- 上升腿中持续更新 `zzHigh`，一旦 `low < zzHigh − revAmount` → 确认**波段高点**
- 下降腿中持续更新 `zzLow`，一旦 `high > zzLow + revAmount` → 确认**波段低点**

确认瞬间调用 `f_processLeg()` 处理刚结束的那条腿。

### 3.3 筹码分布（分段、静态、无衰减）

> ⚠️ **重要**：本脚本**没有使用任何衰减模型**。这是它与通达信 / 同花顺式"筹码分布"（带衰减系数）最大的差别——这里是**静态、全量、无衰减**的**分段成交量分布图**。若你期望的是"当前流通筹码成本"，需自行加入衰减系数。

**分箱规则**：

```pine
float barRange = math.max(legHigh - legLow, syminfo.mintick)
int   numBoxes = math.max(1, int(math.round(barRange / targetBoxHeight)))
numBoxes := math.min(numBoxes, maxBoxes)          // 默认上限 20
float adjustedBoxHeight = barRange / numBoxes
```

其中 `targetBoxHeight`（名义箱高）由 `ATR(14)/10` 推导，若箱子数超限则自动放大箱高：

```pine
float boxHeightLimit  = nz(globalAtr14, syminfo.mintick * 10) / 10
float safeBase       = math.max(nz(baseBoxHeight, syminfo.mintick * 10), syminfo.mintick)
float targetBoxHeight = (groupRange / safeBase) > maxBoxes ? groupRange / maxBoxes : safeBase
```

**成交量分摊（重叠面积比例法）**：

```pine
float overlapHeight = math.max(0, math.min(boxTop, b.h) - math.max(boxBottom, b.l))
float overlapRatio  = overlapHeight / ltfBarRange
volDist.set(boxIndex, volDist.get(boxIndex) + nz(b.v * overlapRatio))
deltaDist.set(boxIndex, deltaDist.get(boxIndex) + (b.buyV - b.sellV) * overlapRatio)
```

等价于假设「K 线内成交量在价格上均匀分布」，按与各箱的重叠高度占比线性均摊，同时累计 **Delta 分布**（买量 − 卖量）。

**POC（控制点）** = 成交量最大箱体的中心价：

```pine
float pocPrice = legLow + (maxVolIdx * adjustedBoxHeight) + (adjustedBoxHeight / 2)
```

**关键常数**：

| 常数 | 值 |
|---|---|
| 名义箱高 | `ATR(14) / 10` |
| 最大箱数 | 20（可调 10–150） |
| 零成交量替身值 | `1.0` |
| `ltfHistory` 容量 | 5000 |
| 未测试 POC 上限 | 多头 10 条 + 空头 10 条 |
| `historicalPocs` 缓存 | 50 条 |

### 3.4 异常量气泡与 AVWAP

```pine
float volSma   = ta.sma(safeVolume, 20)
float volRatio = safeVolume / volSma
if volRatio >= bubbleMult      // 默认 2.0
    triggerAvwapReset := true
```

| 视觉 | 规则 |
|---|---|
| 气泡大小 | `ratio ≥ 3.0` 大号；`≥ 2.0` 中号；否则小号 |
| 气泡颜色 | 阳线 `upEndC #00E5FF`/40；阴线 `dnEndC #FF5252`/40 |
| 成交量数字 | `ratio ≥ 3.0`（`bubbleMult × 1.5`）时才显示 |
| 位置 | `hl2` |

**AVWAP 滚动重置**：

```pine
if triggerAvwapReset
    avwapCumVol := safeVolume
    avwapCumSrc := hlc3 * safeVolume
    isAvwapActive := true
else if isAvwapActive
    avwapCumVol += safeVolume
    avwapCumSrc += hlc3 * safeVolume
currentAvwap = avwapCumSrc / avwapCumVol
```

即从**最近一次放量 K 线**起算的滚动 VWAP（典型价 `hlc3` 加权），重置时打 `AVWAP\n重置` 标签。

### 3.5 双模交易计划引擎

**支撑阻力选取**：遍历 `sourcePocs`，找出**现价下方最近的两条 POC**（`poc1`/`poc2`）与**上方最近的两条**（`tpPoc1`/`tpPoc2`）。

若上方没有 POC → `isSkyHighMode = true`，退而用 `zzHigh`（波段前高）当阻力，标签变成 `上方阻力 (前高)`；若连前高都不在上方 → `上方阻力 (无)`。

**统一使用 ATR(14) 作为基准**，并强制止损倍数大于入场倍数：

```pine
float safeSlAtrMult = math.max(slAtrMult, targetAtrMult + syminfo.mintick / math.max(safeGlobalAtr14, syminfo.mintick))
```

| 价格 | 公式 |
|---|---|
| 左侧抄底目标 1 | `poc1 − ATR14 × targetAtrMult` |
| 左侧抄底目标 2 | `poc2 − ATR14 × targetAtrMult` |
| 左侧止盈 | `tpPoc1 − ATR14 × tpAtrMult` |
| 左侧止损 1 | `poc1 − ATR14 × safeSlAtrMult` |
| 左侧止损 2 | `poc2 − ATR14 × safeSlAtrMult` |
| 右侧突破开仓 | `currentAvwap + ATR14 × targetAtrMult` |
| 右侧防守底线 | `min(poc1, currentAvwap) − ATR14 × safeSlAtrMult` |
| 右侧目标 | `tpPoc1 − ATR14 × tpAtrMult`（天空模式：`rightBo + ATR14 × tpAtrMult × 2.0`） |

> 💡 源码注释强调：左侧用**减号**（深水区极值接盘、捕获扫损流动性），并强制 `slAtrMult ≥ targetAtrMult` 以杜绝「止损价高于入场价」的极端参数悖论。

### 3.6 四维胜率评分（满分 100）

`vR = ATR(5) / ATR(14)`（短/长 ATR 比，代表波动率扩张程度）

**左侧模式**（需 `leftPocObj` 存在）：

| 维度 | 条件 | 分值 |
|---|---|---|
| F1 筹码厚度 `pocVol/legVol` | `>0.25` / `>0.15` / 其他 | 25 / 15 / 5 |
| F2 POC Delta | `>0` / 其他 | 25 / 5 |
| F3 主力成本共振 | 无 AVWAP→15；`|poc1−AVWAP| ≤ ATR14`→30；`poc1 > AVWAP`→20；`AVWAP > poc1+2×ATR14`→0；其余 | 0–30 |
| F4 波动率情绪 `vR` | `<1.2` / `<1.5` / 其他 | 20 / 10 / 0 |

**右侧模式**（需 `rightBo` 存在）：

| 维度 | 条件 | 分值 |
|---|---|---|
| F1 量能 `vol/20SMA` | `≥bubbleMult` / `≥1.2` / 其他 | 30 / 15 / 5 |
| F2 生命线位置 | `close ≥ AVWAP`→25；否则 5；AVWAP 缺失→10 | 5–25 |
| F3 盈亏比 `(Tp−Bo)/(Bo−Sl)` | `≥2.0` / `≥1.2` / 其他（`Bo ≤ Sl` 时保持 15） | 25 / 15 / 0 或 15 |
| F4 波动率 | `1.0 ≤ vR ≤ 2.2`→20；否则 10 | 10 / 20 |

**评级**：≥80 高胜率 ★★★★☆（石灰绿）→ ≥60 中等 ★★★☆☆（黄）→ ≥40 一般 ★★☆☆☆（橙）→ 其余 高风险 ★☆☆☆☆（红）

---

## 四、参数速查

### 波段检测（Swing Detection）

| 参数 | 默认 | 说明 |
|---|---|---|
| `atrPeriod` | 5 | ZigZag 反转量所用 ATR 的周期，越小越敏感 |
| `swingMult` | 2.5 | 反转阈值 = ATR(5) × 2.5；越大捕捉越大的结构波段 |

### 分布图设置（Profile Settings）

| 参数 | 默认 | 说明 |
|---|---|---|
| `maxBoxes` | 20（10–150） | 每条腿最多画多少个筹码箱，同时决定箱高自适应 |
| `alignMode` | 左侧 | 框内成交量文本的对齐（左/右/居中） |
| `showBoxVol` | true | 是否在每个框后追加成交量数字 |
| `extendPoc` | true | 未测试 POC 是否向右延伸直到被价格触及 |

### 成交量异常（Volume Anomalies）

| 参数 | 默认 | 说明 |
|---|---|---|
| `showBubbles` | true | 显示成交量气泡 |
| `bubbleMult` | 2.0 | 量 ≥ 20 根量 SMA × 该倍数即触发气泡与 AVWAP 重置 |
| `showAvwap` | true | 叠加异常量 AVWAP |

### 样式与颜色（Style & Colors）

| 参数 | 默认 | 说明 |
|---|---|---|
| `colorMode` | 成交量渐变 | 成交量渐变 / 多空差值（买入 vs 卖出） |
| `upStartC` / `upMidC` / `upEndC` | `#01579B` / `#2962FF` / `#00E5FF` | 上涨腿低/中/高量渐变 |
| `dnStartC` / `dnMidC` / `dnEndC` | `#311B92` / `#C51162` / `#FF5252` | 下跌腿低/中/高量渐变 |
| `avwapC` | `#9b03a8` | AVWAP 线颜色 |

### 阶梯抄底与止盈止损（Trade Plan）

| 参数 | 默认 | 说明 |
|---|---|---|
| `tradeMode` | 左侧抄底 (逆势震荡) | **核心开关**，切换右下看板与全部计算逻辑 |
| `targetAtrMult` | 1.0 | 入场缓冲（左侧：支撑下方接针距离；右侧：突破确认） |
| `tpAtrMult` | 1.0 | 止盈抢跑（在上方阻力下方提前减仓的 ATR 距离） |
| `slAtrMult` | 2.5 | 止损向下延伸的 ATR 倍数，**必须大于入场倍数** |

### 高级设置（Advanced）

| 参数 | 默认 | 说明 |
|---|---|---|
| `ltfSelect` | 30 | 底层数据精度（分钟），可选 1 / 5 / 15 / 30 |

---

## 五、绘图与视觉元素

| 元素 | 说明 |
|---|---|
| **筹码箱** | 等宽字体进度条 `█/░`（长度 5–30），可选成交量数字；底色 90% 透明 |
| **腿线** | 灰色 50% 透明、点线、宽 2，连接两个波段枢轴 |
| **POC 线** | 未测试版虚线宽 2（持续右延）；历史副本实线 80% 透明，供右侧模式调用 |
| **腿摘要标签** | 位于腿中点，显示「波段量 / 多空差 Delta / 控制点 POC」，文字色按 Delta 正负 |
| **放量气泡** | 圆形，tooltip 显示「成交量激增 X.XX 倍 / AVWAP 将以此 K 线为新锚点」 |
| **AVWAP 线** | 紫色 `#9b03a8`，`plot.style_linebr` |
| **交易计划圆点** | 左侧：止盈（橙）/ 目标 1（青）/ 目标 2（蓝）；右侧：突破（紫）/ 目标（橙）/ 止损（红） |
| **右侧水平参考线** | 绿色「右侧防守-历史核心支撑」、橙色「右侧目标-上方筹码阻力」 |
| **右下看板** | 5 列 × 6 行 |

---

## 六、告警系统（5 条 alert()）

| 警报 | 判定式 | 频率 |
|---|---|---|
| 【左侧抄底】 | `ta.crossunder(low, leftT1) and isLeft` | 每根 K 线一次 |
| 【左侧深跌】 | `ta.crossunder(low, leftT2) and isLeft` | 同上 |
| 【左侧止盈】 | `ta.crossover(high, leftTp) and isLeft` | 同上 |
| 【右侧放量突破确认】 | `ta.crossover(close, rightBo)[1] and isVolBreakout[1]` | 同上 |
| 【右侧破位止损确认】 | `ta.crossunder(close, rightSl)[1]` | 同上 |

其中 `isVolBreakout = safeVolume > ta.sma(safeVolume, 20) * 1.2`。

> ⚠️ **创建警报的正确姿势**：本脚本使用的是 `alert()` **运行时调用**，而**不是** `alertcondition()`。因此在「创建警报」对话框的条件下拉框里**看不到具体条目**，必须选择：
> **条件 → 本指标名称 → 「任何 alert() 函数调用 (Any alert() function call)」**
> 消息内容会自动使用脚本内写好的文案。
>
> 另外：`alert()` 只在**实时 K 线**触发，历史回放不会产生警报。

---

## 七、使用建议

### 左侧抄底模式怎么用

1. 等价格运行到**未测试 POC 附近**（看板上橙色虚线延伸出的价位）
2. 挂单放在 `目标 1`（近支撑下方 `targetAtrMult` 倍 ATR）——这里是主力扫流动性的常见位置
3. 止损放在 `风控止损`（`slAtrMult` 倍 ATR）
4. 止盈参考 `上方阻力`（`tpPoc1` 下方 `tpAtrMult` 倍 ATR 抢跑减仓）
5. 看板会给出**预期利润率 + 盈亏比 + 多维胜率预测**，低于 40 分建议放弃

### 右侧突破模式怎么用

1. 确认 **AVWAP 生命线**方向（面板显示「多头趋势 / 空头趋势」）
2. 等待放量收盘价突破 `突破买入价`（AVWAP + ATR × `targetAtrMult`）
3. 防守底线 = `min(poc1, AVWAP) − ATR × slAtrMult`
4. 上方无阻力时进入「天空模式」，止盈自动切换为 ATR 追踪（`rightBo + ATR × tpAtrMult × 2.0`）

### 参数调优建议

| 场景 | 调整 |
|---|---|
| 波段太小、信号太碎 | 调大 `swingMult`（2.5 → 3.5）或 `atrPeriod`（5 → 10） |
| 筹码柱太密看不清 | 调小 `maxBoxes`（20 → 12） |
| 想看更细的筹码结构 | 调小 `ltfSelect`（30 → 15 或 5），但注意性能 |
| 止损太近被扫 | 调大 `slAtrMult`（2.5 → 3.0），同时适当减小 `targetAtrMult` |

---

## 八、已知问题与限制

1. **绘图对象会被自动回收**：`max_boxes_count=500` / `max_lines_count=500` / `max_labels_count=500`。把 `maxBoxes` 调到 150 或长期运行后，早期波段的筹码箱会被 TradingView 自动删除，表现为「分布图消失」。
2. **`request.security_lower_tf` 历史深度有限**：图表左侧很老区间取不到 LTF 数据，脚本会退化为「用当前 K 线本身当唯一一根 LTF bar」，POC 精度大幅下降。
3. **日线 + 1 分钟组合风险极高**：加密货币一天 1440 根、美股约 390 根，极可能触发 Pine 的 intrabar 数据量上限，导致数据被截断。**日线请用 15 或 30 分钟**。
4. **零成交量被替换为 1.0**：会产生极小量纲的虚假筹码与 MFI 资金流，通常可忽略，但在极端流动性枯竭品种上需注意。
5. ~~看板止损显示与真实计算可能不一致~~ **【已修复 · 2026-11-01】**：旧版看板（右侧「防守底线」行的 ATR 倍数栏）显示的是用户输入的 `slAtrMult`，而实际 `rightSl` 计算用的是 `safeSlAtrMult = max(slAtrMult, targetAtrMult + mintick/ATR14)`。当用户把 `slAtrMult` 设得比 `targetAtrMult` 还小时，触发钳制，显示值与实际计算不一致，会误导风控距离判断。**现已将该栏改为显示实际生效的 `safeSlAtrMult`，与 `rightSl` 计算完全同源。** 仍建议保持 `slAtrMult > targetAtrMult`，以从输入层面避免钳制。
6. **未测试 POC 数组有清理上限**：多头/空头各保留 10 条，超出后按 `endBar` 裁断，极老的 POC 会停止延伸。
7. **`historicalPocs` 只 shift 不删线**：`shift()` 丢弃引用但 `line` 对象未删除，长期运行会持续消耗 `max_lines_count=500` 配额。
8. **无 `alertcondition`**：只能通过「任何 alert() 函数调用」方式建警报（见上文）。
