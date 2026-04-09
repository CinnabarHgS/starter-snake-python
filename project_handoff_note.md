# Battlesnake 项目交接说明

## 1. 当前项目处于什么阶段

目前项目已经完成了从 starter code 到 **heuristic baseline + 第一版 MCTS + mixed-match 实验框架** 的搭建。

当前已经具备：
- 本地 Flask server 框架，按 `PORT` 启动不同蛇实例。fileciteturn12file0
- 本地单局对战脚本 `run_game.py`，使用 Battlesnake CLI、11x11、`hz_hazard_pits`、timeout 1000ms。fileciteturn12file1
- `game_logic.py`：可复用的 heuristic、合法动作、flood fill、简化状态模拟器。fileciteturn12file2
- `logger.py`：自动记录 summary（placement / turns survived / final length / performance score）。
- `batch_run.py`：同版本 self-play 的批量实验。
- `run_game_mixed.py` / `batch_run_mixed.py` / `run_all_mixed_slots.py`：A/B 混编对局与槽位轮换实验。
- `main_heuristic.py`：旧版本 heuristic agent。
- `main_mcts.py`：当前 MCTS agent。

换句话说，现在**不是“能不能实现”阶段，而是“如何通过实验把 MCTS 调到比 heuristic 更强”阶段**。

---

## 2. 当前代码结构建议理解方式

建议把项目分成 4 层看：

### A. Agent 入口层
- `main_heuristic.py`：直接调用 heuristic 选动作
- `main_mcts.py`：调用 `mcts_move(...)`
- `server.py`：把 `/start` `/move` `/end` API 接到具体 agent 上，并写日志。fileciteturn12file0

### B. 规则/评估层
- `game_logic.py`
  - 合法动作判断
  - heuristic move evaluation
  - flood fill
  - simplified simulator `simulate_one_turn(...)`
  - `evaluate_state_for_snake(...)`

这部分是后续优化的核心。

### C. 搜索层
- `mcts.py`
  - Node
  - UCB selection
  - expansion
  - rollout
  - backpropagation

### D. 实验层
- `run_game.py` / `batch_run.py`：同版本 self-play
- `run_game_mixed.py` / `batch_run_mixed.py` / `run_all_mixed_slots.py`：mixed match（新旧版本混编）
- `logger.py`：最终 summary 输出

---

## 3. 当前实验结论（截至现在）

### 3.1 Heuristic baseline
Heuristic baseline 已经稳定，适合作为 baseline 和 rollout policy。

已知较可信的一组 self-play（50 局）结果：
- Average placement: **2.80**
- Average turns survived: **53.48**
- Average final length: **8.98**
- Average performance score: **0.5636**
- Win rate: **22%**

这说明 heuristic baseline：
- 能跑
- 能稳定活到中期
- 适合作 baseline
- 但本身不是很强

### 3.2 Vanilla MCTS
第一版 vanilla MCTS 能跑，但 mixed match 里明显弱于 heuristic baseline。

### 3.3 Heuristic-guided rollout
把 rollout 从 random 改成 heuristic-guided rollout 后，性能有提升，但 still not enough。

### 3.4 新版 leaf evaluation 有效
把 `evaluate_state_for_snake()` 从“只看自己”改成“更看对手相对信息”后，mixed match 提升明显：

**new eval**
- Average placement: **2.90**
- Average turns survived: **64.65**
- Average final length: **6.25**
- Average performance score: **0.5921**
- Win rate: **10%**

**old eval**
- Average placement: **3.30**
- Average turns survived: **44.10**
- Average final length: **5.60**
- Average performance score: **0.4534**
- Win rate: **0%**

结论：
- **新版 evaluation 必须保留**
- 但当前 MCTS 仍未稳定打赢 heuristic baseline

---

## 4. 当前推荐固定配置

在继续做实验之前，建议把当前主线版本固定为：

- `time_limit_ms = 600`
- `ROLLOUT_DEPTH = 4`
- `heuristic-guided rollout`
- `evaluate_state_for_snake = new`

原因：
- 原先每 turn 接近 0.9 秒，太接近 timeout（比赛 timeout 是 1000ms）。fileciteturn12file1
- 降低预算和深度后，mixed match 至少从“明显打不过”提升到“有一定竞争力”。
- `new eval` 的实验已经证明有效。

---

## 5. 接下来最应该做什么

### 优先级 1：调 `EXPLORATION_C`
这是下一步最值得做的实验。

当前 `mcts.py` 里用的是标准 UCB 常数 1.4，但未必最适合这个游戏。

建议做 3 组：
- `EXPLORATION_C = 0.7`
- `EXPLORATION_C = 1.4`
- `EXPLORATION_C = 2.0`

其他全部固定：
- `time_limit_ms = 600`
- `ROLLOUT_DEPTH = 4`
- `evaluate_state_for_snake = new`
- mixed match
- 每槽位 5 局（共 20 局）先筛选

**目的：** 这是一个很清晰的第二个改进点（selection stage tuning）。

---

### 优先级 2：如果 `EXPLORATION_C` 调完还不够，再调 rollout depth
候选值：
- `ROLLOUT_DEPTH = 3`
- `ROLLOUT_DEPTH = 4`
- `ROLLOUT_DEPTH = 5`

注意：
- 不建议马上回到 6
- depth 越深，速度越慢
- 先看 mixed match 总体表现有没有进一步改善

---

### 优先级 3：再考虑 leaf evaluation 的进一步增强
如果参数调优后仍然明显输给 heuristic baseline，可以继续增强 `evaluate_state_for_snake()`：

建议增加的方向：
- `my_length - max_enemy_length` 的权重继续调
- 对 surviving opponent 数量的惩罚继续调
- 增加“我是否处于 head-to-head 优势”的奖励
- 增加“我能否进入更大安全区域”的权重

但这一步要注意：
- 一次只改一个因素
- 不要同时动 4 个权重

---

### 优先级 4：最后再考虑模拟器真实性
当前 `simulate_one_turn(...)` 还是近似环境，主要近似包括：
- food 只会被吃掉，不会重新生成
- hazard 伤害是简化常数
- 对手用 heuristic policy，不是搜索 agent。fileciteturn12file2

这一步当然值得做，但不是当前第一优先。
原因是：
- 改动大
- 容易引入 bug
- 当前 mixed match 已经证明更主要的问题还在“搜索目标和预算”，不是环境近似本身

---

## 6. 现在最正确的实验顺序

### 实验 A：selection 参数实验（推荐先做）
固定当前主线版本，只改 `EXPLORATION_C`。

配置：
- Mixed match
- 每槽位 5 局
- 4 个槽位
- 总共 20 局

比较指标：
- Average placement
- Average turns survived
- Average final length
- Average performance score
- Win rate

### 实验 B：从实验 A 中选一个最佳 `EXPLORATION_C`
然后放大到：
- 每槽位 10 局
- 共 40 局

### 实验 C：必要时再做 rollout depth
只在最佳 `EXPLORATION_C` 上继续测。

---

## 7. 现在怎么跑实验

### 7.1 同版本 self-play
用于看行为风格，不用于最终判断版本强弱。

```powershell
python batch_run.py
```

### 7.2 Mixed match
用于真正比较 **Candidate（MCTS） vs Base（heuristic）**。

如果用自动槽位轮换：

```powershell
$env:EVAL_VERSION="new"
python run_all_mixed_slots.py
```

注意：
- 跑 `old` 和 `new` 两轮时，结果文件必须分开保存
- 不要把 old/new 混在同一个 csv 里

建议命名：
- `mixed_slot_summaries_old.csv`
- `mixed_slot_summaries_new.csv`
- `game_summaries_old.csv`
- `game_summaries_new.csv`

---

## 8. 调参规则（非常重要）

### 规则 1：一次只改一个东西
不要同时改：
- `EXPLORATION_C`
- `ROLLOUT_DEPTH`
- `time_limit_ms`
- evaluation 权重

否则最后看不出到底是哪个因素起作用。

### 规则 2：先小样本筛选，再大样本验证
推荐流程：
- 小实验：每槽位 5 局（总 20 局）
- 大实验：每槽位 10 局或 20 局（总 40/80 局）

### 规则 3：主比较必须用 mixed match
不要再用 `AAAA` vs `BBBB` 的 self-play 平均排名来判断谁更强。

原因：
- 同版本自博弈只能看“行为风格”和“稳定性”
- 真正回答“新版本是否比旧版本强”，必须用：
  - `B A A A`
  - `A B A A`
  - `A A B A`
  - `A A A B`

### 规则 4：结果分开存档
每做完一轮实验，立即把日志和汇总文件改名保存。

---

## 9. 当前最值得报告里写的实验线

目前最完整的一条实验线是：

1. **Heuristic baseline**
2. **Vanilla MCTS**
3. **MCTS + heuristic-guided rollout**
4. **MCTS + heuristic-guided rollout + new evaluation**
5. **MCTS + heuristic-guided rollout + new evaluation + tuned exploration**（下一步要做）

这个结构非常适合报告：
- baseline
- vanilla search
- simulation stage improvement
- evaluation improvement
- selection stage tuning

---

## 10. 当前对代码的小建议

### 建议 1：精简 `main.py`
`main.py` 里还保留了不少旧 heuristic 代码，建议后续删掉或只保留最小入口，不然和 `game_logic.py` 重复。

### 建议 2：把实验配置参数集中管理
建议集中写在 `mcts.py` 或单独 `config.py`：
- `EXPLORATION_C`
- `ROLLOUT_DEPTH`
- `time_limit_ms`

### 建议 3：给每轮实验记一个名字
例如：
- `mcts_v1_random_rollout`
- `mcts_v2_heuristic_rollout`
- `mcts_v3_new_eval`
- `mcts_v4_c07`

这样后面做表格会轻松很多。

---

## 11. 目前项目最重要的一句话结论

**我们已经证明：**
- heuristic baseline 是稳定可用的 baseline
- MCTS 框架已经跑通
- heuristic-guided rollout 有提升
- 新版 opponent-aware evaluation 有显著提升

**但我们还没有证明：**
- 当前 Candidate 已经稳定强于 heuristic baseline

所以接下来工作的核心不是“再发明新算法”，而是：

> **通过 mixed match + 小步调参，把当前 MCTS 调到真正优于 baseline。**

---

## 12. 队友接手后最先做的事（按顺序）

1. 先确认当前主线配置：
   - `time_limit_ms = 600`
   - `ROLLOUT_DEPTH = 4`
   - `EVAL_VERSION = new`
2. 跑 3 组 `EXPLORATION_C` 小实验：
   - 0.7
   - 1.4
   - 2.0
3. 每组 mixed match 跑 20 局（每槽位 5 局）
4. 选最好的一个 `EXPLORATION_C`
5. 用最佳版本做 40 或 80 局 mixed match 验证
6. 如果仍然弱于 baseline，再继续调 evaluation 权重

