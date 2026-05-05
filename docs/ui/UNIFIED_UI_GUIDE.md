# MoonEcho UI 设计规范

> 统一的设计规范，简洁实用，避免风格错乱
> 版本：v1.0 | 更新：2026-05-05

---

## 核心理念

**深夜情绪容器** — 温暖、安全、私密、不评判

视觉设计必须：
- 降低视觉刺激（暗色系减少眼睛疲劳）
- 传递安全感和温度
- 营造私密氛围
- 不增加认知负担（简洁、无干扰）

**风格关键词**：暗色系主调、柔和圆润、微光感、呼吸感

---

## 1. 颜色系统

### 1.1 暗色主题（默认）

```scss
// 背景色
--bg-primary: #121212;     // 一级背景（页面底色）
--bg-secondary: #1E1E1E;   // 二级背景（卡片、输入框）
--bg-tertiary: #2A2A2A;    // 三级背景（弹窗、浮层）

// 文字色
--text-primary: #F5F5F5;   // 主文字
--text-secondary: #B3B3B3; // 次文字
--text-tertiary: #808080;  // 弱文字（禁用、占位符）

// 边框色
--border-primary: #333333;  // 分割线
--border-input: #404040;    // 输入框边框
--border-focus: #7C6FE0;    // 焦点边框

// 功能色
--color-success: #4ADE80;
--color-warning: #FBBF24;
--color-error: #F87171;
--color-info: #60A5FA;

// 品牌色
--brand-primary: #7C6FE0;  // 品牌主色
--brand-light: #A89CF5;    // hover状态
--brand-dark: #5B4FC4;      // 按下状态
```

### 1.2 情绪色调（用于情绪标识，不用作大面积背景）

| 色调 | 色值 | 含义 |
|------|------|------|
| 暖橘 | #FF9A5C | 开心、正向 |
| 浅绿 | #8FCCA0 | 平静、中性 |
| 灰蓝 | #8BA7C4 | 低落、沉闷 |
| 深蓝 | #4A6FA5 | 难过、忧伤 |
| 暗紫 | #6B4C7A | 崩溃、混乱 |

**应用原则**：
- 每种颜色有独立语义，不能混用
- 不作为大面积背景，仅用于标识
- 同一页面不超过2种情绪色
- 配合图标/文字使用，不只依赖颜色

### 1.3 AI 角色色

| 角色 | 色值 | 感觉 |
|------|------|------|
| 小温 | #FFB5BA | 温暖粉色 |
| 老黑 | #8B9DC3 | 冷静灰蓝 |
| 阿理 | #7CB9A0 | 沉稳绿 |

---

## 2. 字体系统

```scss
--font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Noto Sans SC', sans-serif;

--font-size-xs: 10px;
--font-size-sm: 12px;
--font-size-base: 14px;   // 正文
--font-size-md: 16px;     // 较大正文
--font-size-lg: 18px;     // 标题
--font-size-xl: 20px;     // 大标题
--font-size-2xl: 24px;     // 页面标题
```

| 层级 | 字号 | 字重 | 用途 |
|------|------|------|------|
| H1 | 24px | 600 | 页面主标题 |
| H2 | 20px | 600 | 区块标题 |
| H3 | 18px | 500 | 小标题 |
| Body | 14-16px | 400 | 正文 |
| Caption | 12px | 400 | 说明文字 |

---

## 3. 间距系统（8px 网格）

```scss
--space-2xs: 4px;   // 紧凑间距
--space-xs: 8px;    // 小间距
--space-sm: 12px;   // 标准间距
--space-md: 16px;   // 区块间距
--space-lg: 24px;   // 大区块间距
--space-xl: 32px;   // 页面间距
--space-2xl: 48px;  // 特大间距
```

---

## 4. 圆角系统

```scss
--radius-xs: 4px;     // 标签、徽章
--radius-sm: 8px;     // 按钮、输入框
--radius-md: 12px;    // 卡片、弹窗
--radius-lg: 16px;    // 大卡片
--radius-xl: 24px;    // 底部弹窗
--radius-full: 9999px; // 头像、圆形按钮
```

---

## 5. 阴影系统

```scss
--shadow-sm: 0 1px 2px rgba(0,0,0,0.2);
--shadow-md: 0 4px 8px rgba(0,0,0,0.3);
--shadow-lg: 0 8px 24px rgba(0,0,0,0.4);
--shadow-glow: 0 0 12px rgba(124,111,224,0.3);
```

---

## 6. 图标规范

### 6.1 图标来源
- **主选**：Lucide Icons（线性风格统一）
- **备选**：Remix Icon、Tabler Icons

### 6.2 图标规范
- 风格：线性图标，圆角端点
- 线宽：1.5px
- 尺寸：16px / 20px / 24px
- 颜色：继承文字颜色

### 6.3 核心图标清单

| 功能 | 图标名称 | 用途 |
|------|---------|------|
| 首页 | home / message-circle | AI对话入口 |
| 日记 | book-open / calendar | 情绪日记 |
| 树洞 | wind / eye-off | 匿名吐槽区 |
| 广场 | users / compass | 动态广场 |
| 我的 | user / smile | 个人中心 |
| 发布 | plus / edit-3 | 发布按钮 |
| 情绪 | heart / smile / frown | 情绪选择 |
| 设置 | settings / cog | 设置入口 |

### 6.4 重要提醒
- ❌ **禁止使用 emoji 作为功能图标**
- ✅ 保持简洁，文字优先，图标辅助

---

## 7. 组件规范

### 7.1 按钮

**主按钮**
```scss
.primary-btn {
  height: 88rpx;
  padding: 0 var(--space-md);
  background-color: var(--brand-primary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  font-weight: 500;
  color: #FFFFFF;
}
```

**次按钮**
```scss
.secondary-btn {
  height: 88rpx;
  padding: 0 var(--space-md);
  background-color: transparent;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  color: var(--text-primary);
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
  border: 1px solid var(--border-input);
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

---

## 8. 动画规范

| 类型 | 时长 | 用途 |
|------|------|------|
| micro | 150ms | 按钮点击反馈 |
| normal | 250ms | 展开/收起、状态切换 |
| complex | 350ms | 页面转场 |

```scss
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 9. 底部导航栏

- 高度：56px（含安全区 83px）
- 图标尺寸：24px
- 文字尺寸：10px
- 未选中态：#808080
- 选中态：品牌色 #7C6FE0
- 中间发布按钮：48px 圆形，品牌色背景

---

## 10. 禁止事项

- ❌ 禁止使用 emoji 作为功能图标
- ❌ 禁止随机阴影值
- ❌ 禁止混用多种图标风格
- ❌ 禁止无规则的圆角大小
- ❌ 禁止过多彩色/渐变装饰

---

## 11. 页面结构示例

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

---

## 12. 设计检查清单

- [ ] 默认使用暗色主题配色
- [ ] 所有颜色使用 CSS 变量
- [ ] 所有间距使用 8px 基准的间距系统变量
- [ ] 所有圆角使用圆角系统变量
- [ ] 无 emoji 作为功能图标
- [ ] 文字对比度 ≥4.5:1
- [ ] 情绪色调不超过2种/页
