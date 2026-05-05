# MoonEcho UI 设计规范

> 基于 ui_design.md 和 frontend_tech.md 制定统一的 UI 设计标准。
> 版本：v1.4 | 更新：参考 ui_design.md v1.3 + frontend_tech.md v1.1

---

## 0. 设计理念

**核心定位**：深夜情绪容器 — 温暖、安全、私密、不评判

回声的核心使用场景是**深夜**，用户情绪脆弱、需要宣泄。视觉设计必须：
- 降低视觉刺激（**暗色系减少眼睛疲劳**）
- 传递安全感和温度（不是冰冷的工具感）
- 营造私密氛围（像深夜和一个信任的人对话）
- 不增加认知负担（简洁、无干扰）

**风格关键词**：暗色系主调、柔和圆润、微光感、呼吸感

---

## 1. 颜色系统

### 1.1 主题选择
> **默认使用暗色主题**（适合深夜使用场景）

### 1.2 背景色（暗色主题）

| Token | 色值 | 名称 | 用途 |
|-------|------|------|------|
| --bg-primary | #121212 | 深夜黑 | 一级背景（页面底色） |
| --bg-secondary | #1E1E1E | 温暖灰 | 二级背景（卡片、输入框） |
| --bg-tertiary | #2A2A2A | 浅灰 | 三级背景（弹窗、浮层） |
| --bg-card | #1E1E1E | 卡片背景 | 卡片/容器背景 |

### 1.3 文字色（暗色主题）

| Token | 色值 | 名称 | 用途 |
|-------|------|------|------|
| --text-primary | #F5F5F5 | 主文字 | 标题、重要正文 |
| --text-secondary | #B3B3B3 | 次文字 | 辅助说明、时间戳 |
| --text-tertiary | #808080 | 弱文字 | 占位符、禁用状态 |
| --text-on-brand | #FFFFFF | 品牌色上文字 | 按钮/标签上的文字 |

### 1.4 边框色

| Token | 色值 | 用途 |
|-------|------|------|
| --border-primary | #333333 | 卡片分割、列表分隔 |
| --border-secondary | #404040 | 输入框边框 |
| --border-focus | #7C6FE0 | 输入框聚焦态 |

### 1.5 功能色

| Token | 色值 | 用途 |
|-------|------|------|
| --color-success | #4ADE80 | 成功提示 |
| --color-warning | #FBBF24 | 警告提示 |
| --color-error | #F87171 | 错误提示 |
| --color-info | #60A5FA | 信息/链接 |

### 1.6 品牌色

| Token | 色值 | 用途 |
|-------|------|------|
| --brand-primary | #7C6FE0 | 品牌主色 |
| --brand-light | #A89CF5 | 渐变起始、hover |
| --brand-dark | #5B4FC4 | 按下状态 |

### 1.7 情绪色调（品牌核心）

| 色调名称 | 色值 | 含义 | 使用场景 |
|---------|------|------|---------|
| 暖橘 | #FF9A5C | 充满能量、开心 | 正向情绪记录 |
| 浅绿 | #8FCCA0 | 平静、安稳 | 中性情绪 |
| 灰蓝 | #8BA7C4 | 低落、沉闷 | 略显低落的情绪 |
| 深蓝 | #4A6FA5 | 难过、忧伤 | 明显负面情绪 |
| 暗紫 | #6B4C7A | 崩溃、混乱 | 无法名状的复杂情绪 |

**应用原则**：
- 每种颜色都有独立语义，不能混用
- 情绪色用于标识、强调，不作为大面积背景
- 同一页面情绪色调不宜超过2种
- 不只依赖颜色区分，同时配图标/文字

### 1.8 AI 性格色

| AI角色 | 色值 | 含义联想 |
|--------|------|---------|
| 小温 | #FFB5BA | 温暖粉色（温柔姐姐感） |
| 老黑 | #8B9DC3 | 灰蓝色（冷静损友感） |
| 阿理 | #7CB9A0 | 沉稳绿（可靠大哥感） |

### 1.9 色彩可访问性

- 主文字与背景：对比比 >= 7:1（WCAG AAA）
- 次文字与背景：对比比 >= 4.5:1（WCAG AA）

---

## 2. 字体系统

### 2.1 字体家族

```
font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Noto Sans SC', 'Helvetica Neue', sans-serif;
```

### 2.2 字号层级

| 层级 | 字号 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| display | 24px | 600 | 1.3 | 页面主标题 |
| h1 | 24px | 600 | 1.3 | 页面主标题 |
| h2 | 20px | 600 | 1.4 | 区块标题 |
| h3 | 18px | 500 | 1.4 | 小标题 |
| body | 16px | 400 | 1.6 | 正文内容 |
| body-sm | 14px | 400 | 1.5 | 辅助正文 |
| caption | 12px | 400 | 1.4 | 说明文字、时间戳 |
| micro | 10px | 400 | 1.3 | 极小提示 |

### 2.3 CSS 变量

```scss
--font-size-xs: 12px;
--font-size-sm: 14px;
--font-size-base: 16px;
--font-size-md: 16px;
--font-size-lg: 18px;
--font-size-xl: 20px;
--font-size-2xl: 24px;
--font-size-3xl: 32px; // 用于统计数字等特殊场景
```

---

## 3. 间距系统

### 3.1 基础间距单位
> 基于 **4px 基准网格系统**（与 variables.scss 一致）

| Token | 值 | 用途 |
|-------|-----|------|
| --space-2xs | 4px | 紧凑元素间距 |
| --space-xs | 8px | 小元素间距 |
| --space-sm | 12px | 标准内边距 |
| --space-md | 16px | 区块间距 |
| --space-lg | 24px | 大区块间距 |
| --space-xl | 32px | 页面级间距 |
| --space-2xl | 48px | 特大间距 |

### 3.2 应用规则
- 页面左右边距：`var(--space-sm)` (12px)
- 卡片内边距：`var(--space-sm)` (12px)
- 列表项间距：`var(--space-xs)` (8px)
- 输入框内边距：`var(--space-xs)` (8px)

---

## 4. 圆角系统

| Token | 值 | 用途 |
|-------|-----|------|
| --radius-xs | 4px | 小元素（标签、徽章） |
| --radius-sm | 8px | 按钮、输入框 |
| --radius-md | 12px | 卡片、弹窗 |
| --radius-lg | 16px | 大卡片、底部弹窗 |
| --radius-xl | 24px | 特殊大圆角 |
| --radius-full | 9999px | 头像、圆形按钮 |

---

## 5. 阴影系统

| Token | 值 | 用途 |
|-------|-----|------|
| --shadow-sm | 0 1px 2px rgba(0,0,0,0.2) | 微弱浮起 |
| --shadow-md | 0 4px 8px rgba(0,0,0,0.3) | 卡片悬浮 |
| --shadow-lg | 0 8px 24px rgba(0,0,0,0.4) | 弹窗、模态框 |
| --shadow-glow | 0 0 12px rgba(124,111,224,0.3) | 品牌色发光效果 |

---

## 6. 图标规范

### 6.1 图标来源
- **主选**：Lucide Icons（开源、线性风格统一）
- **备选**：Remix Icon、Tabler Icons

### 6.2 图标规范

| 属性 | 规范 |
|------|------|
| 风格 | 线性图标，圆角端点 |
| 线宽 | 1.5px |
| 尺寸 | 16px / 20px / 24px |
| 颜色 | 继承文字颜色或指定功能色 |

### 6.3 核心图标清单

| 功能 | 图标名称 | 用途 |
|------|---------|------|
| 首页/对话 | message-circle / home | AI对话入口 |
| 日记 | book-open / calendar | 情绪日记 |
| 树洞 | wind / eye-off | 匿名吐槽区 |
| 广场 | users / compass | 动态广场 |
| 我的 | user / smile | 个人中心 |
| 发布 | plus / edit-3 | 发布按钮 |
| 情绪 | heart / smile / frown | 情绪选择 |
| 设置 | settings / cog | 设置入口 |

### 6.4 重要提醒
- ❌ **禁止使用 emoji 作为结构图标**
- ✅ 保持简洁，文字优先，图标辅助

---

## 7. 组件规范

### 7.1 按钮

#### 主按钮
```scss
.primary-btn {
  height: 88rpx;
  padding: 0 var(--space-md);
  background-color: var(--brand-primary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--text-on-brand);

  &:active {
    background-color: var(--brand-dark);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}
```

#### 次按钮
```scss
.secondary-btn {
  height: 88rpx;
  padding: 0 var(--space-md);
  background-color: transparent;
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  color: var(--text-primary);

  &:active {
    background-color: var(--bg-tertiary);
  }
}
```

### 7.2 卡片

```scss
.card {
  padding: var(--space-sm);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
}
```

### 7.3 输入框

```scss
.input {
  height: 88rpx;
  padding: 0 var(--space-xs);
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  color: var(--text-primary);

  &:focus {
    border-color: var(--border-focus);
  }

  &::placeholder {
    color: var(--text-tertiary);
  }
}
```

### 7.4 标签/Tag

```scss
.tag {
  display: inline-flex;
  align-items: center;
  padding: var(--space-3xs) var(--space-2xs);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}
```

---

## 8. 动画规范

### 8.1 时长规范

| 类型 | 时长 | 用途 |
|------|------|------|
| micro | 150ms | 按钮点击反馈 |
| normal | 250ms | 展开/收起、状态切换 |
| complex | 350ms | 页面转场 |

### 8.2 支持 reduced-motion

```scss
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 9. 布局规范

### 9.1 页面结构

```
┌─────────────────────────────────┐
│         Status Bar (系统)        │
├─────────────────────────────────┤
│         Header (88rpx)           │
├─────────────────────────────────┤
│                                 │
│         Content Area            │
│         (flex: 1, scroll-y)      │
│                                 │
├─────────────────────────────────┤
│         TabBar (56px + 安全区)   │
└─────────────────────────────────┘
```

### 9.2 底部导航栏规范
- 导航栏高度：56px（含安全区 83px）
- 图标尺寸：24px
- 文字尺寸：10px
- 未选中态：#808080
- 选中态：品牌色 #7C6FE0
- 中间发布按钮：48px 圆形，品牌色背景，白色图标

---

## 10. 组件库选择

> 参考 frontend_tech.md

| 选择项 | 组件库 | 理由 |
|--------|--------|------|
| **主组件库** | wot-design-uni | 原生暗色模式、TypeScript完善、主题定制灵活 |
| **辅助组件库** | uni-ui | 补充官方特色组件、稳定可靠 |
| **自定义组件** | 项目专用 | AI对话气泡、情绪选择器 |

---

## 11. 注意事项

### 11.1 禁止事项
- ❌ 禁止使用 emoji 作为功能图标
- ❌ 禁止随机阴影值
- ❌ 禁止混用多种图标风格
- ❌ 禁止无规则的圆角大小
- ❌ 禁止过多彩色/渐变装饰

### 11.2 推荐做法
- ✅ 使用暗色主题（默认）
- ✅ 使用 CSS 变量管理所有设计 token
- ✅ 保持简洁，减少视觉噪音

---

## 12. 实施检查清单

- [ ] 默认使用暗色主题配色
- [ ] 所有颜色使用 CSS 变量
- [ ] 所有间距使用 8px 基准的间距系统变量
- [ ] 所有圆角使用圆角系统变量
- [ ] 无 emoji 作为功能图标
- [ ] 文字对比度 ≥4.5:1
- [ ] 情绪色调不超过2种/页
