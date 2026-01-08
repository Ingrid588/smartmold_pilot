# SmartMold 数据结构重构总结

## ✅ 已完成

### 1. 数据模型修正 (`models.py`)
**核心原则：App是计算器，存储原始数据，计算派生指标**

- **Step 1 (Viscosity)**: ✅ 已正确
  - 输入字段: `speed_percent`, `speed_mm_s`, `fill_time`, `peak_pressure`
  - 计算字段: `shear_rate`, `viscosity` (App计算)

- **Step 2 (Cavity Balance)**: ✅ 已正确
  - 包含 `test_type` 字段区分 "Short_Shot" 和 "VP_Switch"

- **Step 3 (Pressure Drop)**: ✅ 需在UI层强制枚举
  - Position: Nozzle, Runner, Gate, Part_50%, Part_99%

- **Machine Info**: ✅ 已包含
  - `screw_diameter`, `intensification_ratio`, `max_pressure`

### 2. 种子数据生成器 (`seed_data.py`)
✅ **新文件已创建**

- 生成符合物理规律的原始数据（Raw Data）
- 使用Power Law模型模拟剪切变稀效应
- 所有数据基于真实材料参数（PA6 GF30）
- 测试命令: `python seed_data.py`

关键特性:
- 粘度曲线: 根据速度反推压力和时间（不直接生成粘度）
- 型腔平衡: 区分短射和满射
- 压力降: 使用标准测量位置枚举值
- 工艺窗口: 基于物理边界判断Pass/Fail

### 3. Excel模板更新 (`excel_data_parser.py`)
✅ **已重构**

- **Step1**: 改为 `速度%`, `实际速度`, `填充时间`, `峰值压力`
- **Step2**: 添加 `测试类型` 列（Short_Shot/VP_Switch）
- **Step3**: 使用标准位置枚举值
- **机台参数**: 增加螺杆直径、增压比、最大压力（必填）

新模板特点:
- 使用 `seed_data.py` 生成的真实示例数据
- 说明文档强调"App是计算器"原则
- 所有示例数据符合物理规律

### 4. PDF生成逻辑 (`pdf_generator.py`)
⏳ **待更新** - 当前PDF生成器需要修改为:

1. **数据源**: 从原始数据计算派生指标
   ```python
   # 当前: 直接读取speeds和viscosities
   # 应改为: 读取speed_percent, fill_time, peak_pressure
   #        然后调用algorithms.py计算shear_rate和viscosity
   ```

2. **排版**: 1:1复刻Excel模板布局
   - Header: 三栏布局 (Part Info | Mold Info | Machine Info)
   - Body: 每步独立的 Data Table + Chart
   - Conclusion: 每步下方的结论区域

3. **报告内容**:
   - Step1: 显示原始数据表 + 计算后的粘度曲线图 + 拐点结论
   - Step2: 短射/满射对比表 + 平衡图 + 不合格腔列表
   - 等等...

## 📊 测试数据示例

### Step 1 粘度曲线（原始数据）
```
速度%  | 实际速度(mm/s) | 填充时间(s) | 峰值压力(Bar)
10     | 20            | 12.605      | 6609.7
20     | 40            | 6.166       | 8311.6
35     | 70            | 3.622       | 10214.7
```
→ App计算得到剪切率和粘度曲线

### Step 2 型腔平衡
```
测试类型      | 腔号 | 重量(g)
Short_Shot   | 1    | 6.483
Short_Shot   | 2    | 6.578
...
VP_Switch    | 1    | 12.797
VP_Switch    | 2    | 12.894
```

### Step 3 压力降（标准位置）
```
位置          | 压力(Bar)
Nozzle       | 1200.0
Runner       | 980.2
Gate         | 751.4
Part_50%     | 519.6
Part_99%     | 279.8
```

## 🔧 下一步行动

1. **更新 `scientific_molding_6steps.py`**
   - 修改Demo Data按钮逻辑
   - 填充原始数据而非计算值
   - 调用 `algorithms.py` 实时计算

2. **更新 `pdf_generator.py`**
   - 从原始数据读取
   - 调用计算函数获取派生指标
   - 复刻Excel布局

3. **更新UI显示**
   - 表格显示原始数据列
   - 图表显示计算结果
   - 结论区域显示推荐值

## 📁 生成的文件

- `seed_data.py` - 种子数据生成器
- `seed_data_output.json` - 示例数据输出
- `SmartMold_数据模板_v2.xlsx` - 更新后的Excel模板

## 🎯 核心思想

**App是计算器，不是记录本**
- 用户提供: 原始测量值（Raw Data）
- App计算: 派生指标（Insight）
- 报告展示: 计算结果 + 工程建议
