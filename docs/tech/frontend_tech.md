# 回声 — 前端UI组件库选型文档

> 文档版本：v1.1
> 更新时间：2026-04-23
> 适用项目：回声（深夜情绪急救站）

---

## 一、主流Uni-app UI组件库对比

### 1.1 组件库概览

| 组件库 | Vue3支持 | 组件数量 | 暗色模式 | 主题定制 | 文档质量 | 社区活跃度 | 授权方式 |
|--------|----------|----------|----------|----------|----------|------------|----------|
| **wot-design-uni** | 完整支持 | 60+ | 原生支持 | CSS变量 | 优秀 | 高(持续更新) | MIT免费 |
| **uview-plus** | 完整支持 | 70+ | 支持 | SCSS变量 | 良好 | 高 | MIT免费 |
| **uni-ui** | 官方支持 | 40+ | 支持 | CSS变量 | 优秀 | 高(官方维护) | MIT免费 |
| **TuniaoUI** | 完整支持 | 50+ | 原生支持 | 丰富的主题 | 优秀 | 中 | 部分收费 |
| **ThorUI** | 支持 | 80+ | 支持 | SCSS变量 | 良好 | 中 | 商业收费 |
| **FirstUI** | 支持 | 50+ | 支持 | 预设主题 | 良好 | 中 | 部分/全部收费 |

---

### 1.2 各组件库详细分析

#### 1. wot-design-uni (推荐)

**项目地址**：https://github.com/Moonofweisheng/wot-design-uni

**核心优势**：
- 专为Vue3 + TypeScript设计，类型定义完善
- 原生暗色模式支持，自动跟随系统或手动切换
- 使用CSS变量实现主题定制，灵活度高
- 组件API设计借鉴Element Plus，学习成本低
- 支持`easycom`自动导入，开发体验好
- 持续高频更新，社区活跃

**组件亮点**：
- `wd-message`：消息组件，适合对话场景
- `wd-notice-bar`：公告栏，适合提示信息
- `wd-skeleton`：骨架屏，加载体验好
- `wd-popup`：弹窗，支持多种位置
- `wd-action-sheet`：操作菜单
- `wd-picker`：选择器，支持级联
- `wd-swipe-action`：滑动操作，适合消息列表

**暗色模式实现**：
```typescript
// 配置暗色模式
import { useTheme } from 'wot-design-uni'

const { setTheme, theme } = useTheme()

// 切换暗色模式
setTheme('dark')

// 或跟随系统
setTheme('system')
```

**主题定制**：
```scss
// 自定义情绪色调变量
:root {
  --wd-color-theme: #FF9A5C;    // 暖橘
  --wd-color-success: #8FCCA0;  // 浅绿
  --wd-color-info: #8BA7C4;     // 灰蓝
}

.dark {
  --wd-color-theme: #ff9c6e;
  --wd-color-success: #73d13d;
}
```

**适用场景**：完全满足本项目AI对话、表单交互、列表展示需求

---

#### 2. uview-plus

**项目地址**：https://github.com/umicro/uview-plus

**核心优势**：
- uView的Vue3版本，继承原uView生态
- 组件丰富，覆盖面广
- 社区用户基数大，问题解决快
- 文档详细，示例丰富

**主要组件**：
- `u-message`：消息提示
- `u-card`：卡片组件，适合树洞
- `u-list`：列表组件，支持虚拟列表
- `u-avatar`：头像组件
- `u-badge`：徽标组件
- `u-upload`：上传组件
- `u-rate`：评分组件
- `u-tag`：标签组件，适合情绪标签

**劣势分析**：
- 暗色模式非原生支持，需手动配置
- TypeScript类型定义不如wot-design-uni完善
- 主题定制使用SCSS变量，运行时切换较复杂

---

#### 3. uni-ui (官方推荐)

**项目地址**：https://gitcode.com/dcloudio/uni-ui

**核心优势**：
- DCloud官方维护，稳定性最高
- 与Uni-app版本同步更新，兼容性最佳
- 代码质量高，遵循最佳实践
- 免费，无商业授权风险

**主要组件**：
- `uni-list`：列表组件
- `uni-card`：卡片组件
- `uni-nav-bar`：导航栏
- `uni-popup`：弹出层
- `uni-segmented-control`：分段器
- `uni-scroll-list`：滚动列表

**劣势分析**：
- 组件数量较少，部分功能需自行实现
- 暗色模式需通过CSS变量手动配置
- 无高频组件如骨架屏、虚拟列表等

---

#### 4. TuniaoUI

**项目地址**：https://github.com/tuniaoTech/tuniaoui-rc-view

**核心优势**：
- 设计风格现代，视觉效果好
- 原生暗色模式支持
- 丰富的主题预设（含暗色主题）
- 图标库完善

**主要组件**：
- `tn-button`：按钮组件
- `tn-card`：卡片组件
- `tn-navbar`：导航栏
- `tn-form`：表单组件
- `tn-swiper`：轮播
- `tn-image`：图片组件
- `tn-icon`：图标组件

**收费情况**：
- 基础组件免费
- 高级组件（如虚拟列表、复杂表单）收费
- 商业授权需付费

---

#### 5. ThorUI

**项目地址**：https://thorui.cn/

**核心优势**：
- 组件数量最多（80+）
- 提供完整模板（如商城、社交）
- 配套ThorUI Admin后台模板

**主要组件**：
- 完整的表单组件
- 丰富的列表组件
- 图表组件
- 自定义键盘

**收费情况**：
- 基础版免费有限制
- 完整版需购买授权（约199-399元）
- 商业项目需付费授权

---

#### 6. FirstUI

**项目地址**：https://www.firstui.cn/

**核心优势**：
- 设计规范统一
- 组件粒度细致
- 组件体积小

**收费情况**：
- 基础版部分免费
- 完整版收费
- VIP版提供更多服务

---

### 1.3 综合评分

| 维度 | wot-design-uni | uview-plus | uni-ui | TuniaoUI | ThorUI |
|------|----------------|------------|--------|----------|--------|
| Vue3/TS支持 | 9 | 7 | 8 | 8 | 7 |
| 暗色模式 | 10 | 6 | 7 | 9 | 7 |
| 主题定制 | 9 | 8 | 7 | 8 | 8 |
| 组件丰富度 | 9 | 10 | 7 | 8 | 10 |
| 文档质量 | 9 | 8 | 10 | 9 | 8 |
| 社区活跃度 | 9 | 8 | 9 | 7 | 7 |
| 免费使用 | 10 | 10 | 10 | 7 | 5 |
| **总分** | **65** | **57** | **58** | **56** | **52** |

---

## 二、推荐方案

### 2.1 组件库选择策略

| 选择项 | 组件库 | 理由 |
|--------|--------|------|
| **主组件库** | wot-design-uni | 原生暗色模式、TypeScript支持完善、主题定制灵活、活跃维护 |
| **辅助组件库** | uni-ui | 补充官方特色组件、稳定可靠、无授权风险 |
| **自定义组件** | 项目专用 | AI对话气泡、情绪选择器、虚拟滚动消息列表 |

### 2.2 选择理由详解

**为什么选择wot-design-uni作为主组件库**：

1. **暗色模式原生支持**
   - 项目定位"深夜情绪急救站"，暗色模式是核心需求
   - wot-design-uni提供`ConfigProvider`全局配置，一键切换主题
   - 无需额外开发暗色适配工作

2. **情绪色调系统兼容性**
   - 使用CSS变量，支持运行时动态修改
   - 可轻松实现5种情绪色彩的切换
   ```scss
   :root {
     // 暖橘 - 愉悦/温暖
     --emotion-warm: #FF9A5C;
     // 浅绿 - 平静/舒适
     --emotion-calm: #8FCCA0;
     // 灰蓝 - 忧郁/低落
     --emotion-blue: #8BA7C4;
     // 深蓝 - 难过/忧伤
     --emotion-anxious: #4A6FA5;
     // 暗紫 - 崩溃/混乱
     --emotion-night: #6B4C7A;
   }
   ```

3. **TypeScript类型完善**
   - 项目使用TypeScript，类型安全性重要
   - wot-design-uni提供完整的类型定义
   - IDE智能提示，开发效率高

4. **活跃的社区维护**
   - 2025-2026持续高频更新
   - Issue响应及时，PR活跃
   - 大型商业项目案例

### 2.3 补充方案

**何时使用uni-ui补充**：
- 需要`uni-segmented-control`分段选择器（情绪状态选择）
- 需要`uni-sticky`吸顶组件（消息列表头部）
- 需要`uni-datetime-picker`时间选择器（日记记录）

---

## 二续、多端输出策略

### 2.5.1 输出平台矩阵

| 平台 | 优先级 | 分发渠道 | 核心场景 | 功能完整度 |
|------|--------|---------|---------|-----------|
| 微信小程序 | P0 | 微信搜索/扫码/分享 | 主要使用场景 | 95% |
| Android App | P0 | 应用商店/APK下载 | 深度用户、推送稳定 | 100% |
| iOS App | P1 | App Store | iOS用户群体 | 100% |
| H5 | P1 | 浏览器/微信外链 | 推广落地页、分享裂变 | 80% |

### 2.5.2 各端功能差异说明

| 功能模块 | 微信小程序 | Android/iOS App | H5 | 差异原因 |
|---------|-----------|-----------------|-----|---------|
| AI流式输出 | 分段显示 | SSE原生支持 | EventSource | 小程序不支持SSE |
| 本地存储 | 键值存储 | SQLite | 键值存储 | 小程序无SQLite |
| 极光推送 | 模板消息 | 原生推送 | 浏览器通知 | 平台限制 |
| 语音输入 | 录音上传 | 原生SDK | 浏览器API | 能力差异 |
| 图片压缩 | 原生API | 原生API | Canvas | 实现方式不同 |
| WebSocket | 支持 | 支持 | 支持 | 无差异 |
| 分享功能 | 微信生态 | 全平台 | 复制链接 | 平台限制 |

### 2.5.3 条件编译规范

**常用条件编译宏：**
- `#ifdef APP-PLUS` - App端（Android+iOS）
- `#ifdef APP-ANDROID` - 仅Android
- `#ifdef APP-IOS` - 仅iOS
- `#ifdef H5` - H5端
- `#ifdef MP-WEIXIN` - 微信小程序
- `#ifndef MP-WEIXIN` - 非微信小程序

**使用示例：**
```typescript
// 平台判断
// #ifdef APP-PLUS
// App端特有逻辑
// #endif

// 多端合并
// #ifdef APP-PLUS || MP-WEIXIN
// App和小程序共有逻辑
// #endif
```

**条件编译清单：**

| 场景 | 条件编译 | 代码位置 |
|------|---------|---------|
| AI流式输出 | APP-PLUS/H5/MP-WEIXIN 分别实现 | useStreaming.ts |
| 本地存储 | APP-PLUS 用 SQLite，其他用 Storage | db.ts |
| 极光推送 | 仅 APP-PLUS | useNotification.ts |
| 图片压缩 | APP-PLUS/MP-WEIXIN 用原生，H5用Canvas | imageCompress.ts |
| 语音输入 | 各端分别实现 | useVoiceInput.ts |
| 状态栏适配 | APP-PLUS 单独处理 | App.vue |

### 2.5.4 manifest.json 关键配置

```json
{
  "name": "回声",
  "appid": "__UNI__XXXXX",
  
  // App端配置
  "app-plus": {
    "statusbar": {
      "immersed": true,
      "style": "dark"
    },
    "splashscreen": {
      "alwaysShowBeforeRender": true,
      "waiting": true
    },
    "modules": {
      "Push": {},
      "SQLite": {}
    },
    "distribute": {
      "android": {
        "permissions": [
          "<uses-permission android:name=\"android.permission.VIBRATE\"/>",
          "<uses-permission android:name=\"android.permission.RECORD_AUDIO\"/>"
        ]
      }
    }
  },
  
  // 微信小程序配置
  "mp-weixin": {
    "appid": "wxXXXXXXXX",
    "setting": {
      "urlCheck": false
    },
    "usingComponents": true
  },
  
  // H5配置
  "h5": {
    "title": "回声 - 深夜情绪急救站",
    "router": {
      "mode": "history"
    }
  }
}
```

---

## 三、项目结构建议

### 3.1 目录结构

```
ai_meet/
├── src/                          # 源码目录
│   ├── pages/                    # 页面目录
│   │   ├── index/                # 首页模块
│   │   │   └── index.vue         # 首页 - AI对话入口
│   │   │
│   │   ├── chat/                 # AI对话模块
│   │   │   ├── index.vue         # 对话主页
│   │   │   └── history.vue       # 历史记录
│   │   │
│   │   ├── diary/                # 情绪日记模块
│   │   │   ├── index.vue         # 日记列表
│   │   │   ├── edit.vue          # 编辑日记
│   │   │   └── report.vue        # AI周报
│   │   │
│   │   ├── treehole/             # 树洞模块
│   │   │   ├── index.vue         # 树洞列表
│   │   │   ├── detail.vue        # 详情页
│   │   │   └── publish.vue       # 发布页
│   │   │
│   │   ├── square/               # 动态广场
│   │   │   ├── index.vue         # 广场列表
│   │   │   ├── detail.vue        # 动态详情
│   │   │   └── publish.vue       # 发布动态
│   │   │
│   │   ├── message/              # 消息模块
│   │   │   ├── index.vue         # 消息列表
│   │   │   └── chat.vue           # 私聊页面
│   │   │
│   │   ├── profile/              # 个人中心
│   │   │   ├── index.vue         # 个人主页
│   │   │   ├── settings.vue      # 设置页
│   │   │   └── edit.vue           # 编辑资料
│   │   │
│   │   └── auth/                 # 认证模块
│   │       ├── login.vue         # 登录页
│   │       └── register.vue      # 注册页
│   │
│   ├── components/               # 公共组件
│   │   ├── common/               # 通用组件
│   │   │   ├── NavBar.vue        # 导航栏
│   │   │   ├── TabBar.vue        # 底部导航
│   │   │   ├── Loading.vue       # 加载状态
│   │   │   └── Empty.vue         # 空状态
│   │   │
│   │   ├── chat/                 # 对话相关组件
│   │   │   ├── ChatBubble.vue    # AI对话气泡（流式）
│   │   │   ├── TypingIndicator.vue  # 打字动画
│   │   │   ├── MessageInput.vue  # 消息输入框
│   │   │   └── StreamingText.vue # 流式文本渲染
│   │   │
│   │   ├── diary/                # 日记相关组件
│   │   │   ├── EmotionPicker.vue # 情绪选择器
│   │   │   ├── EmotionTag.vue    # 情绪标签
│   │   │   └── DiaryCard.vue     # 日记卡片
│   │   │
│   │   ├── social/                # 社交相关组件
│   │   │   ├── TreeholeCard.vue  # 树洞卡片
│   │   │   ├── PostCard.vue      # 动态卡片
│   │   │   ├── CommentItem.vue   # 评论项
│   │   │   └── UserAvatar.vue    # 用户头像
│   │   │
│   │   └── message/              # 消息相关组件
│   │       ├── MessageItem.vue   # 消息列表项
│   │       └── VirtualList.vue   # 虚拟滚动列表
│   │
│   ├── composables/              # 组合式函数（hooks）
│   │   ├── useChat.ts            # 对话逻辑
│   │   ├── useStreaming.ts       # 流式输出处理（HTTP SSE）
│   │   ├── useTheme.ts           # 主题切换
│   │   ├── useEmotion.ts         # 情绪处理
│   │   ├── useUpload.ts          # 文件上传
│   │   ├── useNotification.ts    # 通知处理（极光推送）
│   │   ├── useSync.ts            # 数据同步（离线/在线切换、冲突解决）
│   │   └── useWebSocket.ts       # WebSocket连接管理（心跳、重连、离线缓存）
│   │
│   ├── stores/                   # Pinia状态管理
│   │   ├── index.ts              # Store入口
│   │   ├── user.ts               # 用户状态
│   │   ├── chat.ts               # 对话状态
│   │   ├── message.ts            # 消息状态
│   │   ├── diary.ts              # 日记状态（本地CRUD、同步管理）
│   │   └── settings.ts           # 设置状态
│   │
│   ├── api/                      # API请求封装
│   │   ├── index.ts              # Axios实例配置
│   │   ├── modules/              # API模块
│   │   │   ├── auth.ts           # 认证接口
│   │   │   ├── chat.ts           # 对话接口
│   │   │   ├── diary.ts          # 日记接口
│   │   │   ├── treehole.ts       # 树洞接口
│   │   │   ├── social.ts         # 社交接口
│   │   │   └── user.ts           # 用户接口
│   │   └── types/                # API类型定义
│   │       └── index.ts
│   │
│   ├── styles/                   # 样式目录
│   │   ├── variables.scss       # 样式变量
│   │   ├── theme.scss            # 主题样式
│   │   ├── emotions.scss         # 情绪色彩系统
│   │   ├── dark.scss             # 暗色样式
│   │   ├── animations.scss      # 动画样式
│   │   └── common.scss           # 公共样式
│   │
│   ├── utils/                    # 工具函数
│   │   ├── request.ts            # 请求封装
│   │   ├── storage.ts            # 本地存储
│   │   ├── websocket.ts          # WebSocket封装
│   │   ├── date.ts               # 日期处理
│   │   ├── format.ts             # 格式化工具
│   │   └── permission.ts         # 权限处理
│   │
│   ├── types/                    # TypeScript类型
│   │   ├── global.d.ts           # 全局类型
│   │   ├── chat.d.ts             # 对话类型
│   │   ├── user.d.ts             # 用户类型
│   │   └── emotion.d.ts          # 情绪类型
│   │
│   ├── static/                   # 静态资源
│   │   ├── images/               # 图片资源
│   │   │   ├── avatar/           # 默认头像
│   │   │   ├── emotions/         # 情绪图标
│   │   │   ├── icons/            # 功能图标
│   │   │   └── backgrounds/      # 背景图
│   │   │
│   │   └── fonts/                # 字体文件
│   │
│   ├── App.vue                   # 应用入口
│   ├── main.ts                   # 主入口文件
│   ├── pages.json                # 页面配置
│   ├── manifest.json             # 应用配置
│   └── uni.scss                  # 全局样式变量
│
├── .env                          # 环境变量
├── .env.development              # 开发环境
├── .env.production               # 生产环境
├── tsconfig.json                 # TypeScript配置
├── vite.config.ts                # Vite配置
└── package.json                  # 项目配置
```

### 3.2 样式变量文件

**文件：src/styles/variables.scss**

```scss
// ==================== 基础变量 ====================

// 主色调
$color-primary: #FF9A5C;
$color-primary-light: #FFB88A;
$color-primary-dark: #E07830;

// 功能色
$color-success: #8FCCA0;
$color-warning: #FBBF24;
$color-error: #F87171;
$color-info: #8BA7C4;

// ==================== 情绪色彩系统 ====================

// 暖橘 - 愉悦/温暖
$emotion-warm: #FF9A5C;
$emotion-warm-bg: rgba(255, 154, 92, 0.1);

// 浅绿 - 平静/舒适
$emotion-calm: #8FCCA0;
$emotion-calm-bg: rgba(143, 204, 160, 0.1);

// 灰蓝 - 低落/沉闷
$emotion-blue: #8BA7C4;
$emotion-blue-bg: rgba(139, 167, 196, 0.1);

// 深蓝 - 难过/忧伤
$emotion-anxious: #4A6FA5;
$emotion-anxious-bg: rgba(74, 111, 165, 0.1);

// 暗紫 - 崩溃/混乱
$emotion-night: #6B4C7A;
$emotion-night-bg: rgba(107, 76, 122, 0.1);

// ==================== 中性色 ====================

// 亮色模式
$bg-color: #f5f7fa;
$bg-color-page: #ffffff;
$text-color-primary: #1f2937;
$text-color-secondary: #6b7280;
$text-color-placeholder: #9ca3af;
$border-color: #e5e7eb;

// 暗色模式
$dark-bg-color: #0f172a;
$dark-bg-color-page: #1e293b;
$dark-text-color-primary: #f1f5f9;
$dark-text-color-secondary: #94a3b8;
$dark-border-color: #334155;

// ==================== 间距 ====================

$spacing-xs: 4px;
$spacing-sm: 8px;
$spacing-md: 16px;
$spacing-lg: 24px;
$spacing-xl: 32px;

// ==================== 圆角 ====================

$border-radius-sm: 4px;
$border-radius-md: 8px;
$border-radius-lg: 12px;
$border-radius-xl: 16px;
$border-radius-full: 9999px;

// ==================== 阴影 ====================

$shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
$shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
$shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

// 暗色模式阴影
$dark-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
$dark-shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
$dark-shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.4);

// ==================== 动画 ====================

$transition-fast: 0.15s;
$transition-base: 0.3s;
$transition-slow: 0.5s;

// ==================== 字体 ====================

$font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC',
  'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;

$font-size-xs: 11px;
$font-size-sm: 12px;
$font-size-base: 14px;
$font-size-md: 16px;
$font-size-lg: 18px;
$font-size-xl: 20px;
$font-size-2xl: 24px;
```

### 3.3 API请求封装

**文件：src/api/index.ts**

```typescript
import { useUserStore } from '@/stores/user'
import { useSettingsStore } from '@/stores/settings'

// API基础配置
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.huisheng.app'

// 请求拦截器
const request = <T = any>(options: UniApp.RequestOptions): Promise<T> => {
  return new Promise((resolve, reject) => {
    const userStore = useUserStore()
    const settingsStore = useSettingsStore()

    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': userStore.token ? `Bearer ${userStore.token}` : '',
        'X-Device-Id': settingsStore.deviceId,
        ...options.header,
      },
      timeout: 30000,
      success: (res) => {
        if (res.statusCode === 200) {
          const data = res.data as ApiResponse<T>
          if (data.success) {
            resolve(data.data)
          } else {
            // 业务错误处理
            const error = data.error || { code: 'UNKNOWN', message: '请求失败' }
            handleBusinessError(error.code, error.message)
            reject(new Error(error.message))
          }
        } else if (res.statusCode === 401) {
          // 未授权，跳转登录
          userStore.logout()
          uni.reLaunch({ url: '/pages/auth/login' })
          reject(new Error('请先登录'))
        } else {
          reject(new Error(`请求失败: ${res.statusCode}`))
        }
      },
      fail: (err) => {
        uni.showToast({
          title: '网络请求失败',
          icon: 'none',
        })
        reject(err)
      },
    })
  })
}

// 快捷方法
export const api = {
  get: <T = any>(url: string, data?: any) => request<T>({ url, method: 'GET', data }),
  post: <T = any>(url: string, data?: any) => request<T>({ url, method: 'POST', data }),
  put: <T = any>(url: string, data?: any) => request<T>({ url, method: 'PUT', data }),
  delete: <T = any>(url: string, data?: any) => request<T>({ url, method: 'DELETE', data }),
}

export default api

// 类型定义 - 与后端 tech_architecture.md 保持一致
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: any
  }
}
```

---

## 四、关键组件实现方案

### 4.1 AI对话气泡（流式输出）

> **协议说明**：AI对话使用HTTP SSE流式协议，流式模式下直接渲染已接收的chunk文本，
> 取消打字机模拟效果；仅在加载历史消息时使用打字机效果。

**文件：src/components/chat/ChatBubble.vue**

```vue
<template>
  <view
    class="chat-bubble"
    :class="[
      `chat-bubble--${role}`,
      { 'chat-bubble--streaming': isStreaming }
    ]"
  >
    <!-- AI头像 -->
    <view v-if="role === 'assistant'" class="chat-bubble__avatar">
      <image
        :src="avatarUrl"
        mode="aspectFill"
        class="chat-bubble__avatar-img"
      />
    </view>

    <!-- 消息内容 -->
    <view class="chat-bubble__content">
      <!-- 文本内容 -->
      <view class="chat-bubble__text">
        <text>{{ displayText }}</text>
        <!-- 流式接收中的光标 -->
        <text v-if="isStreaming" class="chat-bubble__cursor">|</text>
      </view>

      <!-- 时间戳（非流式状态才显示） -->
      <view v-if="!isStreaming && displayComplete" class="chat-bubble__time">
        {{ formatTime(timestamp) }}
      </view>
    </view>

    <!-- 用户头像 -->
    <view v-if="role === 'user'" class="chat-bubble__avatar">
      <image
        :src="avatarUrl"
        mode="aspectFill"
        class="chat-bubble__avatar-img"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'

interface Props {
  role: 'user' | 'assistant'
  content: string
  avatarUrl?: string
  timestamp?: number
  /** 是否正在流式接收中（SSE实时chunk） */
  isStreaming?: boolean
  /** 是否为历史消息（历史消息使用打字机效果） */
  isHistory?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  avatarUrl: '/static/images/avatar/default-ai.png',
  timestamp: Date.now(),
  isStreaming: false,
  isHistory: false,
})

// 显示文本
const displayText = ref('')
// 显示是否完成（用于控制时间戳展示时机）
const displayComplete = ref(false)
let typewriterTimer: number | null = null

/**
 * 历史消息打字机效果
 * 仅在加载历史消息时使用，模拟逐字显示
 */
const startTypewriter = () => {
  if (typewriterTimer) {
    clearInterval(typewriterTimer)
  }

  displayComplete.value = false
  let index = 0
  displayText.value = ''

  typewriterTimer = setInterval(() => {
    if (index < props.content.length) {
      displayText.value += props.content[index]
      index++
    } else {
      if (typewriterTimer) {
        clearInterval(typewriterTimer)
        typewriterTimer = null
      }
      displayComplete.value = true
    }
  }, 30) // 每30ms输出一个字符
}

/**
 * 流式模式：直接渲染已接收的chunk文本
 * 每次chunk追加时，直接同步到displayText，不使用打字机模拟
 */
const renderStreamingChunk = () => {
  displayText.value = props.content
  displayComplete.value = false
}

// 监听内容变化，根据模式选择渲染策略
watch(
  () => props.content,
  () => {
    if (props.isStreaming) {
      // 流式模式：直接渲染已接收的chunk文本，不做打字机模拟
      renderStreamingChunk()
    } else if (props.isHistory) {
      // 历史消息模式：使用打字机效果逐字显示
      startTypewriter()
    } else {
      // 普通模式（如用户消息）：直接显示全部内容
      displayText.value = props.content
      displayComplete.value = true
    }
  },
  { immediate: true }
)

// 流式结束时标记完成
watch(
  () => props.isStreaming,
  (newVal, oldVal) => {
    if (oldVal === true && newVal === false) {
      // 从流式中切换到非流式，表示本次响应完成
      displayComplete.value = true
    }
  }
)

// 清理定时器
onUnmounted(() => {
  if (typewriterTimer) {
    clearInterval(typewriterTimer)
  }
})

// 格式化时间
const formatTime = (ts: number) => {
  const date = new Date(ts)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}
</script>

<style lang="scss" scoped>
.chat-bubble {
  display: flex;
  align-items: flex-start;
  padding: 16rpx 24rpx;
  margin-bottom: 24rpx;

  &--user {
    flex-direction: row-reverse;

    .chat-bubble__content {
      background: var(--emotion-warm);
      color: #fff;
      border-radius: 24rpx 24rpx 4rpx 24rpx;
    }
  }

  &--assistant {
    .chat-bubble__content {
      background: var(--wd-color-bg-container);
      color: var(--wd-color-text);
      border-radius: 24rpx 24rpx 24rpx 4rpx;
    }
  }

  &--streaming {
    .chat-bubble__text {
      min-height: 1em;
    }
  }

  &__avatar {
    flex-shrink: 0;
    width: 80rpx;
    height: 80rpx;
    border-radius: 50%;
    overflow: hidden;

    &-img {
      width: 100%;
      height: 100%;
    }
  }

  &__content {
    max-width: 70%;
    padding: 20rpx 24rpx;
    word-break: break-word;
  }

  &__text {
    font-size: 28rpx;
    line-height: 1.6;
  }

  &__cursor {
    display: inline-block;
    animation: blink 1s infinite;
    margin-left: 2rpx;
    color: var(--emotion-warm);
    font-weight: bold;
  }

  &__time {
    margin-top: 8rpx;
    font-size: 22rpx;
    opacity: 0.6;
    text-align: right;
  }
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 暗色模式 */
.dark {
  .chat-bubble--assistant .chat-bubble__content {
    background: rgba(255, 255, 255, 0.1);
  }
}
</style>
```

---

### 4.2 情绪色调选择器

**文件：src/components/diary/EmotionPicker.vue**

```vue
<template>
  <view class="emotion-picker">
    <view class="emotion-picker__label">此刻的情绪</view>

    <view class="emotion-picker__options">
      <view
        v-for="emotion in emotions"
        :key="emotion.value"
        class="emotion-picker__item"
        :class="{
          'emotion-picker__item--active': modelValue === emotion.value
        }"
        :style="{ '--emotion-color': emotion.color }"
        @tap="handleSelect(emotion.value)"
      >
        <view
          class="emotion-picker__color-block"
          :style="{ background: emotion.color }"
        ></view>
        <text class="emotion-picker__name">{{ emotion.label }}</text>
      </view>
    </view>

    <!-- 二层标签选择 -->
    <view v-if="modelValue && subLabels.length > 0" class="emotion-picker__sub-labels">
      <text class="emotion-picker__sub-title">更具体地描述一下：</text>
      <view class="emotion-picker__sub-options">
        <view
          v-for="sub in subLabels"
          :key="sub"
          class="emotion-picker__sub-item"
          :class="{ 'emotion-picker__sub-item--active': selectedSubLabel === sub }"
          @tap="handleSubLabelSelect(sub)"
        >
          {{ sub }}
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface Props {
  modelValue?: string
  subLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  subLabel: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:subLabel': [value: string]
  'change': [emotion: { emotion: string; label: string; subLabel: string; color: string }]
}>()

// 情绪列表 - 色块+文字标签，与ui_design.md统一
const emotions = [
  { value: 'warm', label: '暖橘', color: '#FF9A5C' },
  { value: 'calm', label: '浅绿', color: '#8FCCA0' },
  { value: 'blue', label: '灰蓝', color: '#8BA7C4' },
  { value: 'sad', label: '深蓝', color: '#4A6FA5' },
  { value: 'chaos', label: '暗紫', color: '#6B4C7A' },
]

// 二层标签映射
const subLabelMap: Record<string, string[]> = {
  warm: ['开心', '温暖', '期待', '满足'],
  calm: ['平静', '安稳', '放松', '舒适'],
  blue: ['低落', '沉闷', '疲惫', '无聊'],
  sad: ['难过', '忧伤', '失落', '心痛'],
  chaos: ['崩溃', '混乱', '无助', '绝望'],
}

// 当前选中的二层标签
const selectedSubLabel = ref(props.subLabel)

// 计算当前情绪的二层标签
const subLabels = computed(() => {
  return props.modelValue ? subLabelMap[props.modelValue] || [] : []
})

// 选择情绪
const handleSelect = (value: string) => {
  emit('update:modelValue', value)
  // 清空二层标签
  selectedSubLabel.value = ''
  emit('update:subLabel', '')
  triggerEmotionChange(value, '')
}

// 选择二层标签
const handleSubLabelSelect = (sub: string) => {
  selectedSubLabel.value = sub
  emit('update:subLabel', sub)
  triggerEmotionChange(props.modelValue, sub)
}

// 触发变化事件
const triggerEmotionChange = (emotion: string, subLabel: string) => {
  const selected = emotions.find(e => e.value === emotion)
  if (selected) {
    emit('change', {
      emotion: selected.value,
      label: selected.label,
      subLabel: subLabel,
      color: selected.color,
    })
  }
}

// 监听props变化
watch(() => props.subLabel, (val) => {
  selectedSubLabel.value = val
})
</script>

<style lang="scss" scoped>
.emotion-picker {
  padding: 24rpx;

  &__label {
    font-size: 28rpx;
    color: var(--wd-color-text-secondary);
    margin-bottom: 24rpx;
  }

  &__options {
    display: flex;
    justify-content: space-between;
    gap: 16rpx;
  }

  &__item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20rpx 12rpx;
    border-radius: 16rpx;
    background: var(--wd-color-bg-container);
    border: 2rpx solid transparent;
    transition: all 0.3s;

    &:active {
      transform: scale(0.95);
    }

    &--active {
      border-color: var(--emotion-color);
      background: rgba(255, 255, 255, 0.05);
    }
  }

  &__color-block {
    width: 64rpx;
    height: 64rpx;
    border-radius: 50%;
    margin-bottom: 12rpx;
  }

  &__name {
    font-size: 24rpx;
    color: var(--wd-color-text);
  }

  &__sub-labels {
    margin-top: 32rpx;
    padding-top: 24rpx;
    border-top: 1rpx solid var(--wd-color-border);
  }

  &__sub-title {
    display: block;
    font-size: 26rpx;
    color: var(--wd-color-text-secondary);
    margin-bottom: 16rpx;
  }

  &__sub-options {
    display: flex;
    flex-wrap: wrap;
    gap: 16rpx;
  }

  &__sub-item {
    padding: 12rpx 24rpx;
    border-radius: 24rpx;
    background: var(--wd-color-bg-container);
    font-size: 26rpx;
    color: var(--wd-color-text);
    transition: all 0.2s;

    &:active {
      transform: scale(0.95);
    }

    &--active {
      background: var(--wd-color-theme);
      color: #fff;
    }
  }
}
</style>
```

---

### 4.3 树洞匿名卡片

**文件：src/components/social/TreeholeCard.vue**

```vue
<template>
  <view class="treehole-card" @tap="handleTap">
    <!-- 卡片头部 -->
    <view class="treehole-card__header">
      <view class="treehole-card__avatar">
        <image
          :src="defaultAvatar"
          mode="aspectFill"
          class="treehole-card__avatar-img"
        />
        <view class="treehole-card__mask"></view>
      </view>
      <view class="treehole-card__meta">
        <text class="treehole-card__nickname">{{ anonymousName }}</text>
        <text class="treehole-card__time">{{ formatTime(createdAt) }}</text>
      </view>
    </view>

    <!-- 卡片内容 -->
    <view class="treehole-card__content">
      <text class="treehole-card__text">{{ content }}</text>

      <!-- 情绪标签 -->
      <view v-if="emotion" class="treehole-card__emotion-tag">
        <view
          class="treehole-card__tag"
          :style="{ background: emotionColor }"
        >
          {{ emotionLabel }}
        </view>
      </view>
    </view>

    <!-- 卡片底栏 -->
    <view class="treehole-card__footer">
      <view class="treehole-card__actions">
        <view class="treehole-card__action" @tap.stop="handleLike">
          <wd-icon name="thumb-up" :color="isResonated ? '#FF9A5C' : '#999'" />
          <text>{{ resonanceCount }}</text>
        </view>
        <view class="treehole-card__action" @tap.stop="handleComment">
          <wd-icon name="comment" />
          <text>{{ commentCount }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  id: string
  content: string
  emotion?: string
  createdAt: number
  resonanceCount: number
  commentCount: number
  isResonated?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isResonated: false,
})

const emit = defineEmits<{
  tap: [id: string]
  like: [id: string]
  comment: [id: string]
}>()

// 默认头像（匿名身份）
const defaultAvatar = '/static/images/avatar/anonymous.png'

// 生成匿名昵称
const anonymousName = computed(() => {
  const adjectives = ['迷路的', '失眠的', '落泪的', '沉默的', '孤独的']
  const nouns = ['猫咪', '月亮', '星星', '萤火虫', '夜莺']
  const adj = adjectives[Math.floor(Math.random() * adjectives.length)]
  const noun = nouns[Math.floor(Math.random() * nouns.length)]
  return `${adj}${noun}`
})

// 情绪相关
const emotionMap: Record<string, { label: string; color: string }> = {
  warm: { label: '暖橘', color: '#FF9A5C' },
  calm: { label: '浅绿', color: '#8FCCA0' },
  blue: { label: '灰蓝', color: '#8BA7C4' },
  sad: { label: '深蓝', color: '#4A6FA5' },
  chaos: { label: '暗紫', color: '#6B4C7A' },
}

const emotionInfo = computed(() => {
  return props.emotion ? emotionMap[props.emotion] : null
})

const emotionLabel = computed(() => emotionInfo.value?.label || '')
const emotionColor = computed(() => emotionInfo.value?.color || '#999')

// 格式化时间
const formatTime = (ts: number) => {
  const now = Date.now()
  const diff = now - ts
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour

  if (diff < minute) return '刚刚'
  if (diff < hour) return `${Math.floor(diff / minute)}分钟前`
  if (diff < day) return `${Math.floor(diff / hour)}小时前`
  return `${Math.floor(diff / day)}天前`
}

// 事件处理
const handleTap = () => emit('tap', props.id)
const handleLike = () => emit('like', props.id)
const handleComment = () => emit('comment', props.id)
</script>

<style lang="scss" scoped>
.treehole-card {
  background: var(--wd-color-bg-container);
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;

  &__header {
    display: flex;
    align-items: center;
    margin-bottom: 20rpx;
  }

  &__avatar {
    position: relative;
    width: 72rpx;
    height: 72rpx;

    &-img {
      width: 100%;
      height: 100%;
      border-radius: 50%;
      filter: blur(2px); /* 匿名模糊效果 */
    }

    .treehole-card__mask {
      position: absolute;
      inset: 0;
      border-radius: 50%;
      background: rgba(114, 46, 209, 0.3);
    }
  }

  &__meta {
    margin-left: 16rpx;
  }

  &__nickname {
    display: block;
    font-size: 28rpx;
    color: var(--wd-color-text);
  }

  &__time {
    display: block;
    font-size: 24rpx;
    color: var(--wd-color-text-secondary);
    margin-top: 4rpx;
  }

  &__content {
    margin-bottom: 20rpx;
  }

  &__text {
    font-size: 28rpx;
    line-height: 1.7;
    color: var(--wd-color-text);
  }

  &__emotion-tag {
    margin-top: 16rpx;
  }

  &__tag {
    display: inline-block;
    padding: 6rpx 16rpx;
    border-radius: 20rpx;
    font-size: 22rpx;
    color: #fff;
  }

  &__footer {
    display: flex;
    justify-content: flex-end;
  }

  &__actions {
    display: flex;
    gap: 32rpx;
  }

  &__action {
    display: flex;
    align-items: center;
    gap: 8rpx;
    font-size: 24rpx;
    color: var(--wd-color-text-secondary);
  }
}
</style>
```

---

### 4.4 消息列表虚拟滚动

**文件：src/components/message/VirtualList.vue**

```vue
<template>
  <scroll-view
    :scroll-y="true"
    :scroll-top="scrollTop"
    class="virtual-list"
    @scroll="handleScroll"
    @scrolltolower="handleScrollToLower"
  >
    <!-- 可视区域内容 -->
    <view
      class="virtual-list__content"
      :style="{ height: totalHeight + 'px' }"
    >
      <view
        class="virtual-list__items"
        :style="{ transform: `translateY(${offsetY}px)` }"
      >
        <view
          v-for="item in visibleItems"
          :key="item.id"
          class="virtual-list__item"
          :style="{ height: itemHeight + 'px' }"
        >
          <slot :item="item.data" :index="item.index" />
        </view>
      </view>
    </view>

    <!-- 加载更多 -->
    <view v-if="loading" class="virtual-list__loading">
      <wd-loading />
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

interface Props {
  items: any[]
  itemHeight: number
  bufferSize?: number
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  bufferSize: 5,
  loading: false,
})

const emit = defineEmits<{
  loadMore: []
}>()

// 容器高度
const containerHeight = ref(0)

// 滚动位置
const scrollTop = ref(0)
const currentScrollTop = ref(0)

// 总高度
const totalHeight = computed(() => props.items.length * props.itemHeight)

// 可视区域能显示的条目数
const visibleCount = computed(() =>
  Math.ceil(containerHeight.value / props.itemHeight) + props.bufferSize * 2
)

// 开始索引
const startIndex = computed(() => {
  const index = Math.floor(currentScrollTop.value / props.itemHeight) - props.bufferSize
  return Math.max(0, index)
})

// 结束索引
const endIndex = computed(() =>
  Math.min(props.items.length - 1, startIndex.value + visibleCount.value)
)

// 偏移量
const offsetY = computed(() => startIndex.value * props.itemHeight)

// 可视项目
const visibleItems = computed(() => {
  return props.items
    .slice(startIndex.value, endIndex.value + 1)
    .map((data, i) => ({
      id: data.id || startIndex.value + i,
      index: startIndex.value + i,
      data,
    }))
})

// 处理滚动
const handleScroll = (e: any) => {
  currentScrollTop.value = e.detail.scrollTop
}

// 滚动到底部
const handleScrollToLower = () => {
  if (!props.loading) {
    emit('loadMore')
  }
}

// 滚动到底部方法
const scrollToBottom = () => {
  scrollTop.value = totalHeight.value
}

// 获取容器高度
onMounted(() => {
  const query = uni.createSelectorQuery().in(getCurrentInstance())
  query.select('.virtual-list').boundingClientRect((rect: any) => {
    containerHeight.value = rect.height
  }).exec()
})

// 获取当前组件实例
import { getCurrentInstance } from 'vue'

// 暴露方法
defineExpose({
  scrollToBottom,
})
</script>

<style lang="scss" scoped>
.virtual-list {
  height: 100%;

  &__content {
    position: relative;
  }

  &__items {
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
  }

  &__item {
    box-sizing: border-box;
  }

  &__loading {
    display: flex;
    justify-content: center;
    padding: 24rpx;
  }
}
</style>
```

---

## 五、技术实现要点

### 5.1 流式输出实现（HTTP SSE）

> **重要说明**：AI对话使用HTTP SSE协议接收流式响应，非WebSocket。
> - **App端**：使用 `uni.request` 的 `enableChunked: true` + `onChunkReceived`
> - **H5端**：使用浏览器原生 `EventSource`
> - **小程序端**：降级为普通HTTP请求分段显示

```typescript
// src/composables/useStreaming.ts
import { ref, onUnmounted, computed } from 'vue'
import { useUserStore } from '@/stores/user'

// 平台检测
const platform = computed(() => {
  // #ifdef APP-PLUS
  return 'app'
  // #endif
  // #ifdef H5
  return 'h5'
  // #endif
  // #ifdef MP-WEIXIN
  return 'mp-weixin'
  // #endif
  return 'unknown'
})

export interface StreamOptions {
  /** API端点 */
  url: string
  /** 请求体 */
  body: any
  /** 开始流式时的回调 */
  onStart?: () => void
  /** 接收到数据块时的回调 */
  onChunk?: (chunk: string) => void
  /** 流式完成时的回调 */
  onComplete?: (fullContent: string) => void
  /** 错误时的回调 */
  onError?: (error: Error) => void
}

export const useStreaming = () => {
  const content = ref('')
  const isStreaming = ref(false)
  const error = ref<Error | null>(null)

  // 请求任务引用（用于App端取消请求）
  let requestTask: UniApp.RequestTask | null = null
  // EventSource引用（用于H5端关闭连接）
  let eventSource: EventSource | null = null

  /**
   * App端流式请求实现
   * 使用 uni.request 的 enableChunked + onChunkReceived
   */
  const streamForApp = (options: StreamOptions) => {
    const userStore = useUserStore()
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://api.huisheng.app'

    return new Promise<string>((resolve, reject) => {
      content.value = ''
      isStreaming.value = true
      error.value = null
      options.onStart?.()

      requestTask = uni.request({
        url: baseUrl + options.url,
        method: 'POST',
        data: options.body,
        header: {
          'Content-Type': 'application/json',
          'Authorization': userStore.token ? `Bearer ${userStore.token}` : '',
          'Accept': 'text/event-stream',
        },
        enableChunked: true, // 开启分块传输
        timeout: 120000, // 流式请求超时时间设置为2分钟
        success: (res) => {
          if (res.statusCode === 200) {
            // 最终响应可能包含完整的聚合内容
            const fullContent = typeof res.data === 'string'
              ? res.data
              : (res.data as any).content || ''
            options.onComplete?.(fullContent)
            resolve(fullContent)
          } else {
            const err = new Error(`请求失败: ${res.statusCode}`)
            error.value = err
            options.onError?.(err)
            reject(err)
          }
        },
        fail: (err) => {
          const e = new Error(err.errMsg || '网络请求失败')
          error.value = e
          options.onError?.(e)
          reject(e)
        },
      })

      // 监听分块数据
      requestTask.onChunkReceived?.((response) => {
        try {
          // 将ArrayBuffer转换为字符串
          const uint8Array = new Uint8Array(response.data)
          const decoder = new TextDecoder('utf-8')
          const chunkText = decoder.decode(uint8Array)

          // 解析SSE数据格式: "data: {json}\n\n"
          const lines = chunkText.split('\n')
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonStr = line.slice(6).trim()
              if (jsonStr === '[DONE]') {
                // 流式结束标记
                isStreaming.value = false
                options.onComplete?.(content.value)
                return
              }
              try {
                const data = JSON.parse(jsonStr)
                if (data.content) {
                  content.value += data.content
                  options.onChunk?.(data.content)
                }
              } catch {
                // 非JSON格式的数据，直接追加
                if (jsonStr) {
                  content.value += jsonStr
                  options.onChunk?.(jsonStr)
                }
              }
            }
          }
        } catch (e) {
          console.error('解析chunk数据失败:', e)
        }
      })
    })
  }

  /**
   * H5端流式请求实现
   * 使用浏览器原生 EventSource
   */
  const streamForH5 = (options: StreamOptions) => {
    return new Promise<string>((resolve, reject) => {
      content.value = ''
      isStreaming.value = true
      error.value = null
      options.onStart?.()

      const userStore = useUserStore()
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://api.huisheng.app'

      // 构建带参数的URL（EventSource只支持GET）
      const params = new URLSearchParams({
        message: options.body.message || '',
        sessionId: options.body.sessionId || '',
      })
      const url = `${baseUrl}${options.url}?${params.toString()}`

      eventSource = new EventSource(url, {
        withCredentials: false,
      })

      // 添加认证头（通过自定义header方式，或使用query参数传递token）
      // 注意：EventSource不支持自定义header，需通过URL传递token或使用cookie

      eventSource.onmessage = (event) => {
        const data = event.data
        if (data === '[DONE]') {
          isStreaming.value = false
          options.onComplete?.(content.value)
          eventSource?.close()
          resolve(content.value)
          return
        }

        try {
          const parsed = JSON.parse(data)
          if (parsed.content) {
            content.value += parsed.content
            options.onChunk?.(parsed.content)
          }
        } catch {
          // 非JSON格式，直接追加
          content.value += data
          options.onChunk?.(data)
        }
      }

      eventSource.onerror = (e) => {
        isStreaming.value = false
        const err = new Error('EventSource连接错误')
        error.value = err
        options.onError?.(err)
        eventSource?.close()
        reject(err)
      }
    })
  }

  /**
   * 小程序端降级实现
   * 使用普通HTTP请求，支持长文本分段显示
   */
  const streamForMiniProgram = (options: StreamOptions) => {
    return new Promise<string>((resolve, reject) => {
      content.value = ''
      isStreaming.value = true
      error.value = null
      options.onStart?.()

      const userStore = useUserStore()
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://api.huisheng.app'

      uni.request({
        url: baseUrl + options.url,
        method: 'POST',
        data: {
          ...options.body,
          stream: false, // 小程序端不使用流式
        },
        header: {
          'Content-Type': 'application/json',
          'Authorization': userStore.token ? `Bearer ${userStore.token}` : '',
        },
        timeout: 60000,
        success: (res) => {
          if (res.statusCode === 200) {
            const data = res.data as any
            const fullContent = data.content || data.data?.content || ''
            // 模拟分段显示效果
            const words = fullContent.split('')
            let index = 0
            const timer = setInterval(() => {
              if (index < words.length) {
                content.value += words[index]
                options.onChunk?.(words[index])
                index++
              } else {
                clearInterval(timer)
                isStreaming.value = false
                options.onComplete?.(content.value)
              }
            }, 30) // 30ms逐字显示
            resolve(fullContent)
          } else {
            const err = new Error(`请求失败: ${res.statusCode}`)
            error.value = err
            options.onError?.(err)
            reject(err)
          }
        },
        fail: (err) => {
          const e = new Error(err.errMsg || '网络请求失败')
          error.value = e
          options.onError?.(e)
          reject(e)
        },
      })
    })
  }

  /**
   * 统一流式请求入口
   * 根据平台自动选择实现方式
   */
  const startStream = async (options: StreamOptions) => {
    // #ifdef APP-PLUS
    return streamForApp(options)
    // #endif
    // #ifdef H5
    return streamForH5(options)
    // #endif
    // #ifdef MP-WEIXIN
    return streamForMiniProgram(options)
    // #endif
    // 默认使用App实现
    return streamForApp(options)
  }

  /**
   * 发送AI对话消息
   */
  const sendMessage = async (message: string, sessionId?: string) => {
    return startStream({
      url: '/api/v1/ai/chat/stream',
      body: {
        message,
        sessionId: sessionId || `session_${Date.now()}`,
      },
    })
  }

  /**
   * 停止流式请求
   */
  const stopStream = () => {
    if (requestTask) {
      requestTask.abort()
      requestTask = null
    }
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isStreaming.value = false
  }

  /**
   * 重置状态
   */
  const reset = () => {
    content.value = ''
    isStreaming.value = false
    error.value = null
  }

  // 组件卸载时清理
  onUnmounted(() => {
    stopStream()
  })

  return {
    content,
    isStreaming,
    error,
    startStream,
    sendMessage,
    stopStream,
    reset,
  }
}
```

### 5.2 主题切换实现

```typescript
// src/composables/useTheme.ts
import { ref, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'

export const useTheme = () => {
  const settingsStore = useSettingsStore()
  const isDark = ref(settingsStore.theme === 'dark')

  const toggleTheme = () => {
    isDark.value = !isDark.value
    settingsStore.setTheme(isDark.value ? 'dark' : 'light')
    applyTheme(isDark.value)
  }

  const applyTheme = (dark: boolean) => {
    // 设置页面根元素class
    const pages = getCurrentPages()
    const page = pages[pages.length - 1]
    if (page) {
      const pageStyle = dark ? 'background: #0f172a' : 'background: #f5f7fa'
      // 通过CSS变量设置主题
      uni.setPageStyle({
        style: {
          backgroundColor: dark ? '#0f172a' : '#f5f7fa',
        },
      })
    }
  }

  // 初始化主题
  watch(() => settingsStore.theme, (newTheme) => {
    isDark.value = newTheme === 'dark'
    applyTheme(isDark.value)
  }, { immediate: true })

  return {
    isDark,
    toggleTheme,
  }
}
```

---

## 六、开发规范建议

### 6.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `ChatBubble.vue` |
| 组合式函数 | camelCase + use前缀 | `useStreaming.ts` |
| Store文件 | camelCase | `user.ts` |
| API文件 | camelCase | `chat.ts` |
| 样式文件 | kebab-case | `variables.scss` |
| 静态资源 | kebab-case | `avatar-default.png` |

### 6.2 组件开发规范

```vue
<template>
  <!-- 模板内容 -->
</template>

<script setup lang="ts">
// 1. 导入
import { ref, computed, watch } from 'vue'

// 2. Props定义
interface Props {
  // ...
}

const props = withDefaults(defineProps<Props>(), {
  // ...
})

// 3. Emits定义
const emit = defineEmits<{
  // ...
}>()

// 4. 响应式状态
const state = ref()

// 5. 计算属性
const computed = computed(() => {})

// 6. 方法
const handleSomething = () => {}

// 7. 生命周期
onMounted(() => {})
</script>

<style lang="scss" scoped>
// 组件样式
</style>
```

---

## 七、图表库选型

### 7.1 选型策略

| 图表类型 | 选型方案 | 理由 |
|---------|---------|------|
| **日历热力图** | 自定义组件（CSS Grid + 色块填充） | 无需复杂交互，纯CSS实现更轻量 |
| **情绪曲线图** | uCharts | Uni-app专用图表库，跨端兼容性好 |
| **环形图** | uCharts | 同上，支持动画与交互 |

### 7.2 uCharts 选型理由

**项目地址**：https://doc.ucharts.cn/

**核心优势**：
- 专为Uni-app设计，一套代码多端运行
- 支持Vue3 + TypeScript，类型定义完善
- 图表类型丰富：折线图、柱状图、饼图、环形图等
- 轻量级，支持按需引入
- 中文文档完善，社区活跃

**安装方式**：
```bash
npm install @qiun/ucharts
```

### 7.3 日历热力图自定义组件设计

**文件：src/components/diary/CalendarHeatmap.vue**

```vue
<template>
  <view class="calendar-heatmap">
    <!-- 月份标题 -->
    <view class="heatmap-header">
      <text class="heatmap-title">{{ currentMonth }}</text>
      <view class="heatmap-nav">
        <wd-button size="small" @click="prevMonth">上月</wd-button>
        <wd-button size="small" @click="nextMonth">下月</wd-button>
      </view>
    </view>

    <!-- 星期标题 -->
    <view class="heatmap-weekdays">
      <text v-for="day in weekdays" :key="day" class="heatmap-weekday">{{ day }}</text>
    </view>

    <!-- 日期网格 -->
    <view class="heatmap-grid">
      <view
        v-for="(cell, index) in calendarCells"
        :key="index"
        class="heatmap-cell"
        :class="{ 'heatmap-cell--empty': !cell.date }"
        :style="{ background: getCellColor(cell) }"
        @tap="cell.date && handleCellTap(cell)"
      >
        <text v-if="cell.date" class="heatmap-day">{{ cell.day }}</text>
      </view>
    </view>

    <!-- 情绪图例 -->
    <view class="heatmap-legend">
      <text class="legend-label">情绪强度：</text>
      <view class="legend-colors">
        <view
          v-for="(color, index) in legendColors"
          :key="index"
          class="legend-color"
          :style="{ background: color }"
        />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  /** 情绪数据，key为日期（YYYY-MM-DD），value为情绪强度（0-10） */
  emotionData: Record<string, number>
  /** 当前选中的日期 */
  selectedDate?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  select: [date: string, intensity: number]
}>()

// 当前年月
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth())

// 星期标题
const weekdays = ['日', '一', '二', '三', '四', '五', '六']

// 情绪色彩
const emotionColors = {
  low: '#1a1a2e',      // 无记录
  warm: '#FF9A5C',     // 暖橘
  calm: '#8FCCA0',     // 浅绿
  blue: '#8BA7C4',     // 灰蓝
  sad: '#4A6FA5',      // 深蓝
  chaos: '#6B4C7A',    // 暗紫
}

// 图例颜色
const legendColors = ['#1a1a2e', '#3b3b5c', '#5c5c8a', '#7d7db8', '#9e9ee5', '#FF9A5C']

// 计算日历单元格
const calendarCells = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value

  // 当月第一天
  const firstDay = new Date(year, month, 1)
  const firstDayOfWeek = firstDay.getDay()

  // 当月天数
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  // 生成单元格（包含前置空白）
  const cells = []

  // 前置空白（上月日期占位）
  for (let i = 0; i < firstDayOfWeek; i++) {
    cells.push({ date: null, day: null, intensity: 0 })
  }

  // 当月日期
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const intensity = props.emotionData[dateStr] || 0
    cells.push({
      date: dateStr,
      day: day,
      intensity
    })
  }

  return cells
})

// 获取单元格颜色
const getCellColor = (cell: any) => {
  if (!cell.date) return 'transparent'
  if (cell.intensity === 0) return emotionColors.low

  // 根据强度映射颜色深度
  const intensity = cell.intensity
  if (intensity <= 2) return 'rgba(255, 122, 69, 0.2)'
  if (intensity <= 4) return 'rgba(255, 122, 69, 0.4)'
  if (intensity <= 6) return 'rgba(255, 122, 69, 0.6)'
  if (intensity <= 8) return 'rgba(255, 122, 69, 0.8)'
  return emotionColors.warm
}

// 上月
const prevMonth = () => {
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

// 下月
const nextMonth = () => {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

// 点击单元格
const handleCellTap = (cell: any) => {
  emit('select', cell.date, cell.intensity)
}

// 格式化月份显示
const currentMonth = computed(() => {
  return `${currentYear.value}年${currentMonth.value + 1}月`
})
</script>

<style lang="scss" scoped>
.calendar-heatmap {
  padding: 24rpx;
  background: var(--wd-color-bg-container);
  border-radius: 16rpx;

  .heatmap-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24rpx;

    .heatmap-title {
      font-size: 32rpx;
      font-weight: 600;
      color: var(--wd-color-text);
    }

    .heatmap-nav {
      display: flex;
      gap: 16rpx;
    }
  }

  .heatmap-weekdays {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    margin-bottom: 16rpx;

    .heatmap-weekday {
      text-align: center;
      font-size: 24rpx;
      color: var(--wd-color-text-secondary);
    }
  }

  .heatmap-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 8rpx;

    .heatmap-cell {
      aspect-ratio: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8rpx;
      cursor: pointer;
      transition: transform 0.2s;

      &:active {
        transform: scale(0.95);
      }

      &--empty {
        background: transparent;
      }

      .heatmap-day {
        font-size: 22rpx;
        color: rgba(255, 255, 255, 0.9);
      }
    }
  }

  .heatmap-legend {
    display: flex;
    align-items: center;
    margin-top: 24rpx;

    .legend-label {
      font-size: 24rpx;
      color: var(--wd-color-text-secondary);
      margin-right: 16rpx;
    }

    .legend-colors {
      display: flex;
      gap: 8rpx;

      .legend-color {
        width: 32rpx;
        height: 32rpx;
        border-radius: 4rpx;
      }
    }
  }
}
</style>
```

### 7.4 uCharts 情绪曲线图集成方案

**文件：src/components/charts/EmotionLineChart.vue**

```vue
<template>
  <view class="emotion-chart">
    <qiun-ucharts
      type="line"
      :opts="chartOpts"
      :chartData="chartData"
      :canvas2d="true"
    />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  /** 情绪数据，日期为key，强度为value */
  data: Array<{ date: string; intensity: number }>
}

const props = defineProps<Props>()

// 图表配置
const chartOpts = {
  color: ['#FF9A5C', '#8FCCA0'],
  padding: [15, 10, 0, 15],
  enableScroll: false,
  legend: {
    show: false
  },
  xAxis: {
    disableGrid: true,
    axisLine: false,
    fontSize: 10,
    fontColor: '#94a3b8'
  },
  yAxis: {
    gridType: 'dash',
    dashLength: 4,
    gridColor: '#334155',
    splitNumber: 5,
    min: 0,
    max: 10,
    fontSize: 10,
    fontColor: '#94a3b8'
  },
  extra: {
    line: {
      type: 'curve', // 曲线类型
      width: 2,
      activeType: 'hollow'
    }
  }
}

// 图表数据
const chartData = computed(() => {
  return {
    categories: props.data.map(d => d.date.slice(5)), // 只显示月-日
    series: [{
      name: '情绪强度',
      data: props.data.map(d => d.intensity)
    }]
  }
})
</script>

<style lang="scss" scoped>
.emotion-chart {
  width: 100%;
  height: 400rpx;
}
</style>
```

### 7.5 uCharts 环形图集成方案

**文件：src/components/charts/EmotionRingChart.vue**

```vue
<template>
  <view class="emotion-ring">
    <qiun-ucharts
      type="ring"
      :opts="chartOpts"
      :chartData="chartData"
      :canvas2d="true"
    />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  /** 各情绪分布数据 */
  data: Array<{ emotion: string; count: number; color: string }>
}

const props = defineProps<Props>()

// 图表配置
const chartOpts = {
  color: props.data.map(d => d.color),
  padding: [5, 5, 5, 5],
  legend: {
    show: true,
    position: 'right',
    lineHeight: 20,
    fontSize: 12,
    fontColor: '#94a3b8'
  },
  title: {
    name: '情绪分布',
    fontSize: 14,
    fontColor: '#f1f5f9'
  },
  extra: {
    ring: {
      ringWidth: 30,
      activeOpacity: 0.5,
      activeRadius: 10,
      offsetAngle: 0,
      labelWidth: 15,
      border: true,
      borderWidth: 2,
      borderColor: '#1e293b'
    }
  }
}

// 图表数据
const chartData = computed(() => {
  return {
    series: [{
      data: props.data.map(d => ({
        name: d.emotion,
        value: d.count
      }))
    }]
  }
})
</script>

<style lang="scss" scoped>
.emotion-ring {
  width: 100%;
  height: 400rpx;
}
</style>
```

---

## 八、P2 技术优化方案

> 以下为 P2 优先级技术优化建议的详细实现方案，涵盖图表库选型落地、匿名身份后端化、Store 补齐、主题切换升级、语音输入、图片压缩、举报弹窗、危机干预弹窗及全局错误处理。

### 8.1 P2-11：图表库选型落地 - 日历热力图用 CSS，曲线/环形用 uCharts

**方案摘要**：在第七章选型分析的基础上，明确最终落地策略与集成规范。

| 图表类型 | 实现方案 | 包体积 | 跨端兼容 | 交互复杂度 |
|---------|---------|--------|---------|-----------|
| 日历热力图 | CSS Grid + 色块填充 | 0KB（纯CSS） | 全端一致 | 低（点击选中） |
| 情绪曲线图 | uCharts `line` + `curve` | ~40KB（按需） | 全端兼容 | 中（滑动查看） |
| 情绪环形图 | uCharts `ring` | ~30KB（按需） | 全端兼容 | 中（点击高亮） |

**落地规范**：

1. **uCharts 按需引入**：仅引入 `line` 和 `ring` 模块，避免全量打包
   ```bash
   # 安装 uCharts 核心包
   npm install @qiun/ucharts
   ```
2. **CSS 热力图设计原则**：
   - 使用 `CSS Grid` 布局 `7列` 网格，每个色块为 `1:1` 正方形
   - 色块颜色通过 `CSS 变量` 动态映射情绪类型与强度
   - 不引入任何第三方图表库，零额外体积
3. **uCharts 封装规范**：
   - 统一封装为 `src/components/charts/` 目录下的独立组件
   - 通过 `props` 传入数据，组件内部处理数据转换与图表渲染
   - 暗色模式下通过 `chartOpts` 切换配色方案
4. **组件清单**：
   - `src/components/diary/CalendarHeatmap.vue` — 日历热力图（CSS 实现，已定义于 7.3）
   - `src/components/charts/EmotionLineChart.vue` — 情绪曲线图（uCharts，已定义于 7.4）
   - `src/components/charts/EmotionRingChart.vue` — 情绪环形图（uCharts，已定义于 7.5）

---

### 8.2 P2-12：匿名头像改为后端预生成，前端不生成

**问题**：当前 `TreeholeCard.vue` 中使用前端硬编码的默认头像路径 `/static/images/avatar/anonymous.png`，所有匿名用户头像相同，缺乏辨识度，且前端生成存在一致性风险。

**方案**：匿名头像由后端在用户首次进入树洞时预生成并返回，前端仅负责展示。

**后端职责**：
1. 用户首次进入树洞模块时，后端调用头像生成服务
2. 基于用户ID哈希 + 随机种子，生成独一无二的匿名头像（SVG/PNG）
3. 头像存储至 OSS，URL 随树洞帖子数据一并返回
4. 同一用户在同一树洞帖子中保持头像一致

**前端改造**：

```typescript
// src/components/social/TreeholeCard.vue 改造要点

interface Props {
  id: string
  content: string
  emotion?: string
  createdAt: number
  resonanceCount: number
  commentCount: number
  isResonated?: boolean
  /** 匿名头像URL，由后端预生成并返回 */
  anonymousAvatar?: string
}

// 头像展示逻辑：优先使用后端返回的匿名头像，否则使用兜底图
const avatarSrc = computed(() => {
  return props.anonymousAvatar || '/static/images/avatar/anonymous-fallback.png'
})
```

**API 响应结构**：
```typescript
// GET /api/v1/treehole/posts 响应
interface TreeholePost {
  id: string
  content: string
  emotion?: string
  createdAt: number
  resonanceCount: number
  commentCount: number
  // 匿名身份信息，由后端生成
  anonymousIdentity: {
    avatarUrl: string    // 后端预生成的匿名头像URL
    nickname: string     // 后端生成的匿名昵称（P2-13）
  }
}
```

**兜底策略**：
- 前端保留一张兜底匿名头像 `anonymous-fallback.png`，仅在后端数据异常时使用
- 匿名头像模糊效果（`filter: blur(2px)`）保持不变，增强匿名感

---

### 8.3 P2-13：匿名昵称由后端生成（200+200词库）

**问题**：当前 `TreeholeCard.vue` 中匿名昵称由前端随机拼接生成，词库仅 `5+5=25` 种组合，极易重复且缺乏趣味性。

**方案**：匿名昵称由后端基于 `200形容词 + 200名词` 词库生成，前端仅展示。

**后端词库设计**：

| 词库 | 数量 | 示例 | 风格要求 |
|------|------|------|---------|
| 形容词 | 200+ | 迷路的、失眠的、落泪的、沉默的、孤独的、温柔的、倔强的... | 情绪化、有画面感、贴合深夜场景 |
| 名词 | 200+ | 猫咪、月亮、星星、萤火虫、夜莺、晚风、云朵、灯塔... | 自然意象、安静美好、有治愈感 |

**组合空间**：200 x 200 = 40,000 种不重复昵称，足以支撑大规模匿名用户。

**后端生成规则**：
1. 基于用户ID + 帖子ID的哈希值作为随机种子，保证同一用户在同一帖子中昵称一致
2. 同一用户在不同帖子中使用不同昵称，增强匿名性
3. 昵称格式：`{形容词}{名词}`，如"迷路的月亮"

**前端改造**：

```typescript
// src/components/social/TreeholeCard.vue 改造要点

// 删除前端随机生成匿名昵称的逻辑（原 anonymousName computed）
// 改为从 props 中直接获取后端返回的匿名昵称

interface Props {
  id: string
  content: string
  emotion?: string
  createdAt: number
  resonanceCount: number
  commentCount: number
  isResonated?: boolean
  anonymousAvatar?: string
  /** 匿名昵称，由后端基于200+200词库生成 */
  anonymousNickname: string
}

// 直接使用后端返回的昵称
const displayName = computed(() => props.anonymousNickname)
```

**前端词库兜底**（离线/弱网场景）：

```typescript
// src/utils/anonymousName.ts
// 前端保留精简版词库（20+20），仅在后端数据缺失时作为兜底

const fallbackAdjectives = [
  '迷路的', '失眠的', '落泪的', '沉默的', '孤独的',
  '温柔的', '倔强的', '躲藏的', '漂泊的', '等待的',
  '醒着的', '寻路的', '微凉的', '安静的', '放空的',
  '回忆的', '停泊的', '漫游的', '轻叹的', '漫步的',
]

const fallbackNouns = [
  '猫咪', '月亮', '星星', '萤火虫', '夜莺',
  '晚风', '云朵', '灯塔', '树影', '海浪',
  '露珠', '雪花', '鲸鱼', '蝴蝶', '港湾',
  '潮汐', '山谷', '森林', '溪流', '月光',
]

/**
 * 基于字符串哈希生成兜底匿名昵称
 * 仅在后端未返回匿名昵称时使用
 */
export function generateFallbackNickname(seed: string): string {
  let hash = 0
  for (let i = 0; i < seed.length; i++) {
    hash = ((hash << 5) - hash + seed.charCodeAt(i)) | 0
  }
  const adjIndex = Math.abs(hash) % fallbackAdjectives.length
  const nounIndex = Math.abs(hash >> 8) % fallbackNouns.length
  return `${fallbackAdjectives[adjIndex]}${fallbackNouns[nounIndex]}`
}
```

---

### 8.4 P2-14：Pinia Store 补齐 6 个缺失 Store

**问题**：当前 `src/stores/` 目录仅包含 5 个 Store（user、chat、message、diary、settings），缺少树洞、广场、通知、搜索、情绪、同步等模块的状态管理。

**补齐方案**：

| 序号 | Store 名称 | 文件路径 | 职责说明 |
|------|-----------|---------|---------|
| 1 | `treehole` | `src/stores/treehole.ts` | 树洞列表、帖子详情、匿名身份缓存、发帖/评论状态 |
| 2 | `square` | `src/stores/square.ts` | 动态广场列表、动态详情、发布/点赞/收藏状态 |
| 3 | `notification` | `src/stores/notification.ts` | 通知列表、未读计数、极光推送注册与消息处理 |
| 4 | `search` | `src/stores/search.ts` | 搜索关键词、搜索历史、搜索结果缓存、搜索建议 |
| 5 | `emotion` | `src/stores/emotion.ts` | 当前情绪状态、情绪色彩映射、情绪切换动画控制 |
| 6 | `sync` | `src/stores/sync.ts` | 离线/在线状态、数据同步队列、冲突解决策略、同步进度 |

**各 Store 详细设计**：

#### 8.4.1 treehole.ts

```typescript
// src/stores/treehole.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'

export const useTreeholeStore = defineStore('treehole', () => {
  // ===== 状态 =====
  /** 帖子列表 */
  const posts = ref<TreeholePost[]>([])
  /** 当前查看的帖子详情 */
  const currentPost = ref<TreeholePostDetail | null>(null)
  /** 匿名身份缓存：key 为帖子ID，value 为匿名身份信息 */
  const anonymousIdentities = ref<Record<string, AnonymousIdentity>>({})
  /** 是否正在加载 */
  const loading = ref(false)
  /** 是否还有更多数据 */
  const hasMore = ref(true)
  /** 当前页码 */
  const currentPage = ref(1)
  /** 页面大小 */
  const pageSize = 20

  // ===== 计算属性 =====
  /** 未读评论数 */
  const unreadCommentCount = computed(() => {
    return posts.value.reduce((count, post) => count + (post.unreadComments || 0), 0)
  })

  // ===== 操作 =====
  /** 加载帖子列表 */
  const fetchPosts = async (refresh = false) => {
    if (loading.value) return
    loading.value = true
    try {
      if (refresh) {
        currentPage.value = 1
        hasMore.value = true
      }
      const result = await api.get<TreeholePost[]>('/api/v1/treehole/posts', {
        page: currentPage.value,
        pageSize,
      })
      if (refresh) {
        posts.value = result
      } else {
        posts.value.push(...result)
      }
      hasMore.value = result.length >= pageSize
      currentPage.value++
    } finally {
      loading.value = false
    }
  }

  /** 获取帖子详情 */
  const fetchPostDetail = async (postId: string) => {
    const result = await api.get<TreeholePostDetail>(`/api/v1/treehole/posts/${postId}`)
    currentPost.value = result
    // 缓存匿名身份
    if (result.anonymousIdentity) {
      anonymousIdentities.value[postId] = result.anonymousIdentity
    }
  }

  /** 发布树洞帖子 */
  const publishPost = async (content: string, emotion?: string) => {
    const result = await api.post<TreeholePost>('/api/v1/treehole/posts', {
      content,
      emotion,
    })
    // 新帖子插入列表顶部
    posts.value.unshift(result)
    return result
  }

  /** 点赞/取消点赞 */
  const toggleLike = async (postId: string) => {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return
    await api.post(`/api/v1/treehole/posts/${postId}/resonate`)
    post.isResonated = !post.isResonated
    post.resonanceCount += post.isResonated ? 1 : -1
  }

  /** 重置状态 */
  const reset = () => {
    posts.value = []
    currentPost.value = null
    currentPage.value = 1
    hasMore.value = true
  }

  return {
    posts,
    currentPost,
    anonymousIdentities,
    loading,
    hasMore,
    unreadCommentCount,
    fetchPosts,
    fetchPostDetail,
    publishPost,
    toggleLike,
    reset,
  }
})

// ===== 类型定义 =====
interface TreeholePost {
  id: string
  content: string
  emotion?: string
  createdAt: number
  resonanceCount: number
  commentCount: number
  isResonated: boolean
  unreadComments?: number
  anonymousIdentity: AnonymousIdentity
}

interface TreeholePostDetail extends TreeholePost {
  comments: Comment[]
}

interface AnonymousIdentity {
  avatarUrl: string
  nickname: string
}

interface Comment {
  id: string
  content: string
  createdAt: number
  anonymousIdentity: AnonymousIdentity
}
```

#### 8.4.2 square.ts

```typescript
// src/stores/square.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'

export const useSquareStore = defineStore('square', () => {
  // ===== 状态 =====
  /** 动态列表 */
  const feeds = ref<SquareFeed[]>([])
  /** 热门标签 */
  const hotTags = ref<string[]>([])
  /** 当前查看的动态详情 */
  const currentFeed = ref<SquareFeedDetail | null>(null)
  /** 是否正在加载 */
  const loading = ref(false)
  /** 是否还有更多 */
  const hasMore = ref(true)
  const currentPage = ref(1)
  const pageSize = 20

  // ===== 操作 =====
  /** 加载动态列表 */
  const fetchFeeds = async (refresh = false) => {
    if (loading.value) return
    loading.value = true
    try {
      if (refresh) {
        currentPage.value = 1
        hasMore.value = true
      }
      const result = await api.get<SquareFeed[]>('/api/v1/square/feeds', {
        page: currentPage.value,
        pageSize,
      })
      if (refresh) {
        feeds.value = result
      } else {
        feeds.value.push(...result)
      }
      hasMore.value = result.length >= pageSize
      currentPage.value++
    } finally {
      loading.value = false
    }
  }

  /** 发布动态 */
  const publishFeed = async (data: { content: string; images?: string[]; tags?: string[] }) => {
    const result = await api.post<SquareFeed>('/api/v1/square/feeds', data)
    feeds.value.unshift(result)
    return result
  }

  /** 点赞 */
  const toggleLike = async (feedId: string) => {
    const feed = feeds.value.find(f => f.id === feedId)
    if (!feed) return
    await api.post(`/api/v1/square/feeds/${feedId}/like`)
    feed.isLiked = !feed.isLiked
    feed.likeCount += feed.isLiked ? 1 : -1
  }

  /** 收藏 */
  const toggleFavorite = async (feedId: string) => {
    const feed = feeds.value.find(f => f.id === feedId)
    if (!feed) return
    await api.post(`/api/v1/square/feeds/${feedId}/favorite`)
    feed.isFavorited = !feed.isFavorited
  }

  /** 获取热门标签 */
  const fetchHotTags = async () => {
    const result = await api.get<string[]>('/api/v1/square/hot-tags')
    hotTags.value = result
  }

  return {
    feeds,
    hotTags,
    currentFeed,
    loading,
    hasMore,
    fetchFeeds,
    publishFeed,
    toggleLike,
    toggleFavorite,
    fetchHotTags,
  }
})

interface SquareFeed {
  id: string
  content: string
  images?: string[]
  tags?: string[]
  authorId: string
  authorNickname: string
  authorAvatar: string
  likeCount: number
  commentCount: number
  isLiked: boolean
  isFavorited: boolean
  createdAt: number
}

interface SquareFeedDetail extends SquareFeed {
  comments: SquareComment[]
}

interface SquareComment {
  id: string
  content: string
  authorId: string
  authorNickname: string
  authorAvatar: string
  createdAt: number
}
```

#### 8.4.3 notification.ts

```typescript
// src/stores/notification.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'

export const useNotificationStore = defineStore('notification', () => {
  // ===== 状态 =====
  /** 通知列表 */
  const notifications = ref<NotificationItem[]>([])
  /** 未读通知数 */
  const unreadCount = ref(0)
  /** 极光推送注册ID */
  const registrationId = ref('')
  /** 是否已注册极光推送 */
  const isPushRegistered = ref(false)
  /** 是否正在加载 */
  const loading = ref(false)

  // ===== 计算属性 =====
  /** 按类型分组的通知 */
  const groupedNotifications = computed(() => {
    const groups: Record<string, NotificationItem[]> = {}
    for (const item of notifications.value) {
      const type = item.type
      if (!groups[type]) groups[type] = []
      groups[type].push(item)
    }
    return groups
  })

  // ===== 操作 =====
  /** 注册极光推送 */
  const registerPush = async () => {
    // #ifdef APP-PLUS
    const jpush = uni.requireNativePlugin('JPush')
    jpush.addConnectEventListener(() => {
      isPushRegistered.value = true
    })
    jpush.addRegistrationListener((result: any) => {
      registrationId.value = result.registrationId
      // 将注册ID上报服务端
      api.post('/api/v1/user/push-register', {
        registrationId: result.registrationId,
        platform: 'app',
      })
    })
    jpush.init()
    // #endif
  }

  /** 获取通知列表 */
  const fetchNotifications = async () => {
    loading.value = true
    try {
      const result = await api.get<NotificationItem[]>('/api/v1/notifications')
      notifications.value = result
      unreadCount.value = result.filter(n => !n.isRead).length
    } finally {
      loading.value = false
    }
  }

  /** 标记通知为已读 */
  const markAsRead = async (notificationId: string) => {
    await api.patch(`/api/v1/notifications/${notificationId}/read`)
    const item = notifications.value.find(n => n.id === notificationId)
    if (item && !item.isRead) {
      item.isRead = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  }

  /** 全部标记已读 */
  const markAllAsRead = async () => {
    await api.patch('/api/v1/notifications/read-all')
    notifications.value.forEach(n => { n.isRead = true })
    unreadCount.value = 0
  }

  return {
    notifications,
    unreadCount,
    registrationId,
    isPushRegistered,
    loading,
    groupedNotifications,
    registerPush,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
  }
})

interface NotificationItem {
  id: string
  type: 'like' | 'comment' | 'system' | 'crisis' | 'report'
  title: string
  content: string
  isRead: boolean
  relatedId?: string
  createdAt: number
}
```

#### 8.4.4 search.ts

```typescript
// src/stores/search.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'
import { getStorage, setStorage } from '@/utils/storage'

export const useSearchStore = defineStore('search', () => {
  // ===== 状态 =====
  /** 搜索关键词 */
  const keyword = ref('')
  /** 搜索结果 */
  const results = ref<SearchResult[]>([])
  /** 搜索历史（持久化到本地） */
  const searchHistory = ref<string[]>(getStorage('search_history') || [])
  /** 搜索建议 */
  const suggestions = ref<string[]>([])
  /** 是否正在搜索 */
  const searching = ref(false)
  /** 当前搜索类型 */
  const searchType = ref<'all' | 'treehole' | 'square' | 'diary'>('all')

  // ===== 常量 =====
  const MAX_HISTORY = 20

  // ===== 操作 =====
  /** 执行搜索 */
  const search = async (kw: string) => {
    if (!kw.trim()) return
    keyword.value = kw
    searching.value = true
    try {
      const result = await api.get<SearchResult[]>('/api/v1/search', {
        keyword: kw,
        type: searchType.value,
      })
      results.value = result
      addToHistory(kw)
    } finally {
      searching.value = false
    }
  }

  /** 获取搜索建议 */
  const fetchSuggestions = async (kw: string) => {
    if (!kw.trim()) {
      suggestions.value = []
      return
    }
    const result = await api.get<string[]>('/api/v1/search/suggestions', { keyword: kw })
    suggestions.value = result
  }

  /** 添加到搜索历史 */
  const addToHistory = (kw: string) => {
    const idx = searchHistory.value.indexOf(kw)
    if (idx > -1) searchHistory.value.splice(idx, 1)
    searchHistory.value.unshift(kw)
    if (searchHistory.value.length > MAX_HISTORY) {
      searchHistory.value = searchHistory.value.slice(0, MAX_HISTORY)
    }
    setStorage('search_history', searchHistory.value)
  }

  /** 清空搜索历史 */
  const clearHistory = () => {
    searchHistory.value = []
    setStorage('search_history', [])
  }

  /** 重置搜索状态 */
  const reset = () => {
    keyword.value = ''
    results.value = []
    suggestions.value = []
  }

  return {
    keyword,
    results,
    searchHistory,
    suggestions,
    searching,
    searchType,
    search,
    fetchSuggestions,
    clearHistory,
    reset,
  }
})

interface SearchResult {
  id: string
  type: 'treehole' | 'square' | 'diary'
  title: string
  content: string
  highlight?: string  // 高亮摘要
  createdAt: number
}
```

#### 8.4.5 emotion.ts

```typescript
// src/stores/emotion.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** 情绪类型定义 */
export type EmotionType = 'warm' | 'calm' | 'blue' | 'sad' | 'chaos'

/** 情绪配置映射 */
const EMOTION_CONFIG: Record<EmotionType, {
  label: string
  color: string
  bgColor: string
  subLabels: string[]
}> = {
  warm: {
    label: '暖橘',
    color: '#FF9A5C',
    bgColor: 'rgba(255, 154, 92, 0.1)',
    subLabels: ['开心', '温暖', '期待', '满足'],
  },
  calm: {
    label: '浅绿',
    color: '#8FCCA0',
    bgColor: 'rgba(143, 204, 160, 0.1)',
    subLabels: ['平静', '安稳', '放松', '舒适'],
  },
  blue: {
    label: '灰蓝',
    color: '#8BA7C4',
    bgColor: 'rgba(139, 167, 196, 0.1)',
    subLabels: ['低落', '沉闷', '疲惫', '无聊'],
  },
  sad: {
    label: '深蓝',
    color: '#4A6FA5',
    bgColor: 'rgba(74, 111, 165, 0.1)',
    subLabels: ['难过', '忧伤', '失落', '心痛'],
  },
  chaos: {
    label: '暗紫',
    color: '#6B4C7A',
    bgColor: 'rgba(107, 76, 122, 0.1)',
    subLabels: ['崩溃', '混乱', '无助', '绝望'],
  },
}

export const useEmotionStore = defineStore('emotion', () => {
  // ===== 状态 =====
  /** 当前选中的情绪类型 */
  const currentEmotion = ref<EmotionType>('warm')
  /** 当前选中的二层标签 */
  const currentSubLabel = ref('')
  /** 情绪切换动画是否进行中 */
  const isTransitioning = ref(false)

  // ===== 计算属性 =====
  /** 当前情绪配置 */
  const emotionConfig = computed(() => EMOTION_CONFIG[currentEmotion.value])
  /** 当前情绪色彩 */
  const emotionColor = computed(() => emotionConfig.value.color)
  /** 当前情绪背景色 */
  const emotionBgColor = computed(() => emotionConfig.value.bgColor)
  /** 当前情绪标签文字 */
  const emotionLabel = computed(() => emotionConfig.value.label)
  /** 当前情绪二层标签列表 */
  const emotionSubLabels = computed(() => emotionConfig.value.subLabels)

  // ===== 操作 =====
  /** 设置情绪类型（带动画过渡） */
  const setEmotion = (emotion: EmotionType) => {
    isTransitioning.value = true
    currentEmotion.value = emotion
    currentSubLabel.value = ''
    // 动画结束后重置状态
    setTimeout(() => {
      isTransitioning.value = false
    }, 300)
  }

  /** 设置二层标签 */
  const setSubLabel = (subLabel: string) => {
    currentSubLabel.value = subLabel
  }

  /** 重置情绪状态 */
  const reset = () => {
    currentEmotion.value = 'warm'
    currentSubLabel.value = ''
    isTransitioning.value = false
  }

  return {
    currentEmotion,
    currentSubLabel,
    isTransitioning,
    emotionConfig,
    emotionColor,
    emotionBgColor,
    emotionLabel,
    emotionSubLabels,
    setEmotion,
    setSubLabel,
    reset,
  }
})
```

#### 8.4.6 sync.ts

```typescript
// src/stores/sync.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'
import { getStorage, setStorage } from '@/utils/storage'

export const useSyncStore = defineStore('sync', () => {
  // ===== 状态 =====
  /** 网络是否在线 */
  const isOnline = ref(true)
  /** 同步状态：idle / syncing / error */
  const syncStatus = ref<'idle' | 'syncing' | 'error'>('idle')
  /** 离线操作队列（待同步的操作列表） */
  const pendingQueue = ref<SyncOperation[]>(getStorage('sync_pending') || [])
  /** 同步进度（0-100） */
  const syncProgress = ref(0)
  /** 上次同步时间戳 */
  const lastSyncTime = ref<number>(getStorage('sync_last_time') || 0)
  /** 同步错误信息 */
  const syncError = ref<string>('')

  // ===== 计算属性 =====
  /** 是否有待同步的操作 */
  const hasPending = computed(() => pendingQueue.value.length > 0)
  /** 待同步操作数量 */
  const pendingCount = computed(() => pendingQueue.value.length)

  // ===== 操作 =====
  /** 监听网络状态变化 */
  const initNetworkListener = () => {
    uni.onNetworkStatusChange((result) => {
      const wasOffline = !isOnline.value
      isOnline.value = result.isConnected
      // 从离线恢复到在线时，自动触发同步
      if (wasOffline && result.isConnected && hasPending.value) {
        syncPendingOperations()
      }
    })
  }

  /** 添加离线操作到队列 */
  const addPendingOperation = (operation: Omit<SyncOperation, 'id' | 'createdAt'>) => {
    const op: SyncOperation = {
      id: `sync_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      createdAt: Date.now(),
      ...operation,
    }
    pendingQueue.value.push(op)
    persistQueue()
  }

  /** 同步离线操作 */
  const syncPendingOperations = async () => {
    if (!isOnline.value || syncStatus.value === 'syncing' || !hasPending.value) return

    syncStatus.value = 'syncing'
    syncError.value = ''
    const total = pendingQueue.value.length
    let completed = 0

    try {
      // 按创建时间排序，先入先出
      const sorted = [...pendingQueue.value].sort((a, b) => a.createdAt - b.createdAt)

      for (const op of sorted) {
        try {
          await api.request({
            url: op.url,
            method: op.method,
            data: op.data,
          })
          // 成功后从队列中移除
          const idx = pendingQueue.value.findIndex(item => item.id === op.id)
          if (idx > -1) pendingQueue.value.splice(idx, 1)
        } catch (err) {
          // 单条失败不影响后续同步
          console.warn(`同步操作失败: ${op.id}`, err)
        }
        completed++
        syncProgress.value = Math.round((completed / total) * 100)
      }

      persistQueue()
      lastSyncTime.value = Date.now()
      setStorage('sync_last_time', lastSyncTime.value)
      syncStatus.value = 'idle'
      syncProgress.value = 100
    } catch (err) {
      syncStatus.value = 'error'
      syncError.value = err instanceof Error ? err.message : '同步失败'
    }
  }

  /** 持久化队列到本地存储 */
  const persistQueue = () => {
    setStorage('sync_pending', pendingQueue.value)
  }

  /** 清空同步队列（谨慎使用） */
  const clearQueue = () => {
    pendingQueue.value = []
    persistQueue()
  }

  return {
    isOnline,
    syncStatus,
    pendingQueue,
    syncProgress,
    lastSyncTime,
    syncError,
    hasPending,
    pendingCount,
    initNetworkListener,
    addPendingOperation,
    syncPendingOperations,
    clearQueue,
  }
})

interface SyncOperation {
  id: string
  /** 请求URL */
  url: string
  /** 请求方法 */
  method: 'POST' | 'PUT' | 'DELETE'
  /** 请求数据 */
  data: any
  /** 创建时间 */
  createdAt: number
}
```

**Store 目录更新**：

```
src/stores/
├── index.ts              # Store入口（导出所有Store）
├── user.ts               # 用户状态
├── chat.ts               # 对话状态
├── message.ts            # 消息状态
├── diary.ts              # 日记状态
├── settings.ts           # 设置状态
├── treehole.ts           # 树洞状态（新增）
├── square.ts             # 广场状态（新增）
├── notification.ts       # 通知状态（新增）
├── search.ts             # 搜索状态（新增）
├── emotion.ts            # 情绪状态（新增）
└── sync.ts               # 同步状态（新增）
```

---

### 8.5 P2-15：主题切换使用 wot-design-uni 的 ConfigProvider

**问题**：当前 `useTheme.ts` 通过手动设置 `CSS class` 和 `uni.setPageStyle` 实现主题切换，存在以下问题：
1. 每个页面需手动调用 `applyTheme`，容易遗漏
2. 组件库内部组件无法感知主题变化
3. 情绪色彩与主题切换未打通

**方案**：使用 wot-design-uni 提供的 `wd-config-provider` 组件实现全局主题配置，一处在根组件配置，全应用生效。

**实现方案**：

```vue
<!-- src/App.vue -->
<template>
  <wd-config-provider :themeVars="themeVars" :theme="currentTheme">
    <!-- 应用根节点 -->
    <router-view />
  </wd-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useEmotionStore } from '@/stores/emotion'

const settingsStore = useSettingsStore()
const emotionStore = useEmotionStore()

/** 当前主题：light / dark */
const currentTheme = computed(() => settingsStore.theme)

/** 主题变量：融合 wot-design-uni 默认变量 + 情绪色彩变量 */
const themeVars = computed(() => {
  const emotionColor = emotionStore.emotionColor
  const emotionBgColor = emotionStore.emotionBgColor

  return {
    // 覆盖 wot-design-uni 主题色为当前情绪色
    '--wd-color-theme': emotionColor,
    '--wd-color-theme-light': emotionBgColor,

    // 情绪色彩系统
    '--emotion-warm': '#FF9A5C',
    '--emotion-calm': '#8FCCA0',
    '--emotion-blue': '#8BA7C4',
    '--emotion-anxious': '#4A6FA5',
    '--emotion-night': '#6B4C7A',

    // 当前激活情绪色
    '--emotion-active': emotionColor,
    '--emotion-active-bg': emotionBgColor,
  }
})
</script>
```

**重构 useTheme.ts**：

```typescript
// src/composables/useTheme.ts（重构版）
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

export type ThemeMode = 'light' | 'dark' | 'system'

export const useTheme = () => {
  const settingsStore = useSettingsStore()

  /** 当前是否为暗色模式 */
  const isDark = computed(() => {
    if (settingsStore.theme === 'system') {
      return uni.getSystemInfoSync().theme === 'dark'
    }
    return settingsStore.theme === 'dark'
  })

  /** 当前主题模式 */
  const themeMode = computed(() => settingsStore.theme as ThemeMode)

  /** 切换主题 */
  const toggleTheme = () => {
    const modes: ThemeMode[] = ['light', 'dark', 'system']
    const currentIdx = modes.indexOf(settingsStore.theme as ThemeMode)
    const nextMode = modes[(currentIdx + 1) % modes.length]
    settingsStore.setTheme(nextMode)
  }

  /** 设置指定主题 */
  const setTheme = (mode: ThemeMode) => {
    settingsStore.setTheme(mode)
  }

  return {
    isDark,
    themeMode,
    toggleTheme,
    setTheme,
  }
}
```

**关键变化**：
1. 移除手动 `applyTheme` 逻辑，主题切换由 `wd-config-provider` 自动处理
2. 情绪色彩通过 `themeVars` 动态注入，组件库组件自动响应
3. 主题切换支持三种模式：亮色 / 暗色 / 跟随系统
4. 仅在 `App.vue` 根组件配置一次，无需每个页面重复调用

---

### 8.6 P2-16：语音输入集成科大讯飞 SDK

**方案**：在消息输入组件中集成科大讯飞语音听写（流式版）SDK，支持语音转文字实时输入。

**技术选型**：

| 项目 | 选择 | 说明 |
|------|------|------|
| SDK | 科大讯飞语音听写（流式版）WebAPI | 支持实时流式语音识别 |
| 协议 | WebSocket | 讯飞语音听写使用 WebSocket 协议通信 |
| 端侧差异 | App端：原生插件；H5端：WebSocket直连；小程序端：录音上传 | 各端实现方式不同 |

**集成架构**：

```
用户按住说话
    │
    ▼
┌──────────────────────────┐
│     VoiceInput 组件       │
│  ┌────────────────────┐  │
│  │  录音状态管理       │  │
│  │  - 按下：开始录音   │  │
│  │  - 松开：停止录音   │  │
│  │  - 上滑：取消输入   │  │
│  └────────────────────┘  │
│           │               │
│           ▼               │
│  ┌────────────────────┐  │
│  │  useVoiceInput     │  │
│  │  - 管理SDK连接      │  │
│  │  - 接收识别结果     │  │
│  │  - 处理错误重试     │  │
│  └────────────────────┘  │
│           │               │
│           ▼               │
│  ┌────────────────────┐  │
│  │  识别结果回调       │  │
│  │  - 实时中间结果     │  │
│  │  - 最终识别结果     │  │
│  └────────────────────┘  │
└──────────────────────────┘
```

**composable 实现**：

```typescript
// src/composables/useVoiceInput.ts
import { ref, onUnmounted } from 'vue'

/** 科大讯飞语音听写配置 */
const XFYUN_CONFIG = {
  /** AppID */
  appId: import.meta.env.VITE_XFYUN_APP_ID,
  /** APIKey */
  apiKey: import.meta.env.VITE_XFYUN_API_KEY,
  /** APISecret */
  apiSecret: import.meta.env.VITE_XFYUN_API_SECRET,
  /** 识别语言 */
  language: 'zh_cn',
  /** 识别领域 */
  domain: 'iat',
  /** 采样率 */
  sampleRate: 16000,
}

export const useVoiceInput = () => {
  // ===== 状态 =====
  /** 是否正在录音 */
  const isRecording = ref(false)
  /** 是否正在识别中（录音结束但识别尚未完成） */
  const isRecognizing = ref(false)
  /** 实时中间识别结果 */
  const interimResult = ref('')
  /** 最终识别结果 */
  const finalResult = ref('')
  /** 录音时长（秒） */
  const duration = ref(0)
  /** 音量大小（0-100） */
  const volume = ref(0)
  /** 错误信息 */
  const error = ref<string>('')

  // 内部变量
  let recorderManager: UniApp.RecorderManager | null = null
  let wsConnection: any = null
  let durationTimer: ReturnType<typeof setInterval> | null = null
  let audioDataQueue: ArrayBuffer[] = []

  // ===== 方法 =====

  /** 开始录音 */
  const startRecording = () => {
    error.value = ''
    interimResult.value = ''
    finalResult.value = ''
    duration.value = 0
    audioDataQueue = []

    // 获取录音管理器
    recorderManager = uni.getRecorderManager()

    // 监听录音数据
    recorderManager.onFrameRecorded((res) => {
      audioDataQueue.push(res.frameBuffer)
      // 将音频数据发送给讯飞识别服务
      sendAudioToXfyun(res.frameBuffer)
    })

    // 监听录音结束
    recorderManager.onStop(() => {
      isRecording.value = false
      isRecognizing.value = true
      // 通知讯飞服务音频传输结束
      finishXfyunRecognition()
    })

    // 监听录音错误
    recorderManager.onError((err) => {
      error.value = `录音失败: ${err.errMsg}`
      isRecording.value = false
    })

    // 开始录音（PCM格式，16kHz采样率）
    recorderManager.start({
      format: 'PCM',
      sampleRate: 16000,
      numberOfChannels: 1,
      encodeBitRate: 96000,
      frameSize: 10, // 每帧10ms
    })

    isRecording.value = true

    // 开始计时
    durationTimer = setInterval(() => {
      duration.value++
      // 最长60秒自动停止
      if (duration.value >= 60) {
        stopRecording()
      }
    }, 1000)

    // 建立讯飞WebSocket连接
    connectXfyun()
  }

  /** 停止录音 */
  const stopRecording = () => {
    if (durationTimer) {
      clearInterval(durationTimer)
      durationTimer = null
    }
    recorderManager?.stop()
  }

  /** 取消录音（不进行识别） */
  const cancelRecording = () => {
    if (durationTimer) {
      clearInterval(durationTimer)
      durationTimer = null
    }
    recorderManager?.stop()
    closeXfyunConnection()
    isRecording.value = false
    isRecognizing.value = false
    interimResult.value = ''
    finalResult.value = ''
  }

  /** 建立讯飞WebSocket连接 */
  const connectXfyun = () => {
    // #ifdef H5
    // H5端：直接通过WebSocket连接讯飞语音听写服务
    // 生成鉴权URL（后端代理方式更安全，此处简化说明）
    const authUrl = generateXfyunAuthUrl()
    wsConnection = new WebSocket(authUrl)

    wsConnection.onopen = () => {
      // 发送首帧参数
      const params = {
        common: {
          app_id: XFYUN_CONFIG.appId,
        },
        business: {
          language: XFYUN_CONFIG.language,
          domain: XFYUN_CONFIG.domain,
          accent: 'mandarin',
          vad_eos: 2000,
          dwa: 'wpgs', // 动态修正
        },
        data: {
          status: 0, // 首帧
          format: 'audio/L16;rate=16000',
          encoding: 'raw',
        },
      }
      wsConnection.send(JSON.stringify(params))
    }

    wsConnection.onmessage = (event: MessageEvent) => {
      const result = JSON.parse(event.data)
      if (result.code !== 0) {
        error.value = `识别错误: ${result.message}`
        return
      }
      const data = result.data
      if (data.result) {
        if (data.status === 2) {
          // 最终结果
          finalResult.value = data.result.ws
            .map((w: any) => w.cw.map((c: any) => c.w).join(''))
            .join('')
          isRecognizing.value = false
        } else {
          // 中间结果
          interimResult.value = data.result.ws
            .map((w: any) => w.cw.map((c: any) => c.w).join(''))
            .join('')
        }
      }
    }

    wsConnection.onerror = () => {
      error.value = '语音识别服务连接失败'
      isRecognizing.value = false
    }
    // #endif

    // #ifdef APP-PLUS
    // App端：使用讯飞原生插件（更稳定，延迟更低）
    const xfyunPlugin = uni.requireNativePlugin('Xfyun-Speech')
    if (xfyunPlugin) {
      xfyunPlugin.startListening({
        appId: XFYUN_CONFIG.appId,
        language: XFYUN_CONFIG.language,
        domain: XFYUN_CONFIG.domain,
      }, (result: any) => {
        if (result.isFinal) {
          finalResult.value = result.text
          isRecognizing.value = false
        } else {
          interimResult.value = result.text
        }
      }, (err: any) => {
        error.value = `识别错误: ${err.message}`
        isRecognizing.value = false
      })
    }
    // #endif
  }

  /** 发送音频数据到讯飞服务 */
  const sendAudioToXfyun = (audioData: ArrayBuffer) => {
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      const params = {
        data: {
          status: 1, // 数据帧
          format: 'audio/L16;rate=16000',
          encoding: 'raw',
          audio: arrayBufferToBase64(audioData),
        },
      }
      wsConnection.send(JSON.stringify(params))
    }
  }

  /** 结束识别 */
  const finishXfyunRecognition = () => {
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      const params = {
        data: {
          status: 2, // 结束帧
          format: 'audio/L16;rate=16000',
          encoding: 'raw',
        },
      }
      wsConnection.send(JSON.stringify(params))
    }
  }

  /** 关闭讯飞连接 */
  const closeXfyunConnection = () => {
    if (wsConnection) {
      wsConnection.close()
      wsConnection = null
    }
  }

  /** 生成讯飞鉴权URL（简化版，生产环境应由后端生成） */
  const generateXfyunAuthUrl = (): string => {
    // 生产环境中，鉴权URL应由后端API生成，避免APIKey/Secret泄露
    // 此处仅作为逻辑说明
    return `${import.meta.env.VITE_XFYUN_WS_URL}`
  }

  /** ArrayBuffer转Base64 */
  const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
  }

  // 组件卸载时清理
  onUnmounted(() => {
    cancelRecording()
  })

  return {
    isRecording,
    isRecognizing,
    interimResult,
    finalResult,
    duration,
    volume,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  }
}
```

**语音输入按钮组件**：

```vue
<!-- src/components/chat/VoiceInput.vue -->
<template>
  <view class="voice-input">
    <!-- 语音输入按钮（长按录音） -->
    <view
      class="voice-input__btn"
      :class="{
        'voice-input__btn--recording': isRecording,
        'voice-input__btn--cancel': isCancelling,
      }"
      @touchstart.prevent="handleTouchStart"
      @touchmove.prevent="handleTouchMove"
      @touchend.prevent="handleTouchEnd"
    >
      <wd-icon :name="isRecording ? 'microphone-open' : 'microphone'" size="24px" />
      <text class="voice-input__text">
        {{ isRecording ? (isCancelling ? '松开取消' : '松开发送') : '按住说话' }}
      </text>
    </view>

    <!-- 录音状态浮层 -->
    <wd-popup v-model="showRecordingPopup" position="center" :close-on-click-overlay="false">
      <view class="voice-input__popup">
        <view class="voice-input__wave">
          <!-- 音量波形动画 -->
          <view
            v-for="i in 5"
            :key="i"
            class="voice-input__wave-bar"
            :style="{ height: getWaveHeight(i) + 'px' }"
          />
        </view>
        <text class="voice-input__duration">{{ formatDuration(duration) }}</text>
        <text class="voice-input__hint">
          {{ isCancelling ? '松开取消发送' : '上滑取消发送' }}
        </text>
      </view>
    </wd-popup>

    <!-- 识别结果预览 -->
    <view v-if="interimResult || finalResult" class="voice-input__preview">
      <text class="voice-input__result">{{ finalResult || interimResult }}</text>
      <text v-if="isRecognizing && !finalResult" class="voice-input__recognizing">识别中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useVoiceInput } from '@/composables/useVoiceInput'

const emit = defineEmits<{
  /** 语音识别完成，返回最终文本 */
  result: [text: string]
  /** 录音取消 */
  cancel: []
}>()

const {
  isRecording,
  isRecognizing,
  interimResult,
  finalResult,
  duration,
  volume,
  error,
  startRecording,
  stopRecording,
  cancelRecording,
} = useVoiceInput()

// 是否正在取消（上滑触发）
const isCancelling = ref(false)
// 是否显示录音浮层
const showRecordingPopup = ref(false)
// 触摸起始Y坐标
const touchStartY = ref(0)

// 监听识别完成
watch(finalResult, (result) => {
  if (result) {
    emit('result', result)
    showRecordingPopup.value = false
  }
})

// 监听错误
watch(error, (err) => {
  if (err) {
    uni.showToast({ title: err, icon: 'none' })
    showRecordingPopup.value = false
  }
})

// 触摸开始
const handleTouchStart = (e: any) => {
  touchStartY.value = e.touches[0].clientY
  isCancelling.value = false
  showRecordingPopup.value = true
  startRecording()
}

// 触摸移动（检测上滑取消）
const handleTouchMove = (e: any) => {
  const deltaY = touchStartY.value - e.touches[0].clientY
  isCancelling.value = deltaY > 80 // 上滑超过80px视为取消
}

// 触摸结束
const handleTouchEnd = () => {
  if (isCancelling.value) {
    cancelRecording()
    emit('cancel')
  } else {
    stopRecording()
  }
  isCancelling.value = false
}

// 音量波形高度
const getWaveHeight = (index: number) => {
  const baseHeight = 8
  const maxExtra = 30
  const volumeRatio = volume.value / 100
  const wave = Math.sin((Date.now() / 200) + index * 0.8) * 0.5 + 0.5
  return baseHeight + wave * maxExtra * volumeRatio
}

// 格式化时长
const formatDuration = (seconds: number) => {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0')
  const s = (seconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}
</script>
```

**鉴权安全建议**：
- 讯飞鉴权URL应由后端API动态生成，前端仅调用后端接口获取URL
- `VITE_XFYUN_API_KEY` 和 `VITE_XFYUN_API_SECRET` 不应暴露在前端代码中
- App端使用原生插件可避免鉴权信息泄露风险

---

### 8.7 P2-17：图片上传压缩方案补充

**问题**：当前 `useUpload.ts` 缺少图片压缩逻辑，直接上传原图可能导致：上传速度慢、流量消耗大、OSS存储成本高。

**方案**：在前端上传前对图片进行压缩处理，平衡图片质量与体积。

**压缩策略**：

| 场景 | 最大尺寸 | 最大体积 | 压缩质量 | 输出格式 |
|------|---------|---------|---------|---------|
| 头像 | 512 x 512 | 200KB | 0.8 | JPEG |
| 树洞配图 | 1280 x 1280 | 500KB | 0.75 | JPEG |
| 广场动态 | 1920 x 1920 | 1MB | 0.8 | JPEG |
| 日记配图 | 1920 x 1920 | 1MB | 0.8 | JPEG |

**压缩工具实现**：

```typescript
// src/utils/imageCompress.ts

/** 压缩配置 */
interface CompressOptions {
  /** 最大宽度 */
  maxWidth?: number
  /** 最大高度 */
  maxHeight?: number
  /** 压缩质量（0-1） */
  quality?: number
  /** 输出格式 */
  format?: 'jpeg' | 'png' | 'webp'
  /** 最大文件体积（字节），超过此体积将逐步降低质量 */
  maxSize?: number
}

/** 默认压缩配置 */
const DEFAULT_OPTIONS: Required<CompressOptions> = {
  maxWidth: 1920,
  maxHeight: 1920,
  quality: 0.8,
  format: 'jpeg',
  maxSize: 1024 * 1024, // 1MB
}

/**
 * 图片压缩主函数
 * 根据平台选择不同的压缩实现
 */
export async function compressImage(
  filePath: string,
  options: CompressOptions = {}
): Promise<CompressResult> {
  const opts = { ...DEFAULT_OPTIONS, ...options }

  // 获取图片原始信息
  const info = await getImageInfo(filePath)

  // 计算缩放尺寸
  const { width, height } = calculateTargetSize(info.width, info.height, opts.maxWidth, opts.maxHeight)

  // #ifdef APP-PLUS || MP-WEIXIN
  // App端和小程序端：使用 uni.compressImage 原生API
  return compressForNative(filePath, opts.quality, opts.maxSize)
  // #endif

  // #ifdef H5
  // H5端：使用 Canvas 压缩
  return compressForH5(filePath, width, height, opts)
  // #endif
}

/**
 * App端/小程序端压缩
 * 使用 uni.compressImage 原生API
 */
async function compressForNative(
  filePath: string,
  quality: number,
  maxSize: number
): Promise<CompressResult> {
  let currentQuality = quality
  let compressedPath = filePath

  // 逐步降低质量直到体积满足要求
  for (let attempt = 0; attempt < 3; attempt++) {
    const result = await new Promise<UniApp.CompressImageRes>((resolve, reject) => {
      uni.compressImage({
        src: filePath,
        quality: Math.round(currentQuality * 100),
        success: resolve,
        fail: reject,
      })
    })
    compressedPath = result.tempFilePath

    // 获取压缩后文件体积
    const fileInfo = await getFileInfo(compressedPath)
    if (fileInfo.size <= maxSize || currentQuality <= 0.3) {
      break
    }
    // 降低质量继续压缩
    currentQuality -= 0.15
  }

  const finalInfo = await getFileInfo(compressedPath)
  return {
    path: compressedPath,
    size: finalInfo.size,
    width: 0,  // 原生API不返回尺寸，使用时再获取
    height: 0,
  }
}

/**
 * H5端压缩
 * 使用 Canvas 进行精确控制
 */
async function compressForH5(
  filePath: string,
  targetWidth: number,
  targetHeight: number,
  opts: Required<CompressOptions>
): Promise<CompressResult> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = targetWidth
      canvas.height = targetHeight

      const ctx = canvas.getContext('2d')!
      ctx.drawImage(img, 0, 0, targetWidth, targetHeight)

      const mimeType = `image/${opts.format}`
      let quality = opts.quality
      let dataUrl: string

      // 逐步降低质量直到体积满足要求
      for (let attempt = 0; attempt < 5; attempt++) {
        dataUrl = canvas.toDataURL(mimeType, quality)
        const size = Math.round((dataUrl.length - `data:${mimeType};base64,`.length) * 0.75)
        if (size <= opts.maxSize || quality <= 0.3) {
          resolve({
            path: dataUrl,
            size,
            width: targetWidth,
            height: targetHeight,
          })
          return
        }
        quality -= 0.1
      }

      // 最终兜底
      dataUrl = canvas.toDataURL(mimeType, 0.3)
      const size = Math.round((dataUrl.length - `data:${mimeType};base64,`.length) * 0.75)
      resolve({
        path: dataUrl,
        size,
        width: targetWidth,
        height: targetHeight,
      })
    }
    img.onerror = reject
    img.src = filePath
  })
}

/**
 * 计算目标缩放尺寸（等比缩放）
 */
function calculateTargetSize(
  srcWidth: number,
  srcHeight: number,
  maxWidth: number,
  maxHeight: number
): { width: number; height: number } {
  let width = srcWidth
  let height = srcHeight

  if (width > maxWidth) {
    height = Math.round(height * (maxWidth / width))
    width = maxWidth
  }
  if (height > maxHeight) {
    width = Math.round(width * (maxHeight / height))
    height = maxHeight
  }

  return { width, height }
}

/**
 * 获取图片信息
 */
function getImageInfo(filePath: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    uni.getImageInfo({
      src: filePath,
      success: (res) => resolve({ width: res.width, height: res.height }),
      fail: reject,
    })
  })
}

/**
 * 获取文件信息
 */
function getFileInfo(filePath: string): Promise<{ size: number }> {
  return new Promise((resolve, reject) => {
    // #ifdef APP-PLUS || MP-WEIXIN
    uni.getFileInfo({
      filePath,
      success: (res) => resolve({ size: res.size }),
      fail: reject,
    })
    // #endif
    // #ifdef H5
    resolve({ size: 0 }) // H5端通过Canvas已获取体积
    // #endif
  })
}

/** 压缩结果 */
interface CompressResult {
  /** 压缩后的文件路径（或H5端的Base64 DataURL） */
  path: string
  /** 文件体积（字节） */
  size: number
  /** 图片宽度 */
  width: number
  /** 图片高度 */
  height: number
}

/**
 * 预设压缩配置
 */
export const COMPRESS_PRESETS = {
  /** 头像压缩 */
  avatar: { maxWidth: 512, maxHeight: 512, quality: 0.8, maxSize: 200 * 1024 },
  /** 树洞配图压缩 */
  treehole: { maxWidth: 1280, maxHeight: 1280, quality: 0.75, maxSize: 500 * 1024 },
  /** 广场动态压缩 */
  square: { maxWidth: 1920, maxHeight: 1920, quality: 0.8, maxSize: 1024 * 1024 },
  /** 日记配图压缩 */
  diary: { maxWidth: 1920, maxHeight: 1920, quality: 0.8, maxSize: 1024 * 1024 },
} as const
```

**useUpload 集成压缩**：

```typescript
// src/composables/useUpload.ts（改造要点）

import { compressImage, COMPRESS_PRESETS } from '@/utils/imageCompress'

export const useUpload = () => {
  /**
   * 上传图片（带压缩）
   * @param filePath 本地文件路径
   * @param scene 上传场景，决定压缩参数
   */
  const uploadImage = async (
    filePath: string,
    scene: keyof typeof COMPRESS_PRESETS = 'square'
  ): Promise<UploadResult> => {
    // 1. 压缩图片
    const compressed = await compressImage(filePath, COMPRESS_PRESETS[scene])

    // 2. 上传到OSS
    const result = await uploadToOSS(compressed.path)

    return {
      url: result.url,
      size: compressed.size,
      width: compressed.width,
      height: compressed.height,
    }
  }

  /** 上传到OSS（具体实现依赖后端签名URL方案） */
  const uploadToOSS = async (filePath: string) => {
    // 1. 获取后端签名上传URL
    const { uploadUrl, fileUrl } = await api.get<{
      uploadUrl: string
      fileUrl: string
    }>('/api/v1/upload/signature', { fileType: 'image' })

    // 2. 上传文件到OSS
    await new Promise<void>((resolve, reject) => {
      uni.uploadFile({
        url: uploadUrl,
        filePath,
        name: 'file',
        success: () => resolve(),
        fail: (err) => reject(new Error(err.errMsg || '上传失败')),
      })
    })

    return { url: fileUrl }
  }

  return { uploadImage }
}

interface UploadResult {
  url: string
  size: number
  width: number
  height: number
}
```

---

### 8.8 P2-18：举报弹窗组件补充

**方案**：实现标准化的举报弹窗组件，用于树洞、广场、评论等场景的举报功能。

**举报类型定义**：

| 类型ID | 类型名称 | 适用场景 |
|--------|---------|---------|
| spam | 垃圾信息 | 广告、刷屏 |
| abuse | 辱骂攻击 | 人身攻击、语言暴力 |
| harm | 自伤/伤人 | 自残、暴力倾向 |
| privacy | 隐私泄露 | 个人信息暴露 |
| inappropriate | 不当内容 | 色情、违法内容 |
| other | 其他 | 不属于以上分类 |

**举报弹窗组件**：

```vue
<!-- src/components/common/ReportDialog.vue -->
<template>
  <wd-popup
    v-model="visible"
    position="bottom"
    :safe-area-inset-bottom="true"
    custom-style="border-radius: 24rpx 24rpx 0 0"
    @close="handleClose"
  >
    <view class="report-dialog">
      <!-- 标题栏 -->
      <view class="report-dialog__header">
        <text class="report-dialog__title">举报内容</text>
        <wd-icon name="close" class="report-dialog__close" @click="handleClose" />
      </view>

      <!-- 举报类型选择 -->
      <view class="report-dialog__types">
        <view
          v-for="item in reportTypes"
          :key="item.value"
          class="report-dialog__type-item"
          :class="{ 'report-dialog__type-item--active': selectedType === item.value }"
          @tap="selectedType = item.value"
        >
          <wd-icon
            :name="selectedType === item.value ? 'check-circle-filled' : 'circle'"
            :color="selectedType === item.value ? '#FF9A5C' : '#9ca3af'"
          />
          <view class="report-dialog__type-info">
            <text class="report-dialog__type-label">{{ item.label }}</text>
            <text class="report-dialog__type-desc">{{ item.description }}</text>
          </view>
        </view>
      </view>

      <!-- 补充描述 -->
      <view class="report-dialog__detail">
        <wd-textarea
          v-model="detail"
          placeholder="请补充举报原因（选填）"
          :maxlength="200"
          :show-word-limit="true"
        />
      </view>

      <!-- 提交按钮 -->
      <view class="report-dialog__footer">
        <wd-button
          type="error"
          block
          :disabled="!selectedType"
          :loading="submitting"
          @click="handleSubmit"
        >
          提交举报
        </wd-button>
      </view>

      <!-- 温馨提示 -->
      <view class="report-dialog__notice">
        <text>我们会认真处理每一条举报，恶意举报将受到处罚。</text>
      </view>
    </view>
  </wd-popup>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'

interface Props {
  /** 是否显示弹窗 */
  modelValue: boolean
  /** 举报目标ID */
  targetId: string
  /** 举报目标类型 */
  targetType: 'post' | 'comment' | 'user'
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  /** 举报提交成功 */
  submitted: [data: { targetId: string; type: string; targetType: string }]
}>()

// 举报类型选项
const reportTypes = [
  { value: 'spam', label: '垃圾信息', description: '广告、刷屏等垃圾内容' },
  { value: 'abuse', label: '辱骂攻击', description: '人身攻击、语言暴力' },
  { value: 'harm', label: '自伤/伤人', description: '涉及自残或暴力倾向' },
  { value: 'privacy', label: '隐私泄露', description: '暴露他人隐私信息' },
  { value: 'inappropriate', label: '不当内容', description: '色情、违法等不当内容' },
  { value: 'other', label: '其他', description: '不属于以上分类的问题' },
]

// 选中的举报类型
const selectedType = ref('')
// 补充描述
const detail = ref('')
// 是否正在提交
const submitting = ref(false)
// 弹窗可见性
const visible = ref(props.modelValue)

// 监听props变化
import { watch } from 'vue'
watch(() => props.modelValue, (val) => {
  visible.value = val
})

// 关闭弹窗
const handleClose = () => {
  visible.value = false
  emit('update:modelValue', false)
  // 重置状态
  selectedType.value = ''
  detail.value = ''
}

// 提交举报
const handleSubmit = async () => {
  if (!selectedType.value || submitting.value) return

  submitting.value = true
  try {
    await api.post('/api/v1/reports', {
      targetId: props.targetId,
      targetType: props.targetType,
      type: selectedType.value,
      detail: detail.value,
    })

    uni.showToast({ title: '举报成功，我们会尽快处理', icon: 'none' })
    emit('submitted', {
      targetId: props.targetId,
      type: selectedType.value,
      targetType: props.targetType,
    })
    handleClose()
  } catch (err) {
    uni.showToast({ title: '举报失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.report-dialog {
  padding: 32rpx;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32rpx;
  }

  &__title {
    font-size: 32rpx;
    font-weight: 600;
    color: var(--wd-color-text);
  }

  &__close {
    font-size: 40rpx;
    color: var(--wd-color-text-secondary);
  }

  &__types {
    margin-bottom: 32rpx;
  }

  &__type-item {
    display: flex;
    align-items: center;
    padding: 24rpx 16rpx;
    border-radius: 12rpx;
    margin-bottom: 8rpx;
    transition: background 0.2s;

    &:active {
      background: var(--wd-color-bg-container);
    }

    &--active {
      background: rgba(255, 154, 92, 0.08);
    }
  }

  &__type-info {
    margin-left: 16rpx;
  }

  &__type-label {
    display: block;
    font-size: 28rpx;
    color: var(--wd-color-text);
  }

  &__type-desc {
    display: block;
    font-size: 24rpx;
    color: var(--wd-color-text-secondary);
    margin-top: 4rpx;
  }

  &__detail {
    margin-bottom: 32rpx;
  }

  &__footer {
    margin-bottom: 24rpx;
  }

  &__notice {
    text-align: center;
    font-size: 22rpx;
    color: var(--wd-color-text-secondary);
  }
}
</style>
```

**使用示例**：

```vue
<!-- 在树洞详情页使用 -->
<ReportDialog
  v-model="showReportDialog"
  :target-id="postId"
  target-type="post"
  @submitted="handleReportSubmitted"
/>
```

---

### 8.9 P2-19：危机干预弹窗前端实现补充

**背景**：当AI对话检测到用户存在自伤/伤人风险时，系统需立即弹出危机干预弹窗，提供紧急求助资源。

**危机等级定义**：

| 等级 | 触发条件 | 弹窗行为 |
|------|---------|---------|
| yellow | AI检测到轻度负面情绪倾向 | 温和提示 + 心理热线推荐 |
| red | AI检测到明确的自伤/伤人意图 | 全屏弹窗 + 24h热线 + 一键拨打 |

**危机干预弹窗组件**：

```vue
<!-- src/components/common/CrisisIntervention.vue -->
<template>
  <!-- 黄色预警：温和提示 -->
  <wd-popup
    v-if="level === 'yellow'"
    v-model="visible"
    position="center"
    :close-on-click-overlay="true"
    custom-style="border-radius: 24rpx; width: 85%;"
  >
    <view class="crisis-dialog crisis-dialog--yellow">
      <view class="crisis-dialog__icon">
        <text class="crisis-dialog__emoji">&#x1F4AC;</text>
      </view>
      <text class="crisis-dialog__title">我们关心你</text>
      <text class="crisis-dialog__desc">
        检测到你可能正在经历一些困难，你不是一个人，我们在这里陪伴你。
      </text>

      <!-- 推荐资源 -->
      <view class="crisis-dialog__resources">
        <view
          v-for="resource in warmResources"
          :key="resource.name"
          class="crisis-dialog__resource-item"
          @tap="handleCallResource(resource)"
        >
          <wd-icon name="phone" color="#FF9A5C" />
          <view class="crisis-dialog__resource-info">
            <text class="crisis-dialog__resource-name">{{ resource.name }}</text>
            <text class="crisis-dialog__resource-phone">{{ resource.phone }}</text>
          </view>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="crisis-dialog__actions">
        <wd-button size="small" @click="handleDismiss">我知道了</wd-button>
        <wd-button size="small" type="error" @click="handleEmergencyCall">
          需要帮助
        </wd-button>
      </view>
    </view>
  </wd-popup>

  <!-- 红色预警：全屏紧急干预 -->
  <wd-popup
    v-if="level === 'red'"
    v-model="visible"
    position="center"
    :close-on-click-overlay="false"
    custom-style="border-radius: 0; width: 100%; height: 100%;"
  >
    <view class="crisis-dialog crisis-dialog--red">
      <view class="crisis-dialog__emergency">
        <view class="crisis-dialog__pulse">
          <view class="crisis-dialog__pulse-ring" />
          <text class="crisis-dialog__pulse-icon">&#x2764;&#xFE0F;</text>
        </view>

        <text class="crisis-dialog__emergency-title">你的安全最重要</text>
        <text class="crisis-dialog__emergency-desc">
          我们检测到你可能正在经历非常困难的时刻。请立即寻求专业帮助，你不是一个人。
        </text>

        <!-- 24小时紧急热线 -->
        <view class="crisis-dialog__hotlines">
          <view
            v-for="hotline in emergencyHotlines"
            :key="hotline.name"
            class="crisis-dialog__hotline-item"
            @tap="handleCallHotline(hotline)"
          >
            <view class="crisis-dialog__hotline-icon">
              <wd-icon name="phone" size="28px" color="#fff" />
            </view>
            <view class="crisis-dialog__hotline-info">
              <text class="crisis-dialog__hotline-name">{{ hotline.name }}</text>
              <text class="crisis-dialog__hotline-phone">{{ hotline.phone }}</text>
            </view>
            <wd-button size="small" type="error" plain>拨打</wd-button>
          </view>
        </view>

        <!-- 底部操作 -->
        <view class="crisis-dialog__emergency-actions">
          <wd-button type="error" block @click="handleEmergencyCall">
            拨打24小时心理援助热线
          </wd-button>
          <wd-button block plain custom-style="margin-top: 16rpx;" @click="handleDismiss">
            我已安全，关闭此页面
          </wd-button>
        </view>
      </view>
    </view>
  </wd-popup>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  /** 是否显示弹窗 */
  modelValue: boolean
  /** 危机等级 */
  level: 'yellow' | 'red'
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  /** 用户点击了拨打热线 */
  call: [phone: string]
  /** 用户关闭了弹窗 */
  dismiss: []
}>()

const visible = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
  visible.value = val
})

// 温和提示资源
const warmResources = [
  { name: '北京心理危机研究与干预中心', phone: '010-82951332' },
  { name: '希望24热线', phone: '400-161-9995' },
]

// 紧急热线
const emergencyHotlines = [
  { name: '24小时心理援助热线', phone: '400-161-9995' },
  { name: '北京心理危机干预中心', phone: '010-82951332' },
  { name: '全国心理援助热线', phone: '010-82951332' },
]

// 拨打热线
const handleCallHotline = (hotline: { name: string; phone: string }) => {
  uni.makePhoneCall({
    phoneNumber: hotline.phone,
    fail: () => {
      // 用户取消拨打
    },
  })
  emit('call', hotline.phone)
}

// 拨打紧急热线
const handleEmergencyCall = () => {
  uni.makePhoneCall({
    phoneNumber: '400-161-9995',
    fail: () => {},
  })
  emit('call', '400-161-9995')
}

// 拨打推荐资源
const handleCallResource = (resource: { name: string; phone: string }) => {
  uni.makePhoneCall({
    phoneNumber: resource.phone,
    fail: () => {},
  })
  emit('call', resource.phone)
}

// 关闭弹窗
const handleDismiss = () => {
  visible.value = false
  emit('update:modelValue', false)
  emit('dismiss')
}
</script>

<style lang="scss" scoped>
.crisis-dialog {
  padding: 48rpx 32rpx;

  &--yellow {
    text-align: center;
  }

  &--red {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background: linear-gradient(180deg, #1a0a0a 0%, #0f172a 100%);
  }

  &__icon {
    margin-bottom: 24rpx;
  }

  &__emoji {
    font-size: 64rpx;
  }

  &__title {
    display: block;
    font-size: 36rpx;
    font-weight: 600;
    color: var(--wd-color-text);
    margin-bottom: 16rpx;
  }

  &__desc {
    display: block;
    font-size: 28rpx;
    color: var(--wd-color-text-secondary);
    line-height: 1.6;
    margin-bottom: 32rpx;
  }

  &__resources {
    margin-bottom: 32rpx;
    text-align: left;
  }

  &__resource-item {
    display: flex;
    align-items: center;
    padding: 20rpx;
    background: rgba(255, 154, 92, 0.06);
    border-radius: 12rpx;
    margin-bottom: 12rpx;
  }

  &__resource-info {
    margin-left: 16rpx;
  }

  &__resource-name {
    display: block;
    font-size: 26rpx;
    color: var(--wd-color-text);
  }

  &__resource-phone {
    display: block;
    font-size: 24rpx;
    color: var(--wd-color-theme);
    margin-top: 4rpx;
  }

  &__actions {
    display: flex;
    justify-content: center;
    gap: 24rpx;
  }

  // 红色预警样式
  &__emergency {
    text-align: center;
    width: 100%;
  }

  &__pulse {
    position: relative;
    width: 160rpx;
    height: 160rpx;
    margin: 0 auto 32rpx;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__pulse-ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 4rpx solid #F87171;
    animation: pulse-ring 2s infinite;
  }

  &__pulse-icon {
    font-size: 64rpx;
  }

  &__emergency-title {
    display: block;
    font-size: 40rpx;
    font-weight: 700;
    color: #F87171;
    margin-bottom: 16rpx;
  }

  &__emergency-desc {
    display: block;
    font-size: 28rpx;
    color: #94a3b8;
    line-height: 1.6;
    margin-bottom: 48rpx;
  }

  &__hotlines {
    margin-bottom: 48rpx;
  }

  &__hotline-item {
    display: flex;
    align-items: center;
    padding: 24rpx;
    background: rgba(248, 113, 113, 0.1);
    border: 2rpx solid rgba(248, 113, 113, 0.2);
    border-radius: 16rpx;
    margin-bottom: 16rpx;
  }

  &__hotline-icon {
    width: 80rpx;
    height: 80rpx;
    border-radius: 50%;
    background: #F87171;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__hotline-info {
    flex: 1;
    margin-left: 20rpx;
  }

  &__hotline-name {
    display: block;
    font-size: 28rpx;
    color: #f1f5f9;
  }

  &__hotline-phone {
    display: block;
    font-size: 32rpx;
    font-weight: 600;
    color: #F87171;
    margin-top: 4rpx;
  }

  &__emergency-actions {
    padding: 0 32rpx;
  }
}

@keyframes pulse-ring {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.3);
    opacity: 0.3;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
```

**与后端协作**：
- AI对话服务检测到危机关键词后，在SSE流式响应中插入 `crisis_event` 事件
- 前端监听 `crisis_event`，根据等级自动弹出对应弹窗
- 红色等级弹窗不可通过点击遮罩关闭，必须通过按钮操作

**SSE 危机事件格式**：

```typescript
// AI对话SSE响应中可能包含的危机事件
// data: {"type": "crisis_event", "level": "yellow", "message": "..."}

// useStreaming.ts 中的危机事件监听
if (data.type === 'crisis_event') {
  // 触发危机干预弹窗
  crisisLevel.value = data.level
  showCrisisDialog.value = true
}
```

---

### 8.10 P2-20：全局错误处理和网络异常体验设计

**方案**：建立统一的全局错误处理机制，覆盖 HTTP 错误、业务错误、网络异常、运行时异常等场景，并设计友好的用户提示体验。

**错误分类与处理策略**：

| 错误类别 | 触发场景 | 处理策略 | 用户提示 |
|---------|---------|---------|---------|
| 网络断开 | 无网络连接 | 离线模式 + 本地缓存 | 全局网络断开提示条 |
| 网络超时 | 请求超过30s | 自动重试1次 | Toast提示"网络超时" |
| HTTP 4xx | 参数错误/权限不足 | 直接提示 | Toast提示具体错误 |
| HTTP 401 | Token失效 | 自动刷新Token/跳转登录 | 静默处理 |
| HTTP 5xx | 服务端错误 | 降级/重试 | Toast提示"服务开小差了" |
| 业务错误 | 业务逻辑异常 | 按错误码提示 | Toast提示对应信息 |
| SSE断连 | 流式输出中断 | 自动重连 | 气泡显示"重新生成"按钮 |
| 运行时异常 | JS代码报错 | 全局捕获 + 上报 | 静默处理 |

**全局错误处理实现**：

```typescript
// src/utils/errorHandler.ts

import { useSyncStore } from '@/stores/sync'

/** 错误码与中文提示映射 */
const ERROR_CODE_MAP: Record<string, string> = {
  // 通用错误
  VALIDATION_ERROR: '参数错误，请检查输入',
  USER_NOT_FOUND: '用户不存在',
  INVALID_PASSWORD: '密码错误',
  INVALID_VERIFY_CODE: '验证码错误或已过期',
  ACCOUNT_DISABLED: '账号已被禁用',

  // 内容相关
  SENSITIVE_CONTENT: '内容包含敏感信息，请修改后重试',
  RATE_LIMIT_EXCEEDED: '发布频率过高，请稍后再试',
  CONTENT_TOO_LONG: '内容过长，请精简后重试',
  UNSUPPORTED_IMAGE_FORMAT: '图片格式不支持',

  // AI服务
  AI_SERVICE_UNAVAILABLE: 'AI服务暂时不可用，请稍后再试',
  AI_QUOTA_EXCEEDED: 'AI对话次数已达上限',
  AI_RESPONSE_TIMEOUT: 'AI响应超时，请重试',

  // 社交相关
  POST_NOT_FOUND: '帖子不存在或已删除',
  COMMENT_NOT_FOUND: '评论不存在或已删除',
  NO_PERMISSION: '无权操作此内容',
  USER_BLOCKED: '已被对方拉黑',

  // 上传相关
  FILE_TOO_LARGE: '文件大小超过限制',
  UNSUPPORTED_FILE_FORMAT: '文件格式不支持',
  UPLOAD_FAILED: '上传失败，请重试',

  // 权限相关
  UNAUTHORIZED: '未登录，请先登录',
  TOKEN_EXPIRED: '登录已过期，请重新登录',
  FORBIDDEN: '无权访问此内容',
}

/**
 * 初始化全局错误处理
 * 在 main.ts 中调用
 */
export function setupGlobalErrorHandler() {
  // 1. Vue全局错误处理
  const app = getApp()
  if (app && app.config) {
    app.config.errorHandler = (err, instance, info) => {
      console.error('[Vue Error]', err, info)
      // 上报错误到监控服务
      reportError({
        type: 'vue_error',
        message: err instanceof Error ? err.message : String(err),
        stack: err instanceof Error ? err.stack : '',
        component: instance?.$options?.name || 'unknown',
        info,
      })
    }
  }

  // 2. 全局未捕获Promise异常
  // @ts-ignore
  if (typeof window !== 'undefined') {
    window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
      console.error('[Unhandled Rejection]', event.reason)
      reportError({
        type: 'unhandled_rejection',
        message: String(event.reason),
      })
      event.preventDefault()
    })
  }

  // 3. 监听网络状态
  uni.onNetworkStatusChange((result) => {
    const syncStore = useSyncStore()
    syncStore.isOnline = result.isConnected
    if (!result.isConnected) {
      showNetworkOfflineBar()
    } else {
      hideNetworkOfflineBar()
    }
  })
}

/**
 * 统一HTTP错误处理
 * 在 api/index.ts 的请求拦截器中调用
 */
export function handleHttpError(statusCode: number, errorData?: any): void {
  switch (statusCode) {
    case 400:
      showToast(errorData?.message || '请求参数错误')
      break
    case 401:
      handleUnauthorized()
      break
    case 403:
      showToast('无权访问此内容')
      break
    case 404:
      showToast('请求的资源不存在')
      break
    case 429:
      showToast('请求频率过高，请稍后再试')
      break
    case 500:
    case 502:
    case 503:
      showToast('服务开小差了，请稍后重试')
      break
    default:
      showToast(`请求失败（${statusCode}）`)
  }
}

/**
 * 统一业务错误处理
 */
export function handleBusinessError(code: string, message?: string): void {
  const displayMessage = ERROR_CODE_MAP[code] || message || '操作失败'
  showToast(displayMessage)

  // 特殊错误码的额外处理
  if (code === 'UNAUTHORIZED' || code === 'TOKEN_EXPIRED') {
    // 登录相关错误，跳转登录页
    handleUnauthorized()
  }
}

/**
 * 处理401未授权
 * 尝试刷新Token，失败则跳转登录页
 */
async function handleUnauthorized() {
  const { useUserStore } = await import('@/stores/user')
  const userStore = useUserStore()

  try {
    // 尝试刷新Token
    const refreshed = await userStore.refreshToken()
    if (!refreshed) {
      // 刷新失败，跳转登录页
      userStore.logout()
      uni.reLaunch({ url: '/pages/auth/login' })
    }
  } catch {
    userStore.logout()
    uni.reLaunch({ url: '/pages/auth/login' })
  }
}

/**
 * 网络异常重试封装
 * 对可重试的请求进行自动重试
 */
export async function requestWithRetry<T>(
  requestFn: () => Promise<T>,
  options: {
    maxRetries?: number
    retryDelay?: number
    shouldRetry?: (error: any) => boolean
  } = {}
): Promise<T> {
  const {
    maxRetries = 2,
    retryDelay = 1000,
    shouldRetry = (err) => {
      // 网络错误和5xx错误可重试
      return !err.statusCode || err.statusCode >= 500
    },
  } = options

  let lastError: any
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn()
    } catch (err) {
      lastError = err
      if (attempt < maxRetries && shouldRetry(err)) {
        // 等待后重试
        await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)))
      } else {
        throw err
      }
    }
  }
  throw lastError
}

// ===== UI反馈工具 =====

/** 显示Toast提示 */
function showToast(title: string, icon: 'none' | 'success' | 'error' = 'none') {
  uni.showToast({ title, icon, duration: 2500 })
}

/** 显示全局网络断开提示条 */
function showNetworkOfflineBar() {
  // 通过事件总线通知全局组件显示网络断开提示条
  uni.$emit('network:offline')
}

/** 隐藏全局网络断开提示条 */
function hideNetworkOfflineBar() {
  uni.$emit('network:online')
}

/** 上报错误到监控服务 */
function reportError(error: {
  type: string
  message: string
  stack?: string
  component?: string
  info?: string
}) {
  // 上报到错误监控服务（如Sentry、Fundebug等）
  console.warn('[Error Report]', error)
  // 后续集成错误监控SDK后，在此处上报
}

/**
 * SSE断连重连逻辑
 * 在 useStreaming.ts 中集成
 */
export function handleSSEDisconnect(
  reconnectFn: () => Promise<void>,
  options: {
    maxRetries?: number
    baseDelay?: number
  } = {}
) {
  const { maxRetries = 3, baseDelay = 1000 } = options
  let retryCount = 0

  const attemptReconnect = async () => {
    while (retryCount < maxRetries) {
      try {
        await reconnectFn()
        return // 重连成功
      } catch {
        retryCount++
        const delay = baseDelay * Math.pow(2, retryCount) // 指数退避
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
    // 重连失败，提示用户
    showToast('AI服务连接中断，请点击重试')
  }

  attemptReconnect()
}
```

**全局网络状态提示组件**：

```vue
<!-- src/components/common/NetworkStatusBar.vue -->
<template>
  <view
    v-if="!isOnline"
    class="network-status-bar network-status-bar--offline"
  >
    <wd-icon name="warning" size="14px" color="#FBBF24" />
    <text class="network-status-bar__text">网络已断开，部分功能不可用</text>
  </view>
  <view
    v-else-if="showRestored"
    class="network-status-bar network-status-bar--restored"
  >
    <wd-icon name="check-circle" size="14px" color="#8FCCA0" />
    <text class="network-status-bar__text">网络已恢复</text>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useSyncStore } from '@/stores/sync'

const syncStore = useSyncStore()
const isOnline = computed(() => syncStore.isOnline)
const showRestored = ref(false)
let restoredTimer: ReturnType<typeof setTimeout> | null = null

import { computed } from 'vue'

// 监听网络恢复事件
onMounted(() => {
  uni.$on('network:online', () => {
    showRestored.value = true
    if (restoredTimer) clearTimeout(restoredTimer)
    restoredTimer = setTimeout(() => {
      showRestored.value = false
    }, 3000)
  })
})

onUnmounted(() => {
  uni.$off('network:online')
  if (restoredTimer) clearTimeout(restoredTimer)
})
</script>

<style lang="scss" scoped>
.network-status-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx 24rpx;
  font-size: 24rpx;

  &--offline {
    background: rgba(251, 191, 36, 0.15);
    color: #FBBF24;
  }

  &--restored {
    background: rgba(143, 204, 160, 0.15);
    color: #8FCCA0;
    animation: slide-down 0.3s ease;
  }

  &__text {
    margin-left: 8rpx;
  }
}

@keyframes slide-down {
  from {
    transform: translateY(-100%);
  }
  to {
    transform: translateY(0);
  }
}
</style>
```

**API请求拦截器改造（集成全局错误处理）**：

```typescript
// src/api/index.ts（改造要点）

import { handleHttpError, handleBusinessError, requestWithRetry } from '@/utils/errorHandler'

const request = <T = any>(options: UniApp.RequestOptions): Promise<T> => {
  return new Promise((resolve, reject) => {
    const userStore = useUserStore()
    const settingsStore = useSettingsStore()

    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': userStore.token ? `Bearer ${userStore.token}` : '',
        'X-Device-Id': settingsStore.deviceId,
        ...options.header,
      },
      timeout: 30000,
      success: (res) => {
        if (res.statusCode === 200) {
          const data = res.data as ApiResponse<T>
          if (data.success) {
            resolve(data.data)
          } else {
            // 统一业务错误处理
            handleBusinessError(data.error?.code || 'UNKNOWN', data.error?.message)
            reject(new Error(data.error?.message || '请求失败'))
          }
        } else if (res.statusCode === 401) {
          // 统一401处理
          handleUnauthorized()
          reject(new Error('请先登录'))
        } else {
          // 统一HTTP错误处理
          handleHttpError(res.statusCode, res.data)
          reject(new Error(`请求失败: ${res.statusCode}`))
        }
      },
      fail: (err) => {
        // 网络层错误
        const syncStore = useSyncStore()
        syncStore.isOnline = false
        handleHttpError(0, { message: '网络请求失败' })
        reject(new Error(err.errMsg || '网络请求失败'))
      },
    })
  })
}
```

**在 main.ts 中初始化**：

```typescript
// src/main.ts
import { createSSRApp } from 'vue'
import App from './App.vue'
import { setupGlobalErrorHandler } from '@/utils/errorHandler'

export function createApp() {
  const app = createSSRApp(App)

  // 初始化全局错误处理
  setupGlobalErrorHandler()

  return { app }
}
```

---

### 8.11 P0-F2：情绪日记本地存储方案

**方案概述**：情绪日记采用本地优先存储策略，App端使用 SQLite 数据库实现结构化存储，H5/小程序端使用 Storage 降级方案，支持离线编辑和云端同步。

#### App端 SQLite 封装

```typescript
// src/utils/db.ts

/**
 * SQLite 数据库封装
 * 仅在 APP-PLUS 环境下可用
 */

// 数据库配置
const DB_NAME = 'ai_meet_local'
const DB_VERSION = 1

// 数据库连接实例
let dbInstance: PlusSQLite | null = null

/**
 * 表结构定义
 */
const TABLE_SCHEMAS = {
  // 情绪日记表
  diary: `
    CREATE TABLE IF NOT EXISTS diary (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      date TEXT NOT NULL,
      mood_score INTEGER,
      mood_label TEXT,
      content TEXT,
      tags TEXT,
      images TEXT,
      is_private INTEGER DEFAULT 0,
      is_anonymous INTEGER DEFAULT 0,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      sync_status INTEGER DEFAULT 0,
      server_id TEXT,
      is_deleted INTEGER DEFAULT 0
    )
  `,
  // 同步记录表
  sync_log: `
    CREATE TABLE IF NOT EXISTS sync_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      table_name TEXT NOT NULL,
      record_id TEXT NOT NULL,
      action TEXT NOT NULL,
      timestamp TEXT NOT NULL
    )
  `,
}

/**
 * 同步状态枚举
 */
export enum SyncStatus {
  PENDING = 0,    // 待同步
  SYNCING = 1,    // 同步中
  SYNCED = 2,     // 已同步
  CONFLICT = 3,   // 冲突
}

/**
 * 打开数据库连接
 */
export function openDatabase(): Promise<boolean> {
  return new Promise((resolve, reject) => {
    // #ifdef APP-PLUS
    if (dbInstance) {
      resolve(true)
      return
    }

    plus.sqlite.openDatabase({
      name: DB_NAME,
      path: `_doc/${DB_NAME}.db`,
      success: () => {
        console.log('[SQLite] 数据库打开成功')
        dbInstance = plus.sqlite
        // 执行建表
        initTables().then(() => resolve(true)).catch(reject)
      },
      fail: (e) => {
        console.error('[SQLite] 数据库打开失败', e)
        reject(e)
      },
    })
    // #endif

    // #ifndef APP-PLUS
    console.warn('[SQLite] 非 APP 环境，使用 Storage 降级方案')
    resolve(false)
    // #endif
  })
}

/**
 * 初始化数据库表
 */
async function initTables(): Promise<void> {
  for (const sql of Object.values(TABLE_SCHEMAS)) {
    await executeSql(sql)
  }
}

/**
 * 执行 SQL 语句（增删改）
 */
export function executeSql(sql: string, params?: any[]): Promise<void> {
  return new Promise((resolve, reject) => {
    // #ifdef APP-PLUS
    plus.sqlite.executeSql({
      name: DB_NAME,
      sql: params ? formatSql(sql, params) : sql,
      success: () => resolve(),
      fail: (e) => {
        console.error('[SQLite] SQL执行失败', sql, e)
        reject(e)
      },
    })
    // #endif

    // #ifndef APP-PLUS
    resolve()
    // #endif
  })
}

/**
 * 查询数据
 */
export function selectSql<T = any>(sql: string, params?: any[]): Promise<T[]> {
  return new Promise((resolve, reject) => {
    // #ifdef APP-PLUS
    plus.sqlite.selectSql({
      name: DB_NAME,
      sql: params ? formatSql(sql, params) : sql,
      success: (data) => resolve(data as T[]),
      fail: (e) => {
        console.error('[SQLite] 查询失败', sql, e)
        reject(e)
      },
    })
    // #endif

    // #ifndef APP-PLUS
    resolve([])
    // #endif
  })
}

/**
 * 格式化 SQL 参数（简单实现）
 */
function formatSql(sql: string, params: any[]): string {
  let result = sql
  params.forEach((param, index) => {
    const placeholder = `?${index + 1}`
    let value: string
    if (param === null || param === undefined) {
      value = 'NULL'
    } else if (typeof param === 'string') {
      value = `'${param.replace(/'/g, "''")}'`
    } else if (typeof param === 'number') {
      value = String(param)
    } else {
      value = `'${JSON.stringify(param).replace(/'/g, "''")}'`
    }
    result = result.replace(placeholder, value)
  })
  return result
}

/**
 * 关闭数据库连接
 */
export function closeDatabase(): Promise<void> {
  return new Promise((resolve, reject) => {
    // #ifdef APP-PLUS
    if (!dbInstance) {
      resolve()
      return
    }

    plus.sqlite.closeDatabase({
      name: DB_NAME,
      success: () => {
        dbInstance = null
        console.log('[SQLite] 数据库已关闭')
        resolve()
      },
      fail: (e) => {
        console.error('[SQLite] 关闭数据库失败', e)
        reject(e)
      },
    })
    // #endif

    // #ifndef APP-PLUS
    resolve()
    // #endif
  })
}

// ===== 日记相关 CRUD 操作 =====

export interface DiaryRecord {
  id: string
  user_id: string
  date: string
  mood_score: number | null
  mood_label: string | null
  content: string | null
  tags: string | null  // JSON 字符串
  images: string | null  // JSON 字符串
  is_private: number
  is_anonymous: number
  created_at: string
  updated_at: string
  sync_status: SyncStatus
  server_id: string | null
  is_deleted: number
}

/**
 * 插入日记
 */
export async function insertDiary(diary: Omit<DiaryRecord, 'sync_status'>): Promise<void> {
  const sql = `
    INSERT INTO diary (
      id, user_id, date, mood_score, mood_label, content, tags, images,
      is_private, is_anonymous, created_at, updated_at, sync_status, server_id, is_deleted
    ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15)
  `
  await executeSql(sql, [
    diary.id,
    diary.user_id,
    diary.date,
    diary.mood_score,
    diary.mood_label,
    diary.content,
    diary.tags,
    diary.images,
    diary.is_private,
    diary.is_anonymous,
    diary.created_at,
    diary.updated_at,
    SyncStatus.PENDING,
    diary.server_id,
    0,
  ])
}

/**
 * 更新日记
 */
export async function updateDiary(
  id: string,
  updates: Partial<DiaryRecord>
): Promise<void> {
  const fields: string[] = []
  const values: any[] = []

  Object.entries(updates).forEach(([key, value]) => {
    if (key !== 'id') {
      fields.push(`${key} = ?`)
      values.push(value)
    }
  })

  if (fields.length === 0) return

  fields.push('sync_status = ?', 'updated_at = ?')
  values.push(SyncStatus.PENDING, new Date().toISOString())
  values.push(id)

  await executeSql(`UPDATE diary SET ${fields.join(', ')} WHERE id = ?`, values)
}

/**
 * 删除日记（软删除）
 */
export async function deleteDiary(id: string): Promise<void> {
  await executeSql(
    'UPDATE diary SET is_deleted = 1, sync_status = ? WHERE id = ?',
    [SyncStatus.PENDING, id]
  )
}

/**
 * 查询日记列表
 */
export async function getDiaries(
  userId: string,
  options: {
    startDate?: string
    endDate?: string
    limit?: number
    offset?: number
  } = {}
): Promise<DiaryRecord[]> {
  let sql = 'SELECT * FROM diary WHERE user_id = ? AND is_deleted = 0'
  const params: any[] = [userId]

  if (options.startDate) {
    sql += ' AND date >= ?'
    params.push(options.startDate)
  }
  if (options.endDate) {
    sql += ' AND date <= ?'
    params.push(options.endDate)
  }

  sql += ' ORDER BY date DESC'

  if (options.limit) {
    sql += ' LIMIT ?'
    params.push(options.limit)
    if (options.offset) {
      sql += ' OFFSET ?'
      params.push(options.offset)
    }
  }

  return selectSql<DiaryRecord>(sql, params)
}

/**
 * 获取待同步的日记记录
 */
export async function getPendingDiaries(userId: string): Promise<DiaryRecord[]> {
  return selectSql<DiaryRecord>(
    'SELECT * FROM diary WHERE user_id = ? AND sync_status = ?',
    [userId, SyncStatus.PENDING]
  )
}

/**
 * 标记日记为已同步
 */
export async function markDiarySynced(id: string, serverId: string): Promise<void> {
  await executeSql(
    'UPDATE diary SET sync_status = ?, server_id = ? WHERE id = ?',
    [SyncStatus.SYNCED, serverId, id]
  )
}
```

#### H5/小程序降级方案

```typescript
// src/utils/storageFallback.ts

/**
 * H5/小程序端存储降级方案
 * 使用 uni.setStorageSync / uni.getStorageSync 实现
 */

import { SyncStatus, DiaryRecord } from './db'

// 存储键前缀
const STORAGE_PREFIX = 'ai_meet_'

// 键名定义
const KEYS = {
  DIARY_LIST: (userId: string) => `${STORAGE_PREFIX}diary_${userId}`,
  DIARY_ITEM: (userId: string, date: string) => `${STORAGE_PREFIX}diary_${userId}_${date}`,
  PENDING_QUEUE: (userId: string) => `${STORAGE_PREFIX}diary_pending_${userId}`,
  SYNC_META: (userId: string) => `${STORAGE_PREFIX}diary_sync_${userId}`,
}

// 存储容量限制（单位：字节，小程序约 10MB）
const STORAGE_QUOTA = 10 * 1024 * 1024

/**
 * 检测存储容量
 */
export function getStorageUsage(): { used: number; quota: number } {
  let used = 0

  try {
    // #ifdef MP-WEIXIN
    const info = uni.getStorageInfoSync()
    used = (info as any).currentSize * 1024 // 微信小程序返回 KB
    // #endif

    // #ifndef MP-WEIXIN
    // H5 环境估算
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key?.startsWith(STORAGE_PREFIX)) {
        const value = localStorage.getItem(key)
        if (value) {
          used += key.length + value.length
        }
      }
    }
    // #endif
  } catch (e) {
    console.warn('[Storage] 获取存储容量失败', e)
  }

  return { used, quota: STORAGE_QUOTA }
}

/**
 * 检查存储空间是否充足
 */
export function checkStorageAvailable(requiredSize: number): boolean {
  const { used, quota } = getStorageUsage()
  return used + requiredSize < quota
}

/**
 * 清理过期数据
 * 删除超过 30 天的已同步数据
 */
export function cleanupExpiredData(userId: string): void {
  const key = KEYS.DIARY_LIST(userId)
  const list = uni.getStorageSync(key) || []
  const thirtyDaysAgo = new Date()
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

  const filteredList = list.filter((item: any) => {
    if (item.sync_status === SyncStatus.SYNCED && new Date(item.date) < thirtyDaysAgo) {
      // 删除具体数据
      uni.removeStorageSync(KEYS.DIARY_ITEM(userId, item.date))
      return false
    }
    return true
  })

  uni.setStorageSync(key, filteredList)
}

/**
 * 存储日记（H5/小程序）
 */
export function saveDiaryToStorage(diary: DiaryRecord): boolean {
  const { used, quota } = getStorageUsage()
  const diarySize = JSON.stringify(diary).length

  // 检查容量
  if (used + diarySize > quota * 0.9) {
    // 容量紧张，触发清理
    cleanupExpiredData(diary.user_id)
    // 再次检查
    const newUsage = getStorageUsage()
    if (newUsage.used + diarySize > quota * 0.95) {
      console.error('[Storage] 存储空间不足')
      return false
    }
  }

  try {
    // 存储到列表索引
    const listKey = KEYS.DIARY_LIST(diary.user_id)
    let list = uni.getStorageSync(listKey) || []

    // 检查是否已存在
    const existingIndex = list.findIndex((item: any) => item.date === diary.date)
    if (existingIndex >= 0) {
      list[existingIndex] = { ...list[existingIndex], ...diary }
    } else {
      list.push({
        id: diary.id,
        date: diary.date,
        mood_score: diary.mood_score,
        sync_status: diary.sync_status,
      })
    }

    uni.setStorageSync(listKey, list)

    // 存储完整数据
    const itemKey = KEYS.DIARY_ITEM(diary.user_id, diary.date)
    uni.setStorageSync(itemKey, diary)

    // 添加到待同步队列
    if (diary.sync_status === SyncStatus.PENDING) {
      addToPendingQueue(diary.user_id, diary.id)
    }

    return true
  } catch (e) {
    console.error('[Storage] 保存日记失败', e)
    return false
  }
}

/**
 * 获取日记详情
 */
export function getDiaryFromStorage(userId: string, date: string): DiaryRecord | null {
  const key = KEYS.DIARY_ITEM(userId, date)
  return uni.getStorageSync(key) || null
}

/**
 * 获取日记列表
 */
export function getDiaryListFromStorage(
  userId: string,
  options: {
    startDate?: string
    endDate?: string
    limit?: number
  } = {}
): DiaryRecord[] {
  const listKey = KEYS.DIARY_LIST(userId)
  const list = uni.getStorageSync(listKey) || []

  let result = list.filter((item: any) => {
    if (options.startDate && item.date < options.startDate) return false
    if (options.endDate && item.date > options.endDate) return false
    return true
  })

  // 按日期倒序
  result.sort((a: any, b: any) => b.date.localeCompare(a.date))

  if (options.limit) {
    result = result.slice(0, options.limit)
  }

  // 获取完整数据
  return result.map((item: any) => {
    const fullData = getDiaryFromStorage(userId, item.date)
    return fullData || item
  })
}

/**
 * 删除日记
 */
export function deleteDiaryFromStorage(userId: string, date: string): void {
  // 更新列表
  const listKey = KEYS.DIARY_LIST(userId)
  let list = uni.getStorageSync(listKey) || []
  list = list.filter((item: any) => item.date !== date)
  uni.setStorageSync(listKey, list)

  // 删除详情
  const itemKey = KEYS.DIARY_ITEM(userId, date)
  uni.removeStorageSync(itemKey)

  // 从待同步队列移除
  removeFromPendingQueue(userId, date)
}

/**
 * 添加到待同步队列
 */
function addToPendingQueue(userId: string, diaryId: string): void {
  const key = KEYS.PENDING_QUEUE(userId)
  let queue = uni.getStorageSync(key) || []
  if (!queue.includes(diaryId)) {
    queue.push(diaryId)
    uni.setStorageSync(key, queue)
  }
}

/**
 * 从待同步队列移除
 */
function removeFromPendingQueue(userId: string, diaryId: string): void {
  const key = KEYS.PENDING_QUEUE(userId)
  let queue = uni.getStorageSync(key) || []
  queue = queue.filter((id: string) => id !== diaryId)
  uni.setStorageSync(key, queue)
}

/**
 * 获取待同步队列
 */
export function getPendingQueue(userId: string): string[] {
  const key = KEYS.PENDING_QUEUE(userId)
  return uni.getStorageSync(key) || []
}

/**
 * 清空待同步队列
 */
export function clearPendingQueue(userId: string): void {
  const key = KEYS.PENDING_QUEUE(userId)
  uni.removeStorageSync(key)
}

/**
 * 获取同步元数据
 */
export function getSyncMeta(userId: string): {
  lastSyncTime: string | null
  conflictCount: number
} {
  const key = KEYS.SYNC_META(userId)
  return uni.getStorageSync(key) || { lastSyncTime: null, conflictCount: 0 }
}

/**
 * 更新同步元数据
 */
export function updateSyncMeta(
  userId: string,
  meta: Partial<{ lastSyncTime: string; conflictCount: number }>
): void {
  const key = KEYS.SYNC_META(userId)
  const current = getSyncMeta(userId)
  uni.setStorageSync(key, { ...current, ...meta })
}
```

#### stores/diary.ts 完整实现

```typescript
// src/stores/diary.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  openDatabase,
  insertDiary,
  updateDiary as dbUpdateDiary,
  deleteDiary as dbDeleteDiary,
  getDiaries,
  getPendingDiaries,
  markDiarySynced,
  DiaryRecord,
  SyncStatus,
} from '@/utils/db'
import {
  saveDiaryToStorage,
  getDiaryFromStorage,
  getDiaryListFromStorage,
  deleteDiaryFromStorage,
  getPendingQueue,
  updateSyncMeta,
  getSyncMeta,
} from '@/utils/storageFallback'
import { diaryApi } from '@/api/diary'
import { useUserStore } from './user'

// 冲突记录类型
interface ConflictRecord {
  local: DiaryRecord
  server: any
  resolved: boolean
  resolution?: 'local' | 'server'
}

export const useDiaryStore = defineStore('diary', () => {
  // ===== 状态 =====

  // 是否使用 SQLite（App端）
  const useSQLite = ref(false)

  // 日记列表（当前用户）
  const diaries = ref<DiaryRecord[]>([])

  // 当前选中的日记
  const currentDiary = ref<DiaryRecord | null>(null)

  // 同步状态
  const isSyncing = ref(false)
  const lastSyncTime = ref<string | null>(null)
  const syncConflict = ref<ConflictRecord | null>(null)

  // 离线操作队列
  const offlineQueue = ref<string[]>([])

  // ===== 计算属性 =====

  // 按日期分组的日记
  const diariesByMonth = computed(() => {
    const grouped: Record<string, DiaryRecord[]> = {}
    diaries.value.forEach((diary) => {
      const month = diary.date.substring(0, 7) // YYYY-MM
      if (!grouped[month]) {
        grouped[month] = []
      }
      grouped[month].push(diary)
    })
    return grouped
  })

  // 待同步数量
  const pendingCount = computed(() => {
    return diaries.value.filter((d) => d.sync_status === SyncStatus.PENDING).length
  })

  // ===== 初始化 =====

  /**
   * 初始化存储
   */
  async function initStorage(): Promise<void> {
    try {
      // 尝试打开 SQLite
      const sqliteAvailable = await openDatabase()
      useSQLite.value = sqliteAvailable
      console.log(`[DiaryStore] 使用存储方式: ${sqliteAvailable ? 'SQLite' : 'Storage'}`)
    } catch (e) {
      console.warn('[DiaryStore] SQLite 不可用，使用 Storage 降级')
      useSQLite.value = false
    }
  }

  // ===== CRUD 操作 =====

  /**
   * 创建日记
   */
  async function createDiary(data: {
    date: string
    mood_score?: number
    mood_label?: string
    content?: string
    tags?: string[]
    images?: string[]
    is_private?: boolean
    is_anonymous?: boolean
  }): Promise<DiaryRecord> {
    const userStore = useUserStore()
    const userId = userStore.userInfo?.id
    if (!userId) throw new Error('用户未登录')

    const now = new Date().toISOString()
    const diary: DiaryRecord = {
      id: `local_${Date.now()}_${Math.random().toString(36).slice(2)}`,
      user_id: userId,
      date: data.date,
      mood_score: data.mood_score ?? null,
      mood_label: data.mood_label ?? null,
      content: data.content ?? null,
      tags: data.tags ? JSON.stringify(data.tags) : null,
      images: data.images ? JSON.stringify(data.images) : null,
      is_private: data.is_private ? 1 : 0,
      is_anonymous: data.is_anonymous ? 1 : 0,
      created_at: now,
      updated_at: now,
      sync_status: SyncStatus.PENDING,
      server_id: null,
      is_deleted: 0,
    }

    if (useSQLite.value) {
      await insertDiary(diary)
    } else {
      saveDiaryToStorage(diary)
    }

    // 更新本地状态
    diaries.value.unshift(diary)

    // 尝试同步
    syncToCloud()

    return diary
  }

  /**
   * 更新日记
   */
  async function updateDiary(
    id: string,
    data: Partial<Omit<DiaryRecord, 'id' | 'user_id' | 'created_at'>>
  ): Promise<void> {
    if (useSQLite.value) {
      await dbUpdateDiary(id, data)
    } else {
      const userStore = useUserStore()
      const userId = userStore.userInfo?.id
      if (userId) {
        const existing = diaries.value.find((d) => d.id === id)
        if (existing) {
          const updated = { ...existing, ...data, updated_at: new Date().toISOString() }
          saveDiaryToStorage(updated)
        }
      }
    }

    // 更新本地状态
    const index = diaries.value.findIndex((d) => d.id === id)
    if (index >= 0) {
      diaries.value[index] = {
        ...diaries.value[index],
        ...data,
        updated_at: new Date().toISOString(),
        sync_status: SyncStatus.PENDING,
      }
    }

    // 尝试同步
    syncToCloud()
  }

  /**
   * 删除日记
   */
  async function deleteDiary(id: string): Promise<void> {
    if (useSQLite.value) {
      await dbDeleteDiary(id)
    } else {
      const userStore = useUserStore()
      const userId = userStore.userInfo?.id
      const diary = diaries.value.find((d) => d.id === id)
      if (userId && diary) {
        deleteDiaryFromStorage(userId, diary.date)
      }
    }

    // 更新本地状态
    diaries.value = diaries.value.filter((d) => d.id !== id)

    // 尝试同步删除到云端
    syncToCloud()
  }

  /**
   * 加载日记列表
   */
  async function loadDiaries(options?: {
    startDate?: string
    endDate?: string
    limit?: number
  }): Promise<void> {
    const userStore = useUserStore()
    const userId = userStore.userInfo?.id
    if (!userId) return

    if (useSQLite.value) {
      diaries.value = await getDiaries(userId, options)
    } else {
      diaries.value = getDiaryListFromStorage(userId, options)
    }
  }

  // ===== 同步逻辑 =====

  /**
   * 同步到云端
   */
  async function syncToCloud(): Promise<void> {
    const userStore = useUserStore()
    const userId = userStore.userInfo?.id
    if (!userId || !userStore.token) {
      console.log('[DiaryStore] 未登录，跳过同步')
      return
    }

    if (isSyncing.value) {
      console.log('[DiaryStore] 正在同步中，跳过')
      return
    }

    isSyncing.value = true

    try {
      // 获取待同步数据
      let pendingDiaries: DiaryRecord[]
      if (useSQLite.value) {
        pendingDiaries = await getPendingDiaries(userId)
      } else {
        const pendingIds = getPendingQueue(userId)
        pendingDiaries = pendingIds
          .map((id) => diaries.value.find((d) => d.id === id))
          .filter(Boolean) as DiaryRecord[]
      }

      if (pendingDiaries.length === 0) {
        console.log('[DiaryStore] 无待同步数据')
        return
      }

      console.log(`[DiaryStore] 开始同步 ${pendingDiaries.length} 条日记`)

      for (const diary of pendingDiaries) {
        try {
          if (diary.is_deleted === 1) {
            // 删除操作
            if (diary.server_id) {
              await diaryApi.delete(diary.server_id)
            }
          } else {
            // 新增或更新
            const response = await diaryApi.upsert({
              local_id: diary.id,
              server_id: diary.server_id,
              date: diary.date,
              mood_score: diary.mood_score,
              mood_label: diary.mood_label,
              content: diary.content,
              tags: diary.tags ? JSON.parse(diary.tags) : [],
              images: diary.images ? JSON.parse(diary.images) : [],
              is_private: diary.is_private === 1,
              is_anonymous: diary.is_anonymous === 1,
              updated_at: diary.updated_at,
            })

            // 标记已同步
            if (useSQLite.value) {
              await markDiarySynced(diary.id, response.id)
            } else {
              diary.server_id = response.id
              diary.sync_status = SyncStatus.SYNCED
              saveDiaryToStorage(diary)
            }

            // 更新本地状态
            const index = diaries.value.findIndex((d) => d.id === diary.id)
            if (index >= 0) {
              diaries.value[index].sync_status = SyncStatus.SYNCED
              diaries.value[index].server_id = response.id
            }
          }
        } catch (e: any) {
          console.error('[DiaryStore] 同步失败', diary.id, e)

          // 检查是否冲突
          if (e.code === 'CONFLICT') {
            await handleSyncConflict(diary, e.serverData)
          }
        }
      }

      // 更新同步时间
      lastSyncTime.value = new Date().toISOString()
      if (!useSQLite.value) {
        updateSyncMeta(userId, { lastSyncTime: lastSyncTime.value })
      }
    } finally {
      isSyncing.value = false
    }
  }

  /**
   * 从云端拉取
   */
  async function pullFromCloud(): Promise<void> {
    const userStore = useUserStore()
    const userId = userStore.userInfo?.id
    if (!userId) return

    isSyncing.value = true

    try {
      const meta = getSyncMeta(userId)
      const response = await diaryApi.getList({
        since: meta.lastSyncTime,
      })

      for (const serverDiary of response.list) {
        // 检查本地是否存在
        const localDiary = diaries.value.find(
          (d) => d.server_id === serverDiary.id || d.date === serverDiary.date
        )

        if (localDiary) {
          // 存在，检查是否冲突
          if (localDiary.sync_status === SyncStatus.PENDING) {
            // 本地有修改，检查时间戳
            if (new Date(serverDiary.updated_at) > new Date(localDiary.updated_at)) {
              // 服务器更新，触发冲突
              await handleSyncConflict(localDiary, serverDiary)
            }
          } else {
            // 直接更新本地
            await mergeServerData(localDiary.id, serverDiary)
          }
        } else {
          // 不存在，创建本地记录
          const newDiary: DiaryRecord = {
            id: `server_${serverDiary.id}`,
            user_id: userId,
            date: serverDiary.date,
            mood_score: serverDiary.mood_score,
            mood_label: serverDiary.mood_label,
            content: serverDiary.content,
            tags: JSON.stringify(serverDiary.tags),
            images: JSON.stringify(serverDiary.images),
            is_private: serverDiary.is_private ? 1 : 0,
            is_anonymous: serverDiary.is_anonymous ? 1 : 0,
            created_at: serverDiary.created_at,
            updated_at: serverDiary.updated_at,
            sync_status: SyncStatus.SYNCED,
            server_id: serverDiary.id,
            is_deleted: 0,
          }

          if (useSQLite.value) {
            await insertDiary(newDiary)
          } else {
            saveDiaryToStorage(newDiary)
          }

          diaries.value.push(newDiary)
        }
      }

      lastSyncTime.value = new Date().toISOString()
      updateSyncMeta(userId, { lastSyncTime: lastSyncTime.value })
    } finally {
      isSyncing.value = false
    }
  }

  /**
   * 处理同步冲突
   */
  async function handleSyncConflict(local: DiaryRecord, server: any): Promise<void> {
    syncConflict.value = {
      local,
      server,
      resolved: false,
    }

    // 自动解决策略：Last-Write-Wins
    const localTime = new Date(local.updated_at).getTime()
    const serverTime = new Date(server.updated_at).getTime()

    // 如果时间差小于 1 分钟，自动选择最新
    if (Math.abs(localTime - serverTime) < 60 * 1000) {
      if (localTime >= serverTime) {
        await resolveConflict('local')
      } else {
        await resolveConflict('server')
      }
    }
    // 否则需要用户手动选择（通过 syncConflict 状态通知 UI）
  }

  /**
   * 解决冲突
   */
  async function resolveConflict(resolution: 'local' | 'server'): Promise<void> {
    if (!syncConflict.value) return

    const { local, server } = syncConflict.value

    if (resolution === 'server') {
      // 使用服务器版本
      await mergeServerData(local.id, server)
    } else {
      // 使用本地版本，强制推送
      const response = await diaryApi.upsert({
        local_id: local.id,
        server_id: local.server_id,
        date: local.date,
        mood_score: local.mood_score,
        mood_label: local.mood_label,
        content: local.content,
        tags: local.tags ? JSON.parse(local.tags) : [],
        images: local.images ? JSON.parse(local.images) : [],
        is_private: local.is_private === 1,
        is_anonymous: local.is_anonymous === 1,
        updated_at: local.updated_at,
        force: true, // 强制覆盖
      })

      if (useSQLite.value) {
        await markDiarySynced(local.id, response.id)
      } else {
        local.server_id = response.id
        local.sync_status = SyncStatus.SYNCED
        saveDiaryToStorage(local)
      }
    }

    syncConflict.value.resolved = true
    syncConflict.value.resolution = resolution

    // 清除冲突状态
    setTimeout(() => {
      syncConflict.value = null
    }, 3000)
  }

  /**
   * 合并服务器数据到本地
   */
  async function mergeServerData(localId: string, server: any): Promise<void> {
    const index = diaries.value.findIndex((d) => d.id === localId)
    if (index < 0) return

    const merged: DiaryRecord = {
      ...diaries.value[index],
      mood_score: server.mood_score,
      mood_label: server.mood_label,
      content: server.content,
      tags: JSON.stringify(server.tags),
      images: JSON.stringify(server.images),
      is_private: server.is_private ? 1 : 0,
      is_anonymous: server.is_anonymous ? 1 : 0,
      updated_at: server.updated_at,
      sync_status: SyncStatus.SYNCED,
      server_id: server.id,
    }

    if (useSQLite.value) {
      await dbUpdateDiary(localId, merged)
    } else {
      saveDiaryToStorage(merged)
    }

    diaries.value[index] = merged
  }

  return {
    // 状态
    useSQLite,
    diaries,
    currentDiary,
    isSyncing,
    lastSyncTime,
    syncConflict,
    offlineQueue,

    // 计算属性
    diariesByMonth,
    pendingCount,

    // 方法
    initStorage,
    createDiary,
    updateDiary,
    deleteDiary,
    loadDiaries,
    syncToCloud,
    pullFromCloud,
    resolveConflict,
  }
})
```

---

### 8.12 P0-F3：WebSocket 前端封装

**方案概述**：封装 uni.connectSocket API，实现连接管理、心跳保活、自动重连、离线缓存和消息分发功能。

#### utils/websocket.ts 完整实现

```typescript
// src/utils/websocket.ts

import { useUserStore } from '@/stores/user'

/**
 * WebSocket 配置
 */
interface WsConfig {
  baseUrl: string
  heartbeatInterval: number  // 心跳间隔（毫秒）
  reconnectBaseDelay: number // 重连基础延迟（毫秒）
  reconnectMaxDelay: number  // 重连最大延迟（毫秒）
  maxReconnectAttempts: number // 最大重连次数
  offlineQueueMaxSize: number // 离线队列最大长度
}

const defaultConfig: WsConfig = {
  baseUrl: '',
  heartbeatInterval: 30000,     // 30秒
  reconnectBaseDelay: 1000,     // 1秒
  reconnectMaxDelay: 30000,     // 30秒
  maxReconnectAttempts: 10,     // 最多重连10次
  offlineQueueMaxSize: 100,     // 最多缓存100条离线消息
}

/**
 * 消息类型定义
 */
export interface WsMessage {
  type: string
  payload?: any
  timestamp?: string
  messageId?: string
}

/**
 * 消息处理器类型
 */
type MessageHandler = (message: WsMessage) => void

/**
 * WebSocket 连接状态
 */
export enum WsConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
}

/**
 * WebSocket 管理器
 */
class WebSocketManager {
  private config: WsConfig
  private socketTask: UniApp.SocketTask | null = null
  private state: WsConnectionState = WsConnectionState.DISCONNECTED
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectAttempts = 0
  private offlineQueue: WsMessage[] = []
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map()
  private stateListeners: Set<(state: WsConnectionState) => void> = new Set()

  constructor(config: Partial<WsConfig> = {}) {
    this.config = { ...defaultConfig, ...config }
  }

  /**
   * 获取当前连接状态
   */
  getState(): WsConnectionState {
    return this.state
  }

  /**
   * 设置连接状态并通知监听器
   */
  private setState(newState: WsConnectionState): void {
    this.state = newState
    this.stateListeners.forEach((listener) => listener(newState))
  }

  /**
   * 监听连接状态变化
   */
  onStateChange(listener: (state: WsConnectionState) => void): () => void {
    this.stateListeners.add(listener)
    return () => {
      this.stateListeners.delete(listener)
    }
  }

  /**
   * 建立 WebSocket 连接
   * URL 格式: ws://host/ws/chat/{userId}?token={token}
   */
  async connect(): Promise<void> {
    if (this.state === WsConnectionState.CONNECTED ||
        this.state === WsConnectionState.CONNECTING) {
      console.log('[WebSocket] 已连接或正在连接中')
      return
    }

    const userStore = useUserStore()
    const userId = userStore.userInfo?.id
    const token = userStore.token

    if (!userId || !token) {
      console.error('[WebSocket] 用户未登录，无法建立连接')
      return
    }

    this.setState(WsConnectionState.CONNECTING)

    // 构建 WebSocket URL
    const wsUrl = `${this.config.baseUrl}/ws/chat/${userId}?token=${token}`

    return new Promise((resolve, reject) => {
      this.socketTask = uni.connectSocket({
        url: wsUrl,
        success: () => {
          console.log('[WebSocket] 连接请求已发送')
        },
        fail: (err) => {
          console.error('[WebSocket] 连接失败', err)
          this.setState(WsConnectionState.DISCONNECTED)
          reject(err)
        },
      })

      // 注册事件处理
      this.socketTask?.onOpen(() => {
        console.log('[WebSocket] 连接已建立')
        this.setState(WsConnectionState.CONNECTED)
        this.reconnectAttempts = 0
        this.startHeartbeat()
        // 发送离线队列中的消息
        this.flushOfflineQueue()
        resolve()
      })

      this.socketTask?.onMessage((res) => {
        this.handleMessage(res.data)
      })

      this.socketTask?.onError((err) => {
        console.error('[WebSocket] 连接错误', err)
        this.handleDisconnect()
      })

      this.socketTask?.onClose((res) => {
        console.log('[WebSocket] 连接关闭', res.code, res.reason)
        this.handleDisconnect()
      })
    })
  }

  /**
   * 主动断开连接
   */
  disconnect(): void {
    console.log('[WebSocket] 主动断开连接')
    this.stopHeartbeat()
    this.clearReconnectTimer()

    if (this.socketTask) {
      this.socketTask.close({
        code: 1000,
        reason: 'Client disconnect',
      })
      this.socketTask = null
    }

    this.setState(WsConnectionState.DISCONNECTED)
  }

  /**
   * 发送消息
   */
  send(message: WsMessage): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.state !== WsConnectionState.CONNECTED || !this.socketTask) {
        // 连接不可用，加入离线队列
        console.log('[WebSocket] 连接不可用，消息加入离线队列')
        this.addToOfflineQueue(message)
        resolve()
        return
      }

      const data = JSON.stringify(message)
      this.socketTask.send({
        data,
        success: () => {
          console.log('[WebSocket] 消息发送成功', message.type)
          resolve()
        },
        fail: (err) => {
          console.error('[WebSocket] 消息发送失败', err)
          // 发送失败，加入离线队列
          this.addToOfflineQueue(message)
          reject(err)
        },
      })
    })
  }

  /**
   * 注册消息处理器
   */
  onMessage(type: string, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set())
    }
    this.messageHandlers.get(type)!.add(handler)

    // 返回取消注册函数
    return () => {
      this.messageHandlers.get(type)?.delete(handler)
    }
  }

  /**
   * 处理收到的消息
   */
  private handleMessage(data: string | ArrayBuffer): void {
    try {
      const message: WsMessage = JSON.parse(data as string)

      // 处理心跳响应
      if (message.type === 'pong') {
        console.log('[WebSocket] 收到心跳响应')
        return
      }

      console.log('[WebSocket] 收到消息', message.type, message)

      // 分发到对应处理器
      const handlers = this.messageHandlers.get(message.type)
      if (handlers && handlers.size > 0) {
        handlers.forEach((handler) => {
          try {
            handler(message)
          } catch (e) {
            console.error('[WebSocket] 消息处理器执行错误', e)
          }
        })
      }

      // 通用处理器
      const globalHandlers = this.messageHandlers.get('*')
      if (globalHandlers) {
        globalHandlers.forEach((handler) => handler(message))
      }
    } catch (e) {
      console.error('[WebSocket] 消息解析失败', e, data)
    }
  }

  /**
   * 处理断连
   */
  private handleDisconnect(): void {
    this.stopHeartbeat()
    this.socketTask = null

    if (this.state === WsConnectionState.DISCONNECTED) {
      return
    }

    this.setState(WsConnectionState.RECONNECTING)
    this.scheduleReconnect()
  }

  /**
   * 启动心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()

    this.heartbeatTimer = setInterval(() => {
      if (this.state === WsConnectionState.CONNECTED) {
        this.send({ type: 'ping' })
      }
    }, this.config.heartbeatInterval)
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 安排重连（指数退避 + 随机抖动）
   */
  private scheduleReconnect(): void {
    this.clearReconnectTimer()

    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('[WebSocket] 达到最大重连次数，停止重连')
      this.setState(WsConnectionState.DISCONNECTED)
      return
    }

    // 指数退避：1s → 2s → 4s → 8s → 16s → 30s
    let delay = this.config.reconnectBaseDelay * Math.pow(2, this.reconnectAttempts)
    delay = Math.min(delay, this.config.reconnectMaxDelay)

    // 添加随机抖动（0-25%）
    const jitter = delay * (Math.random() * 0.25)
    delay += jitter

    console.log(`[WebSocket] ${delay}ms 后进行第 ${this.reconnectAttempts + 1} 次重连`)

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++
      this.connect().catch(() => {
        // 重连失败会再次触发 scheduleReconnect
      })
    }, delay)
  }

  /**
   * 清除重连定时器
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  /**
   * 添加到离线队列
   */
  private addToOfflineQueue(message: WsMessage): void {
    if (this.offlineQueue.length >= this.config.offlineQueueMaxSize) {
      // 队列满，移除最旧的消息
      this.offlineQueue.shift()
      console.warn('[WebSocket] 离线队列已满，移除最旧消息')
    }
    this.offlineQueue.push(message)
    console.log(`[WebSocket] 消息已加入离线队列，当前队列长度: ${this.offlineQueue.length}`)
  }

  /**
   * 发送离线队列中的消息
   */
  private flushOfflineQueue(): void {
    if (this.offlineQueue.length === 0) return

    console.log(`[WebSocket] 开始发送离线队列中的 ${this.offlineQueue.length} 条消息`)

    const queue = [...this.offlineQueue]
    this.offlineQueue = []

    queue.forEach((message) => {
      this.send(message)
    })
  }

  /**
   * 获取离线队列长度
   */
  getOfflineQueueLength(): number {
    return this.offlineQueue.length
  }

  /**
   * 清空离线队列
   */
  clearOfflineQueue(): void {
    this.offlineQueue = []
  }
}

// 全局单例
let wsInstance: WebSocketManager | null = null

/**
 * 获取 WebSocket 管理器实例
 */
export function getWebSocketManager(config?: Partial<WsConfig>): WebSocketManager {
  if (!wsInstance) {
    // 从环境变量获取基础 URL
    const baseUrl = config?.baseUrl || getWsBaseUrl()
    wsInstance = new WebSocketManager({ ...config, baseUrl })
  }
  return wsInstance
}

/**
 * 获取 WebSocket 基础 URL
 */
function getWsBaseUrl(): string {
  // #ifdef APP-PLUS
  return 'ws://your-api-host.com'
  // #endif

  // #ifdef H5
  // H5 环境根据当前域名动态构建
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}`
  // #endif

  // #ifdef MP-WEIXIN
  return 'wss://your-api-host.com'
  // #endif

  // 默认
  return 'ws://localhost:8080'
}

export { WebSocketManager }
```

#### stores/message.ts 完整实现

```typescript
// src/stores/message.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getWebSocketManager,
  WsMessage,
  WsConnectionState,
} from '@/utils/websocket'
import { useUserStore } from './user'

/**
 * 会话类型
 */
export interface Conversation {
  id: string
  type: 'private' | 'group'
  name: string
  avatar: string
  lastMessage?: Message
  unreadCount: number
  updatedAt: string
}

/**
 * 消息类型
 */
export interface Message {
  id: string
  conversationId: string
  senderId: string
  senderName: string
  senderAvatar: string
  content: string
  type: 'text' | 'image' | 'voice' | 'ai_card'
  status: 'sending' | 'sent' | 'delivered' | 'read' | 'failed'
  createdAt: string
  extra?: Record<string, any>
}

/**
 * 离线消息项
 */
interface OfflineQueueItem {
  message: Message
  resolve: () => void
  reject: (err: Error) => void
}

export const useMessageStore = defineStore('message', () => {
  // ===== 状态 =====

  // 会话列表
  const conversations = ref<Conversation[]>([])

  // 消息列表（按会话ID分组）
  const messages = ref<Map<string, Message[]>>(new Map())

  // 未读消息总数
  const unreadCount = computed(() => {
    return conversations.value.reduce((sum, conv) => sum + conv.unreadCount, 0)
  })

  // WebSocket 连接状态
  const connectionState = ref<WsConnectionState>(WsConnectionState.DISCONNECTED)

  // 离线消息队列（发送失败的消息）
  const offlineQueue = ref<OfflineQueueItem[]>([])

  // WebSocket 管理器
  let wsManager: ReturnType<typeof getWebSocketManager> | null = null

  // ===== 初始化 =====

  /**
   * 初始化消息服务
   */
  async function init(): Promise<void> {
    const userStore = useUserStore()
    if (!userStore.userInfo?.id) {
      console.log('[MessageStore] 用户未登录，跳过初始化')
      return
    }

    // 获取 WebSocket 管理器
    wsManager = getWebSocketManager()

    // 监听连接状态
    wsManager.onStateChange((state) => {
      connectionState.value = state
    })

    // 注册消息处理器
    registerMessageHandlers()

    // 建立连接
    await wsManager.connect()
  }

  /**
   * 注册消息处理器
   */
  function registerMessageHandlers(): void {
    if (!wsManager) return

    // 私聊消息
    wsManager.onMessage('private_message', (msg) => {
      const message = msg.payload as Message
      receiveMessage(message)
    })

    // 群聊消息
    wsManager.onMessage('group_message', (msg) => {
      const message = msg.payload as Message
      receiveMessage(message)
    })

    // AI 消息
    wsManager.onMessage('ai_message', (msg) => {
      const message = msg.payload as Message
      receiveMessage(message)
    })

    // 消息已读回执
    wsManager.onMessage('message_read', (msg) => {
      const { conversationId, messageIds } = msg.payload
      markMessagesAsRead(conversationId, messageIds)
    })

    // 消息发送确认
    wsManager.onMessage('message_ack', (msg) => {
      const { tempId, messageId, conversationId } = msg.payload
      updateMessageStatus(conversationId, tempId, 'sent', messageId)
    })

    // 消息投递确认
    wsManager.onMessage('message_delivered', (msg) => {
      const { conversationId, messageId } = msg.payload
      updateMessageStatus(conversationId, messageId, 'delivered')
    })

    // 好友请求通知
    wsManager.onMessage('friend_request', (msg) => {
      uni.$emit('friend_request', msg.payload)
    })

    // 系统通知
    wsManager.onMessage('system_notice', (msg) => {
      uni.$emit('system_notice', msg.payload)
    })
  }

  // ===== 消息操作 =====

  /**
   * 发送消息
   */
  async function sendMessage(params: {
    conversationId: string
    content: string
    type?: 'text' | 'image' | 'voice'
    extra?: Record<string, any>
  }): Promise<Message> {
    const userStore = useUserStore()
    const currentUser = userStore.userInfo
    if (!currentUser) throw new Error('用户未登录')

    // 生成临时消息ID
    const tempId = `temp_${Date.now()}_${Math.random().toString(36).slice(2)}`

    // 创建消息对象
    const message: Message = {
      id: tempId,
      conversationId: params.conversationId,
      senderId: currentUser.id,
      senderName: currentUser.nickname,
      senderAvatar: currentUser.avatar,
      content: params.content,
      type: params.type || 'text',
      status: 'sending',
      createdAt: new Date().toISOString(),
      extra: params.extra,
    }

    // 添加到本地消息列表
    addMessageToLocal(params.conversationId, message)

    // 发送消息
    try {
      await wsManager?.send({
        type: 'send_message',
        payload: {
          tempId,
          conversationId: params.conversationId,
          content: params.content,
          type: params.type || 'text',
          extra: params.extra,
        },
      })
    } catch (e) {
      // 发送失败，更新状态
      updateMessageStatus(params.conversationId, tempId, 'failed')
      throw e
    }

    return message
  }

  /**
   * 接收消息
   */
  function receiveMessage(message: Message): void {
    // 添加到消息列表
    addMessageToLocal(message.conversationId, message)

    // 更新会话
    updateConversation(message.conversationId, message)

    // 增加未读数（非当前页面时）
    const currentRoute = getCurrentPageRoute()
    const isInChat = currentRoute === `/pages/chat/index` &&
      getCurrentConversationId() === message.conversationId

    if (!isInChat) {
      incrementUnreadCount(message.conversationId)
    }

    // 触发消息事件
    uni.$emit('new_message', message)
  }

  /**
   * 添加消息到本地列表
   */
  function addMessageToLocal(conversationId: string, message: Message): void {
    if (!messages.value.has(conversationId)) {
      messages.value.set(conversationId, [])
    }
    const list = messages.value.get(conversationId)!
    // 检查是否已存在（避免重复）
    if (!list.find((m) => m.id === message.id)) {
      list.push(message)
      // 触发响应式更新
      messages.value = new Map(messages.value)
    }
  }

  /**
   * 更新消息状态
   */
  function updateMessageStatus(
    conversationId: string,
    messageId: string,
    status: Message['status'],
    newId?: string
  ): void {
    const list = messages.value.get(conversationId)
    if (!list) return

    const index = list.findIndex((m) => m.id === messageId)
    if (index >= 0) {
      list[index].status = status
      if (newId) {
        list[index].id = newId
      }
      messages.value = new Map(messages.value)
    }
  }

  /**
   * 标记消息已读
   */
  async function markAsRead(conversationId: string): Promise<void> {
    const list = messages.value.get(conversationId)
    if (!list) return

    // 获取未读消息ID
    const unreadIds = list
      .filter((m) => m.status !== 'read' && m.senderId !== useUserStore().userInfo?.id)
      .map((m) => m.id)

    if (unreadIds.length === 0) return

    // 更新本地状态
    list.forEach((m) => {
      if (unreadIds.includes(m.id)) {
        m.status = 'read'
      }
    })
    messages.value = new Map(messages.value)

    // 清除会话未读数
    const conv = conversations.value.find((c) => c.id === conversationId)
    if (conv) {
      conv.unreadCount = 0
    }

    // 发送已读回执
    await wsManager?.send({
      type: 'mark_read',
      payload: {
        conversationId,
        messageIds: unreadIds,
      },
    })
  }

  /**
   * 批量标记消息已读
   */
  function markMessagesAsRead(conversationId: string, messageIds: string[]): void {
    const list = messages.value.get(conversationId)
    if (!list) return

    list.forEach((m) => {
      if (messageIds.includes(m.id)) {
        m.status = 'read'
      }
    })
    messages.value = new Map(messages.value)
  }

  // ===== 会话操作 =====

  /**
   * 更新会话
   */
  function updateConversation(conversationId: string, lastMessage: Message): void {
    let conv = conversations.value.find((c) => c.id === conversationId)

    if (!conv) {
      // 创建新会话
      conv = {
        id: conversationId,
        type: 'private', // 默认私聊
        name: lastMessage.senderName,
        avatar: lastMessage.senderAvatar,
        lastMessage,
        unreadCount: 0,
        updatedAt: lastMessage.createdAt,
      }
      conversations.value.unshift(conv)
    } else {
      // 更新已有会话
      conv.lastMessage = lastMessage
      conv.updatedAt = lastMessage.createdAt
      // 移到列表顶部
      const index = conversations.value.indexOf(conv)
      if (index > 0) {
        conversations.value.splice(index, 1)
        conversations.value.unshift(conv)
      }
    }
  }

  /**
   * 增加未读数
   */
  function incrementUnreadCount(conversationId: string): void {
    const conv = conversations.value.find((c) => c.id === conversationId)
    if (conv) {
      conv.unreadCount++
    }
  }

  /**
   * 加载会话列表
   */
  async function loadConversations(): Promise<void> {
    // 从本地缓存或API加载
    // TODO: 实现
  }

  /**
   * 加载历史消息
   */
  async function loadMessages(
    conversationId: string,
    options?: { beforeId?: string; limit?: number }
  ): Promise<Message[]> {
    // 从本地缓存或API加载
    // TODO: 实现
    return []
  }

  // ===== 辅助方法 =====

  /**
   * 获取当前页面路由
   */
  function getCurrentPageRoute(): string {
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    return currentPage ? `/${currentPage.route}` : ''
  }

  /**
   * 获取当前聊天会话ID
   */
  function getCurrentConversationId(): string | null {
    // 从页面参数中获取
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    if (currentPage) {
      const options = (currentPage as any).options || {}
      return options.conversationId || null
    }
    return null
  }

  /**
   * 销毁
   */
  function destroy(): void {
    if (wsManager) {
      wsManager.disconnect()
      wsManager = null
    }
    conversations.value = []
    messages.value = new Map()
  }

  return {
    // 状态
    conversations,
    messages,
    unreadCount,
    connectionState,
    offlineQueue,

    // 方法
    init,
    sendMessage,
    receiveMessage,
    markAsRead,
    loadConversations,
    loadMessages,
    destroy,
  }
})
```

---

### 8.13 P0-F4：推送前端集成方案

**方案概述**：集成极光推送 SDK，实现消息推送、别名管理、点击跳转、角标管理等功能。

#### composables/useNotification.ts 完整实现

```typescript
// src/composables/useNotification.ts

import { ref } from 'vue'
import { useUserStore } from '@/stores/user'

/**
 * 推送通知类型
 */
export type NotificationType =
  | 'ai_care'       // AI关怀提醒
  | 'mood_report'   // 情绪报告
  | 'friend_request'// 好友请求
  | 'comment'       // 评论通知
  | 'like'          // 点赞通知
  | 'system'        // 系统通知

/**
 * 推送消息载荷
 */
export interface NotificationPayload {
  type: NotificationType
  title: string
  content: string
  extra?: Record<string, any>
  postId?: string   // 帖子ID（评论/点赞）
  userId?: string   // 用户ID
}

/**
 * 推送类型到路由映射
 */
const ROUTE_MAP: Record<NotificationType, string | ((payload: NotificationPayload) => string)> = {
  ai_care: '/pages/chat/index',
  mood_report: '/pages/diary/report',
  friend_request: '/pages/message/friend-requests',
  comment: (payload) => `/pages/square/detail?id=${payload.postId}`,
  like: (payload) => `/pages/square/detail?id=${payload.postId}`,
  system: '/pages/profile/settings',
}

/**
 * 推送通知组合式函数
 */
export function useNotification() {
  const isInitialized = ref(false)
  const registrationId = ref<string | null>(null)
  const hasPermission = ref(false)

  /**
   * 初始化极光推送 SDK
   */
  async function initJPush(): Promise<void> {
    // #ifdef APP-PLUS
    if (isInitialized.value) {
      console.log('[JPush] 已初始化')
      return
    }

    return new Promise((resolve, reject) => {
      // 获取 JPush 插件
      const jpush = plus.push

      if (!jpush) {
        console.error('[JPush] 极光推送插件未安装')
        reject(new Error('极光推送插件未安装'))
        return
      }

      // 监听推送消息
      jpush.addEventListener('receive', (msg: any) => {
        console.log('[JPush] 收到推送消息', msg)
        handlePushMessage(msg)
      })

      // 监听通知点击
      jpush.addEventListener('click', (msg: any) => {
        console.log('[JPush] 用户点击通知', msg)
        handleNotificationClick(msg)
      })

      // 获取注册ID
      jpush.getRegistrationID((rid: string) => {
        registrationId.value = rid
        console.log('[JPush] 注册ID:', rid)
      })

      isInitialized.value = true
      console.log('[JPush] 初始化成功')
      resolve()
    })
    // #endif

    // #ifndef APP-PLUS
    console.log('[JPush] 非 APP 环境，跳过初始化')
    isInitialized.value = true
    resolve()
    // #endif
  }

  /**
   * 设置用户别名
   * 用户登录后调用
   */
  async function setAlias(userId: string): Promise<void> {
    // #ifdef APP-PLUS
    return new Promise((resolve, reject) => {
      const jpush = plus.push

      if (!jpush) {
        reject(new Error('极光推送插件未安装'))
        return
      }

      jpush.setAlias({ alias: userId }, () => {
        console.log('[JPush] 设置别名成功:', userId)
        resolve()
      }, (err: any) => {
        console.error('[JPush] 设置别名失败', err)
        reject(err)
      })
    })
    // #endif

    // #ifndef APP-PLUS
    console.log('[JPush] 非 APP 环境，跳过设置别名')
    resolve()
    // #endif
  }

  /**
   * 删除用户别名
   * 用户退出登录后调用
   */
  async function deleteAlias(): Promise<void> {
    // #ifdef APP-PLUS
    return new Promise((resolve, reject) => {
      const jpush = plus.push

      if (!jpush) {
        reject(new Error('极光推送插件未安装'))
        return
      }

      jpush.deleteAlias({}, () => {
        console.log('[JPush] 删除别名成功')
        resolve()
      }, (err: any) => {
        console.error('[JPush] 删除别名失败', err)
        reject(err)
      })
    })
    // #endif

    // #ifndef APP-PLUS
    resolve()
    // #endif
  }

  /**
   * 处理推送消息
   */
  function handlePushMessage(msg: any): void {
    try {
      // 解析消息内容
      let payload: NotificationPayload

      if (typeof msg.content === 'string') {
        payload = JSON.parse(msg.content)
      } else {
        payload = msg.content
      }

      console.log('[JPush] 解析后的推送载荷:', payload)

      // 更新未读数或角标
      incrementBadge()

      // 触发事件供其他组件监听
      uni.$emit('notification:received', payload)
    } catch (e) {
      console.error('[JPush] 解析推送消息失败', e)
    }
  }

  /**
   * 处理通知点击
   */
  function handleNotificationClick(msg: any): void {
    try {
      let payload: NotificationPayload

      if (typeof msg.content === 'string') {
        payload = JSON.parse(msg.content)
      } else {
        payload = msg.content
      }

      console.log('[JPush] 点击通知，准备跳转:', payload)

      // 清除角标
      setBadge(0)

      // 获取目标路由
      const routeResolver = ROUTE_MAP[payload.type]
      if (!routeResolver) {
        console.warn('[JPush] 未知的通知类型:', payload.type)
        return
      }

      const targetRoute = typeof routeResolver === 'function'
        ? routeResolver(payload)
        : routeResolver

      // 执行跳转
      uni.navigateTo({
        url: targetRoute,
        fail: (err) => {
          console.error('[JPush] 路由跳转失败', err)
          // 尝试 reLaunch
          uni.reLaunch({ url: '/pages/index/index' })
        },
      })
    } catch (e) {
      console.error('[JPush] 处理通知点击失败', e)
    }
  }

  /**
   * 请求通知权限
   * 首次启动时调用
   */
  async function requestPermission(): Promise<boolean> {
    // #ifdef APP-PLUS
    return new Promise((resolve) => {
      const jpush = plus.push

      if (!jpush) {
        resolve(false)
        return
      }

      // iOS 需要显式请求权限
      if (uni.getSystemInfoSync().platform === 'ios') {
        jpush.requestPermission((granted: boolean) => {
          hasPermission.value = granted
          console.log('[JPush] 通知权限:', granted ? '已授权' : '未授权')
          resolve(granted)
        })
      } else {
        // Android 默认有权限
        hasPermission.value = true
        resolve(true)
      }
    })
    // #endif

    // #ifndef APP-PLUS
    hasPermission.value = false
    resolve(false)
    // #endif
  }

  /**
   * 获取角标数
   */
  function getBadge(): number {
    // #ifdef APP-PLUS
    return plus.runtime.arguments?.badge || 0
    // #endif

    // #ifndef APP-PLUS
    return 0
    // #endif
  }

  /**
   * 设置角标数
   */
  function setBadge(count: number): void {
    // #ifdef APP-PLUS
    const jpush = plus.push

    if (jpush) {
      jpush.setBadge(count)
      console.log('[JPush] 设置角标数:', count)
    }
    // #endif
  }

  /**
   * 增加角标数
   */
  function incrementBadge(): void {
    const current = getBadge()
    setBadge(current + 1)
  }

  /**
   * 设置标签
   * 用于分组推送
   */
  async function setTags(tags: string[]): Promise<void> {
    // #ifdef APP-PLUS
    return new Promise((resolve, reject) => {
      const jpush = plus.push

      if (!jpush) {
        reject(new Error('极光推送插件未安装'))
        return
      }

      jpush.setTags({ tags }, () => {
        console.log('[JPush] 设置标签成功:', tags)
        resolve()
      }, (err: any) => {
        console.error('[JPush] 设置标签失败', err)
        reject(err)
      })
    })
    // #endif

    // #ifndef APP-PLUS
    resolve()
    // #endif
  }

  return {
    isInitialized,
    registrationId,
    hasPermission,

    initJPush,
    setAlias,
    deleteAlias,
    requestPermission,
    getBadge,
    setBadge,
    incrementBadge,
    setTags,
  }
}

/**
 * 全局推送初始化
 * 在 App.vue 中调用
 */
export async function initPushNotification(): Promise<void> {
  const { initJPush, requestPermission, setAlias } = useNotification()
  const userStore = useUserStore()

  // 初始化 JPush
  await initJPush()

  // 请求权限
  await requestPermission()

  // 如果已登录，设置别名
  if (userStore.userInfo?.id) {
    await setAlias(userStore.userInfo.id)
  }
}

/**
 * 登出时清理推送
 */
export async function cleanupPushNotification(): Promise<void> {
  const { deleteAlias, setBadge } = useNotification()

  // 删除别名
  await deleteAlias()

  // 清除角标
  setBadge(0)
}
```

#### App.vue 中的初始化逻辑

```vue
<!-- src/App.vue -->
<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { useDiaryStore } from '@/stores/diary'
import { useMessageStore } from '@/stores/message'
import { initPushNotification, cleanupPushNotification } from '@/composables/useNotification'
import { setupGlobalErrorHandler } from '@/utils/errorHandler'

onLaunch(async () => {
  console.log('[App] 应用启动')

  // 1. 初始化全局错误处理
  setupGlobalErrorHandler()

  // 2. 初始化用户状态
  const userStore = useUserStore()
  await userStore.initFromStorage()

  // 3. 初始化日记存储
  const diaryStore = useDiaryStore()
  await diaryStore.initStorage()

  // 4. 初始化消息服务（WebSocket）
  if (userStore.isLoggedIn) {
    const messageStore = useMessageStore()
    await messageStore.init()
  }

  // 5. 初始化推送通知
  await initPushNotification()
})

onShow(() => {
  console.log('[App] 应用显示')

  // 检查登录状态，更新推送别名
  const userStore = useUserStore()
  if (userStore.isLoggedIn) {
    const { setAlias } = useNotification()
    setAlias(userStore.userInfo!.id)
  }

  // 触发同步
  const diaryStore = useDiaryStore()
  diaryStore.syncToCloud()
})

onHide(() => {
  console.log('[App] 应用隐藏')

  // 断开 WebSocket 连接以节省资源
  const messageStore = useMessageStore()
  // 可选：不立即断开，让心跳保持连接
  // messageStore.destroy()
})

// 监听用户登录事件
uni.$on('user:login', async (userId: string) => {
  console.log('[App] 用户登录，初始化服务')

  // 设置推送别名
  const { setAlias } = useNotification()
  await setAlias(userId)

  // 初始化消息服务
  const messageStore = useMessageStore()
  await messageStore.init()
})

// 监听用户登出事件
uni.$on('user:logout', async () => {
  console.log('[App] 用户登出，清理服务')

  // 清理推送
  await cleanupPushNotification()

  // 销毁消息服务
  const messageStore = useMessageStore()
  messageStore.destroy()

  // 清理日记数据
  const diaryStore = useDiaryStore()
  diaryStore.diaries = []
})
</script>

<style lang="scss">
/* 全局样式 */
@import '@/styles/index.scss';
</style>
```

#### 极光推送配置（manifest.json）

```json
{
  "app-plus": {
    "distribute": {
      "android": {
        "permissions": [
          "<uses-permission android:name=\"android.permission.INTERNET\"/>",
          "<uses-permission android:name=\"android.permission.ACCESS_NETWORK_STATE\"/>",
          "<uses-permission android:name=\"android.permission.ACCESS_WIFI_STATE\"/>",
          "<uses-permission android:name=\"android.permission.VIBRATE\"/>",
          "<uses-permission android:name=\"android.permission.RECEIVE_USER_PRESENT\"/>",
          "<uses-permission android:name=\"android.permission.WAKE_LOCK\"/>",
          "<uses-permission android:name=\"android.permission.READ_PHONE_STATE\"/>",
          "<uses-permission android:name=\"android.permission.WRITE_EXTERNAL_STORAGE\"/>",
          "<uses-permission android:name=\"android.permission.READ_EXTERNAL_STORAGE\"/>"
        ]
      },
      "ios": {
        "idfa": false,
        "capabilities": {
          "entitlements": {
            "aps-environment": "production"
          }
        }
      }
    },
    "modules": {
      "Push": {}
    },
    "nativePlugins": [
      {
        "plugins": [
          {
            "__plugin_name__": "JPush"
          }
        ]
      }
    ]
  }
}
```

---

## 九、总结

### 推荐技术栈（含P2优化补充）

| 技术层 | 选择 | 版本 | 备注 |
|--------|------|------|------|
| 框架 | Uni-app | 3.x | - |
| 前端框架 | Vue | 3.4+ | - |
| 语言 | TypeScript | 5.x | - |
| 状态管理 | Pinia | 2.x | 含6个新增Store（P2-14） |
| 主UI库 | wot-design-uni | 最新稳定版 | ConfigProvider主题切换（P2-15） |
| 辅助UI库 | uni-ui | 最新稳定版 | - |
| 图表库 | uCharts | 最新稳定版 | 曲线/环形图（P2-11） |
| 语音识别 | 科大讯飞语音听写SDK | WebAPI/原生插件 | 语音输入（P2-16） |
| HTTP库 | uni.request封装 | - | 含全局错误处理（P2-20） |
| WebSocket | uni.connectSocket封装 | - | - |

### 核心优势

1. **完善的暗色模式支持** - wot-design-uni ConfigProvider原生支持，零额外开发成本
2. **灵活的主题定制** - CSS变量 + ConfigProvider实现情绪色彩动态切换
3. **TypeScript类型安全** - 全栈类型校验，减少运行时错误
4. **活跃的社区维护** - 问题响应及时，持续迭代更新
5. **无商业授权风险** - MIT开源协议，免费商用
6. **完善的错误处理** - 全局错误捕获、网络异常体验、SSE断连重试（P2-20）
7. **安全优先的匿名机制** - 匿名头像/昵称后端生成，前端仅展示（P2-12/13）
8. **离线友好的架构** - 本地缓存 + 离线操作队列 + 自动同步（P2-14 sync Store）

---

> 文档编写：前端开发工程师
> 更新时间：2026-04-23
