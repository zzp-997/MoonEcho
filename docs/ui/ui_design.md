# 回声 APP — UI设计规范文档（新版重构）

> **文档版本**：v3.4
> **更新时间**：2026-05-06
> **设计师**：UI Designer Agent + frontend-developer + Behavioral Nudge Engine
> **文档状态**：基于「Airbnb 官网设计系统」重构
> **设计风格**：温暖人文 · 简洁纯净 — 贴合「深夜情绪急救站」定位
> **核心原则**：不修改任何产品功能/内容，仅优化UI视觉与布局

---

# 零、设计系统来源

## 0.1 参考方案：Airbnb Design System

以 Airbnb 官网设计系统为蓝本，打造适合"深夜情绪急救站"的独特风格：

| 参考系统 | 贡献 | 说明 |
|----------|------|------|
| **Airbnb** | 温暖人文感 | 参考其 Rausch Red 品牌色、三层卡片阴影、温暖字重、纯白背景 |
| **项目定制** | 情绪色系 | 保留PRD定义的5种情绪色调，强化情绪联想 |

## 0.2 设计方向

```
背景层次：
  #ffffff（纯白）→ #f7f7f7（hover）→ #f2f2f2（次级表面）

品牌色：
  Rausch Red #ff385c（Airbnb 标志性红色）
  Deep Rausch #e00b41（按下/暗色变体）

文字色：
  #222222（Airbnb 暖黑色，非纯黑）
  #6a6a6a（次要文字）
  #929292（弱文字）

风格：
  Airbnb 三层阴影系统 + 纯白背景 + Rausch Red 品牌强调
```

## 0.3 设计系统特点对比

| 维度 | Airbnb | 回声APP |
|------|--------|---------|
| 背景 | #ffffff 纯白 | #ffffff 纯白 |
| 品牌色 | #ff385c Rausch Red | #ff385c Rausch Red |
| 卡片阴影 | 三层阴影系统 | 三层阴影系统 |
| 圆角 | 8px-32px | 4px-32px |
| 字重 | 500-700 | 400-700 |

---

# 一、设计风格定义

## 1.1 设计理念

以「情绪容器」为核心设计理念，打造"像被温柔包裹的私人空间"—— 适配回声APP"年轻人的情绪出口+AI朋友"的定位，用纯白背景、Rausch Red 品牌色、三层阴影系统，传递"安全、倾听、不评判"的产品气质。

## 1.2 风格关键词

纯白背景、Rausch Red 品牌色、三层阴影、温暖字重、柔和圆角、细腻间距、人文感、低焦虑

## 1.3 设计禁忌

- 禁止使用纯黑色文字（应用 #222222 暖黑色）
- 禁止过度使用品牌红色（仅用于 CTA 和品牌时刻）
- 禁止使用过轻字重（300 以下用于标题）
- 禁止使用单层厚重阴影（应用三层渐变阴影）
- 禁止使用尖锐边角（圆角 8px 起）

---

# 二、色彩系统（Airbnb 官网风格）

## 2.1 核心基础色

| 变量名 | 色值 | 用途 | 设计说明 |
|--------|------|------|----------|
| `--bg-primary` | #ffffff | 主背景 | 纯白背景 |
| `--bg-surface` | #ffffff | 卡片背景 | 纯白卡片 |
| `--bg-hover` | #f7f7f7 | Hover状态 | 交互反馈 |
| `--bg-elevated` | #ffffff | 弹窗/浮层 | 纯白浮层 |
| `--bg-input` | #ffffff | 输入框背景 | 纯白输入 |
| `--bg-secondary` | #f2f2f2 | 次级表面 | 圆形导航按钮 |
| `--text-primary` | #222222 | 主文字 | Airbnb 暖黑色（非纯黑） |
| `--text-secondary` | #6a6a6a | 次文字 | 次要文字 |
| `--text-muted` | #929292 | 弱文字 | 占位符、时间戳 |
| `--text-disabled` | rgba(0,0,0,0.24) | 禁用文字 | 禁用状态 |
| `--text-inverse` | #ffffff | 反色文字 | 深色背景上 |

## 2.2 Airbnb 品牌色

| 变量名 | 色值 | 用途 | 设计说明 |
|--------|------|------|----------|
| `--brand-primary` | #ff385c | Rausch Red | Airbnb 标志性红色，主 CTA |
| `--brand-hover` | #e00b41 | Deep Rausch | 按下/暗色变体 |
| `--brand-light` | rgba(255,56,92,0.1) | 浅红色背景 | 品牌色背景 |

## 2.3 Airbnb 功能色

| 变量名 | 色值 | 用途 | 设计说明 |
|--------|------|------|----------|
| `--color-success` | #008A05 | 成功 | Airbnb 成功绿 |
| `--color-warning` | #C13515 | 警告 | Airbnb 警告色 |
| `--color-error` | #ff385c | 错误 | 使用品牌红 |
| `--color-info` | #428bff | 信息 | Legal Blue |

## 2.4 Airbnb 边框色

| 变量名 | 色值 | 用途 |
|--------|------|------|
| `--border-subtle` | rgba(0,0,0,0.02) |
| `--border-light` | rgba(0,0,0,0.08) |
| `--border-standard` | rgba(0,0,0,0.12) |
| `--border-interactive` | rgba(0,0,0,0.15) |
| `--border-input` | #c1c1c1 |

## 2.5 情绪色调系统（品牌核心）

| 色调 | 色值 | 含义 | 背景变体 |
|------|------|------|----------|
| 暖橘 | #FF9A5C | 充满能量、开心 | rgba(255,154,92,0.1) |
| 浅绿 | #8FCCA0 | 平静安稳 | rgba(143,204,160,0.1) |
| 灰蓝 | #8BA7C4 | 低落沉闷 | rgba(139,167,196,0.1) |
| 深蓝 | #4A6FA5 | 难过忧伤 | rgba(74,111,165,0.1) |
| 暗紫 | #6B4C7A | 崩溃混乱 | rgba(107,76,122,0.1) |

---

# 三、字体系统

## 3.1 字体家族

```scss
--font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
  'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
```

## 3.2 字体大小

| 变量名 | 值 | 用途 | 字重 |
|--------|-----|------|------|
| `--font-size-xs` | 10px | 最小文字、标签小字 | 400 |
| `--font-size-sm` | 12px | 辅助说明、时间戳、标签 | 400 |
| `--font-size-base` | 14px | 正文、对话内容、日记文本 | 400 |
| `--font-size-md` | 16px | 较大正文、输入框、AI回复 | 500 |
| `--font-size-lg` | 18px | 强调文本、模块标题（小） | 600 |
| `--font-size-xl` | 20px | 页面子标题、情绪日记标题 | 600 |
| `--font-size-2xl` | 24px | 页面主标题、核心模块标题 | 700 |
| `--font-size-3xl` | 28px | APP名称、登录页标题 | 700 |

## 3.3 Airbnb 字重规范

- **400 (Regular)**：正文、辅助说明
- **500 (Medium)**：UI 中等强调、按钮文字
- **600 (Semibold)**：标题、强调文本
- **700 (Bold)**：主要标题

## 3.4 行高与字间距

| 文本类型 | 行高 | 字间距 |
|----------|------|--------|
| 正文、对话、日记 | 1.6 | 0px |
| 辅助文本、标签 | 1.4 | 0px |
| 页面标题 (24px+) | 1.2 | -0.3px |
| 页面大标题 (28px) | 1.1 | -0.5px |

---

# 四、间距系统

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--space-2xs` | 4px | 组件内部微小间距 |
| `--space-xs` | 8px | 组件内部间距、标签间距 |
| `--space-sm` | 12px | 卡片内部间距、按钮内部间距 |
| `--space-md` | 16px | 页面内模块间距、卡片之间间距 |
| `--space-lg` | 24px | 页面上下内边距、核心模块间距 |
| `--space-xl` | 32px | 页面头部、底部大留白 |
| `--space-2xl` | 48px | 登录页、引导页大留白 |

---

# 五、圆角系统

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--radius-micro` | 4px | 小按钮、小标签 |
| `--radius-std` | 8px | Airbnb 标准按钮 |
| `--radius-badge` | 14px | Airbnb badges |
| `--radius-card` | 20px | Airbnb 标准卡片 |
| `--radius-compact` | 8px | 紧凑卡片 |
| `--radius-container` | 32px | Airbnb 大容器 |
| `--radius-full` | 50% | Airbnb 圆形导航按钮 |

---

# 六、阴影系统（Airbnb 三层阴影）

## 6.1 Airbnb 三层阴影系统

Airbnb 的三层阴影系统创造温暖、自然的提拉效果：

| 层级 | 效果 | 使用场景 |
|------|------|----------|
| Level 0 | 无阴影 | 页面背景、文本块 |
| Card (Level 1) | 三层阴影叠加 | 卡片、输入框 |
| Hover (Level 2) | 单层柔和阴影 | 按钮悬停 |
| Active Focus (Level 3) | 聚焦环 | 聚焦元素 |

## 6.2 阴影变量

```scss
// Airbnb 三层卡片阴影
--shadow-card:
  rgba(0, 0, 0, 0.02) 0px 0px 0px 1px,   // 极淡边框环
  rgba(0, 0, 0, 0.04) 0px 2px 6px,      // 柔和环境阴影
  rgba(0, 0, 0, 0.1) 0px 4px 8px;       // 主要提拉

// Airbnb 悬停阴影
--shadow-hover:
  rgba(0, 0, 0, 0.08) 0px 4px 12px;

// Airbnb 输入框阴影
--shadow-input:
  inset 0px 0px 0px 1px rgba(0, 0, 0, 0.1);

// Airbnb 输入框聚焦阴影
--shadow-input-focus:
  inset 0px 0px 0px 1px rgba(0, 0, 0, 0.1),
  0 0 0 2px rgba(255, 56, 92, 0.4);

// Airbnb 按钮阴影
--shadow-btn:
  rgba(0, 0, 0, 0.2) 0px 1px 0px 0px;
```

---

# 七、按钮样式

## 7.1 Primary Dark 按钮（Airbnb Near-Black）

```scss
.btn-primary-dark {
  background-color: #222222;
  color: #ffffff;
  padding: 0px 24px;
  border-radius: var(--radius-std);
  box-shadow: var(--shadow-btn);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);

  &:hover { background-color: #333333; }
  &:active { transform: scale(0.98); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}
```

**用途**：主要 CTA（开始对话、发布、确认）

## 7.2 Primary CTA 按钮（Airbnb Rausch Red）

```scss
.btn-primary-cta {
  background-color: var(--brand-primary);
  color: #ffffff;
  padding: 0px 24px;
  border-radius: var(--radius-std);
  box-shadow: var(--shadow-btn);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-base);

  &:hover { background-color: var(--brand-hover); }
  &:active { transform: scale(0.98); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}
```

**用途**：登录、注册等核心操作

## 7.3 Ghost/Outline 按钮

```scss
.btn-ghost {
  background-color: transparent;
  color: var(--text-primary);
  padding: 0px 24px;
  border: 1px solid var(--border-interactive);
  border-radius: var(--radius-std);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);

  &:active { opacity: 0.8; background-color: var(--bg-hover); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}
```

**用途**：次要操作（取消、返回、AI润色）

## 7.4 Surface 按钮

```scss
.btn-surface {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  padding: 0px 24px;
  border-radius: var(--radius-std);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);

  &:active { opacity: 0.8; }
}
```

**用途**：第三操作、工具栏按钮

## 7.5 Pill/Icon 按钮

```scss
.btn-pill {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: var(--radius-full);
  opacity: 0.7;
  padding: 6px 12px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);

  &:active { opacity: 0.8; }
  &.active { opacity: 1; }
}

.btn-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  background-color: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}
```

**用途**：附加操作、情绪标签选择、共鸣按钮

---

# 八、卡片样式

## 8.1 标准卡片（Airbnb 三层阴影）

```scss
.card {
  background-color: var(--bg-surface);
  border-radius: var(--radius-card);
  padding: var(--space-md);
  box-shadow: var(--shadow-card);
  transition: all var(--transition-base);

  &:hover { box-shadow: var(--shadow-hover); }
}
```

**用途**：情绪日记卡片、动态广场卡片、AI对话卡片

## 8.2 紧凑卡片

```scss
.card-compact {
  background-color: var(--bg-surface);
  border-radius: var(--radius-compact);
  padding: var(--space-sm);
  box-shadow: var(--shadow-card);
}
```

**用途**：列表项、AI角色选择卡片、通知卡片

## 8.3 特色卡片（情绪卡片）

```scss
.card-featured {
  background-color: var(--bg-surface);
  border-radius: var(--radius-container);
  padding: var(--space-lg);
  box-shadow: var(--shadow-card);
  position: relative;

  // 情绪色调装饰条
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    border-radius: var(--radius-std) 0 0 var(--radius-std);
  }

  &.mood-warm::before { background-color: var(--mood-warm); }
  &.mood-calm::before { background-color: var(--mood-calm); }
  &.mood-low::before { background-color: var(--mood-low); }
  &.mood-sad::before { background-color: var(--mood-sad); }
  &.mood-chaos::before { background-color: var(--mood-chaos); }
}
```

**用途**：情绪日记详情卡片、AI主动关怀卡片

---

# 九、输入框样式

## 9.1 Airbnb 风格输入框

```scss
.input-wrapper {
  display: flex;
  align-items: center;
  background: var(--bg-input);
  border-radius: var(--radius-std);
  padding: 0 var(--space-sm);
  height: 48px;
  box-shadow: var(--shadow-input);
  transition: all 0.2s ease;

  &:focus-within {
    box-shadow: var(--shadow-input-focus);
  }
}
```

---

# 十、Z-Index 层级系统

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--z-dropdown` | 100 | 下拉菜单 |
| `--z-sticky` | 200 | 粘性导航 |
| `--z-fixed` | 300 | 底部导航栏 |
| `--z-modal` | 400 | 弹窗 |
| `--z-toast` | 500 | 提示框 |
| `--z-loading` | 600 | 全局加载 |

---

# 十一、交互反馈规范

## 11.1 点击反馈

- **按钮/卡片**：点击时 opacity 降至 0.8
- **文本链接**：点击时颜色加深，无下划线
- **多选/单选**：选中时使用对应情绪色调填充

## 11.2 状态反馈

- **成功**：Toast 提示（功能色）+ 对勾图标，显示 2 秒
- **失败/警告**：Toast 提示，显示 3 秒
- **未完成**：输入框边框变化，提示文本为 `--text-muted`

---

# 十二、特殊场景适配

## 12.1 H5端适配

| 适配项 | 规范 |
|--------|------|
| 屏幕适配 | 响应式布局，320px-480px |
| 触摸适配 | 最小点击区域 44px×44px |
| 兼容性 | 兼容微信浏览器、Chrome、Safari |

## 12.2 情绪场景适配

| 场景 | 适配规则 |
|------|----------|
| 树洞场景 | 使用 `.card-featured` + 情绪装饰条 |
| 情绪日记 | 根据情绪色调自动适配卡片装饰色 |
| AI对话 | 气泡贴合 AI 角色色 |

---

# 十三、Do's and Don'ts

### Do
- 使用 #222222（暖黑色）用于文字
- 仅将 Rausch Red (#ff385c) 用于主 CTA
- 使用 Airbnb 三层阴影系统
- 使用适中圆角：8px 按钮、20px 卡片
- 使用 500-700 温暖字重范围

### Don't
- 不要使用纯黑 (#000000) 用于文字
- 不要将 Rausch Red 用于背景
- 不要使用过轻字重（300-400 用于标题）
- 不要使用单层厚重阴影
- 不要使用尖锐边角

---

> 注：文档部分内容可能由 AI 生成
