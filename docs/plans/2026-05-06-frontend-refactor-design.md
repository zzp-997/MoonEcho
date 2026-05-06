# 回声 APP — 前端全量重构设计文档

> **文档版本**：v1.0
> **创建时间**：2026-05-06
> **设计风格**：纯净白 · 暖橘点缀 — 干净、清晰、安全
> **核心原则**：业务优先使用 wot-design-uni 组件库，可增加样式美化，业务独有组件自定义设计

---

# 一、设计风格定义

## 1.1 风格关键词

纯净白背景、暖橘品牌色、简洁克制、功能清晰、低刺激、安全包容

## 1.2 设计理念

以「纯净容器」为核心，纯白背景让内容呼吸，暖橘点缀传递温暖。日间干净清晰，夜间自动切换深色沉浸。所有颜色走 CSS 变量，一套设计系统覆盖双主题。

## 1.3 设计禁忌

- 禁止颜色硬编码，必须使用 CSS 变量
- 禁止用文本/emoji 模拟图标，必须使用 `wd-icon` 或图片资源
- 禁止页面独立深色主题（如 `treehole-force-dark`），走统一夜间模式
- 禁止大量自定义组件替代组件库已有组件

---

# 二、色彩系统

## 2.1 日间模式（8:00-20:00 默认）

### 背景层次

| 变量 | 色值 | 用途 |
|------|------|------|
| `--bg-primary` | #ffffff | 主画布 |
| `--bg-secondary` | #f5f5f5 | 次级表面、分隔区 |
| `--bg-tertiary` | #eeeeee | 下陷区域、输入框 |
| `--bg-elevated` | #ffffff | 弹窗/浮层（带阴影） |

### 文字色

| 变量 | 色值 | 用途 |
|------|------|------|
| `--text-primary` | #1a1a1a | 主文字 |
| `--text-secondary` | #666666 | 次要文字 |
| `--text-muted` | #999999 | 弱文字/占位符 |
| `--text-disabled` | #cccccc | 禁用文字 |

### 品牌色

| 变量 | 色值 | 用途 |
|------|------|------|
| `--brand-primary` | #FF9A5C | 暖橘 CTA |
| `--brand-hover` | #e88a4a | hover 变体 |
| `--brand-light` | rgba(255,154,92,0.1) | 浅橘背景 |
| `--brand-active` | #d47a3e | active 按下 |

### 功能色

| 变量 | 色值 | 用途 |
|------|------|------|
| `--color-success` | #8FCCA0 | 浅绿/成功 |
| `--color-warning` | #FFB020 | 警告 |
| `--color-error` | #E53935 | 错误/危险 |
| `--color-info` | #8BA7C4 | 灰蓝/信息 |

### 边框色

| 变量 | 色值 | 用途 |
|------|------|------|
| `--border-light` | #f0f0f0 | 极淡分隔线 |
| `--border-standard` | #e0e0e0 | 标准边框 |
| `--border-interactive` | #d0d0d0 | 交互元素边框 |

## 2.2 夜间模式（20:00-8:00 自动）

### 背景层次

| 变量 | 色值 | 用途 |
|------|------|------|
| `--bg-primary` | #0f0f13 | 深黑背景 |
| `--bg-secondary` | #1a1a20 | 卡片/面板 |
| `--bg-tertiary` | #24242c | 输入框/下陷区域 |
| `--bg-elevated` | #1a1a20 | 弹窗/浮层 |

### 文字色

| 变量 | 色值 | 用途 |
|------|------|------|
| `--text-primary` | #f0f0f2 | 主文字 |
| `--text-secondary` | #a0a0ac | 次要文字 |
| `--text-muted` | #6a6a78 | 弱文字 |
| `--text-disabled` | #4a4a56 | 禁用文字 |

### 品牌色（夜间提亮15%）

| 变量 | 色值 | 用途 |
|------|------|------|
| `--brand-primary` | #FFB07A | 暖橘（夜间提亮） |
| `--brand-hover` | #e89560 | hover 变体 |
| `--brand-light` | rgba(255,176,122,0.12) | 浅橘背景 |
| `--brand-active` | #d48550 | active 按下 |

### 边框色

| 变量 | 色值 | 用途 |
|------|------|------|
| `--border-light` | rgba(255,255,255,0.04) | 极淡 |
| `--border-standard` | rgba(255,255,255,0.08) | 标准 |
| `--border-interactive` | rgba(255,255,255,0.12) | 交互 |

## 2.3 情绪色调系统（PRD定义，双主题适配）

| 色调 | 变量 | 日间色值 | 夜间色值 | 含义 |
|------|------|----------|----------|------|
| 暖橘 | `--mood-warm` | #FF9A5C | #FFB07A | 充满能量、开心 |
| 浅绿 | `--mood-calm` | #8FCCA0 | #a8e6b8 | 平静安稳 |
| 灰蓝 | `--mood-low` | #8BA7C4 | #a3bdd4 | 低落沉闷 |
| 深蓝 | `--mood-sad` | #4A6FA5 | #6b8fc0 | 难过忧伤 |
| 暗紫 | `--mood-chaos` | #6B4C7A | #8b6c9a | 崩溃混乱 |

情绪色调背景变体：`rgba(R,G,B,0.1)` 日间，`rgba(R,G,B,0.12)` 夜间

---

# 三、字体系统

## 3.1 字体家族

```scss
--font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC',
  'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
```

## 3.2 字号

| 变量 | 值 | 用途 | 字重 |
|------|-----|------|------|
| `--font-size-xs` | 11px | 标签小字、时间戳 | 400 |
| `--font-size-sm` | 13px | 辅助说明、列表副标题 | 400 |
| `--font-size-base` | 15px | 正文、对话内容、日记 | 400 |
| `--font-size-md` | 17px | 较大正文、输入框、AI回复 | 500 |
| `--font-size-lg` | 20px | 模块标题、卡片标题 | 600 |
| `--font-size-xl` | 24px | 页面标题 | 700 |
| `--font-size-2xl` | 28px | 大标题、登录页标题 | 700 |

## 3.3 字重

| 变量 | 值 | 用途 |
|------|-----|------|
| `--font-weight-regular` | 400 | 正文 |
| `--font-weight-medium` | 500 | UI中等强调 |
| `--font-weight-semibold` | 600 | 标题 |
| `--font-weight-bold` | 700 | 主要标题 |

## 3.4 行高

| 文本类型 | 行高 |
|----------|------|
| 正文/对话/日记 | 1.6 |
| 辅助文本/标签 | 1.4 |
| 页面标题 (24px+) | 1.2 |
| 大标题 (28px) | 1.1 |

---

# 四、间距系统

| 变量 | 值 | 用途 |
|------|-----|------|
| `--space-2xs` | 4px | 组件内部微小间距 |
| `--space-xs` | 8px | 组件内部间距 |
| `--space-sm` | 12px | 卡片内部间距 |
| `--space-md` | 16px | 页面内模块间距 |
| `--space-lg` | 24px | 页面上下内边距 |
| `--space-xl` | 32px | 页面头部大留白 |
| `--space-2xl` | 48px | 登录页大留白 |

---

# 五、圆角系统

| 变量 | 值 | 用途 |
|------|-----|------|
| `--radius-sm` | 6px | 按钮、输入框、小标签 |
| `--radius-md` | 12px | 卡片、对话框 |
| `--radius-lg` | 18px | 大卡片、弹窗 |
| `--radius-full` | 9999px | 药丸按钮、头像 |

---

# 六、阴影系统

## 6.1 日间阴影

```scss
--shadow-card: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
--shadow-hover: 0 4px 12px rgba(0,0,0,0.1);
--shadow-input: none;
--shadow-input-focus: 0 0 0 2px rgba(255,154,92,0.2);
```

## 6.2 夜间阴影（深色背景上阴影不可见，用边框替代）

```scss
--shadow-card: none;
--shadow-hover: none;
--shadow-input: none;
--shadow-input-focus: 0 0 0 2px rgba(255,176,122,0.25);
```

---

# 七、wot-design-uni 主题覆盖

## 7.1 日间模式变量覆盖

```scss
:root {
  --wd-color-theme: #FF9A5C;
  --wd-color-theme-light: rgba(255, 154, 92, 0.1);
  --wd-color-theme-dark: #e88a4a;

  --wd-color-success: #8FCCA0;
  --wd-color-warning: #FFB020;
  --wd-color-danger: #E53935;
  --wd-color-info: #8BA7C4;

  --wd-bg: #ffffff;
  --wd-bg-secondary: #f5f5f5;

  --wd-text-primary: #1a1a1a;
  --wd-text-secondary: #666666;
  --wd-text-muted: #999999;

  --wd-border-color: #e0e0e0;
  --wd-radius-md: 12px;
}
```

## 7.2 夜间模式变量覆盖

```scss
.dark {
  --wd-color-theme: #FFB07A;
  --wd-color-theme-light: rgba(255, 176, 122, 0.12);
  --wd-color-theme-dark: #e89560;

  --wd-color-success: #a8e6b8;
  --wd-color-danger: #ef5350;
  --wd-color-info: #a3bdd4;

  --wd-bg: #0f0f13;
  --wd-bg-secondary: #1a1a20;

  --wd-text-primary: #f0f0f2;
  --wd-text-secondary: #a0a0ac;
  --wd-text-muted: #6a6a78;

  --wd-border-color: rgba(255, 255, 255, 0.08);
}
```

---

# 八、导航结构

## 8.1 底部 TabBar（4+1 结构）

| 位置 | 图标 | Tab | 页面路径 | 说明 |
|------|------|-----|---------|------|
| 1 | home | 首页 | pages/home/index | AI对话 + 情绪速记入口 |
| 2 | calendar | 日记 | pages/diary/index | 情绪日记列表 + 周报 |
| 3 | add | 发布 | ActionSheet 弹出 | 统一发布入口 |
| 4 | compass | 广场 | pagesSocial/square/index | 顶部 wd-tabs 切换树洞/动态 |
| 5 | user | 我的 | pages/mine/index | 个人中心 + 设置 |

## 8.2 TabBar 样式

| 项目 | 日间 | 夜间 |
|------|------|------|
| 背景 | #ffffff | #0f0f13 |
| 未选图标 | #999999 | #6a6a78 |
| 选中图标 | #FF9A5C | #FFB07A |
| 未选文字 | #999999 | #6a6a78 |
| 选中文字 | #FF9A5C | #FFB07A |
| 上边框 | #f0f0f0 | rgba(255,255,255,0.04) |

---

# 九、组件使用规范

## 9.1 核心原则

1. **wot-design-uni 优先**：组件库已有组件直接使用，仅覆盖主题变量
2. **样式增强**：可通过 CSS 覆盖美化组件库组件外观，但不重新实现功能
3. **自定义组件**：仅用于业务独有场景（情绪色调选择器、社交能量条等）

## 9.2 组件替换清单

| 原实现 | 替换为 | 适用页面 |
|--------|--------|---------|
| 文本模拟图标 `[xxx]` / `<` / `>` / `...` / `✓` | `wd-icon` | 全部页面 |
| 自定义导航栏 | `wd-navbar` | 全部页面 |
| 手写 Tab 切换 | `wd-tabs` | 广场、消息 |
| 手写搜索框 | `wd-search` | 好友列表 |
| 手写列表项 | `wd-cell` | 设置、好友、通知 |
| 手写开关 | `wd-switch`（已部分使用） | 设置、通知 |
| 手写滑动删除 | `wd-swipe-action` | 通知列表、日记列表 |
| 手写弹窗 | `wd-popup`（已部分使用） | 全部弹窗 |
| 手写按钮 | `wd-button` | 全部操作按钮 |
| 手写输入框 | `wd-input` / `wd-textarea` | 登录、发布、编辑 |
| 手写标签 | `wd-tag` | 情绪标签、AI画像 |
| 手写空状态 | `wd-empty` | 列表空态 |
| 手写下拉刷新 | `wd-pull-refresh` | 列表页 |
| 手写骨架屏 | `wd-skeleton` | 加载态 |
| 手写 ActionSheet | `wd-action-sheet`（已部分使用） | 发布入口 |

## 9.3 自定义业务组件

| 组件 | 说明 | 设计规范 |
|------|------|---------|
| EmotionToneSelector | 5色圆形情绪色调选择器 | 选中放大 + 暖橘外圈，走情绪CSS变量 |
| EmotionLabelPicker | 情绪标签选择器（最多3个） | 基于 `wd-tag` 扩展，选中态暖橘填充 |
| SocialEnergyBar | 社交能量条 | 渐变进度条，走主题变量 |
| EmotionCard | 左侧4px情绪色装饰条卡片 | 日记详情、树洞帖子、AI关怀 |
| AIBubble | AI对话气泡 | 18px圆角，`--bg-secondary`背景 |
| UserBubble | 用户消息气泡 | 18px圆角，`--brand-primary`背景，白字 |

---

# 十、主题切换实现

## 10.1 切换规则

| 模式 | 规则 | 优先级 |
|------|------|--------|
| 自动（默认） | 8:00-20:00 日间，20:00-8:00 夜间 | 最低 |
| 跟随系统 | 读取系统深色模式设置 | 中 |
| 手动 | 设置页一键切换 | 最高 |

## 10.2 技术方案

```
App.vue
  └─ <wd-config-provider :themeVars="themeVars" :theme="isDark ? 'dark' : 'light'">
       └─ <router-view />
```

**themeVars 动态计算**：
- `settingsStore.themeMode` → `'light' | 'dark' | 'system' | 'auto'`
- `isDarkMode()` → 结合时间段/系统设置/手动判断
- `themeVars = isDark ? darkVars : lightVars`

**切换过渡**：
```scss
page {
  transition: background-color 0.3s, color 0.3s, border-color 0.3s;
}
```

## 10.3 设置页入口

设置 → 外观 → 主题模式
- 日间模式
- 夜间模式
- 自动切换（8:00-20:00 日间）
- 跟随系统

---

# 十一、页面级改动清单

## 11.1 导航结构变更

| 变更 | 说明 |
|------|------|
| TabBar 从5项改为4+1 | 首页、日记、[+]发布、广场、我的 |
| 删除 community Tab | 合并到广场Tab |
| 删除 chat Tab | AI对话入口移到首页 |
| 全局背景色 | `#f7f4ed` → `#ffffff` |
| TabBar激活色 | `#1c1c1c` → `#FF9A5C` |

## 11.2 各页面改动详情

### auth 模块

| 页面 | 改动类型 | 改动内容 |
|------|----------|---------|
| login.vue | 全面重构 | 自定义input→`wd-input`，图标→`wd-icon`，协议→`wd-checkbox`，按钮→`wd-button`，纯净白+暖橘风格 |
| ai-greeting.vue | 重构 | 进度条→`wd-progress`，文案走变量，图标→`wd-icon` |
| profile.vue | 优化 | 年龄段→`wd-radio-group`，图标→`wd-icon`，走主题变量 |
| minor-notice.vue | 优化 | 图标→`wd-icon`，按钮→`wd-button`，卡片走组件库 |
| minor-lock.vue | 重构 | 移除文本模拟图标→`wd-icon`，走统一夜间模式体系 |

### 首页模块

| 页面 | 改动类型 | 改动内容 |
|------|----------|---------|
| home/index.vue | 功能增加+重构 | 集成AI对话入口卡片（原chat Tab），情绪速记保留，图标→`wd-icon`，快捷入口→`wd-grid`，卡片统一 |
| index/index.vue | **删除** | 登录后直接进home |
| add/index.vue | **删除** | [+]按钮改为ActionSheet |

### 对话模块

| 页面 | 改动类型 | 改动内容 |
|------|----------|---------|
| chat/index.vue | 重构 | 图标→`wd-icon`，输入框走组件风格，气泡走主题变量，增加返回导航 |
| chat/personality.vue | 重构 | 性格卡片美化，头像→真实图片/插画，选中态→暖橘边框+阴影 |

### 日记模块

| 页面 | 改动类型 | 改动内容 |
|------|----------|---------|
| diary/index.vue | 重构 | 导航→`wd-navbar`，周报入口美化，快速记录→`wd-card`，图标→`wd-icon` |
| diary/edit.vue | 优化 | 色调选择器暖橘化，标签→`wd-tag`，输入走主题变量 |
| diary/weekly-report.vue | 优化 | 卡片美化，图标→`wd-icon`，图表考虑引入uCharts |

### 广场模块（合并树洞+动态）

| 页面 | 改动类型 | 改动内容 |
|------|----------|---------|
| 广场统一页 | **新增功能** | 顶部`wd-tabs`切换「树洞/动态」 |
| square/index.vue (主包) | **删除** | 占位页，功能由子包统一广场页替代 |
| pagesSocial/square/index.vue | 重构 | 增加顶部`wd-tabs`树洞/动态切换，走统一主题 |
| pagesSocial/square/publish.vue | 优化 | 图标→`wd-icon`，身份切换→`wd-switch` |
| pagesSocial/square/detail.vue | 重构 | 图标→`wd-icon`，互动区美化 |
| pages/treehole/* (3文件) | **删除** | 与子包重复，统一到子包 |
| pagesSocial/treehole/* | 重构 | 移除`treehole-force-dark`，走统一夜间模式 |
| community/index.vue | **删除** | 功能合并到广场Tab |

### 好友模块

| 页面 | 改动类型 | 改动内容 |
|------|----------|---------|
| friends/index.vue | 重构 | 好友列表→`wd-cell`，搜索→`wd-search`，图标→`wd-icon` |
| friends/requests.vue | 优化 | 申请卡片→`wd-cell`，图标→`wd-icon` |
| friends/profile.vue | 优化 | 标签→`wd-tag`，更多菜单→`wd-action-sheet` |
| friends/request.vue | 优化 | AI帮我想想→`wd-button`，输入→`wd-textarea` |

### 消息/通知

| 页面 | 改动类型 | 改动内容 |
|------|----------|---------|
| message/index.vue | 重构 | Tab→`wd-tabs`，列表→`wd-cell`/`wd-swipe-action` |
| notification/list.vue | 重构 | 滑动删除→`wd-swipe-action`，图标→`wd-icon` |
| notification/settings.vue | 优化 | 列表→`wd-cell`，图标→`wd-icon` |

### 设置/个人

| 页面 | 改动类型 | 改动内容 |
|------|----------|---------|
| settings/index.vue | 重点重构 | 文本图标→`wd-icon`，列表→`wd-cell`分组，新增主题模式入口 |
| profile/edit.vue | 优化 | 头像→`wd-upload`，输入→`wd-input`/`wd-textarea` |
| profile/ai-tags.vue | 优化 | 标签→`wd-tag`，图标→`wd-icon` |
| mine/index.vue | 重构 | 功能列表→`wd-cell`，图标→`wd-icon`，社交级别美化 |

### 组件改动

| 组件 | 改动内容 |
|------|---------|
| MessageBubble/PrivateMessageBubble | 走主题变量，图标→`wd-icon` |
| ChatInput/MessageInput | 输入走组件风格，图标→`wd-icon` |
| CrisisDialog/GentleExit/ExportDialog/PrivacyConsentDialog | 弹窗→`wd-popup`，按钮→`wd-button` |
| DiaryCalendar | 走主题变量，美化色块 |
| DiaryListItem | 滑动删除→`wd-swipe-action` |
| EmotionChart | 考虑引入uCharts替换纯CSS |
| EmotionToneSelector/EmotionLabelPicker | 走主题变量，选中态暖橘化 |
| PostCard (treehole/square) | 移除强制深色，走统一主题，图标→`wd-icon` |
| TopicFilter | →`wd-tabs`或`wd-tag`横向滚动 |
| SocialEnergyBar | 保留自定义，美化样式走变量 |
| SocialLevelGuide | 美化，图标→`wd-icon` |
| ReportDialog | 图标→`wd-icon` |

## 11.3 功能增减汇总

| 类型 | 内容 | 原因 |
|------|------|------|
| **增加** | 首页集成AI对话入口 | chat Tab删除，入口移入首页 |
| **增加** | 广场Tab内树洞/动态切换 | 合并两模块，顶部wd-tabs |
| **增加** | 自动夜间模式（8pm-8am） | 用户体验核心，PRD P2前置 |
| **增加** | 设置页主题模式入口 | 主题切换的操控入口 |
| **删除** | index/index.vue | 登录后直接进首页 |
| **删除** | add/index.vue | [+]改ActionSheet |
| **删除** | community/index.vue | 合并到广场 |
| **删除** | pages/treehole/* 主包版 | 与子包重复 |
| **删除** | chat Tab（独立Tab） | 合并到首页入口 |
| **删除** | `treehole-force-dark` 强制深色 | 走统一夜间模式体系 |

---

> 文档版本：v1.0
> 更新时间：2026-05-06
