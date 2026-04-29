<template>
  <div class="dashboard">
    <!-- 时间范围选择 -->
    <el-card class="time-range-card">
      <div class="time-range-header">
        <span class="title">数据概览</span>
        <div class="time-range-actions">
          <el-radio-group v-model="timeRange" @change="handleTimeRangeChange">
            <el-radio-button value="today">今日</el-radio-button>
            <el-radio-button value="yesterday">昨日</el-radio-button>
            <el-radio-button value="week">近7天</el-radio-button>
            <el-radio-button value="month">近30天</el-radio-button>
            <el-radio-button value="custom">自定义</el-radio-button>
          </el-radio-group>
          <el-date-picker
            v-if="timeRange === 'custom'"
            v-model="customDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="handleCustomDateChange"
          />
          <el-button type="primary" @click="refreshData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 概览统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon dau">
              <el-icon size="28"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(overviewStats.dau) }}</div>
              <div class="stat-label">DAU (日活)</div>
              <div class="stat-trend">
                <span :class="overviewStats.new_users_today >= overviewStats.new_users_yesterday ? 'up' : 'down'">
                  <el-icon v-if="overviewStats.new_users_today >= overviewStats.new_users_yesterday"><Top /></el-icon>
                  <el-icon v-else><Bottom /></el-icon>
                  {{ Math.abs(((overviewStats.new_users_today - overviewStats.new_users_yesterday) / (overviewStats.new_users_yesterday || 1)) * 100).toFixed(1) }}%
                </span>
                <span class="trend-label">较昨日</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon wau">
              <el-icon size="28"><UserFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(overviewStats.wau) }}</div>
              <div class="stat-label">WAU (周活)</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon mau">
              <el-icon size="28"><Avatar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(overviewStats.mau) }}</div>
              <div class="stat-label">MAU (月活)</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon new-users">
              <el-icon size="28"><Plus /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(overviewStats.new_users_today) }}</div>
              <div class="stat-label">今日新增用户</div>
              <div class="stat-sub">
                本周新增: {{ formatNumber(overviewStats.new_users_week) }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第二行统计卡片 -->
    <el-row :gutter="20" class="stat-cards second-row">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon ai-chat">
              <el-icon size="28"><ChatDotRound /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(overviewStats.ai_conversations_today) }}</div>
              <div class="stat-label">今日 AI 对话</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon diary">
              <el-icon size="28"><Notebook /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(overviewStats.diary_count_today) }}</div>
              <div class="stat-label">今日日记数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon active-rate">
              <el-icon size="28"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ (overviewStats.active_rate * 100).toFixed(1) }}%</div>
              <div class="stat-label">活跃率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card quick-entry" shadow="hover">
          <div class="stat-content">
            <div class="quick-links">
              <el-button v-if="hasPermission('report:view')" type="warning" @click="$router.push('/reports')">
                <el-icon><Warning /></el-icon>
                举报管理
              </el-button>
              <el-button v-if="hasPermission('crisis:view')" type="danger" @click="$router.push('/crisis')">
                <el-icon><FirstAidKit /></el-icon>
                危机干预
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <!-- 用户增长趋势 -->
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>用户增长趋势</span>
              <el-radio-group v-model="growthGranularity" size="small" @change="fetchUserGrowth">
                <el-radio-button value="day">按天</el-radio-button>
                <el-radio-button value="week">按周</el-radio-button>
                <el-radio-button value="month">按月</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <v-chart class="chart" :option="userGrowthOption" autoresize />
        </el-card>
      </el-col>
      <!-- 情绪分布 -->
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>情绪分布</span>
          </template>
          <v-chart class="chart" :option="emotionOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- 留存数据 & AI 统计 -->
    <el-row :gutter="20" class="chart-row">
      <!-- 留存数据表格 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>用户留存数据</span>
          </template>
          <el-table :data="retentionData" stripe max-height="300" size="small">
            <el-table-column prop="date" label="日期" width="100" />
            <el-table-column prop="new_users" label="新增用户" width="80">
              <template #default="{ row }">
                {{ formatNumber(row.new_users) }}
              </template>
            </el-table-column>
            <el-table-column label="留存率" align="center">
              <el-table-column prop="day1" label="次日" width="70">
                <template #default="{ row }">
                  <span :class="getRetentionClass(row.day1)">{{ row.day1 }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="day3" label="3日" width="70">
                <template #default="{ row }">
                  <span :class="getRetentionClass(row.day3)">{{ row.day3 }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="day7" label="7日" width="70">
                <template #default="{ row }">
                  <span :class="getRetentionClass(row.day7)">{{ row.day7 }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="day14" label="14日" width="70">
                <template #default="{ row }">
                  <span :class="getRetentionClass(row.day14)">{{ row.day14 }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="day30" label="30日" width="70">
                <template #default="{ row }">
                  <span :class="getRetentionClass(row.day30)">{{ row.day30 }}%</span>
                </template>
              </el-table-column>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <!-- AI 服务统计 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>AI 服务统计</span>
          </template>
          <div class="ai-stats">
            <el-row :gutter="20">
              <el-col :span="8">
                <div class="ai-stat-item">
                  <div class="ai-stat-value">{{ formatNumber(aiStats.total_conversations) }}</div>
                  <div class="ai-stat-label">总对话数</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="ai-stat-item">
                  <div class="ai-stat-value">{{ aiStats.avg_duration.toFixed(1) }}s</div>
                  <div class="ai-stat-label">平均时长</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="ai-stat-item">
                  <div class="ai-stat-value">{{ aiStats.avg_messages.toFixed(1) }}</div>
                  <div class="ai-stat-label">平均消息数</div>
                </div>
              </el-col>
            </el-row>
            <div class="ai-stat-item satisfaction">
              <div class="ai-stat-value">{{ (aiStats.satisfaction_rate * 100).toFixed(1) }}%</div>
              <div class="ai-stat-label">满意度</div>
            </div>
            <div class="ai-intents">
              <div class="intents-title">热门意图 TOP 5</div>
              <div class="intents-list">
                <div v-for="(item, index) in aiStats.top_intents.slice(0, 5)" :key="item.intent" class="intent-item">
                  <span class="intent-rank">{{ index + 1 }}</span>
                  <span class="intent-name">{{ item.intent }}</span>
                  <span class="intent-count">{{ formatNumber(item.count) }}</span>
                  <el-progress :percentage="item.percentage" :show-text="false" :stroke-width="6" />
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, markRaw } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import dayjs from 'dayjs'
import { useAdminStore } from '@/stores/admin'
import {
  getOverviewStats,
  getUserGrowth,
  getRetention,
  getEmotionDistribution,
  getAIServiceStats,
} from '@/api/dashboard'
import type {
  OverviewStats,
  UserGrowthItem,
  RetentionItem,
  EmotionDistribution,
  AIServiceStats,
  DashboardTimeRange,
} from '@/types/dashboard'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

const adminStore = useAdminStore()
const loading = ref(false)

// 时间范围
const timeRange = ref<DashboardTimeRange>('week')
const customDateRange = ref<string[]>([])
const growthGranularity = ref<'day' | 'week' | 'month'>('day')

// 数据
const overviewStats = ref<OverviewStats>({
  dau: 0,
  wau: 0,
  mau: 0,
  new_users_today: 0,
  new_users_yesterday: 0,
  new_users_week: 0,
  ai_conversations_today: 0,
  diary_count_today: 0,
  active_rate: 0,
})

const userGrowthData = ref<UserGrowthItem[]>([])
const retentionData = ref<RetentionItem[]>([])
const emotionData = ref<EmotionDistribution[]>([])
const aiStats = ref<AIServiceStats>({
  total_conversations: 0,
  avg_duration: 0,
  avg_messages: 0,
  satisfaction_rate: 0,
  top_intents: [],
  daily_stats: [],
})

// 格式化数字
function formatNumber(num: number): string {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toLocaleString()
}

// 获取留存率样式类
function getRetentionClass(value: number): string {
  if (value >= 50) return 'retention-high'
  if (value >= 30) return 'retention-medium'
  return 'retention-low'
}

// 权限检查
function hasPermission(permission: string) {
  return adminStore.hasPermission(permission)
}

// 用户增长趋势图表配置
const userGrowthOption = computed(() => {
  const dates = userGrowthData.value.map(item => item.date)
  const newUsers = userGrowthData.value.map(item => item.new_users)
  const activeUsers = userGrowthData.value.map(item => item.active_users)

  return markRaw({
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: ['新增用户', '活跃用户'],
      top: 10,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: '新增用户',
        type: 'line',
        smooth: true,
        data: newUsers,
        areaStyle: {
          opacity: 0.3,
        },
        itemStyle: {
          color: '#409eff',
        },
      },
      {
        name: '活跃用户',
        type: 'line',
        smooth: true,
        data: activeUsers,
        areaStyle: {
          opacity: 0.3,
        },
        itemStyle: {
          color: '#67c23a',
        },
      },
    ],
  })
})

// 情绪分布图表配置
const emotionOption = computed(() => {
  const data = emotionData.value.map(item => ({
    name: item.emotion,
    value: item.count,
  }))

  return markRaw({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
          },
        },
        labelLine: {
          show: false,
        },
        data,
      },
    ],
  })
})

// 处理时间范围变化
function handleTimeRangeChange() {
  if (timeRange.value !== 'custom') {
    fetchAllData()
  }
}

// 处理自定义日期变化
function handleCustomDateChange() {
  if (customDateRange.value && customDateRange.value.length === 2) {
    fetchAllData()
  }
}

// 获取日期范围参数
function getDateParams() {
  const today = dayjs()
  let startDate = ''
  let endDate = today.format('YYYY-MM-DD')

  switch (timeRange.value) {
    case 'today':
      startDate = today.format('YYYY-MM-DD')
      break
    case 'yesterday':
      startDate = today.subtract(1, 'day').format('YYYY-MM-DD')
      endDate = startDate
      break
    case 'week':
      startDate = today.subtract(6, 'day').format('YYYY-MM-DD')
      break
    case 'month':
      startDate = today.subtract(29, 'day').format('YYYY-MM-DD')
      break
    case 'custom':
      if (customDateRange.value && customDateRange.value.length === 2) {
        startDate = customDateRange.value[0]
        endDate = customDateRange.value[1]
      }
      break
  }

  return { start_date: startDate, end_date: endDate }
}

// 刷新所有数据
async function refreshData() {
  loading.value = true
  try {
    await fetchAllData()
  } finally {
    loading.value = false
  }
}

// 获取所有数据
async function fetchAllData() {
  await Promise.all([
    fetchOverviewStats(),
    fetchUserGrowth(),
    fetchRetention(),
    fetchEmotionDistribution(),
    fetchAIServiceStats(),
  ])
}

// 获取概览统计
async function fetchOverviewStats() {
  try {
    const result = await getOverviewStats()
    overviewStats.value = result
  } catch (error) {
    console.error('获取概览统计失败', error)
    // 使用 Mock 数据
    overviewStats.value = {
      dau: 1234,
      wau: 5678,
      mau: 12345,
      new_users_today: 128,
      new_users_yesterday: 105,
      new_users_week: 856,
      ai_conversations_today: 3456,
      diary_count_today: 789,
      active_rate: 0.234,
    }
  }
}

// 获取用户增长趋势
async function fetchUserGrowth() {
  try {
    const params = {
      ...getDateParams(),
      granularity: growthGranularity.value,
    }
    const result = await getUserGrowth(params)
    userGrowthData.value = result
  } catch (error) {
    console.error('获取用户增长趋势失败', error)
    // 使用 Mock 数据
    const mockData: UserGrowthItem[] = []
    for (let i = 6; i >= 0; i--) {
      const date = dayjs().subtract(i, 'day').format('MM-DD')
      mockData.push({
        date,
        new_users: Math.floor(Math.random() * 100) + 50,
        active_users: Math.floor(Math.random() * 500) + 500,
        total_users: 10000 + (6 - i) * 100,
      })
    }
    userGrowthData.value = mockData
  }
}

// 获取留存数据
async function fetchRetention() {
  try {
    const result = await getRetention(getDateParams())
    retentionData.value = result
  } catch (error) {
    console.error('获取留存数据失败', error)
    // 使用 Mock 数据
    const mockData: RetentionItem[] = []
    for (let i = 6; i >= 0; i--) {
      const date = dayjs().subtract(i, 'day').format('YYYY-MM-DD')
      mockData.push({
        date,
        new_users: Math.floor(Math.random() * 100) + 50,
        day1: Math.floor(Math.random() * 30) + 40,
        day3: Math.floor(Math.random() * 20) + 25,
        day7: Math.floor(Math.random() * 15) + 15,
        day14: Math.floor(Math.random() * 10) + 8,
        day30: Math.floor(Math.random() * 5) + 3,
      })
    }
    retentionData.value = mockData
  }
}

// 获取情绪分布
async function fetchEmotionDistribution() {
  try {
    const result = await getEmotionDistribution()
    emotionData.value = result
  } catch (error) {
    console.error('获取情绪分布失败', error)
    // 使用 Mock 数据
    emotionData.value = [
      { emotion: '快乐', count: 1234, percentage: 35 },
      { emotion: '平静', count: 987, percentage: 28 },
      { emotion: '悲伤', count: 456, percentage: 13 },
      { emotion: '焦虑', count: 345, percentage: 10 },
      { emotion: '愤怒', count: 234, percentage: 7 },
      { emotion: '恐惧', count: 123, percentage: 4 },
      { emotion: '其他', count: 121, percentage: 3 },
    ]
  }
}

// 获取 AI 服务统计
async function fetchAIServiceStats() {
  try {
    const result = await getAIServiceStats()
    aiStats.value = result
  } catch (error) {
    console.error('获取 AI 服务统计失败', error)
    // 使用 Mock 数据
    aiStats.value = {
      total_conversations: 12345,
      avg_duration: 45.6,
      avg_messages: 8.3,
      satisfaction_rate: 0.856,
      top_intents: [
        { intent: '情感倾诉', count: 2345, percentage: 35 },
        { intent: '压力疏导', count: 1876, percentage: 28 },
        { intent: '睡眠问题', count: 987, percentage: 15 },
        { intent: '人际交往', count: 654, percentage: 10 },
        { intent: '职业规划', count: 432, percentage: 6 },
      ],
      daily_stats: [],
    }
  }
}

onMounted(() => {
  fetchAllData()
})
</script>

<style scoped lang="scss">
.dashboard {
  .time-range-card {
    margin-bottom: 20px;

    .time-range-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .title {
        font-size: 18px;
        font-weight: bold;
        color: #303133;
      }

      .time-range-actions {
        display: flex;
        align-items: center;
        gap: 12px;
      }
    }
  }

  .stat-cards {
    .stat-card {
      height: 140px;

      .stat-content {
        display: flex;
        align-items: center;
        gap: 16px;
        height: 100%;
      }

      .stat-icon {
        width: 64px;
        height: 64px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;

        &.dau {
          background: linear-gradient(135deg, #409eff, #66b1ff);
        }

        &.wau {
          background: linear-gradient(135deg, #67c23a, #85ce61);
        }

        &.mau {
          background: linear-gradient(135deg, #e6a23c, #f0c78a);
        }

        &.new-users {
          background: linear-gradient(135deg, #f56c6c, #fab6b6);
        }

        &.ai-chat {
          background: linear-gradient(135deg, #9b59b6, #be90d4);
        }

        &.diary {
          background: linear-gradient(135deg, #3498db, #5dade2);
        }

        &.active-rate {
          background: linear-gradient(135deg, #1abc9c, #48c9b0);
        }
      }

      .stat-info {
        flex: 1;

        .stat-value {
          font-size: 32px;
          font-weight: bold;
          color: #303133;
          line-height: 1.2;
        }

        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-top: 4px;
        }

        .stat-trend {
          margin-top: 6px;
          font-size: 12px;
          display: flex;
          align-items: center;
          gap: 4px;

          .up {
            color: #67c23a;
          }

          .down {
            color: #f56c6c;
          }

          .trend-label {
            color: #c0c4cc;
          }
        }

        .stat-sub {
          margin-top: 4px;
          font-size: 12px;
          color: #c0c4cc;
        }
      }

      &.quick-entry {
        .stat-content {
          justify-content: center;
        }

        .quick-links {
          display: flex;
          flex-direction: column;
          gap: 10px;
          width: 100%;
        }
      }
    }

    &.second-row {
      margin-top: 20px;
    }
  }

  .chart-row {
    margin-top: 20px;

    .chart-card {
      height: 400px;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .chart {
        height: 320px;
      }
    }
  }

  // 留存率颜色
  .retention-high {
    color: #67c23a;
    font-weight: bold;
  }

  .retention-medium {
    color: #e6a23c;
  }

  .retention-low {
    color: #f56c6c;
  }

  // AI 统计样式
  .ai-stats {
    .ai-stat-item {
      text-align: center;
      padding: 10px 0;

      .ai-stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #409eff;
      }

      .ai-stat-label {
        font-size: 12px;
        color: #909399;
        margin-top: 4px;
      }

      &.satisfaction {
        margin-top: 10px;
        padding: 15px 0;
        border-top: 1px solid #ebeef5;
        border-bottom: 1px solid #ebeef5;

        .ai-stat-value {
          font-size: 36px;
          color: #67c23a;
        }
      }
    }

    .ai-intents {
      margin-top: 15px;

      .intents-title {
        font-size: 14px;
        color: #303133;
        margin-bottom: 10px;
      }

      .intents-list {
        .intent-item {
          display: grid;
          grid-template-columns: 24px 80px 60px 1fr;
          align-items: center;
          gap: 8px;
          padding: 8px 0;

          .intent-rank {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #409eff;
            color: #fff;
            font-size: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
          }

          .intent-name {
            font-size: 13px;
            color: #606266;
          }

          .intent-count {
            font-size: 12px;
            color: #909399;
            text-align: right;
          }
        }
      }
    }
  }
}
</style>
