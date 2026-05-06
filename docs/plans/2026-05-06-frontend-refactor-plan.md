# 回声 APP 前端全量重构实施计划

> **对于 Claude：** 必需的子技能：使用 executing-plans 按任务逐个实施此计划。

**目标：** 将回声 APP 前端从当前混乱的 UI 状态全面重构为"纯净白 + 暖橘"统一设计系统，集成 wot-design-uni 组件库，实现日间/夜间自动切换主题。

**架构：** 基于 wot-design-uni 的 `wd-config-provider` 全局主题注入 + CSS 变量双主题体系。所有颜色走 CSS 变量，日间模式纯白背景 + 暖橘品牌色，夜间模式深色背景 + 提亮暖橘。组件优先使用 wot-design-uni，业务独有组件自定义但走变量体系。

**技术栈：** Uni-app + Vue3 + TypeScript + wot-design-uni v1.9.2 + Pinia

**设计文档：** `docs/plans/2026-05-06-frontend-refactor-design.md`

---

## 阶段一：设计系统基础（必须最先完成，后续任务依赖此阶段）

### 任务 1：重写 variables.scss — 全新设计变量体系

**文件：**
- 重写：`frontend/src/styles/variables.scss`

**步骤 1：备份旧文件并重写**

将现有 `.login-airbnb` class 删除，写入全新日间+夜间双主题 CSS 变量体系。

```scss
// ============================================
// 回声 - 设计系统变量
// 文件：src/styles/variables.scss
// 说明：纯净白 · 暖橘 — 双主题 CSS 变量
// 参考：docs/plans/2026-05-06-frontend-refactor-design.md
// ============================================

// ==================== 日间模式（默认） ====================
page {
  // 背景层次
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f5;
  --bg-tertiary: #eeeeee;
  --bg-elevated: #ffffff;
  --bg-input: #ffffff;

  // 文字色
  --text-primary: #1a1a1a;
  --text-secondary: #666666;
  --text-muted: #999999;
  --text-disabled: #cccccc;
  --text-inverse: #ffffff;

  // 品牌色
  --brand-primary: #FF9A5C;
  --brand-hover: #e88a4a;
  --brand-active: #d47a3e;
  --brand-light: rgba(255, 154, 92, 0.1);

  // 功能色
  --color-success: #8FCCA0;
  --color-warning: #FFB020;
  --color-error: #E53935;
  --color-info: #8BA7C4;

  // 边框色
  --border-light: #f0f0f0;
  --border-standard: #e0e0e0;
  --border-interactive: #d0d0d0;

  // 阴影
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.1);
  --shadow-input: none;
  --shadow-input-focus: 0 0 0 2px rgba(255, 154, 92, 0.2);
  --shadow-btn: 0 1px 0 0 rgba(0, 0, 0, 0.04);

  // 情绪色调
  --mood-warm: #FF9A5C;
  --mood-warm-bg: rgba(255, 154, 92, 0.1);
  --mood-warm-text: #cc7a3a;
  --mood-calm: #8FCCA0;
  --mood-calm-bg: rgba(143, 204, 160, 0.1);
  --mood-calm-text: #5a9968;
  --mood-low: #8BA7C4;
  --mood-low-bg: rgba(139, 167, 196, 0.1);
  --mood-low-text: #5a7a9a;
  --mood-sad: #4A6FA5;
  --mood-sad-bg: rgba(74, 111, 165, 0.1);
  --mood-sad-text: #3a5580;
  --mood-chaos: #6B4C7A;
  --mood-chaos-bg: rgba(107, 76, 122, 0.1);
  --mood-chaos-text: #503a5a;

  // AI 角色色
  --ai-xiaowen: #FF9A9A;
  --ai-xiaowen-bg: rgba(255, 154, 154, 0.1);
  --ai-laohei: #7A7A8A;
  --ai-laohei-bg: rgba(122, 122, 138, 0.1);
  --ai-ali: #5A8ACA;
  --ai-ali-bg: rgba(90, 138, 202, 0.1);

  // 字体
  --font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  --font-size-xs: 11px;
  --font-size-sm: 13px;
  --font-size-base: 15px;
  --font-size-md: 17px;
  --font-size-lg: 20px;
  --font-size-xl: 24px;
  --font-size-2xl: 28px;
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  // 间距
  --space-2xs: 4px;
  --space-xs: 8px;
  --space-sm: 12px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  // 圆角
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 18px;
  --radius-full: 9999px;

  // 过渡
  --transition-fast: 0.15s;
  --transition-base: 0.3s;

  // Z-Index
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-fixed: 300;
  --z-modal: 400;
  --z-toast: 500;
  --z-loading: 600;
}

// ==================== 夜间模式 ====================
.dark {
  --bg-primary: #0f0f13;
  --bg-secondary: #1a1a20;
  --bg-tertiary: #24242c;
  --bg-elevated: #1a1a20;
  --bg-input: #1a1a20;

  --text-primary: #f0f0f2;
  --text-secondary: #a0a0ac;
  --text-muted: #6a6a78;
  --text-disabled: #4a4a56;
  --text-inverse: #0f0f13;

  --brand-primary: #FFB07A;
  --brand-hover: #e89560;
  --brand-active: #d48550;
  --brand-light: rgba(255, 176, 122, 0.12);

  --color-success: #a8e6b8;
  --color-warning: #ffc94d;
  --color-error: #ef5350;
  --color-info: #a3bdd4;

  --border-light: rgba(255, 255, 255, 0.04);
  --border-standard: rgba(255, 255, 255, 0.08);
  --border-interactive: rgba(255, 255, 255, 0.12);

  --shadow-card: none;
  --shadow-hover: none;
  --shadow-input: none;
  --shadow-input-focus: 0 0 0 2px rgba(255, 176, 122, 0.25);
  --shadow-btn: none;

  --mood-warm: #FFB07A;
  --mood-warm-bg: rgba(255, 176, 122, 0.12);
  --mood-warm-text: #ffca9a;
  --mood-calm: #a8e6b8;
  --mood-calm-bg: rgba(168, 230, 184, 0.12);
  --mood-calm-text: #c0f0d0;
  --mood-low: #a3bdd4;
  --mood-low-bg: rgba(163, 189, 212, 0.12);
  --mood-low-text: #b8d4e8;
  --mood-sad: #6b8fc0;
  --mood-sad-bg: rgba(107, 143, 192, 0.12);
  --mood-sad-text: #8aacda;
  --mood-chaos: #8b6c9a;
  --mood-chaos-bg: rgba(139, 108, 154, 0.12);
  --mood-chaos-text: #a88cba;

  --ai-xiaowen: #ffbaba;
  --ai-xiaowen-bg: rgba(255, 186, 186, 0.12);
  --ai-laohei: #9a9aaa;
  --ai-laohei-bg: rgba(154, 154, 170, 0.12);
  --ai-ali: #7aacda;
  --ai-ali-bg: rgba(122, 172, 218, 0.12);
}
```

**步骤 2：运行 H5 dev 验证变量生效**

运行：`cd frontend && npm run dev:h5`
预期：页面颜色可能暂时异常（因为变量名变了），但不会编译报错

**步骤 3：提交**

```bash
git add frontend/src/styles/variables.scss
git commit -m "refactor: 重写设计系统变量，日间纯净白+夜间深色双主题"
```

---

### 任务 2：重写 theme.scss — 更新 wot-design-uni 覆盖，移除 treehole-force-dark

**文件：**
- 重写：`frontend/src/styles/theme.scss`

**步骤 1：重写 theme.scss**

```scss
// ============================================
// 回声 - 主题核心
// 文件：src/styles/theme.scss
// 说明：页面基础样式、wot-design-uni 主题变量覆盖
// ============================================

// ==================== 页面基础 ====================

page {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: 1.6;
  transition: background-color var(--transition-base) ease,
              color var(--transition-base) ease,
              border-color var(--transition-base) ease;
}

// ==================== wot-design-uni 日间覆盖 ====================

:root {
  --wd-color-theme: var(--brand-primary);
  --wd-color-theme-light: var(--brand-light);
  --wd-color-theme-dark: var(--brand-hover);
  --wd-color-success: var(--color-success);
  --wd-color-warning: var(--color-warning);
  --wd-color-danger: var(--color-error);
  --wd-color-info: var(--color-info);
  --wd-bg: var(--bg-primary);
  --wd-bg-card: var(--bg-secondary);
  --wd-bg-popup: var(--bg-elevated);
  --wd-text: var(--text-primary);
  --wd-text-secondary: var(--text-secondary);
  --wd-text-placeholder: var(--text-muted);
  --wd-border-color: var(--border-standard);
}

// ==================== wot-design-uni 夜间覆盖 ====================

.dark {
  --wd-color-theme: var(--brand-primary);
  --wd-color-theme-light: var(--brand-light);
  --wd-color-theme-dark: var(--brand-hover);
  --wd-bg: var(--bg-primary);
  --wd-bg-card: var(--bg-secondary);
  --wd-bg-popup: var(--bg-elevated);
  --wd-text: var(--text-primary);
  --wd-text-secondary: var(--text-secondary);
  --wd-text-placeholder: var(--text-muted);
  --wd-border-color: var(--border-standard);
}

// ==================== 主题过渡 ====================

.theme-transition {
  transition: background-color var(--transition-base) ease,
              color var(--transition-base) ease,
              border-color var(--transition-base) ease,
              box-shadow var(--transition-base) ease;
}

// ==================== 通用背景类 ====================

.bg-primary { background-color: var(--bg-primary); }
.bg-secondary { background-color: var(--bg-secondary); }
.bg-tertiary { background-color: var(--bg-tertiary); }
.bg-brand { background-color: var(--brand-primary); }
.bg-brand-light { background-color: var(--brand-light); }

// ==================== 通用文字类 ====================

.text-primary { color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.text-muted { color: var(--text-muted); }
.text-brand { color: var(--brand-primary); }

// ==================== 情绪日记覆盖（不受主题影响） ====================

.diary-emotion-override {
  background-color: var(--mood-warm-bg) !important;
}

// ==================== AI 对话气泡 ====================

.bubble-ai {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) var(--radius-sm);
  max-width: 80%;
  padding: var(--space-sm) var(--space-md);
  color: var(--text-primary);
}

.bubble-user {
  background-color: var(--brand-primary);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg);
  max-width: 80%;
  padding: var(--space-sm) var(--space-md);
  color: var(--text-inverse);
}
```

关键变更：
- **移除** `.treehole-force-dark` — 树洞走统一夜间模式
- **移除** `.bg-cream` / `.text-charcoal` / `.text-tertiary` / `.gray-muted` / `.text-on-brand` 等旧Lovable变量引用
- 保留 wot-design-uni 覆盖映射，变量名对齐新的 variables.scss
- 气泡样式改用新变量名

**步骤 2：提交**

```bash
git add frontend/src/styles/theme.scss
git commit -m "refactor: 重写主题核心，移除treehole-force-dark，对齐新变量"
```

---

### 任务 3：重写 dark.scss — 简化为夜间模式组件补丁

**文件：**
- 重写：`frontend/src/styles/dark.scss`

**步骤 1：重写 dark.scss**

```scss
// ============================================
// 回声 - 夜间模式组件补丁
// 文件：src/styles/dark.scss
// 说明：夜间模式下 wot-design-uni 组件的样式补丁
// 核心变量已在 variables.scss .dark 中定义
// ============================================

// 夜间模式下卡片用边框替代阴影
.dark .wd-card {
  border: 1px solid var(--border-standard);
  box-shadow: none;
}

// 夜间模式输入框
.dark .wd-input {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

// 夜间模式弹窗
.dark .wd-popup {
  background-color: var(--bg-elevated);
}

// 夜间模式导航栏
.dark .wd-navbar {
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
}

// 夜间模式TabBar区域（uni-app tabBar 不受 CSS 控制，此处为自定义导航补充）
.dark .custom-tabbar {
  background-color: var(--bg-primary);
  border-top: 1px solid var(--border-light);
}
```

**步骤 2：提交**

```bash
git add frontend/src/styles/dark.scss
git commit -m "refactor: 简化夜间模式组件补丁，核心变量走variables.scss"
```

---

### 任务 4：重写 common.scss — 移除旧Lovable样式，对齐新系统

**文件：**
- 重写：`frontend/src/styles/common.scss`

**步骤 1：重写 common.scss**

保留布局工具类和分割线，移除所有 `.btn-*` / `.card-*` / `.input` / `.tag` / `.avatar` 等自定义组件样式（改用 wot-design-uni 组件）。

```scss
// ============================================
// 回声 - 公共样式
// 文件：src/styles/common.scss
// 说明：全局公共样式、工具类
// ============================================

// 基础重置
view, text {
  box-sizing: border-box;
}

// 安全区域
.safe-area-bottom {
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}
.safe-area-top {
  padding-top: constant(safe-area-inset-top);
  padding-top: env(safe-area-inset-top);
}

// 布局工具类
.flex { display: flex; }
.flex-col { display: flex; flex-direction: column; }
.flex-center { display: flex; align-items: center; justify-content: center; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.flex-1 { flex: 1; }
.items-center { align-items: center; }
.justify-center { justify-content: center; }
.flex-wrap { flex-wrap: wrap; }

// 文字截断
.ellipsis { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ellipsis-2 { display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; }
.ellipsis-3 { display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; overflow: hidden; }

// 间距工具类
.mt-2xs { margin-top: var(--space-2xs); }
.mt-xs { margin-top: var(--space-xs); }
.mt-sm { margin-top: var(--space-sm); }
.mt-md { margin-top: var(--space-md); }
.mt-lg { margin-top: var(--space-lg); }
.mt-xl { margin-top: var(--space-xl); }
.mb-2xs { margin-bottom: var(--space-2xs); }
.mb-xs { margin-bottom: var(--space-xs); }
.mb-sm { margin-bottom: var(--space-sm); }
.mb-md { margin-bottom: var(--space-md); }
.mb-lg { margin-bottom: var(--space-lg); }
.px-xs { padding-left: var(--space-xs); padding-right: var(--space-xs); }
.px-sm { padding-left: var(--space-sm); padding-right: var(--space-sm); }
.px-md { padding-left: var(--space-md); padding-right: var(--space-md); }
.px-lg { padding-left: var(--space-lg); padding-right: var(--space-lg); }
.py-xs { padding-top: var(--space-xs); padding-bottom: var(--space-xs); }
.py-sm { padding-top: var(--space-sm); padding-bottom: var(--space-sm); }
.py-md { padding-top: var(--space-md); padding-bottom: var(--space-md); }

// 分割线
.divider { height: 1px; background-color: var(--border-light); margin: var(--space-md) 0; }

// 情绪装饰条卡片
.emotion-card {
  background-color: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
  }
  &--warm::before { background-color: var(--mood-warm); }
  &--calm::before { background-color: var(--mood-calm); }
  &--low::before { background-color: var(--mood-low); }
  &--sad::before { background-color: var(--mood-sad); }
  &--chaos::before { background-color: var(--mood-chaos); }
}

// 网络断开提示
.network-offline-bar {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: var(--z-toast);
  background-color: var(--color-error);
  color: #ffffff;
  text-align: center;
  padding: var(--space-xs) 0;
  font-size: var(--font-size-sm);
}
```

**步骤 2：提交**

```bash
git add frontend/src/styles/common.scss
git commit -m "refactor: 精简公共样式，移除旧自定义组件样式，改用wot-design-uni"
```

---

### 任务 5：更新 emotions.scss — 夜间模式情绪色适配

**文件：**
- 重写：`frontend/src/styles/emotions.scss`

**步骤 1：重写**

情绪色变量已在 variables.scss 定义，emotions.scss 只保留工具类。移除 `--mood-*-text` 引用（已在 variables 中定义），确保 class 使用正确的变量名。

```scss
// ============================================
// 回声 - 情绪色彩工具类
// 文件：src/styles/emotions.scss
// 说明：情绪色工具类，用于标签、选择器、日记等
// 色值变量在 variables.scss 中定义（含夜间模式适配）
// ============================================

// 情绪主色
.mood-warm { color: var(--mood-warm); }
.mood-calm { color: var(--mood-calm); }
.mood-low { color: var(--mood-low); }
.mood-sad { color: var(--mood-sad); }
.mood-chaos { color: var(--mood-chaos); }

// 情绪背景色
.mood-warm-bg { background-color: var(--mood-warm-bg); }
.mood-calm-bg { background-color: var(--mood-calm-bg); }
.mood-low-bg { background-color: var(--mood-low-bg); }
.mood-sad-bg { background-color: var(--mood-sad-bg); }
.mood-chaos-bg { background-color: var(--mood-chaos-bg); }

// 情绪文字色（柔和版，长文本阅读）
.mood-warm-text { color: var(--mood-warm-text); }
.mood-calm-text { color: var(--mood-calm-text); }
.mood-low-text { color: var(--mood-low-text); }
.mood-sad-text { color: var(--mood-sad-text); }
.mood-chaos-text { color: var(--mood-chaos-text); }

// 情绪边框色
.mood-warm-border { border-color: var(--mood-warm); }
.mood-calm-border { border-color: var(--mood-calm); }
.mood-low-border { border-color: var(--mood-low); }
.mood-sad-border { border-color: var(--mood-sad); }
.mood-chaos-border { border-color: var(--mood-chaos); }

// 情绪标签
.emotion-tag {
  display: inline-flex;
  align-items: center;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  line-height: 1;
  &--warm { color: var(--mood-warm); background-color: var(--mood-warm-bg); }
  &--calm { color: var(--mood-calm); background-color: var(--mood-calm-bg); }
  &--low { color: var(--mood-low); background-color: var(--mood-low-bg); }
  &--sad { color: var(--mood-sad); background-color: var(--mood-sad-bg); }
  &--chaos { color: var(--mood-chaos); background-color: var(--mood-chaos-bg); }
}

// AI 角色色
.ai-xiaowen { color: var(--ai-xiaowen); }
.ai-xiaowen-bg { background-color: var(--ai-xiaowen-bg); }
.ai-laohei { color: var(--ai-laohei); }
.ai-laohei-bg { background-color: var(--ai-laohei-bg); }
.ai-ali { color: var(--ai-ali); }
.ai-ali-bg { background-color: var(--ai-ali-bg); }
```

**步骤 2：提交**

```bash
git add frontend/src/styles/emotions.scss
git commit -m "refactor: 情绪色工具类对齐新变量名，夜间色值走variables.scss"
```

---

### 任务 6：升级 settings store — 新增 auto 模式，实现 applyTheme

**文件：**
- 修改：`frontend/src/stores/settings.ts`

**步骤 1：新增 ThemeMode 类型 'auto'，重写 applyTheme**

关键改动：
- `ThemeMode` 增加 `'auto'`
- `DEFAULT_SETTINGS.theme` 改为 `'auto'`（默认自动模式）
- `isDarkMode` 增加 auto 模式判断（8:00-20:00 日间，其余夜间）
- `applyTheme` 实现：给页面根元素添加/移除 `.dark` class + 调用 `uni.setPageStyle`

```typescript
export type ThemeMode = 'light' | 'dark' | 'system' | 'auto'

const DEFAULT_SETTINGS: Settings = {
  theme: 'auto',  // 默认自动模式
  // ...其余不变
}

// isDarkMode 增加 auto 判断
const isDarkMode = computed(() => {
  if (settings.value.theme === 'light') return false
  if (settings.value.theme === 'dark') return true
  if (settings.value.theme === 'system') {
    const systemInfo = uni.getSystemInfoSync()
    // @ts-ignore
    return systemInfo.osTheme === 'dark'
  }
  // auto: 8:00-20:00 日间，其余夜间
  const hour = new Date().getHours()
  return hour < 8 || hour >= 20
})

// applyTheme 实现
function applyTheme() {
  const dark = isDarkMode.value
  // 设置页面 class
  const pages = getCurrentPages()
  if (pages.length > 0) {
    const page = pages[pages.length - 1]
    const pageEl = page.$el
    if (pageEl) {
      if (dark) {
        pageEl.classList.add('dark')
        pageEl.classList.remove('light')
      } else {
        pageEl.classList.add('light')
        pageEl.classList.remove('dark')
      }
    }
  }
  // 设置页面背景色（uni-app API）
  uni.setPageStyle({
    style: {
      backgroundColor: dark ? '#0f0f13' : '#ffffff',
    }
  })
}
```

**步骤 2：提交**

```bash
git add frontend/src/stores/settings.ts
git commit -m "feat: settings store增加auto主题模式，实现applyTheme"
```

---

### 任务 7：App.vue 集成 wd-config-provider

**文件：**
- 修改：`frontend/src/App.vue`

**步骤 1：在 template 中包裹 wd-config-provider**

```vue
<template>
  <wd-config-provider :theme="isDark ? 'dark' : 'light'">
    <view class="app-container">
      <slot />
    </view>
  </wd-config-provider>
</template>
```

**步骤 2：在 script 中引入 isDark 计算属性**

```typescript
import { useSettingsStore } from '@/stores/settings'
const settingsStore = useSettingsStore()
const isDark = computed(() => settingsStore.isDarkMode)
```

**步骤 3：在 onShow 中增加定时主题检查**

当用户 app 从后台恢复时，检查时间是否跨过了日/夜分界线。

```typescript
onShow(() => {
  // ... 现有逻辑
  settingsStore.applyTheme()
})
```

**步骤 4：提交**

```bash
git add frontend/src/App.vue
git commit -m "feat: App.vue集成wd-config-provider，支持全局主题切换"
```

---

### 任务 8：更新 pages.json — TabBar 4+1 结构 + 全局样式

**文件：**
- 修改：`frontend/src/pages.json`

**步骤 1：更新 globalStyle 背景色**

```json
"globalStyle": {
  "navigationBarTextStyle": "black",
  "navigationBarTitleText": "回声",
  "navigationBarBackgroundColor": "#ffffff",
  "backgroundColor": "#ffffff",
  "backgroundColorTop": "#ffffff",
  "backgroundColorBottom": "#ffffff",
  "backgroundTextStyle": "dark",
  "app-plus": {
    "titleNView": false,
    "background": "#ffffff",
    "scrollIndicator": "none"
  }
}
```

**步骤 2：更新 tabBar 为 4+1 结构**

```json
"tabBar": {
  "color": "#999999",
  "selectedColor": "#FF9A5C",
  "borderStyle": "black",
  "backgroundColor": "#ffffff",
  "list": [
    {
      "pagePath": "pages/home/index",
      "text": "首页",
      "iconPath": "static/images/icons/tab-home.png",
      "selectedIconPath": "static/images/icons/tab-home-active.png"
    },
    {
      "pagePath": "pages/diary/index",
      "text": "日记",
      "iconPath": "static/images/icons/tab-diary.png",
      "selectedIconPath": "static/images/icons/tab-diary-active.png"
    },
    {
      "pagePath": "pagesSocial/square/index",
      "text": "广场",
      "iconPath": "static/images/icons/tab-square.png",
      "selectedIconPath": "static/images/icons/tab-square-active.png"
    },
    {
      "pagePath": "pages/mine/index",
      "text": "我的",
      "iconPath": "static/images/icons/tab-mine.png",
      "selectedIconPath": "static/images/icons/tab-mine-active.png"
    }
  ]
}
```

变更：
- 移除 chat Tab（对话入口移到首页）
- 移除 community Tab（合并到广场）
- selectedColor 改为 `#FF9A5C`
- backgroundColor 改为 `#ffffff`
- color 改为 `#999999`
- 广场路径指向 `pagesSocial/square/index`

**步骤 3：删除 pages 中不再需要的页面路由**

从 `pages` 数组中移除：
- `pages/index/index`（删除文件）
- `pages/chat/index`（保留文件但不再是Tab，改为普通页面）

从 `subPackages.pages` 中移除：
- `add/index`（删除文件）
- `community/index`（删除文件）
- `treehole/index`（删除主包版，保留子包版 — 但子包treehole/index也不再是独立页面，作为square的子组件）

**步骤 4：提交**

```bash
git add frontend/src/pages.json
git commit -m "refactor: TabBar改为4项，全局背景色改为纯白"
```

---

### 任务 9：生成 Tab 图标资源

**文件：**
- 创建：`frontend/src/static/images/icons/tab-home.png`
- 创建：`frontend/src/static/images/icons/tab-home-active.png`
- 创建：`frontend/src/static/images/icons/tab-diary.png`
- 创建：`frontend/src/static/images/icons/tab-diary-active.png`
- 创建：`frontend/src/static/images/icons/tab-square.png`
- 创建：`frontend/src/static/images/icons/tab-square-active.png`
- 创建：`frontend/src/static/images/icons/tab-mine.png`
- 创建：`frontend/src/static/images/icons/tab-mine-active.png`

**步骤 1：使用 wot-design-uni 的 iconfont 或生成简单 PNG**

uni-app tabBar 要求 PNG 图标（81x81px，推荐）。需要为4个Tab各准备2张（normal + active）。

**注意**：如果没有设计资源，可临时使用纯色圆形占位 PNG，后续替换。或使用自定义 TabBar 组件（`wd-tabbar`）替代原生 tabBar，这样可以直接用 `wd-icon`。

**步骤 2：提交**

```bash
git add frontend/src/static/images/icons/
git commit -m "feat: 添加Tab图标资源"
```

---

### 任务 10：删除废弃页面文件

**文件：**
- 删除：`frontend/src/pages/index/index.vue`
- 删除：`frontend/src/pages/add/index.vue`（如果存在于主包）
- 删除：`frontend/src/pages/community/index.vue`
- 删除：`frontend/src/pages/treehole/index.vue`
- 删除：`frontend/src/pages/treehole/publish.vue`
- 删除：`frontend/src/pages/treehole/detail.vue`
- 删除：`frontend/src/pagesSocial/community/index.vue`
- 删除：`frontend/src/pagesSocial/add/index.vue`

**步骤 1：确认这些页面不再被引用后再删除**

用 grep 确认没有其他文件 import 或 navigateTo 这些路径。

**步骤 2：提交**

```bash
git add -A
git commit -m "refactor: 删除废弃页面（index/add/community/treehole主包版）"
```

---

## 阶段二：核心页面重构

### 任务 11：重构 login.vue — 纯净白 + 暖橘

**文件：**
- 重写：`frontend/src/pages/auth/login.vue`

**重构要点：**
- 背景：纯白 `var(--bg-primary)`
- 品牌名：`--font-size-2xl` + `--brand-primary` 色
- 手机号输入：`wd-input`，覆盖 `custom-style` 走主题
- 验证码输入：`wd-input` + `wd-button` (获取验证码用 ghost 类型)
- 登录按钮：`wd-button` type="primary" block
- 隐私协议：`wd-checkbox`
- 微信登录/一键登录：`wd-button` type="info" plain
- 所有文本图标 → `wd-icon`
- 底部安全区域：`safe-area-bottom`

**步骤 1：重写页面**
**步骤 2：H5 预览验证**
**步骤 3：提交**

```bash
git add frontend/src/pages/auth/login.vue
git commit -m "refactor: 登录页重构，纯净白+暖橘，使用wot-design-uni组件"
```

---

### 任务 12：重构 ai-greeting.vue

**文件：**
- 重写：`frontend/src/pages/auth/ai-greeting.vue`

**重构要点：**
- 进度条 → `wd-progress`
- 问候语 → `--font-size-xl` + `--text-primary`
- 时间图标 → `wd-icon name="clock"`
- 背景走 `var(--bg-primary)`

---

### 任务 13：重构 auth/profile.vue

**文件：**
- 重写：`frontend/src/pages/auth/profile.vue`

**重构要点：**
- 昵称输入：`wd-input`
- 年龄段选择：`wd-radio-group`
- 完成按钮：`wd-button` type="primary" block
- 图标 → `wd-icon`

---

### 任务 14-15：重构 minor-notice.vue + minor-lock.vue

**文件：**
- 重写：`frontend/src/pages/auth/minor-notice.vue`
- 重写：`frontend/src/pages/auth/minor-lock.vue`

**重构要点：**
- 移除文本模拟图标 → `wd-icon`
- 按钮 → `wd-button`
- minor-lock 走统一夜间模式（不再独立深色）
- 倒计时 → `wd-count-down`

---

### 任务 16：重构 home/index.vue — 增加 AI 对话入口

**文件：**
- 重写：`frontend/src/pages/home/index.vue`

**重构要点（功能增加）：**
- 集成 AI 对话入口卡片（原 chat Tab 的入口功能）
  - 3种AI性格头像 + 最近对话预览
  - 点击进入 chat/index
- 情绪速记入口保留
- 快捷入口 → `wd-grid`（记日记/树洞/动态/周报）
- 最近日记卡片美化
- 所有图标 → `wd-icon`
- 导航栏 → `wd-navbar` 或自定义（含品牌名）

---

### 任务 17：重构 chat/index.vue — AI 对话主页

**文件：**
- 重写：`frontend/src/pages/chat/index.vue`

**重构要点：**
- 不再是 Tab 页，增加返回导航
- 消息气泡走 `.bubble-ai` / `.bubble-user` class
- 输入框走主题变量
- 图标 → `wd-icon`
- 打字指示器保留 CSS 动画

---

### 任务 18：重构 chat/personality.vue — AI 性格选择

**文件：**
- 重写：`frontend/src/pages/chat/personality.vue`

**重构要点：**
- 3种性格卡片 → `wd-card` 风格
- 选中态 → 暖橘边框 + 浅橘背景
- 头像 → 真实占位图（用 brand-primary 色圆形 + 首字）
- 标签 → `wd-tag`
- 图标 → `wd-icon`

---

### 任务 19-21：重构日记模块（diary/index、edit、weekly-report）

**文件：**
- 重写：`frontend/src/pages/diary/index.vue`
- 修改：`frontend/src/pages/diary/edit.vue`
- 修改：`frontend/src/pages/diary/weekly-report.vue`

**diary/index 重构要点：**
- 导航 → `wd-navbar`
- 快速记录卡片 → `wd-card` 或 emotion-card
- 周报入口 → 独立卡片 + `wd-icon`
- 日记列表 → `wd-cell` 或自定义 emotion-card 列表
- 日历 → 保留 DiaryCalendar 组件，走新变量
- 图标 → `wd-icon`

**diary/edit 重构要点：**
- 情绪色调选择器 → 保留自定义 EmotionToneSelector，走新变量
- 标签选择 → `wd-tag` 或保留 EmotionLabelPicker
- 文字输入 → `wd-textarea`
- AI 润色按钮 → `wd-button` type="info" plain
- 图标 → `wd-icon`

**diary/weekly-report 重构要点：**
- 卡片美化 → emotion-card
- 图表 → 保留 EmotionChart，后续考虑 uCharts
- 图标 → `wd-icon`

---

### 任务 22：重构广场统一页 — 合并树洞+动态

**文件：**
- 重写：`frontend/src/pagesSocial/square/index.vue`

**重构要点（功能增加）：**
- 顶部 `wd-tabs` 切换「树洞/动态」
- 树洞 Tab：显示 treehole 帖子列表
- 动态 Tab：显示 square 动态列表
- 移除 `treehole-force-dark`
- 帖子卡片 → emotion-card 风格（树洞用情绪装饰条）
- 发布按钮 → `wd-icon` 悬浮按钮
- 下拉刷新 → `wd-pull-refresh`
- 图标 → `wd-icon`

**步骤 1：在 square/index.vue 中集成 wd-tabs 和两个列表**
**步骤 2：将 pagesSocial/treehole/index.vue 的列表逻辑内联到树洞 Tab**
**步骤 3：H5 预览验证 Tab 切换和列表渲染**
**步骤 4：提交**

```bash
git add frontend/src/pagesSocial/square/index.vue
git commit -m "feat: 广场页合并树洞+动态，顶部wd-tabs切换"
```

---

### 任务 23-25：重构 square/publish、square/detail、treehole 子页面

**文件：**
- 修改：`frontend/src/pagesSocial/square/publish.vue`
- 修改：`frontend/src/pagesSocial/square/detail.vue`
- 修改：`frontend/src/pagesSocial/treehole/detail.vue`（保留，作为树洞帖子详情）
- 修改：`frontend/src/pagesSocial/treehole/publish.vue`（保留，作为树洞发布页）

**重构要点：**
- 移除 `treehole-force-dark`
- 图标 → `wd-icon`
- 输入 → `wd-textarea`
- 发布 → `wd-button`
- 身份切换 → `wd-switch`
- 匿名身份预览 → 走主题变量

---

### 任务 26-29：重构好友模块

**文件：**
- 重写：`frontend/src/pages/friends/index.vue`
- 修改：`frontend/src/pages/friends/requests.vue`
- 修改：`frontend/src/pages/friends/profile.vue`
- 修改：`frontend/src/pages/friends/request.vue`

**friends/index 重构要点：**
- 搜索 → `wd-search`
- AI好友分组 + 真实好友分组 → `wd-cell`
- 社交能量条 → 保留 SocialEnergyBar，走新变量
- 空状态 → `wd-empty`
- 图标 → `wd-icon`

---

### 任务 30：重构 chat/private.vue — 私聊页

**文件：**
- 修改：`frontend/src/pagesSocial/chat/private.vue`

**重构要点：**
- 消息气泡 → `.bubble-ai` / `.bubble-user` 风格
- 输入框走主题变量
- 图标 → `wd-icon`
- 连接状态 banner → `wd-notice-bar`

---

### 任务 31-33：重构消息 + 通知模块

**文件：**
- 重写：`frontend/src/pages/message/index.vue`
- 重写：`frontend/src/pages/notification/list.vue`
- 修改：`frontend/src/pages/notification/settings.vue`

**message/index 重构要点：**
- Tab → `wd-tabs`
- 列表项 → `wd-cell` + `wd-swipe-action`
- 全部标记已读 → `wd-button`
- 图标 → `wd-icon`

**notification/list 重构要点：**
- 滑动删除 → `wd-swipe-action`（替换手写 touch 逻辑）
- 图标 → `wd-icon`
- 空状态 → `wd-empty`

---

### 任务 34-37：重构设置 + 个人中心模块

**文件：**
- 重写：`frontend/src/pages/settings/index.vue`（重点）
- 修改：`frontend/src/pages/profile/edit.vue`
- 修改：`frontend/src/pages/profile/ai-tags.vue`
- 重写：`frontend/src/pages/mine/index.vue`

**settings/index 重构要点（重点页面）：**
- 所有 `[xxx]` 文本图标 → `wd-icon`
- 列表 → `wd-cell` 分组（账号安全、AI设置、通知、外观、关于）
- 新增「外观」分组：主题模式切换入口
- 开关 → `wd-switch`

**mine/index 重构要点：**
- 用户卡片美化（头像 + 昵称 + 签名）
- 统计数据卡片
- 社交级别可视化美化
- 功能列表 → `wd-cell`
- 图标 → `wd-icon`
- 设置入口 → `wd-icon name="setting"`

---

## 阶段三：组件重构

### 任务 38-48：逐个重构自定义组件

每个组件的核心改动：图标 → `wd-icon`，样式走 CSS 变量，弹窗 → `wd-popup`，按钮 → `wd-button`。

| 任务 | 组件 | 关键改动 |
|------|------|---------|
| 38 | MessageBubble.vue | 走 `.bubble-ai`/`.bubble-user`，图标→`wd-icon` |
| 39 | PrivateMessageBubble.vue | 同上，发送状态→`wd-icon` |
| 40 | ChatInput.vue + MessageInput.vue | 输入走主题变量，图标→`wd-icon` |
| 41 | CrisisDialog.vue + GentleExit.vue | 弹窗→`wd-popup`，按钮→`wd-button` |
| 42 | DiaryCalendar.vue | 走新变量，色块用情绪CSS变量 |
| 43 | DiaryListItem.vue | 滑动删除→`wd-swipe-action` |
| 44 | EmotionToneSelector.vue + EmotionLabelPicker.vue | 选中态暖橘化，走新变量 |
| 45 | PostCard.vue (treehole+square两份) | 移除强制深色，走统一主题，图标→`wd-icon` |
| 46 | TopicFilter.vue | → `wd-tabs` 横向滚动或 `wd-tag` |
| 47 | SocialEnergyBar.vue + SocialLevelGuide.vue | 走新变量，图标→`wd-icon` |
| 48 | AIPolishCard.vue + ReportDialog.vue | 图标→`wd-icon`，按钮→`wd-button` |

---

## 阶段四：收尾验证

### 任务 49：全局搜索清理硬编码颜色

**步骤 1：grep 搜索所有 .vue 文件中的硬编码色值**

```bash
grep -rn '#[0-9a-fA-F]\{3,8\}' frontend/src/pages/ frontend/src/components/ --include="*.vue"
grep -rn 'rgb\|rgba' frontend/src/pages/ frontend/src/components/ --include="*.vue"
```

**步骤 2：将找到的硬编码色值替换为 CSS 变量引用**

**步骤 3：提交**

```bash
git add -A
git commit -m "refactor: 清理所有硬编码色值，统一走CSS变量"
```

---

### 任务 50：全局搜索清理文本模拟图标

**步骤 1：grep 搜索 `[xxx]` `<` `>` `...` `✓` 等文本图标**

```bash
grep -rn '\[.*\]' frontend/src/pages/ frontend/src/components/ --include="*.vue"
```

**步骤 2：替换为 `wd-icon`**

**步骤 3：提交**

---

### 任务 51：日间/夜间模式全流程验证

**步骤 1：启动 H5 dev**

**步骤 2：手动验证每个页面在日间/夜间模式下的表现**

检查点：
- [ ] 背景色正确切换
- [ ] 文字色正确切换
- [ ] 品牌色夜间提亮
- [ ] 卡片阴影/边框切换
- [ ] 情绪色调可辨识
- [ ] 输入框聚焦样式
- [ ] TabBar 适配（原生 tabBar 不支持 CSS 变量，需要特殊处理）

**步骤 3：修复发现的问题**

---

### 任务 52：最终提交 + 更新设计文档版本

**步骤 1：更新设计文档版本号**

**步骤 2：创建总结性 commit**

```bash
git add -A
git commit -m "feat: 前端全量重构完成 — 纯净白+暖橘设计系统+夜间模式"
```

---

> 文档版本：v1.0
> 更新时间：2026-05-06
