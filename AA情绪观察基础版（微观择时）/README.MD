# AA情绪观察基础版（微观择时）

> **Pine Script v6** · 副图指标（0～100 量纲）· `max_labels_count=500`
> 脚本声明：`indicator(title="情绪观察", shorttitle="情绪观察", format=format.price, max_labels_count=500)`

---

## 一、这个指标解决什么问题

它是**微观层面的「情绪极值 + 资金意图」综合雷达**，把六类原本分散的分析手段合并进同一张副图：

| 能力 | 作用 |
|---|---|
| RSI / MACD 柱 双背离检测 | 捕捉常规与**隐藏**顶底背离 |
| MFI 资金流共振 | 用成交量加权验证背离的真实性 |
| CCI 极端偏离 | 刺探 ±200 以上的情绪极限 |
| 筹码重心偏离 | 判断当前价相对 200 日筹码均价的偏离档位 |
| 量能 Z-Score 异动 | 识别天量砸盘 / 爆量抢筹 / 极限缩量 |
| ATR 风控面板 | 直接给出止损距离、均线位置、盈亏比 |

**一句话定位**：宏观指标告诉你"能不能做"，本指标告诉你"现在是不是极值、该不该下手"。

---

## 二、快速上手

### 第 1 步：加载

Pine 编辑器 → 新建指标 → 粘贴本目录同名代码文件 → 添加到图表。

### 第 2 步：选择周期

- ✅ **推荐**：4 小时 / 日线（波段交易）
- ⚠️ 15 分钟以下：背离信号噪音显著增大
- ⚠️ 周线以上：信号极稀疏

### 第 3 步：看这四层

```
① 副图顶部 98.5 高度 ──── T0-T3 指挥官信号丝带（颜色即评级）
② 副图中部 ───────────── RSI 线 + MFI 线 + 双自适应云图 + 背景填充
③ 副图上下边缘 ───────── 背离标签（RSI / RSI+MFI / MACD Hist / 纯 MFI）
④ 副图右侧面板 ───────── ATR / 均线 / 筹码 / 盈亏比 风控信息
```

**丝带颜色含义**：

| 颜色 | 含义 |
|---|---|
| 亮绿 `rgb(0,255,128)` | T0 做多最高指令 |
| 亮红 `rgb(255,50,50)` | T0 逃命 / 清仓指令 |
| 橙 `rgb(255,152,0)` | T1 极值警戒 |
| 青 `rgb(0,213,255)` | T2 风控（盈亏比否决时转红/橙） |
| 白 `rgb(253,253,253)` | T3 前哨 / 无指令 |

---

## 三、核心计算逻辑（代码说明）

### 3.1 RSI 与 MFI 底层

```pine
osc = ta.rsi(src, len)                    // 默认 14

tp  = hlc3
rawMoneyFlow = tp * vwSafeVol
posFlow = tp > tp[1] ? rawMoneyFlow : 0.0
negFlow = tp < tp[1] ? rawMoneyFlow : 0.0
mfiVal  = 100.0 - (100.0 / (1.0 + (sumPosFlow / safeNegFlow)))
```

`vwSafeVol = na(volume) or volume == 0 ? 1.0 : volume` —— **零成交量兜底**，使脚本在无量品种上也能运行（退化为等权）。

### 3.2 防弹枢轴（Pivot）

```pine
oscPivotLow  = ta.pivotlow(osc, lbL, lbR)      // 默认左 3 右 3
macdPivotLow = ta.pivotlow(macdHist, lbL, lbR)
mfiPivotLow  = ta.pivotlow(mfiVal, lbL, lbR)
```

回溯窗口用 `rangeLower`（默认 5）～ `rangeUpper`（默认 60）做**双重约束**，只在合理距离内比较相邻的枢轴。

### 3.3 背离判定（含中轴区间约束）

**RSI 常规底背离**：

```pine
rsiBullAlert = plFound and inRangePl
             and low[lbR] < history_rsiPl_low      // 价格创新低
             and osc[lbR] > history_rsiPl_osc       // RSI 不创新低
             and osc[lbR] < 55.0                    // 必须处于中轴下方
```

**RSI 常规顶背离**：

```pine
rsiBearAlert = phFound and inRangePh
             and high[lbR] > history_rsiPh_high
             and osc[lbR] < history_rsiPh_osc
             and osc[lbR] > 45.0                    // 必须处于中轴上方
```

> 💡 **为什么要加中轴约束**：杜绝「高位误报底背离 / 低位误报顶背离」。`55.0` / `45.0` 这两个硬编码常量是防误报的关键。

**隐藏底背离**：价格不创新低（`low[lbR] > history_rsiPl_low`）但 RSI 创新低（`osc[lbR] < history_rsiPl_osc`）——典型的上升趋势中继信号。

**MACD 柱背离**：额外要求符号约束——底背离要求 `macdHist < 0`（绿柱区），顶背离要求 `macdHist > 0`（红柱区），并配合 `macdTurnUp / macdTurnDown`（连续两根拐头）。

### 3.4 MFI 资金流共振 + 容错窗口

```pine
mfiBullCount = math.sum(mfiBullAlert ? 1 : 0, syncWindow + 1)   // 默认窗口 3
isMfiBullSync = mfiBullCount > 0 or mfiBullCount[lbR] > 0
```

`syncWindow`（默认 3）允许 RSI 与 MFI 的背离点在**前后 3 根 K 线内错开**仍判定共振，避免因一根 K 线的时间差而漏掉信号。

### 3.5 筹码重心（200 日成交量加权均价）

```pine
chipGravityLine = math.sum(vwSafeVol * hlc3, chipLen) / math.max(math.sum(vwSafeVol, chipLen), 1e-10)
chipDistRatio   = (close - chipGravityLine) / math.max(chipGravityLine, 1e-10) * 100.0
```

**自适应标准差**（修正了硬编码 1.0% 的死锁问题）：

```pine
atrBasePct     = (atr / max(close, 1e-10)) * 100.0
chipStdDev     = ta.stdev(chipDistRatio, chipLen)
safeChipStdDev = max(nz(chipStdDev, atrBasePct), atrBasePct * 0.25, 0.05)

chipThreshold = safeChipStdDev * thresholdMult   // 1.0
chipExtreme   = safeChipStdDev * extremeMult      // 2.0
chipNeutral   = max(safeChipStdDev * neutralMult, atrBasePct * 0.1)  // 0.4
```

**七档情绪状态**：

| 条件 | 状态 | 动作提示 |
|---|---|---|
| `> +chipExtreme` | 情绪泡沫 | (空) |
| `> +chipThreshold` | 良性洗盘 | (多) |
| `> +chipNeutral` | 中枢偏强 | (等/多) |
| `[-chipNeutral, +chipNeutral]` | 中枢震荡 | (等) |
| `> −chipThreshold` | 中枢偏弱 | (等/空) |
| `> −chipExtreme` | 底部吸筹 | (多) |
| 其他 | 极限错杀 | (多) |

状态串会自动追加波动率修饰：`(剧烈)` ATR% ≥ 80 / `(极静)` ATR% ≤ 20 / `(稳健)` 其他。

### 3.4.1 缩量赶顶（新增金融逻辑修正）

```pine
is_price_new_high = close >= ta.highest(close[1], 20)
is_rsi_mfi_fumes  = osc < 68 and mfiVal < 65 and (osc < past_20_osc - 3.0)
is_vol_shrinking  = vol_z_score < -0.2
is_blow_off_top   = is_price_new_high and is_rsi_mfi_fumes
                    and is_vol_shrinking and chipDistRatio > chipExtreme
```

> 💡 代码注释特意说明：要求"价创新高 **且** RSI 较 20 日极值衰减 3 点以上"，**避免慢牛锁仓期误触发**。

### 3.6 量能 Z-Score 异动

```pine
vol_z_score = (vwSafeVol - ta.sma(vwSafeVol, volLength)) / ta.stdev(vwSafeVol, volLength)
```

| 阈值 | 默认 | 状态 |
|---|---|---|
| `zScoreExtreme` | 3.0 | 绝户 / 史诗级异动 |
| `zScoreAnomaly` | 2.0 | 常规异动 |
| `zScoreDead` | −1.0 | 极限缩量 |

**四种量价组合**：

| 组合 | 判定式 |
|---|---|
| 🚨 绝户砸盘 `real_juehu` | 极端放量 **且** 实体阴线（实体/振幅 > 0.4）**且** 处于高位 **且** MFI 资金流出 |
| 🚀 史诗抢筹 `epic_buy` | 极端放量 **且** 实体阳线 **且** 处于低位 **且** MFI 资金流入 |
| ⚠️ 异动派发 `normal_dist` | 常规异动（非极端）**且** 实体阴线 **且** 非低位 **且** MFI 流出 |
| 🟢 异动点火 `normal_ignite` | 常规异动 **且** 实体阳线 **且** 非高位 **且** MFI 流入 |

### 3.7 顾比均线（GMMA）中轴带

短期组 6 条 EMA：3 / 5 / 8 / 10 / 12 / 15
长期组 6 条 EMA：30 / 35 / 40 / 45 / 50 / 60

```pine
gmmaNetScore = crossScore + shortOrder + longOrder
// crossScore: 6×6=36 组短长配对，每对 +1/-1，范围 ±36
// shortOrder: 短组内部 5 对排序，范围 ±5
// longOrder : 长组内部 5 对排序，范围 ±5
// 合计范围 ±46
```

配色三档：
- 缠绕区 `|gmmaNetScore| ≤ entangleThreshold(28)` 或长组收缩 → 黄绿渐变
- 多头 `> +28` → 绿色渐变（得分越高越亮）
- 空头 `< −28` → 红橙渐变

### 3.8 5D 综合意图雷达

三层嵌套决策树，输出 `matrixStatus`（状态）+ `matrixAction`（动作）+ `actionCode`（编码）：

**第一层：按筹码偏离分区**
- `chipDistRatio > +chipThreshold` → 高位区
- `chipDistRatio < −chipThreshold` → 低位区
- 其余 → 中枢区

**第二层：按 VW/MFI 共振类型**
- `isTopDiverge` = VW ≥ 70 且 (VW − MFI) > 30 → 价强钱弱
- `isBotDiverge` = VW ≤ 30 且 (MFI − VW) > 30 → 价弱钱强
- `isBullSync` = VW ≥ 70 且 MFI ≥ 65 → 量价齐升
- `isBearSync` = VW ≤ 30 且 MFI ≤ 35 → 量价齐跌

**第三层：按 ADX / 顾比 / K 线形态细分**

完整状态映射（高位区）：

| 子条件 | 状态 | 动作 |
|---|---|---|
| isTopDiverge | 高位无量诱多 | 顶背离逃命 🚨 |
| isBullSync + 阳线 + 低 ATR | 高位锁仓推升 | 防守型持有 |
| isBullSync + 阳线 + 高 ATR | 高位宽幅派发 | 随时雪崩 ⚠️ |
| isBullSync + 阳线 + 中 ATR | 高位极度狂热 | 随时崩盘 ⚠️ |
| isBotDiverge | 强势洗盘黄金坑 | 回调低吸做多 💰 |
| isBearSync + 阴线 + 顾比空头 | 主跌浪彻底确立 | 坚决空仓 |
| isBearSync + 阴线 + 其余 | 高位破位杀跌 | 破位止损 |
| isVwHigh | 高位滞涨预警 | 逐步减仓 |
| 顾比空头 | 均线压制阴跌 | 反抽清仓 |
| 其余 | 高位震荡博弈 | 谨慎持仓 |

低位区与中枢区按同样的对称逻辑展开（中枢区额外包含「放量突破箱体 / 破位跌穿箱体 / 均线开花突破 / 密集区断头铡 / 死水无序震荡 / 中枢缠绕博弈」）。

**最终覆写**（优先级最高，覆盖上面的矩阵结论）：

| 条件 | 状态 | 动作 |
|---|---|---|
| `real_juehu` | 主力清仓逃亡 | 无条件清仓 🚨 |
| `is_blow_off_top` | 高位缩量背离 | 分批止盈/设保护 ⚠️ |
| `epic_buy` | 不计成本抢筹 | 重仓上车 🚀 |

---

## 四、标签系统（实时 vs 确认）

脚本用统一的 `executeLabelEngine()` 函数管理标签，核心区别：

| 类型 | 判定 | 显示 |
|---|---|---|
| **实时预览** | `not barstate.isconfirmed` | 文案后带 `⏳`，每 tick 更新 |
| **滞后确认** | `barstate.isconfirmed` | 收线后定格，进入历史标签池 |

标签池容量 = `maxLabelCount`（默认 120，硬上限 155），超出自动淘汰最旧的标签。

**标签类别**：

- `RSI+MFI底` / `RSI+MFI顶` —— 双共振背离（最重要）
- `RSI底` / `RSI顶` —— 仅 RSI 背离
- `RSI+MFI隐藏底` / `隐藏顶` —— 隐藏背离
- `Hist底` / `Hist顶` / `Hist隐藏底` / `Hist隐藏顶` —— MACD 柱背离
- `潜伏底(MFI背离)` / `撤退顶(MFI背离)` —— 纯 MFI 资金背离（RSI 未确认）

**纯 MFI 信号的去重逻辑**：
```pine
mfiPureBull = mfiBullAlert and rsiBullCountRecent == 0 and not macdBullAlert
```
即**只有当 RSI 与 MACD 都没在同一窗口报过底背离时**才单独弹 MFI 标签，避免相邻 K 线重复弹出冲突标签。

---

## 五、参数速查（17 组）

| 组 | 参数 | 默认 | 说明 |
|---|---|---|---|
| 1. RSI | `len` | 14 | RSI 周期 |
| | `src` | close | 数据源 |
| | `rsiOverbought` | 80 | 超买阈值 |
| | `rsiOversold` | 20 | 超卖阈值 |
| 2. MACD | `macdFast` | 12 | 快线 |
| | `macdSlow` | 26 | 慢线 |
| | `macdSignal` | 9 | 信号线 |
| | `plotMacdBull` 等 4 项 | true | 常规/隐藏 顶底背离开关 |
| 3. 枢轴 | `lbR` | 3 | 枢轴右视距 |
| | `lbL` | 3 | 枢轴左视距 |
| | `rangeUpper` | 60 | 最大回溯范围 |
| | `rangeLower` | 5 | 最小回溯范围 |
| 4. RSI 显示 | `plotBull` 等 4 项 | true | 各类背离显示开关 |
| 5. ATR | `showAtr` | true | 显示 ATR 波动率 |
| | `atrLen` | 14 | ATR 周期 |
| | `atrLookback` | 100 | ATR 极值回溯 |
| | `atrMaxHeight` | 100 | 柱状图高度 |
| 6. MFI | `mfiLen` | 14 | MFI 周期 |
| | `syncWindow` | 3 | MFI 容错窗口(K线数) |
| | `showMfiLine` | true | 显示 MFI 原生折线 |
| 7. CCI | `cciLen` | 20 | CCI 周期 |
| | `cciExtremeOB` | 200 | 极端超买警戒线 |
| | `cciExtremeOS` | −200 | 极端超卖警戒线 |
| 8. 视觉报警 | `showRealTime` | true | 实时预览标签 |
| | `showLagging` | true | 滞后确认标签 |
| | `showBgAlert` | true | 阶梯背景报警 |
| | `maxLabelCount` | 120 | 每类标签池留存数量 |
| 9. 止损面板 | `showAtrPanel` | true | 显示风控面板 |
| | `atrPanelPosStr` | 右上角 | 面板位置（四角可选） |
| | `atrMult` | 2.0 | ATR 止损倍数 (1–4) |
| | `maLen` | 60 | 均线止损周期 |
| | `maType` | EMA | 均线类型（EMA/SMA） |
| | `useAutoPrecision` | true | 价格自适应品种精度 |
| 10. VW-KDJ | `showVwKdj` | true | 显示 VW-KDJ 资金波段 |
| | `vwLookback` | 36 | 极值回溯周期 N |
| | `vwSmooth1/2/3` | 3 / 3 / 3 | 三重资金平滑 |
| | `vwObLevel` | 80 | 超买警戒线 |
| | `vwOsLevel` | 20 | 超卖警戒线 |
| | `vwUseVwmaSrc` | true | 源数据使用 3 日资金均价 |
| 11. 顾比中轴 | `showGmmaBand` | true | 显示中轴顾比带 |
| | `gmmaSrc` | close | 顾比均线数据源 |
| | `entangleThreshold` | 28 | 震荡区强行捕获阈值 |
| 12. 终极方案 | `useVolFilter` | true | 启用量能与右侧过滤 |
| | `volMultInput` | 1.2 | 恐慌盘成交量均线倍数 |
| | `showPctLines` | true | 显示 RSI 生命周期 |
| | `showMfiPctLines` | true | 显示 MFI 生命周期 |
| | `pctLen` | 100 | 分位数通道回溯周期 |
| 13. 筹码 | `chipLen` | 200 | 筹码监控周期(日) |
| | `extremeMult` | 2.0 | 极限偏离倍数 |
| | `thresholdMult` | 1.0 | 常规偏离倍数 |
| | `neutralMult` | 0.4 | 中枢缠绕倍数 |
| 14. 5D 微调 | `diffThreshold` | 30.0 | 背离差值警戒线 |
| | `vwHighLvl` | 70 | VW 超买绝对阈值 |
| | `vwLowLvl` | 30 | VW 超卖绝对阈值 |
| | `mfiBullSyncLvl` | 65 | MFI 多头及格阈值 |
| | `mfiBearSyncLvl` | 35 | MFI 空头及格阈值 |
| | `squeezeMinBars` | 5 | 均线密集需连续确认的K线数 |
| | `atrSqueezeMax` | 40 | 均线密集期最大ATR均值 |
| 15. 小波段核算 | `vwTargetLevel` | 80 | VW 预测目标数值 |
| | `minProfitPct` | 5.0 | 最小预期利润 (%) |
| | `minRrr` | 1.5 | 最低可接受盈亏比 |
| 17. 核心阈值 | `zScoreExtreme` | 3.0 | 绝户/史诗异动阈值 |
| | `zScoreAnomaly` | 2.0 | 常规异动阈值 |
| | `zScoreDead` | −1.0 | 极限缩量阈值 |
| | `bodyRatioMin` | 0.4 | K线实体占振幅最低比例 |
| | `volLength` | 50 | 量能异动基准周期 |

---

## 六、绘图清单

| 元素 | 内容 |
|---|---|
| RSI 线 | 蓝 `#2962FF`，超买转红、超卖转绿 |
| MFI 原生线 | 橙红 `#FF0000` |
| RSI 自适应云图 | 80/20 分位映射价，填充色随分位位置切换 |
| MFI 自适应云图 | 同上 |
| 越界异动填充 | 顶部超常（红）/ 底部真空（绿） |
| ATR 柱状图 | 归一化高度，高波橙 / 低波绿 |
| 水平线 | 中轴线 50（红点线）、超买线 80、超卖线 20 |
| 信号丝带 | 98.5 高度，3px，颜色 = T0-T3 评级 |
| 背离标签 | 见上文「标签类别」 |
| 右侧面板 | 3 列 × 9 行，位置可切四角 |

---

## 七、告警（8 条 alertcondition）

| # | 标题 | 触发 |
|---|---|---|
| 1 | [T0统帅] 强烈做多指令 | T0 且信号为多（史诗抢筹 / 底部共振起爆 / 均线开花突破） |
| 2 | [T0统帅] 紧急逃命/清仓指令 | T0 且信号为空 |
| 3 | [微观量能] 绝户砸盘预警 | `real_juehu` |
| 4 | [微观量能] 史诗抢筹预警 | `epic_buy` |
| 5 | [双背离] RSI+MFI 共振底背离 | `condRsiMfiBot` |
| 6 | [双背离] RSI+MFI 共振顶背离 | `condRsiMfiTop` |
| 7 | [极值共振] 4分以上高危顶部共振 | `topScore >= 4` |
| 8 | [极值共振] 4分以上高胜率底部共振 | `botScore >= 4` 且通过量能过滤 |

**创建方式**：图表上右键 →「添加警报」→ 条件选择本指标 → 下拉选择对应条目。

---

## 八、5 合 1 极值共振打分

**顶部分 `topScore`（满分 5）**
1. `osc >= rsiOverbought` (RSI ≥ 80)
2. `macdTurnDown and macdHist > 0`（红柱开始缩短）
3. `closeCci >= cciExtremeOB` (CCI ≥ 200)
4. `mfiVal >= 80`（资金流超买）
5. `climaxCloudBear`（RSI 与 MFI 同时突破各自 80 分位）

**底部分 `botScore`（满分 5）** —— 对称：RSI ≤ 20 / 绿柱缩短 / CCI ≤ −200 / MFI ≤ 20 / 双云图低位。

≥2 分即触发阶梯背景色（红色深度随分数递增），≥4 分可挂警报。

---

## 九、使用建议

1. **先定方向再看本图**：本指标是**择时**工具，不是**择向**工具。应与宏观指标（流动性压力指数、达利欧看板）联用。
2. **重视"共振"标签**：`RSI+MFI底/顶` 的可信度显著高于单独的 `RSI底/顶`。
3. **量能异动是加速度信号**：`绝户砸盘` / `史诗抢筹` 属于极端事件，出现时往往意味着短期情绪拐点。
4. **盈亏比否决机制**：面板会按 `minProfitPct` 与 `minRrr` 自动否决空间不足的交易，出现「肉小放弃 / 风险失衡」时不要硬做。
5. **隐藏背离用于顺势加仓**：上涨趋势中的隐藏底背离是中继信号，不应当作反转做空依据。

---

## 十、已知问题与限制

1. **标签上限**：`max_labels_count=500`。脚本内部有 3 个标签池（多头 / 空头 / VW-KDJ）+ 14 个实时活动句柄，`safePoolMax = min(maxLabelCount, 155)` 做了硬保护。若把 `maxLabelCount` 调太大，早期标签会被 TradingView 自动回收。
2. **背离需要枢轴确认**：`ta.pivotlow/pivothigh` 需要右侧 `lbR`（默认 3）根 K 线才能确认，因此**信号天然滞后 3 根 K 线**，这是算法固有特性，不是 bug。历史回测时标签位置已用 `offset=-lbR` 修正回枢轴点。
3. **MFI 依赖成交量**：外汇、指数等无量品种上 `volume` 为 `na`，MFI 会退化为等权计算，资金流共振失效。
4. **硬编码常量**：`55.0` / `45.0`（背离中轴约束）、`3`（VW-KDJ 源平滑窗口）等未做成参数，二次开发时需直接改代码。
5. **参数组编号跳跃**：第 16 组之后直接到第 17 组，中间的第 16 组标签未使用（界面上不会显示）。
6. **顾比带位于副图底部**：`fill(hline(5), hline(0))`，与 RSI/MFI 共用同一坐标系，低波动品种上色带可能偏窄不易观察。
