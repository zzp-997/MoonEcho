# 回声 APP — UI设计规范文档

> 文档版本：v2.0
> 更新时间：2026-05-06
> 设计师：UI Designer Agent + Claude
> 文档状态：基于 Lovable Design System 重构
> 设计风格：温暖 Humanist — 奶油色背景、人文字体、柔和边界

---

## 一、设计风格定义

### 1.1 整体视觉风格

**设计理念**：温暖 Humanist — 像一本精心制作的笔记本

Lovable 的网站通过温暖的克制来传递温暖。整个页面坐在奶油色羊皮纸色调的背景上 (#f7f4ed)，这让它与冷白色 conventions 的大多数开发者工具网站立即区分开来。这不是为极简主义而极简主义 — 这是一种深思熟虑的选择，使其平易近人，几乎是 analog 的感觉，像一本精心制作的笔记本。

**风格关键词**：
- 温暖奶油色背景（#f7f4ed）— 手选的感觉
- Camera Plain Variable 字体 — 人文温暖感
- 不透明度灰度系统 — 统一视觉连贯性
- Inset shadow 按钮 — 可触感的深度
- 边框而非阴影 — 温和的边界定义

**设计参考**：
- Lovable 的温暖克制美学
- 人文字体的 editorial feel
- 通过不透明度实现深度层次

---

## 二、色彩系统

### 2.1 核心色板

| 变量名 | 色值 | 用途 |
|--------|------|------|
| `--bg-cream` | #f7f4ed | 温暖奶油色背景（主背景） |
| `--text-charcoal` | #1c1c1c | 近黑色主文字 |
| `--text-off-white` | #fcfbf8 | 暗色按钮上的文字 |

### 2.2 不透明度灰度系统

所有灰度来自 #1c1c1c 不同透明度，形成统一视觉：

| 变量名 | 色值 | 用途 |
|--------|------|------|
| `--gray-100` | #1c1c1c | 主文字/深色表面 |
| `--gray-83` | rgba(28,28,28,0.83) | 强次要文字 |
| `--gray-82` | rgba(28,28,28,0.82) | 正文 |
| `--gray-muted` | #5f5f5d | 弱文字/占位符/次要说明 |
| `--gray-40` | rgba(28,28,28,0.4) | 交互边框 |
| `--gray-4` | rgba(28,28,28,0.04) | 微妙 hover 背景 |
| `--gray-3` | rgba(28,28,28,0.03) | 几乎不可见的背景 |

### 2.3 边框色系统

| 变量名 | 色值 | 用途 |
|--------|------|------|
| `--border-light` | #eceae4 | 温暖分割线（卡片边框等） |
| `--border-interactive` | rgba(28,28,28,0.4) | 交互边框 |

### 2.4 情绪色调系统（品牌核心）

这五种颜色是产品的灵魂，贯穿整个视觉系统：

| 色调名称 | 色值 | 含义 | 使用场景 |
|---------|------|------|---------|
| 暖橘 | #FF9A5C | 充满能量、开心 | 正向情绪记录 |
| 浅绿 | #8FCCA0 | 平静、安稳 | 中性情绪、稳定状态 |
| 灰蓝 | #8BA7C4 | 低落、沉闷 | 略显低落的情绪 |
| 深蓝 | #4A6FA5 | 难过、忧伤 | 明显负面情绪 |
| 暗紫 | #6B4C7A | 崩溃、混乱 | 无法名状的复杂情绪 |

**情绪色调变体**：
- `--mood-warm-bg`: rgba(255,154,92,0.1)
- `--mood-calm-bg`: rgba(143,204,160,0.1)
- `--mood-low-bg`: rgba(139,167,196,0.1)
- `--mood-sad-bg`: rgba(74,111,165,0.1)
- `--mood-chaos-bg`: rgba(107,76,122,0.1)

### 2.5 AI 角色色系统

| AI角色 | 色值 | 含义联想 |
|--------|------|---------|
| 小温 | #FFB5BA | 温暖粉色（温柔姐姐感） |
| 老黑 | #8B9DC3 | 冷静灰蓝（冷静损友感） |
| 阿理 | #7CB9A0 | 沉稳绿（可靠大哥感） |

### 2.6 功能色系统

| 色值 | 用途 |
|------|------|
| #4ADE80 | 成功 |
| #FBBF24 | 警告 |
| #F87171 | 错误 |
| #60A5FA | 信息 |

---

## 三、字体系统

### 3.1 字体家族

```scss
--font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
  'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
```

### 3.2 字体大小

| 变量名 | 值 | 用途 |
|--------|------|------|
| `--font-size-xs` | 10px | 最小文字 |
| `--font-size-sm` | 12px | 辅助说明 |
| `--font-size-base` | 14px | 正文 |
| `--font-size-md` | 16px | 较大正文 |
| `--font-size-lg` | 18px | 强调 |
| `--font-size-xl` | 20px | 标题 |
| `--font-size-2xl` | 24px | 大标题 |
| `--font-size-3xl` | 28px | 区域标题 |
| `--font-size-4xl` | 32px | 页面标题 |

### 3.3 字重

- **400 (Regular)**: 正文、UI、链接、按钮
- **600 (Semibold)**: 标题、强调

---

## 四、间距系统

### 4.1 基础间距（8px 网格）

| 变量名 | 值 |
|--------|------|
| `--space-2xs` | 4px |
| `--space-xs` | 8px |
| `--space-sm` | 12px |
| `--space-md` | 16px |
| `--space-lg` | 24px |
| `--space-xl` | 32px |
| `--space-2xl` | 48px |
| `--space-3xl` | 56px |
| `--space-4xl` | 80px |
| `--space-5xl` | 96px |
| `--space-6xl` | 128px |

---

## 五、圆角系统

| 变量名 | 值 | 用途 |
|--------|------|------|
| `--radius-micro` | 4px | 小按钮 |
| `--radius-std` | 6px | 标准按钮/输入框 |
| `--radius-compact` | 8px | 紧凑卡片 |
| `--radius-card` | 12px | 标准卡片 |
| `--radius-container` | 16px | 大容器 |
| `--radius-full` | 9999px | 药丸/图标按钮 |

---

## 六、阴影系统

### 6.1 Lovable 阴影哲学

Lovable 的深度系统是故意浅的。系统依赖温暖的边框 (`#eceae4`) 在奶油表面上创造温和的边界感，而不是使用戏剧性的 drop shadows。唯一值得注意的阴影模式是暗色按钮上的 inset shadow — 一种微妙的multi-layer技术，白色高光线位于顶部边缘，而暗环和柔和的 drop 处理底部。这创造了一种触感、pressed-into-surface 的感觉，而不是 hovering-above-surface 的感觉。

### 6.2 阴影变量

| 变量名 | 值 | 用途 |
|--------|------|------|
| `--shadow-none` | none | 无阴影 |
| `--shadow-focus` | rgba(0,0,0,0.1) 0px 4px 12px | Focus 状态 |
| `--shadow-btn-inset` | 多层 inset shadow | 暗色按钮 |

**按钮 Inset Shadow 配方**：
```scss
--shadow-btn-inset:
  rgba(255, 255, 255, 0.2) 0px 0.5px 0px 0px inset,
  rgba(0, 0, 0, 0.2) 0px 0px 0px 0.5px inset,
  rgba(0, 0, 0, 0.05) 0px 1px 2px 0px;
```

---

## 七、按钮样式

### 7.1 Primary Dark 按钮

```scss
.btn-primary-dark {
  background-color: #1c1c1c;
  color: #fcfbf8;
  padding: 8px 16px;
  border-radius: 6px;
  box-shadow: var(--shadow-btn-inset);

  &:active { opacity: 0.8; }
  &:focus { box-shadow: var(--shadow-focus); }
}
```

**用途**: 主要 CTA ("开始构建", "获取开始")

### 7.2 Ghost/Outline 按钮

```scss
.btn-ghost {
  background-color: transparent;
  color: #1c1c1c;
  padding: 8px 16px;
  border: 1px solid rgba(28,28,28,0.4);
  border-radius: 6px;

  &:active { opacity: 0.8; }
  &:focus { box-shadow: var(--shadow-focus); }
}
```

**用途**: 次要操作 ("登录", "文档")

### 7.3 Cream Surface 按钮

```scss
.btn-cream {
  background-color: #f7f4ed;
  color: #1c1c1c;
  padding: 8px 16px;
  border-radius: 6px;

  &:active { opacity: 0.8; }
}
```

**用途**: 第三操作、工具栏按钮

### 7.4 Pill/Icon 按钮

```scss
.btn-pill {
  background-color: #f7f4ed;
  color: #1c1c1c;
  border-radius: 9999px;
  box-shadow: var(--shadow-btn-inset);
  opacity: 0.5;

  &:active { opacity: 0.8; }
}
```

**用途**: 附加操作、计划模式切换、语音录制

---

## 八、卡片样式

### 8.1 标准卡片

```scss
.card {
  background-color: #f7f4ed;
  border: 1px solid #eceae4;
  border-radius: 12px;
  padding: 16px;
}
```

### 8.2 紧凑卡片

```scss
.card-compact {
  background-color: #f7f4ed;
  border: 1px solid #eceae4;
  border-radius: 8px;
  padding: 12px;
}
```

### 8.3 特色卡片

```scss
.card-featured {
  background-color: #f7f4ed;
  border: 1px solid #eceae4;
  border-radius: 16px;
  padding: 24px;
}
```

---

## 九、Z-Index 层级系统

| 变量名 | 值 | 用途 |
|--------|------|------|
| `--z-dropdown` | 100 | 下拉菜单 |
| `--z-sticky` | 200 | 粘性元素 |
| `--z-fixed` | 300 | 固定元素 |
| `--z-modal-backdrop` | 400 | 模态框背景 |
| `--z-modal` | 500 | 模态框 |
| `--z-popover` | 600 | 弹出框 |
| `--z-toast` | 700 | 提示信息 |

---

## 十、动画系统

### 10.1 过渡时长

| 变量名 | 值 | 用途 |
|--------|------|------|
| `--transition-fast` | 0.15s | 微交互 |
| `--transition-base` | 0.3s | 标准过渡 |
| `--transition-slow` | 0.5s | 复杂过渡 |

### 10.2 动画原则

- **Duration**: 150-300ms for micro-interactions
- **Easing**: ease-out for entering, ease-in for exiting
- **Motion conveys meaning**: 每个动画必须表达因果关系
- **Respect reduced-motion**: 支持 `prefers-reduced-motion`

---

## 十一，暗色模式

### 11.1 暗色模式变量

```scss
.theme-dark, .dark {
  --bg-primary: #1c1c1c;
  --bg-secondary: #2a2a2a;
  --bg-tertiary: #3a3a3a;
  --text-primary: #f7f4ed;
  --text-secondary: rgba(247, 244, 237, 0.82);
  --text-tertiary: rgba(247, 244, 237, 0.5);
  --border-primary: #333333;
}
```

### 11.2 树洞强制暗色

树洞区域始终使用暗色，不受主题切换影响：

```scss
.treehole-force-dark {
  background-color: #1c1c1c !important;
  --bg-primary: #1c1c1c;
  --bg-secondary: #2a2a2a;
  --bg-tertiary: #3a3a3a;
  --text-primary: #f7f4ed;
  --text-secondary: rgba(247, 244, 237, 0.82);
  --text-tertiary: rgba(247, 244, 237, 0.5);
  --border-primary: #333333;
}
```

---

## 十二、组件样式

### 12.1 输入框

```scss
.input {
  width: 100%;
  padding: 8px 12px;
  font-size: 16px;
  color: #1c1c1c;
  background-color: #f7f4ed;
  border: 1px solid #eceae4;
  border-radius: 6px;

  &::placeholder { color: #5f5f5d; }
  &:focus {
    outline: none;
    border-color: rgba(28,28,28,0.4);
    box-shadow: rgba(0,0,0,0.1) 0px 4px 12px;
  }
}
```

### 12.2 头像

```scss
.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background-color: #fcfbf8;
  color: #1c1c1c;
  font-weight: 600;

  &-sm { width: 32px; height: 32px; }
  &-md { width: 48px; height: 48px; }
  &-lg { width: 64px; height: 64px; }
}
```

### 12.3 标签

```scss
.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  font-size: 12px;
  color: #1c1c1c;
  background-color: #f7f4ed;
  border: 1px solid #eceae4;
  border-radius: 9999px;
}
```

---

## 十三、设计原则

### 13.1 Do's

- 使用温暖奶油色背景 (`#f7f4ed`) 作为页面基础 — 这是品牌的签名温暖
- 使用 Camera Plain Variable 在显示字号带负 letter-spacing
- 从 `#1c1c1c` 以不同透明度派生所有灰度以获得色调统一
- 在暗色按钮上使用 inset shadow 技术以获得触感深度
- 使用 `#eceae4` 边框代替阴影以获得卡片 containment
- 保持字重系统狭窄：400 for body/UI, 600 for headings
- 仅对操作药丸和图标按钮使用全圆角 (9999px)
- 在活动状态上应用 opacity 0.8 以获得 responsive tactile feedback

### 13.2 Don'ts

- 不要使用纯白色 (`#ffffff`) 作为页面背景 — 奶油色是有意为之
- 不要使用重的 box-shadows 作为卡片 — 边框是 containment 机制
- 不要引入饱和的 accent colors — 调色板是故意 warm-neutral
- 不要使用字重 700 (bold) — 600 是系统中的最大字重
- 不要在矩形按钮上应用 9999px radius — 药丸用于图标/操作切换
- 不要使用尖锐的 focus outlines — 系统使用基于柔和阴影的 focus indicators
- 不要混合边框样式 — `#eceae4` 用于 passive, `rgba(28,28,28,0.4)` 用于 interactive
- 不要在标题上增加 letter-spacing — Camera Plain 设计为在规模上紧密运行

---

## 十四、响应式断点

| 名称 | 宽度 | 关键变化 |
|------|------|---------|
| Mobile Small | <600px | 紧密单列，减少 padding |
| Mobile | 600–640px | 标准移动布局 |
| Tablet Small | 640–700px | 2列网格开始 |
| Tablet | 700–768px | 卡片网格扩展 |
| Desktop Small | 768–1024px | 多列布局 |
| Desktop | 1024–1280px | 全功能布局 |
| Large Desktop | 1280–1536px | 最大内容宽度，宽松边距 |

---

## 十五、CSS 变量快速参考

```scss
// 核心
--bg-cream: #f7f4ed;
--text-charcoal: #1c1c1c;
--text-off-white: #fcfbf8;

// 灰度
--gray-100: #1c1c1c;
--gray-83: rgba(28,28,28,0.83);
--gray-82: rgba(28,28,28,0.82);
--gray-muted: #5f5f5d;
--gray-40: rgba(28,28,28,0.4);
--gray-4: rgba(28,28,28,0.04);
--gray-3: rgba(28,28,28,0.03);

// 边框
--border-light: #eceae4;
--border-interactive: rgba(28,28,28,0.4);

// 阴影
--shadow-focus: rgba(0,0,0,0.1) 0px 4px 12px;
--shadow-btn-inset: [多层 inset shadow];

// 圆角
--radius-std: 6px;
--radius-card: 12px;
--radius-full: 9999px;
```
