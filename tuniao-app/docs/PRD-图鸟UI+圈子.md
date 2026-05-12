# 图鸟UI+圈子 产品需求文档 (PRD)

> 文档版本：v1.0
> 更新日期：2026-05-12
> 产品类型：社区/圈子类移动应用

---

## 一、产品概述

### 1.1 产品定位

图鸟UI+圈子是一款基于 **图鸟UI (TuniaoUI)** 组件库开发的社区/圈子类移动应用模板。产品以"酷炫多彩"为设计理念，采用现代化 UI 风格，支持微信小程序、APP、H5 多端适配。

### 1.2 目标用户

| 用户类型 | 特征描述 | 核心需求 |
|---------|---------|---------|
| 内容创作者 | 有分享欲望、追求个性化表达 | 发布动态、获得关注、社交互动 |
| 社区参与者 | 喜欢浏览、评论、点赞 | 发现优质内容、参与活动 |
| 商家用户 | 有商品推广需求 | 商品展示、积分营销、用户转化 |
| 普通用户 | 休闲娱乐为主 | 浏览内容、积分兑换、工具使用 |

### 1.3 产品架构

```
图鸟UI+圈子
├── 首页模块 (homePages)
├── 圈子模块 (circlePages)
├── 广场模块 (activityPages)
├── 优选模块 (preferredPages)
└── 我的模块 (minePages)
```

---

## 二、首页模块 PRD

### 2.1 模块概述

首页作为应用的入口页面，承担着产品形象展示、核心功能导流、内容分发的重要职责。设计风格采用渐变背景、3D 阴影效果，营造高端视觉体验。

### 2.2 页面列表

| 页面名称 | 路由路径 | 功能描述 |
|---------|---------|---------|
| 首页主页面 | pages/home/home.vue | 主入口，展示轮播、推荐内容 |
| 关于我们 | homePages/about | 品牌介绍、团队信息 |
| 全局搜索 | homePages/search | 全站内容搜索入口 |
| 今日热榜 | homePages/hot | 热点资讯聚合展示 |
| 全站导航 | homePages/navigation | 功能导航总览 |
| 前端业务 | homePages/profession | 业务服务介绍 |
| 加载效果 | homePages/loading | 加载状态展示 |

### 2.3 核心功能详解

#### 2.3.1 首页主页面

**功能描述：** 应用主入口页面，展示核心业务入口和推荐内容。

**页面结构：**

1. **顶部导航栏**
   - 品牌Logo（点击跳转关于我们）
   - 搜索框（点击跳转全局搜索）

2. **轮播Banner**
   - 自动轮播，间隔8秒
   - 支持手动滑动切换
   - 展示活动推广、产品宣传内容

3. **快捷入口区**
   - 热点资讯 → 跳转今日热榜
   - 商品分类 → 跳转商品分类页
   - 智能名片 → 跳转名片功能
   - 星选门户 → 跳转品牌官网

4. **广告Banner**
   - 横幅广告位
   - 点击跳转广告详情页

5. **推荐名片区**
   - 横向滑动卡片
   - 展示用户头像、姓名、职位
   - 显示人气、分享、爱心数据
   - 点击查看名片详情

6. **热门项目区**
   - 图文混排布局
   - 大图+小图组合展示
   - 点击查看项目详情

7. **业务范围区**
   - 四宫格卡片布局
   - 包含：UI设计、小程序、前端开发、其他业务
   - 点击跳转业务咨询页

**交互要点：**
- 支持 Android/iOS 双平台适配
- 卡片点击有视觉反馈效果
- 页面滚动到底部触发加载更多

---

## 三、圈子模块 PRD

### 3.1 模块概述

圈子模块是产品的核心社交功能模块，提供内容发布、浏览、互动、视频观看等功能。采用 Tab 切换设计，支持"发现"、"视频"、"世界"三种浏览模式。

### 3.2 页面列表

| 页面名称 | 路由路径 | 功能描述 |
|---------|---------|---------|
| 圈子主页 | pages/circle/circle.vue | 主入口，内容流展示 |
| 博主主页_Me | circlePages/blogger | 个人主页（自己） |
| 博主主页_Ta | circlePages/blogger_other | 他人主页 |
| 编辑发布 | circlePages/edit | 发布动态内容 |
| 广告页 | circlePages/advertise | 广告展示页 |
| 资讯详情 | circlePages/news | 文章/资讯详情 |
| 名片王者 | circlePages/king | 名片功能 |
| 智能名片 | circlePages/business | 名片编辑/展示 |
| 精选圈子 | circlePages/group | 圈子列表 |
| 积分排行 | circlePages/ranking | 用户积分榜单 |
| 圈子详情 | circlePages/details | 动态详情页 |
| 预约接龙 | circlePages/reserve | 活动预约功能 |
| 活动创建 | circlePages/create | 创建新活动 |
| 打造圈子 | circlePages/build | 创建新圈子 |
| 一起群聊 | circlePages/chat | 群聊入口 |
| 对话聊天 | circlePages/chatting | 单聊对话页 |

### 3.3 核心功能详解

#### 3.3.1 圈子主页

**功能描述：** 社交内容流核心页面，支持三种浏览模式。

**Tab页面结构：**

**Tab 1 - 发现页**
- 积分榜入口卡片（显示参与人数）
- 精选圈子横向滚动列表
- 图文内容流（瀑布流+信息流混合）
- 广告卡片穿插展示
- 互动数据：浏览、评论、点赞

**Tab 2 - 视频页**
- 全屏竖向视频播放
- 上下滑动切换视频
- 自动播放/暂停控制
- 视频信息叠加展示

**Tab 3 - 世界页**
- 活动预约接龙列表
- 活动卡片展示：封面、标题、参与人数、标签
- 支持多种活动类型：祝福接力、时光信件、纪念日、团购、婚礼等

**悬浮操作按钮：**
- 点击弹出压屏窗
- 三个选项：发布动态、发起活动、创建圈子
- 带有震动反馈

#### 3.3.2 内容卡片设计

**博主信息区：**
- 头像（圆形，支持点击跳转主页）
- 用户昵称
- 发布时间
- 更多操作按钮

**内容展示区：**
- 标签（#话题）
- 文字描述
- 图片网格（1/2/4/6张自适应布局）

**互动数据区：**
- 浏览量
- 评论数
- 点赞数
- 浏览用户头像组

#### 3.3.3 发布功能

**支持内容类型：**
- 纯文字动态
- 图文动态（最多9张图）
- 话题标签
- 外部链接

**发布流程：**
1. 点击悬浮按钮 → 发布动态
2. 进入编辑页面
3. 输入文字内容（限200字）
4. 添加图片（可选）
5. 选择话题标签（可选）
6. 点击发布

---

## 四、广场模块 PRD

### 4.1 模块概述

广场模块是活动与工具聚合页面，提供知识星球、开源项目、地图打卡、课程学习等特色功能入口，以及丰富的工具集合。

### 4.2 页面列表

| 页面名称 | 路由路径 | 功能描述 |
|---------|---------|---------|
| 广场主页 | pages/activity/activity.vue | 主入口，活动展示 |
| 地图打卡 | activityPages/map | LBS打卡功能 |
| 快速答题 | activityPages/topic | 答题互动 |
| 课程学习 | activityPages/study | 在线课程 |
| 开源项目 | activityPages/project | 开源项目展示 |
| 活动星球 | activityPages/planet | 活动聚合页 |

### 4.3 核心功能详解

#### 4.3.1 广场主页

**页面结构：**

1. **顶部背景图**
   - 品牌宣传图

2. **样机轮播区**
   - 3D手机样机效果
   - 左右滑动切换
   - 展示产品截图/宣传图

3. **快捷入口区（四宫格）**
   - 知识星球 → 活动星球页
   - 开源项目 → 开源项目页
   - 地图打卡 → 地图打卡页
   - 课程学习 → 课程学习页

4. **工具集合区**
   - 网格卡片布局
   - 工具列表：
     - 称呼计算器
     - 支付宝语音生成
     - 一周天气预报
     - 今日星座运势
     - 来碗毒鸡汤
     - 垃圾分一分
     - 手持弹幕
     - 孩子取名
     - 午餐吃什么
     - 朋友圈文案
   - 显示参与人数

5. **友情链接区**
   - 第三方小程序跳转
   - 支持appId配置

---

## 五、优选模块 PRD

### 5.1 模块概述

优选模块是电商/积分商城模块，提供商品展示、积分兑换、商家入驻等功能。采用瀑布流布局，支持多分类筛选。

### 5.2 页面列表

| 页面名称 | 路由路径 | 功能描述 |
|---------|---------|---------|
| 优选主页 | pages/preferred/preferred.vue | 主入口，商品展示 |
| 优质商家 | preferredPages/shop | 商家列表 |
| 商品详情 | preferredPages/product | 商品详情页 |
| 历史订单 | preferredPages/order | 订单记录 |
| 商品分类 | preferredPages/classify | 分类筛选 |
| 商家相册 | preferredPages/photo | 商家图片展示 |
| 品牌官网 | preferredPages/website | 品牌官网页 |
| 积分兑换 | preferredPages/redeem | 积分商品兑换 |
| 免单活动 | preferredPages/award | 免单抽奖活动 |
| 免单获取 | preferredPages/awardget | 免单结果页 |

### 5.3 核心功能详解

#### 5.3.1 优选主页

**Tab分类：**
- 推荐
- 美食
- 科技
- 音乐
- 电影
- 游戏

**推荐Tab页面结构：**

1. **商家推荐轮播**
   - 横向滑动
   - 展示商家头像和名称

2. **积分兑换区**
   - 展示积分商品
   - 显示所需积分
   - 双列网格布局

3. **商家热卖区**
   - 商品卡片：图片、标题、价格、销量
   - 商家信息展示
   - 双列网格布局

4. **商品优选区**
   - 瀑布流布局
   - 商品信息：图片、标题、标签、价格
   - 支持自营/新品标识
   - 懒加载图片

**商品卡片设计：**
- 商品主图
- 商品标题
- 促销标签（满减、免息等）
- 价格（整数+小数分开展示）
- 店铺标识

---

## 六、我的模块 PRD

### 6.1 模块概述

我的模块是用户个人中心，提供账户管理、积分系统、订单管理、系统设置等功能。采用个性化头像动画设计，突出用户身份。

### 6.2 页面列表

| 页面名称 | 路由路径 | 功能描述 |
|---------|---------|---------|
| 我的主页 | pages/mine/mine.vue | 主入口，个人中心 |
| 使用协议 | minePages/protocol | 用户协议展示 |
| 授权登录 | minePages/login | 微信授权登录 |
| 消息通知 | minePages/message | 系统消息列表 |
| 全局设置 | minePages/set | 应用设置 |
| 立即体验 | minePages/start | 引导页 |
| 感谢名单 | minePages/thanks | 开源致谢 |
| 版本更新 | minePages/version | 版本信息 |
| 帮助中心 | minePages/help | 常见问题 |
| 头像上传 | minePages/avatar | 头像设置 |
| 积分明细 | minePages/integral | 积分流水 |
| 积分签到 | minePages/signed | 每日签到 |
| 好物收藏 | minePages/collect | 收藏列表 |
| 账号安全 | minePages/safety | 安全设置 |
| 缺省页 | minePages/default | 空状态展示 |
| 赞赏作者 | minePages/reward | 赞赏功能 |
| 富文本 | minePages/content | 富文本展示 |

### 6.3 核心功能详解

#### 6.3.1 我的主页

**页面结构：**

1. **顶部背景区**
   - 个性化背景图
   - 可爱动画形象（点击跳转感谢页）

2. **用户信息区**
   - 头像（点击跳转设置）
   - 用户昵称
   - 会员等级标识

3. **快捷入口区（双列）**
   - 图鸟官网 → 小程序跳转
   - 图鸟UI → 小程序跳转

4. **常用功能区（四宫格）**
   - 我的圈子 → 博主主页
   - 消息通知 → 消息页
   - 积分明细 → 积分页
   - 积分签到 → 签到页

5. **更多功能区（四宫格）**
   - 历史订单 → 订单页
   - 好物收藏 → 收藏页
   - 收货地址 → 系统地址选择
   - 全局设置 → 设置页

6. **其他功能列表**
   - 关于图鸟
   - 开源地址（点击复制链接）
   - 使用协议

7. **联系与支持**
   - 合作勾搭（客服会话）
   - 问题反馈（系统反馈）
   - 技术支持（拨打电话）

#### 6.3.2 积分系统

**积分获取方式：**
- 每日签到
- 发布动态
- 评论互动
- 邀请好友
- 参与活动

**积分消耗方式：**
- 商品兑换
- 活动参与
- 会员特权

---

## 七、公共组件库

### 7.1 UI组件

项目基于 **图鸟UI (TuniaoUI)** 组件库，包含以下核心组件：

| 组件名称 | 功能描述 |
|---------|---------|
| tn-nav-bar | 自定义导航栏 |
| tn-tabbar | 底部标签栏 |
| tn-tabs | 顶部选项卡 |
| tn-avatar | 头像组件 |
| tn-avatar-group | 头像组 |
| tn-badge | 徽标组件 |
| tn-button | 按钮组件 |
| tn-calendar | 日历组件 |
| tn-card | 卡片组件 |
| tn-collapse | 折叠面板 |
| tn-grid | 宫格组件 |
| tn-lazy-load | 图片懒加载 |
| tn-list-cell | 列表单元格 |
| tn-load-more | 加载更多 |
| tn-swiper | 轮播组件 |
| tn-waterfall | 瀑布流 |

### 7.2 自定义组件

| 组件路径 | 功能描述 |
|---------|---------|
| libs/components/demo-title.vue | 演示标题 |
| libs/components/dynamic-demo-template.vue | 动态演示模板 |
| libs/components/multiple-options-demo.vue | 多选演示 |
| libs/components/nav-index-button.vue | 导航索引按钮 |

---

## 八、数据结构设计

### 8.1 用户数据结构

```typescript
interface User {
  id: string;           // 用户ID
  avatar: string;       // 头像URL
  nickname: string;     // 昵称
  level: number;        // 会员等级
  integral: number;     // 积分余额
  isVip: boolean;       // 是否VIP
  vipLevel: number;     // VIP等级
}
```

### 8.2 动态内容数据结构

```typescript
interface Content {
  id: string;                    // 内容ID
  userAvatar: string;            // 发布者头像
  userName: string;              // 发布者昵称
  date: string;                  // 发布日期
  label: string[];               // 话题标签
  desc: string;                  // 文字描述
  mainImage: string[];           // 图片列表
  collectionCount: number;       // 浏览量
  commentCount: number;          // 评论数
  likeCount: number;             // 点赞数
  viewUser: {
    latestUserAvatar: Array<{src: string}>;
    viewUserCount: number;
  };
}
```

### 8.3 商品数据结构

```typescript
interface Product {
  id: string;            // 商品ID
  title: string;         // 商品标题
  mainImage: string;     // 主图URL
  storeType: number;     // 店铺类型：1自营 2第三方
  newProduct: boolean;   // 是否新品
  tags: string[];        // 促销标签
  price: number;         // 价格（分）
  priceInteger: string;  // 价格整数部分
  priceDecimal: string;  // 价格小数部分
}
```

### 8.4 活动数据结构

```typescript
interface Activity {
  id: string;                    // 活动ID
  userAvatar: string;            // 发布者头像
  userName: string;              // 发布者昵称
  date: string;                  // 发布日期
  color: string;                 // 主题色
  label: string[];               // 活动标签
  title: string;                 // 活动标题
  desc: string;                  // 活动描述
  mainImage: string;             // 封面图
  viewUser: {
    latestUserAvatar: Array<{src: string}>;
    viewUserCount: number;       // 参与人数
  };
  collectionCount: number;       // 浏览量
  commentCount: number;          // 评论数
  likeCount: number;             // 点赞数
}
```

---

## 九、技术架构

### 9.1 技术栈

| 技术领域 | 技术选型 |
|---------|---------|
| 前端框架 | uni-app (Vue.js) |
| UI组件库 | TuniaoUI 图鸟UI |
| 状态管理 | Vuex |
| 样式预处理 | SCSS |
| 构建工具 | HBuilderX |

### 9.2 多端适配

| 平台 | 支持状态 | 备注 |
|------|---------|------|
| 微信小程序 | ✅ 完全支持 | 主要目标平台 |
| APP (iOS/Android) | ✅ 完全支持 | 需云打包 |
| H5 | ✅ 完全支持 | 支持浏览器访问 |
| Finclip | ✅ 完全支持 | 小程序容器 |

### 9.3 目录结构

```
tuniao-app/
├── pages/              # 主页面
│   ├── index.vue       # 入口页
│   ├── home/           # 首页
│   ├── circle/         # 圈子
│   ├── activity/       # 广场
│   ├── preferred/      # 优选
│   └── mine/           # 我的
├── homePages/          # 首页子页面
├── circlePages/        # 圈子子页面
├── activityPages/      # 广场子页面
├── preferredPages/     # 优选子页面
├── minePages/          # 我的子页面
├── tuniao-ui/          # UI组件库
├── libs/               # 工具库
├── store/              # 状态管理
├── static/             # 静态资源
├── App.vue             # 应用入口
├── main.js             # 主入口
├── pages.json          # 页面配置
└── manifest.json       # 应用配置
```

---

## 十、设计规范

### 10.1 配色方案

| 颜色名称 | 色值 | 用途 |
|---------|------|------|
| 主色调 | #FBBD12 | 品牌色、高亮状态 |
| 辅助色 | #00FFC8 | 标签前缀 |
| 价格红 | #E83A30 | 价格展示 |
| 警示色 | #E72F8C | 徽标、提醒 |
| 文字黑 | #080808 | 标题文字 |
| 文字灰 | #AAAAAA | 次要文字 |
| 背景灰 | #F8F8F8 | 页面背景 |

### 10.2 字体规范

| 字体大小 | 适用场景 |
|---------|---------|
| 46rpx | 大标题 |
| 38rpx | 标题 |
| 32rpx | 正文标题 |
| 28rpx | 正文 |
| 24rpx | 辅助文字 |
| 20rpx | 标签文字 |

### 10.3 间距规范

| 间距类型 | 数值 | 适用场景 |
|---------|------|---------|
| 页面边距 | 30rpx | 页面左右边距 |
| 模块间距 | 20rpx | 模块间分隔 |
| 元素间距 | 10rpx | 同行元素间距 |
| 内边距 | 30rpx | 卡片内边距 |

---

## 十一、迭代规划

### 11.1 已完成功能

- [x] 五大核心模块页面搭建
- [x] 自定义底部导航栏
- [x] 内容流展示
- [x] 视频播放功能
- [x] 商品瀑布流展示
- [x] 积分系统框架
- [x] 多端适配

### 11.2 待开发功能

- [ ] 后端接口对接
- [ ] 用户认证系统
- [ ] 即时通讯功能
- [ ] 支付系统
- [ ] 消息推送
- [ ] 数据统计

---

## 十二、附录

### 12.1 相关链接

- 图鸟UI官网：https://tuniaokj.com
- 图鸟UI文档：https://tuniaokj.com/doc
- 开源地址：https://ext.dcloud.net.cn/plugin?id=8503
- 语雀文档：https://www.yuque.com/tuniao

### 12.2 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2026-05-12 | 初始版本，完成PRD文档编写 |

---

> 文档编写：Claude
> 最后更新：2026-05-12
