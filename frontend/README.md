# 回声 - 前端应用

> 深夜情绪急救站 — 年轻人的情绪出口 + AI 朋友

---

## 项目简介

回声是一个面向年轻人的情绪陪伴应用前端，采用 uni-app 框架开发，支持 iOS、Android、H5 和小程序多端运行。

---

## 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 框架 | uni-app + Vue 3 | 跨平台应用框架 |
| 语言 | TypeScript | 类型安全 |
| 状态管理 | Pinia | Vue 3 官方推荐 |
| UI 组件库 | wot-design-uni | Vue3 组件库，原生暗色模式 |
| 样式 | SCSS | CSS 预处理器 |
| 图表 | uCharts | 轻量级跨端图表 |

---

## 项目结构

```
frontend/
├── src/
│   ├── api/               # API 接口封装
│   │   ├── index.ts       # API 统一导出
│   │   ├── chat.ts        # AI 对话接口
│   │   ├── diary.ts       # 日记接口
│   │   ├── notification.ts # 通知接口
│   │   ├── post.ts        # 动态接口
│   │   └── auth.ts        # 认证接口
│   ├── components/         # 公共组件
│   │   ├── chat/          # 聊天相关组件
│   │   │   ├── ChatInput.vue
│   │   │   ├── MessageBubble.vue
│   │   │   ├── CrisisDialog.vue
│   │   │   └── AIAssistHint.vue
│   │   ├── diary/         # 日记相关组件
│   │   ├── home/          # 首页相关组件
│   │   │   └── EmotionBar.vue
│   │   └── treehole/      # 树洞相关组件
│   │       └── PostCard.vue
│   ├── composables/        # 组合式函数
│   │   ├── useAuth.ts     # 认证状态
│   │   ├── useNotification.ts  # 通知
│   │   └── useWebSocket.ts # WebSocket
│   ├── constants/          # 常量定义
│   ├── pages/              # 页面
│   │   ├── auth/           # 认证页面
│   │   │   ├── login.vue
│   │   │   ├── profile.vue
│   │   │   └── ai-greeting.vue
│   │   ├── chat/           # AI 对话页面
│   │   │   ├── index.vue
│   │   │   └── personality.vue
│   │   ├── diary/          # 日记页面
│   │   │   ├── index.vue
│   │   │   ├── edit.vue
│   │   │   └── weekly-report.vue
│   │   ├── treehole/      # 树洞页面
│   │   │   ├── index.vue
│   │   │   ├── detail.vue
│   │   │   └── publish.vue
│   │   ├── community/      # 社区页面
│   │   │   └── index.vue
│   │   ├── friends/       # 好友页面
│   │   ├── notification/   # 通知页面
│   │   ├── message/        # 消息页面
│   │   ├── home/          # 首页
│   │   └── profile/        # 个人资料
│   ├── pagesSocial/        # 社交页面（旧版）
│   ├── stores/             # Pinia 状态管理
│   │   ├── user.ts         # 用户状态
│   │   └── chat.ts         # 聊天状态
│   ├── styles/             # 全局样式
│   │   ├── variables.scss  # CSS 变量
│   │   ├── theme.scss      # 主题配置
│   │   ├── emotions.scss   # 情绪色调
│   │   └── common.scss     # 通用样式
│   ├── types/              # TypeScript 类型
│   ├── utils/              # 工具函数
│   │   └── tracking.ts     # 埋点工具
│   ├── App.vue
│   ├── main.ts
│   ├── manifest.json       # uni-app 配置
│   └── pages.json          # 页面路由配置
├── public/                 # 静态资源
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## 快速开始

### 环境要求

- Node.js 18+
- pnpm 8+（推荐）或 npm

### 1. 安装依赖

```bash
cd frontend
pnpm install
```

### 2. 配置环境变量

```bash
cp .env.example .env.development
# 编辑 .env.development，配置 API 地址
```

主要配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `VITE_API_BASE_URL` | API 基础地址 | http://localhost:8000 |

### 3. 启动开发服务

```bash
# H5 开发
pnpm dev:h5

# 微信小程序
pnpm dev:mp-weixin

# Android / iOS App
pnpm dev:app
```

### 4. 构建

```bash
# 构建 H5
pnpm build:h5

# 构建微信小程序
pnpm build:mp-weixin

# 构建 App
pnpm build:app
```

---

## 设计规范

### 主题

- **默认主题**: 暗色模式（适合深夜使用场景）
- **备选主题**: 亮色模式

### 颜色系统

```scss
// 暗色主题背景
--bg-primary: #121212;     // 一级背景
--bg-secondary: #1E1E1E;   // 二级背景（卡片）
--bg-tertiary: #2A2A2A;    // 三级背景（弹窗）

// 文字色
--text-primary: #F5F5F5;   // 主文字
--text-secondary: #B3B3B3; // 次文字
--text-tertiary: #808080;  // 弱文字

// 品牌色
--brand-primary: #7C6FE0;  // 品牌主色
```

### 情绪色调

| 色调 | 色值 | 含义 |
|------|------|------|
| 暖橘 | #FF9A5C | 开心、正向 |
| 浅绿 | #8FCCA0 | 平静、中性 |
| 灰蓝 | #8BA7C4 | 低落、沉闷 |
| 深蓝 | #4A6FA5 | 难过、忧伤 |
| 暗紫 | #6B4C7A | 崩溃、混乱 |

详细规范请参考 [统一 UI 指南](../UNIFIED_UI_GUIDE.md)

---

## 主要功能

### 1. AI 对话

入口页面，支持：
- 切换 AI 性格（小温/老黑/阿理）
- 流式对话响应
- AI 话题提示
- 危机干预弹窗

### 2. 情绪日记

- 创建/编辑日记
- 选择情绪色调
- 查看历史日记
- AI 周报生成

### 3. 树洞吐槽

- 匿名发布吐槽
- 共鸣功能
- 评论互动

### 4. 动态广场

- 实名发布动态
- 点赞互动
- 好友关系

### 5. 通知中心

- 系统通知
- 互动通知
- AI 消息推送

---

## 组件开发规范

### 命名规范

- 组件文件：大驼峰 `UserCard.vue`
- 组件目录：小驼峰 `chatInput/`
- CSS 类：小写连字符 `.action-sheet`

### 组件结构

```vue
<template>
  <view class="component-name">
    <!-- 模板内容 -->
  </view>
</template>

<script setup lang="ts">
// 组件逻辑
</script>

<style lang="scss" scoped>
.component-name {
  // 样式
}
</style>
```

### 禁止事项

- ❌ 禁止使用 emoji 作为功能图标
- ❌ 禁止随机阴影值
- ❌ 禁止混用多种图标风格
- ❌ 禁止无规则的圆角大小

---

## 页面路由

| 页面路径 | 说明 | TabBar |
|---------|------|--------|
| `/pages/home/index` | 首页 | 是 |
| `/pages/chat/index` | AI 对话 | 是 |
| `/pages/diary/index` | 日记列表 | 是 |
| `/pages/treehole/index` | 树洞入口 | 是 |
| `/pages/community/index` | 广场入口 | 是 |
| `/pages/mine/index` | 个人中心 | 是 |
| `/pages/auth/login` | 登录页 | 否 |
| `/pages/notification/list` | 通知列表 | 否 |
| `/pages/diary/edit` | 编辑日记 | 否 |
| `/pages/treehole/detail` | 树洞详情 | 否 |

---

## API 接口

所有 API 接口封装在 `src/api/` 目录下：

```typescript
// 示例：获取日记列表
import { getDiaryList } from '@/api/diary'

const diaryList = await getDiaryList({ page: 1, page_size: 10 })
```

详细接口定义请参考后端 [API 文档](./backend/README.md#api-文档)

---

## 状态管理

使用 Pinia 管理全局状态：

```typescript
// 用户状态
import { useUserStore } from '@/stores/user'
const userStore = useUserStore()

// 聊天状态
import { useChatStore } from '@/stores/chat'
const chatStore = useChatStore()
```

---

## 部署

### H5 部署

```bash
pnpm build:h5
# 将 dist/build/h5 目录部署到服务器
```

### App 部署

```bash
# Android
pnpm build:app
# 在 dist/build/app 目录生成 apk

# iOS
pnpm build:app
# 在 dist/build/app 目录生成ipa（需 Mac + Xcode）
```

详细部署指南请参考 [部署文档](../docs/deployment_guide.md)

---

## 相关文档

- [产品需求文档](../PRD.md)
- [技术架构文档](../tech_architecture.md)
- [后端接口文档](../backend/README.md)
- [UI 设计规范](../ui_design.md)
- [统一 UI 指南](../UNIFIED_UI_GUIDE.md)
- [前端技术方案](../frontend_tech.md)
