# BBB — 分支与深度扩展代码

本目录是**细分与深度扩展**代码区，共 5 个脚本。

与根目录 5 个「常驻版」指标的差别在于**时间维度的极致细分**：

| 目录 | 定位 |
|---|---|
| 根目录（5 个 AA 指标） | 全天候、跨维度的宏观 + 微观综合监控，日常常驻 |
| **BBB（本目录）** | 针对**某一具体时间尺度或单一逻辑**做深度"精对"剖析 |

> **使用原则**：根目录指标发出预警后，再到 BBB 调用对应细分指标做确认和拆解。

---

## 📁 脚本总览

| # | 脚本 | 图层 | 时间尺度 | 核心用途 |
|---|---|---|---|---|
| 1 | `集合RSI及MFI云图的筹码分布` | 主图叠加 | 微观（图表自身周期） | 波段筹码分布 + RSI/MFI 双云图 |
| 2 | `宏观全景 V7.9(中期细分)` | 副图 | 中期（月频数据） | 货币周期 / 商业周期精调 |
| 3 | `订单流动系统 + 机构级三层云图(微观择时）` | 主图叠加 | 微观 | 订单流 Delta + 结构云图 |
| 4 | `资金加权波段雷达 (VW-KDJ) [微观择时]` | 副图 | 微观 | 量价加权版 KDJ 极值拐点 |
| 5 | `达利欧宏观看板 V26 (远期细分)` | 副图 | 远期（日线 + 季/月频） | 四大经济体债务长波对比 |

---

## 1. `集合RSI及MFI云图的筹码分布`

> `indicator("Structural Leg Profiler + 异常量AVWAP (全场景实战终极版)", "波段分布图+AVWAP+云图", overlay=true, max_boxes_count=500, max_lines_count=500, max_labels_count=500)`

### 定位

**主图一体化交易作战台**。它是根目录 `AA波段分布图（微观择时）` 的**增强版** —— 使用完全相同的波段切分引擎与 AVWAP 逻辑，在此之上追加了 **RSI + MFI 自适应双云图**模块。

> 💡 **与 `AA波段分布图` 的关系**：两者是同源脚本的不同分支。本脚本 = 波段分布图 + RSI/MFI 云图。如果你主要做筹码结构分析，用根目录版本更清爽；如果希望在主图上直接看到量价振荡器的相对位置，用本版本。

### 五大模块

| 模块 | 说明 |
|---|---|
| ① 结构波段识别 | ATR ZigZag（`ATR(5) × 2.5`）自动切分行情腿 |
| ② 筹码 / 成交量分布 | 每完成一条腿画出横向筹码柱与 POC |
| ③ 异常量 AVWAP | 以成交量激增 K 线为锚点的动态 VWAP |
| ④ 双模交易计划引擎 | 左侧逆势抄底 / 右侧顺势突破，自动给入场、止盈、止损 |
| ⑤ RSI + MFI 自适应主图云图 | 把两个 0–100 振荡器按价格区间映射回主图 |

### RSI 云图

```pine
oscRsi      = ta.rsi(close, rsiLen)                                  // 默认 14
rsiPctUpper = ta.percentile_linear_interpolation(oscRsi, pctLen, 80) // 默认 100
rsiPctLower = ta.percentile_linear_interpolation(oscRsi, pctLen, 20)
```

- 上下轨**不做额外平滑**，直接取 100 根 RSI 的 **80 / 20 线性插值分位数**，因此是**自适应**的（不是固定 70/30），行情长期低迷时上下轨会整体下移
- **价格映射**：

```pine
float winHigh  = nz(ta.highest(high, mapLookback), high)   // 默认 60 根
float winLow   = nz(ta.lowest(low,  mapLookback), low)
float winRange = math.max(winHigh - winLow, syminfo.mintick)
f_toPrice(float val) => winLow + (val / 100.0) * winRange
```

即 **RSI=0 映射到 60 根窗口最低价，RSI=100 映射到最高价**，线性插值。

> ⚠️ **关键提醒**：映射窗口每根 K 线滚动，因此云带位置会随视窗漂移。**它不是真实的支撑阻力位，只是"按比例缩放的振荡器"**，不要当作价位直接使用。

### MFI 资金流量云图

```pine
tpRsiMfi = hlc3
rawMf    = tpRsiMfi * safeVolume
posMf    = tpRsiMfi > tpRsiMfi[1] ? rawMf : 0.0
negMf    = tpRsiMfi < tpRsiMfi[1] ? rawMf : 0.0
sumPosMf = math.sum(posMf, mfiLen)        // 默认 14
sumNegMf = math.sum(negMf, mfiLen)
safeNegMf= sumNegMf == 0 ? 0.000001 : sumNegMf
oscMfi   = 100 - (100 / (1 + (sumPosMf / safeNegMf)))
```

- 典型价 = `hlc3 = (H+L+C)/3`
- 资金比 MR = `sumPosMf / sumNegMf`；`MFI = 100 − 100/(1+MR)`
- 云图上下轨同样用 80 / 20 分位（`pctLen=100`），再经同一个 `f_toPrice()` 映射到价格轴

### 动态填充色规则

| 条件 | 颜色 |
|---|---|
| `rsiPctUpper < 60` | `#00ffaa`，透明度 78（整体偏弱 / 超卖区） |
| `rsiPctLower > 50` | `#ff0055`，透明度 78（整体偏强 / 超买区） |
| 其他 | `pctFillColor` `#9c27b0`，透明度 84 |

MFI 云图规则相同（默认填充 `#008cff`，透明度 82）。

> ⚠️ 上沿用 60、下沿用 50，**阈值不对称**，疑似笔误；RSI 与 MFI 两处完全一致地复刻了这个不对称。按源码原样描述，改动前请确认是否有意为之。

### RSI 与 MFI 的"集合"方式

两者**不做数值合成**（无加权平均、无共振打分），而是**图层叠加 + 越界异动填充**：

| 信号 | 判定式 | 含义 |
|---|---|---|
| **顶部超常**（红 `#f30d0d`/58） | `rsiPctUpper > mfiPctUpper` | 价格动能强于资金动能（价涨但钱没跟上） |
| **底部真空**（绿 `#00ff08`/58） | `rsiPctLower < mfiPctLower` | 价格弱于资金流（资金在低位承接） |

比较的是**两个振荡器的分位数**（同为 0–100 量纲），属"价 vs 量"的背离式判读。**它不会触发任何警报，纯视觉提示。**

### 参数速查（共 38 个）

| 组 | 参数 | 默认 | 说明 |
|---|---|---|---|
| 波段检测 | `atrPeriod` | 5 | ZigZag 反转 ATR 周期 |
| | `swingMult` | 2.5 | 反转阈值 = ATR(5) × 2.5 |
| 分布图设置 | `maxBoxes` | 20（10–150） | 每条腿最多筹码箱数，同时决定箱高自适应 |
| | `alignMode` | 左侧 | 成交量文本对齐（左/右/居中） |
| | `showBoxVol` | true | 框内显示成交量数值 |
| | `extendPoc` | true | 延伸未测试 POC |
| 成交量异常 | `showBubbles` | true | 显示成交量气泡 |
| | `bubbleMult` | 2.0 | 激增阈值（× 20 根量 SMA） |
| | `showAvwap` | true | 叠加异常量 AVWAP |
| 样式与颜色 | `colorMode` | 成交量渐变 | 成交量渐变 / 多空差值 |
| | `upStartC` / `upMidC` / `upEndC` | `#01579B` / `#2962FF` / `#00E5FF` | 上涨腿渐变 |
| | `dnStartC` / `dnMidC` / `dnEndC` | `#311B92` / `#C51162` / `#FF5252` | 下跌腿渐变 |
| | `avwapC` | `#9b03a8` | AVWAP 线颜色 |
| 阶梯抄底与止盈止损 | `tradeMode` | 左侧抄底 (逆势震荡) | **核心开关** |
| | `targetAtrMult` | 1.0 | 入场目标价 ATR 倍数（缓冲） |
| | `tpAtrMult` | 1.0 | 止盈目标价 ATR 倍数（抢跑） |
| | `slAtrMult` | 2.5 | 止损目标价 ATR 倍数（防守） |
| 高级设置 | `ltfSelect` | 30 | 底层数据精度（分钟）：1/5/15/30 |
| RSI & MFI 云图 | `rsiLen` | 14 | RSI 周期 |
| | `mfiLen` | 14 | MFI 周期 |
| | `pctLen` | 100 | 自适应分位数通道周期 |
| | `mapLookback` | 60 | 价格映射回溯视窗 |
| | `showOscLines` | false | 显示映射后的 RSI/MFI 原生折线 |
| RSI 云图样式 | `showRsiCloud` | true | 总开关 |
| | `pctColorUp` / `pctColorDn` | `#ff00aa` / `#00ffaa` | 上/下轨线色 |
| | `pctFillColor` | `#9c27b0` | 基础填充色 |
| | `pctFillTrans` | 84 | 基础透明度 |
| MFI 云图样式 | `showMfiCloud` | true | 总开关 |
| | `mfiPctColorUp` / `mfiPctColorDn` | `#ff9800` / `#e0a800` | 上/下轨线色 |
| | `mfiPctFillColor` | `#008cff` | 基础填充色 |
| | `mfiPctFillTrans` | 82 | 基础透明度 |
| 云图越界异动填充 | `showCrossFill` | true | 控制顶部超常 / 底部真空两层填充 |

### 告警（5 条 alert()）

| 警报 | 触发 |
|---|---|
| 【左侧抄底】 | `ta.crossunder(low, leftT1)` |
| 【左侧深跌】 | `ta.crossunder(low, leftT2)` |
| 【左侧止盈】 | `ta.crossover(high, leftTp)` |
| 【右侧放量突破确认】 | `ta.crossover(close, rightBo)[1] and isVolBreakout[1]` |
| 【右侧破位止损确认】 | `ta.crossunder(close, rightSl)[1]` |

> ⚠️ 因为用的是 `alert()` 而非 `alertcondition()`，建警报时需在条件下拉框选择 **「任何 alert() 函数调用」**。

### 使用建议与已知问题

- 用法与根目录 `AA波段分布图` 完全一致，详见该目录的 `README.MD`。
- **云图阈值不对称**（60 / 50），见上文。
- **云带不是真实价位**，不可当支撑阻力。
- **零成交量被替换为 1.0**，MFI 在极端无量品种上会失真。
- `showOscLines` 默认关闭，打开后主图会多出两条映射折线，可能干扰阅读。

---

## 2. `宏观全景 V7.9(中期细分)`

> `indicator("宏观全景 V7.9(中期)", shorttitle="宏观全景V7.9(中期)", overlay=false, max_bars_back=5000)`

### 定位

**中期（3–12 个月）货币周期与商业周期精调器**。用月频宏观数据判定当前周期定位属于哪一格。

### 核心算法

| 模块 | 公式 |
|---|---|
| **货币剪刀差** | `M1同比 − M2同比`，同比窗口 = 12 根月线（`close[1]` 与 `close[13]`），封顶 ±40% |
| **剪刀差动能** | `EMA(raw_scissors, 6 个月)`，再封顶 |
| **期限利差** | `y10 − y2` |
| **流动性溢价** | `y10 − M2同比` |
| **倒挂深度** | `ta.lowest(term_spread, 6 个月)` |
| **铜金比风险偏好** | `COMEX:HG1! / COMEX:GC1!`，与 `EMA(10 月)` 比较 |
| **M1 环比动能** | `SMA(M1环比, 3 个月)`，领先 M1 同比约 6 个月 |
| **实际利率** | `y10 − CPI同比`（居民端）/ `y10 − PPI同比`（企业生死线） |
| **滞胀压力评分** | 4 项各 1 分，≥3 触发预警 |
| **利率分位** | 2 年期收益率的 120 个月滚动分位，≥80 高位、≤20 低位 |

**周期换算工具** `get_bars(months)`：月线 ×1 / 周线 ×4 / 日线 ×21 / 其他 ×21。解决在日线图上周线参数失效的问题。

### 8 态周期定位（互斥，按优先级）

🚨 紧缩崩盘期 → 🕸 低欲陷阱期 → ☠ 衰退确认 → ⚡ 筑底复苏 → ★ 牛市扩张 → ⚠ 警惕回撤 → ☯ 结构行情 → ❄ 熊市防御 → ⚑ 中性博弈

### 参数（18 个）

| 参数 | 默认 | 说明 |
|---|---|---|
| `country` | 中国 | 选择国家/地区（中/美/日/欧盟），切换全部宏观符号映射 |
| `th_rr_high` | 2.5 | 流动性溢价高位阈值 |
| `trend_sens` | 0.5 | 动能判定灵敏度（EMA6 量级，建议 0.3–1.0） |
| `th_credit` | 4.0 | 高收益债利差恶化阈值 (%) |
| `macro_sma_len` | 3 | 通胀 / 利润数据平滑周期（月） |
| `th_ppi_up` | 0.2 | 平滑后 PPI 上行阈值 |
| `th_cpi_up` | 0.1 | 平滑后 CPI 上行阈值 |
| `lookback_months` | 120 | 回测周期（月） |
| `percent_high` | 80 | 高利率分位线 |
| `percent_low` | 20 | 低利率分位线 |
| `cgr_ma_len` | 10 | 铜金比均线周期（月） |
| `cgr_multiplier` | 10000.0 | 铜金比绘图倍率 |
| `cap_val` | 40.0 | 同比数值封顶 |
| `th_real_rate` | 1.5 | 真实宽松判定：实际利率上限 |
| `th_inversion` | −0.3 | 衰退确认：倒挂深度阈值 |
| `th_stagflation` | 3 | 滞胀预警触发分数 |
| `m1_mom_ma_len` | 3 | M1 环比平滑周期（月） |
| `f_sz_in` | small | 字体大小（tiny/small/normal） |

### 已知问题

1. **信用利差硬编码为美国**：`credit_spread = FRED:BAMLH0A0HYM2`，不随 `country` 切换，非美区域的「主动紧缩崩盘」判定会失真。
2. **看板标签与数据源不符**：行 4 标注为「10Y均/现」，实际输出的是 **2 年期**收益率的 120 月均值与现值。
3. **滞胀叠加层覆盖全部背景**：`is_stagflation_warn` 的背景色**最后绘制**，会遮住扩张 / 复苏等主状态颜色。可通过其较深的红色（`@75`）识别，但容易被误判。
4. **`trend_sens` 只影响显示**：该参数仅决定「活化动能」是否显示「平稳」，不参与任何状态判定。
5. **无告警函数**：无 `alertcondition`，无法创建自动化警报。

---

## 3. `订单流动系统 + 机构级三层云图(微观择时）`

> `indicator("订单流动系统 + 机构级三层云图", overlay=true, max_labels_count=500, max_boxes_count=500, calc_bars_count=2000, max_bars_back=5000)`

### 定位

**微观择时 / 订单流 + 结构**。两大能力：
1. 波段成交量分布（Volume Profile）与买卖 Delta
2. 机构级结构云图（VWMA / EMA / HTF EMA 三线 + 状态机填充带）

### 核心算法

**① 波段识别**

```pine
highestSwingHigh = ta.highest(swingLen)     // 默认 50
lowestSwingLow   = ta.lowest(swingLen)
if high == highestSwingHigh : isDownMove := true
if low  == lowestSwingLow   : isDownMove := false     // 同 bar 双触发时后者生效
```

方向翻转时结算上一条腿并绘制完整 Profile。

**② 价格分箱**

```pine
priceBinSize = ta.atr(200) * 0.5
binCount = int(|highSwing.price - lowSwing.price| / priceBinSize)
binStep  = |highSwing.price - lowSwing.price| / binCount
```

箱高 = ATR(200) 的一半，随波动率自适应。

**③ 成交量分摊（注意：按收盘价归类，非区间均分）**

```pine
for k = 0 to binCount - 1
    binMidPrice = swingBottom + k*binStep + binStep/2
    if |binMidPrice - candleClose| < binStep
        volumeBins[k] += candleVol
        if candleClose > candleOpen : buyVolumeBins[k] += candleVol
        else                        : sellVolumeBins[k] += candleVol
```

> ⚠️ **重要差别**：这里**不做 intrabar 分布**，而是把整根 K 线的**全部成交量**归入**收盘价附近**的箱。判定窗为 `±binStep`（宽 2×箱高），而箱间距只有 `binStep`，因此**相邻两箱会同时命中 → 同一笔量被重复计入两个箱**（总量约 1～2 倍虚高）。Delta **百分比**因分子分母同步放大，比例基本不受影响；但**绝对成交量偏大**。
>
> 这与根目录 `AA波段分布图` 使用的「重叠面积比例法」是**两套不同的实现**，横向比较时结论不可直接互换。

**④ 正负 Delta 判定**：`close > open` → 买盘；`close <= open`（含十字星）→ 卖盘。

**⑤ PoC 与直方图**

```pine
volumeRatio  = volumeBins[k] / volumeBins.max()
profileWidth = int(volumeRatio * ((lastSwingIndex - prevSwingIndex)/2))
```

最大量箱即 PoC，边框色 `pocColor`（默认红），线宽 `pocWidthInput`（默认 2）。渐变：低量 90% 透明 → 高量 50% 透明。轮廓用 `polyline.new(..., closed=false, xloc=bar_index)`。

**⑥ 机构级三层云图（V3.3 结构状态机）**

| 层 | 公式 | 默认 | 颜色 |
|---|---|---|---|
| VWMA（资金层） | `ta.vwma(close, vwma_len)` | 20 | `rgb(0,255,170)`，lw2 |
| EMA（趋势层） | `ta.ema(close, ema_slow_len)` | 60 | `rgb(255,152,0)`，lw2 |
| HTF 200（大周期层） | `ta.ema(close, 200)` | 固定 | 白色 70% 透明，圆点 |

云带 = `fill(p_vwma, p_ema, final_color)`。

**结构引擎（枢轴双极确认 + 寿命衰减）**：

```pine
ph = ta.pivothigh(high, 3, 3)
pl = ta.pivotlow (low , 3, 3)
// 新 ph > last_ph → seq_bull+=1；新 ph < last_ph → seq_bear+=1
// 新 pl < last_pl → seq_bear+=1；新 pl > last_pl → seq_bull+=1
// seq_bull >= 2 → struct_state := 1（多头）；seq_bear >= 2 → -1（空头）
// bars_since_pivot >= struct_max_age(25) → struct_state := 0（结构死亡）
```

即需要 **HH 或 HL 连续 2 次**才确认多头结构；LL 或 LH 连续 2 次确认空头；**25 根无新枢轴则结构归零**。

> ⚠️ 源码注释写「3/3 双极确认」，但代码阈值是 `>= 2`，**注释与代码不符**（以代码为准）。

**趋势能量引擎（ADX 迟滞）**：

```pine
[plusDI, minusDI, adxValue] = ta.dmi(14, 14)
ema_slope = (slowEMA - slowEMA[5]) / slowEMA[5] * 100
if adxValue >= 25 or |ema_slope| >= 0.3      : trend_energy := true
else if adxValue < 20 and |ema_slope| < 0.3  : trend_energy := false
```

20～25 为滞滞区，保持原状态，避免抖动。

**乖离率开关**：`spread = |vwmaVal − slowEMA| / slowEMA * 100`，`valid_spread = spread >= 0.3`。

**五色配色决策**：

| 条件 | 颜色 | 含义 |
|---|---|---|
| `not trend_energy` 且 `not valid_spread` | 灰 92 | 中性 / 盘整休眠 |
| `vwma > ema` + 趋势 + 乖离 + 多头结构 | 绿 30 | 强势多头 |
| `vwma > ema` 其余 | 青 `#00BCD4` 70 | 多头蓄势 |
| `vwma < ema` + 趋势 + 乖离 + 空头结构 | 红 30 | 强势空头 |
| `vwma < ema` 其余 | 橙 `#FF9800` 70 | 空头蓄势 |

### 参数（25 个）

| 组 | 参数 | 默认 | 说明 |
|---|---|---|---|
| — | `swingLen` | 50 | 波段长度（摆动高低点回看周期） |
| — | `swingColorUp` / `swingColorDown` | lime / orange | 上涨 / 下跌腿配色 |
| 波段成交量分布 | `showProfile` | true | 显示分布图 |
| | `showHeatMap` | false | 显示热力图（色块延伸到波段末端） |
| | `showZigZag` | false | 显示折线 |
| | `zigZagStyleInput` | Dotted | 线型（Dotted/Dashed/Solid） |
| | `showPOC` | true | 显示控制点 |
| | `pocWidthInput` | 2 | PoC 线宽 |
| | `pocColor` | red | PoC 颜色 |
| — | `dataSizeInput` | Small | 标签字号 |
| 短期趋势辅助线 | `ema_fast_len` | 20 | 快 EMA 周期 |
| | `show_fast_ema` | true | 显示快 EMA |
| | `ema_color_fast` | `rgb(0,213,255)` | 快 EMA 颜色 |
| V3.3 结构状态机 | `show_cloud` | true | 开启结构云图 |
| | `vwma_len` | 20 | VWMA 周期 |
| | `ema_slow_len` | 60 | EMA 周期 |
| | `pivot_len` | 3 | 枢轴长度 |
| | `struct_max_age` | 25 | 结构最大寿命(根) |
| | `adx_period` | 14 | ADX 周期 |
| | `trend_on` | 25 | 趋势启动阈值 |
| | `trend_off` | 20 | 趋势衰减阈值 |
| | `slope_period` | 5 | 斜率周期 |
| | `slope_thresh` | 0.3 | 斜率阈值 (%) |
| | `spread_thresh` | 0.3 | 乖离阈值 (%) |

### 使用建议与已知问题

- **适用品种**：有真实成交量的个股、期货主力连续、加密货币。**外汇现货 / 指数点位图不适用**（脚本未做 `na(volume)` 兜底）。
- **适用周期**：15m / 1H / 4H / 日线。
- ✅ **【已修复 · 2026-11-01】Delta 显示曾放大 100 倍**：旧版代码先 `*100` 再用 `str.tostring(..., format.percent)`，而 `format.percent` 本身会对入参再 ×100，导致 D 值显示为真实值的 100 倍（如真实 20% 会显示为 2000%）。**现已移除三处 tooltip 中多余的 `*100`，直接以分数形式 `(buy-sell)/volume` 传入 `format.percent`**，显示恢复正常。
- ⚠️ **成交量重复计入**：判定窗 `±binStep` 宽于箱距，总量约 1～2 倍虚高。
- ⚠️ **收盘价归类过粗**：长上下影线的量全部归到收盘价箱，Profile 形态失真。
- ⚠️ **历史腿的 box 与 label 从不清理**：历史块里新建的对象未入池，会一直累积到 500 上限；而轮廓 polyline 每次翻转都删除 → **老波段只剩色块和箭头标签、没有轮廓线**。
- ⚠️ **实时标签位置与历史不一致**：历史用 `isDownMove ? swingTop : swingBottom`，实时两段却用 `not isDownMove ? swingTop : swingBottom`，方向相反（疑似复制粘贴漏改）。
- ⚠️ **非热力图模式下 box 参数 `left > right`**：`left = prevSwingIndex + profileWidth`、`right = prevSwingIndex`，几何反向，绘制结果依赖 Pine 内部行为。
- ⚠️ **除零风险**：波段幅度小于 `priceBinSize` 时 `binCount = 0`，`binStep = 0/0`；若各箱量全为 0 则 `volumeRatio = na`。
- ⚠️ **两段约 100 行镜像重复代码**（`if not isDownMove` / `else`），且 `else` 分支中 `not isDownMove` 恒为 `false`，逻辑冗余，维护成本高。

---

## 4. `资金加权波段雷达 (VW-KDJ) [微观择时]`

> `indicator("资金加权波段雷达 (VW-KDJ) [安全装甲版]", shorttitle="VW-KDJ", overlay=false)`

### 定位

**微观择时的极值拐点雷达**。用**成交量加权**改造传统 KDJ 的平滑过程，只在超买 / 超卖区发生金叉死叉时出反转信号。

### 核心算法

**① 自适应「装甲」成交量**

```pine
safeVol = na(volume) or volume == 0 ? 1 : volume
custom_vwma(src, len) => math.sum(src * safeVol, len) / math.max(math.sum(safeVol, len), 1e-10)
```

无成交量时权重退化为 1 → **自动降级为 SMA**，保证外汇、指数等无量品种也能运行。这就是"安全装甲版"的核心。

**② 资金加权改造 KDJ**

```pine
src = useVwmaSrc ? custom_vwma(close, 3) : close        // "3日资金均价"

hh  = ta.highest(high, 36)                                // lookback N=36
ll  = ta.lowest (low , 36)
rsv = (src - ll) / math.max(hh - ll, 1e-10) * 100

var2 = custom_vwma(rsv, 3)      // M1 一次资金平滑
var3 = custom_vwma(var2, 3)      // 波 = 资金活跃线  ← 对应 K
var4 = custom_vwma(var3, 3)      // 段 = 资金基准线  ← 对应 D
```

**与经典 KDJ 的差异（关键）**：

| 经典 KDJ | 本脚本 VW-KDJ |
|---|---|
| `RSV = (C − LLV(L,N)) / (HHV(H,N) − LLV(L,N)) × 100` | 相同，但 `C` 可选替换为 **3 日量价加权均价** |
| `K = 2/3·K[1] + 1/3·RSV`（递归 EMA，含全部历史记忆） | `var2 = VWMA(rsv,3)`，**无递归**，仅 3 根窗口 |
| `D = 2/3·D[1] + 1/3·K` | `var3 = VWMA(var2,3)`、`var4 = VWMA(var3,3)`，共三重 VWMA |
| `J = 3K − 2D` | **未实现、不输出 J 线** |

即：**用三重成交量加权移动平均替代了 KDJ 的递归 EMA 平滑**。效果：
- 量大的 K 线对 K/D 贡献更大，"资金说了算"
- 三重 3 周期平滑等效于对 RSV 施加一个长度约 `3+3+3−2 = 7` 根、且被成交量三重加权的复合窗，比经典 (9,3,3) 更短、更灵敏
- 失去递归记忆 → 极值区停留时间变短，回撤更快

**③ 信号触发（修复不对称性）**

```pine
buyCond  = ta.crossover (var3, var4) and var3[1] < osLevel   // 20
sellCond = ta.crossunder(var3, var4) and var3[1] > obLevel   // 80
```

要求「**交叉前一根**」波值处于超卖 / 超买区，避免半山腰的普通金叉死叉。买卖两侧**对称地**要求前置极值。

> 这让信号频率**显著低于**普通 KDJ：必须先触达 <20 / >80 再回叉才出信号。

### 参数（7 个）

| 参数 | 默认 | 说明 |
|---|---|---|
| `lookback` | 36 | 极值回溯周期 (N) |
| `smooth1` | 3 | 资金平滑 1 (M1) |
| `smooth2` | 3 | 资金平滑 2（波 M2） |
| `smooth3` | 3 | 资金平滑 3（段 M3） |
| `obLevel` | 80 | 超买警戒线（可适当下调至 75） |
| `osLevel` | 20 | 超卖警戒线（可适当上调至 25） |
| `useVwmaSrc` | true | 源数据使用 3 日资金均价（屏蔽主力尾盘微量画线） |

### 使用建议与已知问题

- **适用周期**：4H / 日线为主。`lookback=36` 在 5m/15m 上窗口过短噪音大，在周线上信号极稀疏。
- **性能开销极低**（3 次 `math.sum` × 3 层 + 2 次 highest/lowest），可任意叠加。
- ⚠️ **名为 KDJ 但无 J 线**：`J = 3K − 2D` 未实现，标题里的 "J" 实际不存在，只有 K/D 两线。
- ⚠️ **平滑非递归**：与经典 KDJ 数学本质不同，**不能直接用经典 (9,3,3) 的经验阈值套用**。`lookback=36` 明显长于经典 9，说明作者定位为"波段"而非"短线"。
- ⚠️ **「3日资金均价」硬编码**：`useVwmaSrc=true` 时的窗口固定为 3，界面无法调整。
- ⚠️ **信号稀疏且滞后**：强势单边市中可能长期无信号；极端行情下 `var3` 可在超买区钝化。
- ⚠️ **VWMA 的「量」是当期量**：在成交量极度不均的市场（如某根巨量长阳），该根会主导 3 日均值，可能反而放大骗线 —— 与"防骗线"的设计初衷存在一定张力。
- ⚠️ **无趋势过滤**：单独使用在震荡市效果好、趋势市易误判，建议与云图 / 宏观指标配合做方向过滤。
- ⚠️ **三个平滑参数是级联相乘关系**：调大 `smooth1` 会整体钝化三条线。

---

## 5. `达利欧宏观看板 V26 (远期细分)`

> `indicator("达利欧宏观看板 V26 (远期)", shorttitle="Dalio_V26", overlay=false, max_lines_count=500, max_labels_count=500)`

### 定位

**远期（1–10 年）国家债务周期与主权健康度沙盘**。对美 / 中 / 日 / 欧四大经济体做「债务率 × 利率 × 名义增长」的利息负担与去杠杆压力评级。

### 核心算法

**① 两种计算模式**（与根目录 `AA国家债务经济数据分析` 完全一致）

```pine
f_calc_val(_mode, _debt, _yield, _gdp) =>
    _mode == "模式A…" ? (_gdp - _yield) : ((_debt / 100) * _yield)
```

**② 五级严重度评分**

模式A（越高越好）：`>3.0→0` / `>1.0→1` / `>0.0→2` / `>−2.0→3` / 其他→4
模式B（越低越好）：`<1.5→0` / `<2.5→1` / `<3.5→2` / `<5.0→3` / 其他→4

**③ 债务放大器 `debt_amp`**

```pine
debt_amp = _debt > 200 ? 2 : _debt > 150 ? 1 : 0
severity = math.min(base + debt_amp, 4)
```

> ⚠️ **与根目录版本的差异**：根目录 `AA国家债务经济数据分析` 用的是**连续**公式 `min(max(0, (debt−100)/50), 2)`；本脚本用的是**离散**三档（>200 加 2、>150 加 1、否则 0）。两者在债务率 150–200 区间会有明显分歧，联用时请注意。

**④ 总计利息压力 TP** 与 **⑤ 趋势感知**

```pine
tp = debt × ((debt/100) × yield)          // 例：250% × 3.75% → 937.5
prev_X = nz(res_X[20], res_X)            // 回看 20 根图表 K 线，死区 ±0.1
```

**⑥ 动态全局评测（多国参与时自适应阈值）**

```pine
urgent_thresh  = active_count <= 1 ? 4.0 : active_count == 2 ? 3.5 : 3.0
warning_thresh = active_count <= 1 ? 3.0 : active_count == 2 ? 2.5 : 2.0

is_urgent  = avg_sev >= urgent_thresh  or avg_debt > 160
is_warning = not is_urgent and (avg_sev >= warning_thresh or avg_debt > 120)
```

> **参与国越少，阈值越严**：单国分析需要 severity = 4 才判定"警戒"。

### 参数（7 个）

| 参数 | 默认 | 说明 |
|---|---|---|
| `calc_mode` | 模式A | 决定计算、严重度分档、趋势方向、参考线 |
| `view_mode` | 利息压力指标 | 三选一：总债务/GDP / 利息压力指标 / 总计利息压力 |
| `show_us` / `show_cn` / `show_jp` / `show_eu` | 全 true | 经济体开关（同步控制评测参与） |
| `font_size` | small | 全局字体大小（tiny/small/normal） |

### 看板（右上，5 列 × 9 行）

| 行 | 内容 |
|---|---|
| 0 | 全局提示（合并 5 列） |
| 1 | 表头：宏观监测 / 🇺🇸美国 / 🇨🇳中国 / 🇯🇵日本 / 🇪🇺欧洲 |
| 2 | 总债务/GDP（>130% 显示橙色） |
| 3 | 指标值（模式A「利差(g−i)」/ 模式B「利息负担」） |
| 4 | 总计利息压力 |
| 5 | 状态诊断（强扩张 / 健康 / 中性 / 压力 / 危机） |
| 6 | 近期趋势（↑改善 / →持平 / ↓恶化） |
| 7 | Dalio 视角（三行综合文案） |
| 8 | 评测状态（✅ 参与 / ⬜ 排除） |

### 使用建议与已知问题

- **适用周期**：**日线及以下**。所有数据请求固定为 `"D"` 日线；在周线 / 月线图上使用会触发「请求周期低于图表周期」限制。
- **适用用途**：大类资产配置与国别风险比较，**不适合短线择时**。
- ⚠️ **欧洲用德国 `TVC:DE10Y` 代理**：欧元区周边国家利差被忽略，EU 债务压力被系统性低估。
- ⚠️ **模式 B 单位标注**：表格一律加 `%`，但模式B 是复合量纲，与模式A 的百分点混用，读盘易混淆。
- ⚠️ **TP 量纲特殊**：`tp` 含债务率平方项，跨经济体横向比较时是非线性的；1200 的「债务螺旋」阈值经验性较强。
- ⚠️ **趋势回看 20 根 = 20 个图表 K 线**：语义随图表周期漂移（日线≈1个月，小时线仅20小时），且宏观数据本就月 / 季更新，20 日比较噪声较大。
- ⚠️ **`f_comp_diag` 债务档位文字重复**：`>200` 输出「极高>200%」、`>150` 输出「极高」，两档同为「极高」，区分度不足。
- ⚠️ **模式字符串依赖完整中文长串匹配**：改动选项文案会静默失效。
- ⚠️ **无告警函数**：无 `alertcondition`，无法创建自动化警报。

---

## 🔗 联动使用指南（根目录 ↔ BBB）

```
第 1 层：宏观定方向
  ├─ 根目录 AA流动性压力指数（宏观分析）   → 美元体系水温 / 系统性风险
  ├─ 根目录 AA国家债务经济数据分析         → 目标国债务周期（含单国深度看板）
  └─ 根目录 AA对冲套利风险                 → 跨国套利的真实成本

第 2 层：中期 / 远期精对
  ├─ BBB 宏观全景 V7.9 (中期细分)         → 3–12 个月货币 / 商业周期
  └─ BBB 达利欧宏观看板 V26 (远期细分)     → 1–10 年四大经济体横向对比

第 3 层：微观择时
  ├─ 根目录 AA情绪观察基础版（微观择时）  → 背离 / 极值共振 / 量能异动 / 筹码
  ├─ 根目录 AA波段分布图（微观择时）      → 波段筹码 + AVWAP + 交易计划
  ├─ BBB 集合RSI及MFI云图的筹码分布       → 波段分布图 + RSI/MFI 双云图
  ├─ BBB 订单流动系统 + 机构级三层云图     → 订单流 Delta + 结构云图
  └─ BBB 资金加权波段雷达 (VW-KDJ)        → 量价加权版 KDJ 拐点
```

### 典型工作流

1. **日常挂机**：根目录宏观类指标常开，保持风险雷达在线。
2. **发现预警**：例如流动性压力指数提示进入「流动性黑洞」。
3. **中期确认**：打开 `BBB 宏观全景 V7.9`，用 M1 动能与铜金比确认活钱流向。
4. **远期排雷**：做长线配置前打开 `BBB 达利欧宏观看板 V26`，确认目标国是否处于负利差死局。
5. **微观择时**：用根目录情绪观察 / 波段分布图，或 BBB 的订单流 / VW-KDJ 定位具体买卖点。

---

## ⚙️ 通用技术说明

- **底层语言**：全部脚本为 **Pine Script v6**
- **数据源依赖**：宏观类脚本高度依赖 TradingView 的 `FRED:`、`ECONOMICS:`、`TVC:`、`COMEX:`、`FX_IDC:` 数据源
- **权限要求**：部分 `ECONOMICS:` / `FRED:` 序列可能需要 TradingView 付费方案（Paid plan）才能获取
- **部署建议**：宏观类脚本建议在**日线（D）或更高时间级别**加载，以过滤日内噪音

### 各脚本 Security 请求次数

| 脚本 | 请求次数 | 周期 |
|---|---|---|
| 宏观全景 V7.9 | 约 19 次 | 全部 `1M` |
| 达利欧 V26 | 12 次 | 全部 `D` |
| 订单流 + 三层云图 | 0 次 | 仅用图表自身数据 |
| VW-KDJ | 0 次 | 仅用图表自身数据 |
| 集合RSI及MFI云图 | 1 次 intrabar | `request.security_lower_tf` |

> Pine 的 `request.security` 上限为 **40 次**。宏观脚本已接近上限，请勿随意新增数据源。
