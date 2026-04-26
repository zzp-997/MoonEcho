<template>
  <div class="user-detail" v-loading="loading">
    <el-page-header @back="goBack">
      <template #content>
        <span class="page-title">用户详情</span>
      </template>
    </el-page-header>

    <div class="detail-content" v-if="userDetail">
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>用户信息</span>
            <div>
              <el-tag v-if="userDetail.is_banned" type="danger">已封禁</el-tag>
              <el-tag v-else type="success">正常</el-tag>
              <el-tag v-if="userDetail.is_minor" type="warning" style="margin-left: 8px;">青少年模式</el-tag>
            </div>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户ID">{{ userDetail.id }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ userDetail.phone }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ userDetail.nickname || '-' }}</el-descriptions-item>
          <el-descriptions-item label="头像">
            <el-avatar v-if="userDetail.avatar_url" :src="userDetail.avatar_url" :size="40" />
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="年龄段">{{ userDetail.age_range || '-' }}</el-descriptions-item>
          <el-descriptions-item label="城市">{{ userDetail.city || '-' }}</el-descriptions-item>
          <el-descriptions-item label="职业">{{ userDetail.occupation || '-' }}</el-descriptions-item>
          <el-descriptions-item label="社交能量">{{ userDetail.social_energy || 50 }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ formatDate(userDetail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="最后活跃">{{ userDetail.last_active_at ? formatDate(userDetail.last_active_at) : '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 封禁信息 -->
      <el-card class="info-card" v-if="userDetail.is_banned">
        <template #header>封禁信息</template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="封禁原因">{{ userDetail.ban_reason || '-' }}</el-descriptions-item>
          <el-descriptions-item label="封禁到期">
            {{ userDetail.ban_expired_at ? formatDate(userDetail.ban_expired_at) : '永久封禁' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 日记统计 -->
      <el-card class="info-card">
        <template #header>日记统计</template>
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ diaryStats.total_count || 0 }}</div>
              <div class="stat-label">日记总数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ diaryStats.this_month_count || 0 }}</div>
              <div class="stat-label">本月日记</div>
            </div>
          </el-col>
        </el-row>
        <div class="emotion-chart" v-if="diaryStats.emotion_distribution">
          <div class="chart-title">情绪分布</div>
          <div class="emotion-tags">
            <el-tag v-for="(count, emotion) in diaryStats.emotion_distribution" :key="emotion" style="margin: 4px;">
              {{ emotion }}: {{ count }}
            </el-tag>
          </div>
        </div>
      </el-card>

      <!-- 社交数据 -->
      <el-card class="info-card">
        <template #header>社交数据</template>
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ socialStats.friend_count || 0 }}</div>
              <div class="stat-label">好友数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ socialStats.post_count || 0 }}</div>
              <div class="stat-label">动态数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ socialStats.treehole_count || 0 }}</div>
              <div class="stat-label">树洞数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ socialStats.comment_count || 0 }}</div>
              <div class="stat-label">评论数</div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 操作按钮 -->
      <el-card class="info-card" v-if="hasPermission('user:ban')">
        <template #header>操作</template>
        <div class="action-buttons">
          <el-button
            v-if="!userDetail.is_banned"
            type="danger"
            @click="handleBan"
          >
            封禁用户
          </el-button>
          <el-button
            v-if="userDetail.is_banned"
            type="success"
            @click="handleUnban"
          >
            解封用户
          </el-button>
          <el-button
            type="warning"
            @click="handleMinorMode"
          >
            {{ userDetail.is_minor ? '关闭青少年模式' : '开启青少年模式' }}
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 封禁对话框 -->
    <el-dialog v-model="banDialogVisible" title="封禁用户" width="500px">
      <el-form ref="banFormRef" :model="banForm" :rules="banRules" label-width="100px">
        <el-form-item label="封禁原因" prop="reason">
          <el-input
            v-model="banForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入封禁原因"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="封禁天数">
          <el-input-number v-model="banForm.duration_days" :min="1" :max="365" />
          <span class="ml-10 text-muted">不填则永久封禁</span>
        </el-form-item>
        <el-form-item label="通知用户">
          <el-switch v-model="banForm.notify_user" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="banDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmBan" :loading="processing">确认封禁</el-button>
      </template>
    </el-dialog>

    <!-- 解封对话框 -->
    <el-dialog v-model="unbanDialogVisible" title="解封用户" width="500px">
      <el-form ref="unbanFormRef" :model="unbanForm" :rules="unbanRules" label-width="100px">
        <el-form-item label="解封原因" prop="reason">
          <el-input
            v-model="unbanForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入解封原因"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="通知用户">
          <el-switch v-model="unbanForm.notify_user" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="unbanDialogVisible = false">取消</el-button>
        <el-button type="success" @click="confirmUnban" :loading="processing">确认解封</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import dayjs from 'dayjs'
import { getUserDetail, getUserDiaryStats, getUserSocialStats, banUser, unbanUser, setMinorMode } from '@/api/user'
import { useAdminStore } from '@/stores/admin'
import type { UserDetail, UserDiaryStats, UserSocialStats, BanUserRequest, UnbanUserRequest } from '@/types/user'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const processing = ref(false)
const userDetail = ref<UserDetail | null>(null)
const diaryStats = ref<UserDiaryStats>({
  total_count: 0,
  this_month_count: 0,
  emotion_distribution: {},
  recent_emotions: [],
})
const socialStats = ref<UserSocialStats>({
  friend_count: 0,
  post_count: 0,
  treehole_count: 0,
  comment_count: 0,
})

// 封禁对话框
const banDialogVisible = ref(false)
const banFormRef = ref<FormInstance>()
const banForm = reactive<BanUserRequest>({
  reason: '',
  duration_days: undefined,
  notify_user: true,
})
const banRules: FormRules = {
  reason: [
    { required: true, message: '请输入封禁原因', trigger: 'blur' },
    { min: 5, max: 500, message: '原因长度在5-500字符之间', trigger: 'blur' },
  ],
}

// 解封对话框
const unbanDialogVisible = ref(false)
const unbanFormRef = ref<FormInstance>()
const unbanForm = reactive<UnbanUserRequest>({
  reason: '',
  notify_user: true,
})
const unbanRules: FormRules = {
  reason: [
    { required: true, message: '请输入解封原因', trigger: 'blur' },
    { min: 5, max: 500, message: '原因长度在5-500字符之间', trigger: 'blur' },
  ],
}

function formatDate(date: string): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function hasPermission(permission: string) {
  return adminStore.hasPermission(permission)
}

function goBack() {
  router.push('/users')
}

async function fetchDetail() {
  loading.value = true
  try {
    const id = route.params.id as string
    userDetail.value = await getUserDetail(id)
    // 获取统计数据
    diaryStats.value = await getUserDiaryStats(id)
    socialStats.value = await getUserSocialStats(id)
  } catch (error) {
    console.error('获取用户详情失败', error)
  } finally {
    loading.value = false
  }
}

function handleBan() {
  banForm.reason = ''
  banForm.duration_days = undefined
  banForm.notify_user = true
  banDialogVisible.value = true
}

async function confirmBan() {
  const valid = await banFormRef.value?.validate()
  if (!valid) return

  processing.value = true
  try {
    await banUser(userDetail.value!.id, banForm)
    ElMessage.success('用户已封禁')
    banDialogVisible.value = false
    fetchDetail()
  } catch (error) {
    console.error('封禁用户失败', error)
  } finally {
    processing.value = false
  }
}

function handleUnban() {
  unbanForm.reason = ''
  unbanForm.notify_user = true
  unbanDialogVisible.value = true
}

async function confirmUnban() {
  const valid = await unbanFormRef.value?.validate()
  if (!valid) return

  processing.value = true
  try {
    await unbanUser(userDetail.value!.id, unbanForm)
    ElMessage.success('用户已解封')
    unbanDialogVisible.value = false
    fetchDetail()
  } catch (error) {
    console.error('解封用户失败', error)
  } finally {
    processing.value = false
  }
}

async function handleMinorMode() {
  const action = userDetail.value!.is_minor ? '关闭' : '开启'
  try {
    if (!userDetail.value!.is_minor) {
      const { value } = await ElMessageBox.prompt('请输入监护人手机号', '开启青少年模式', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        inputPattern: /^1[3-9]\d{9}$/,
        inputErrorMessage: '请输入正确的手机号',
      })
      await setMinorMode(userDetail.value!.id, { is_minor: true, guardian_phone: value })
    } else {
      await ElMessageBox.confirm('确定要关闭青少年模式吗？', '关闭青少年模式', { type: 'warning' })
      await setMinorMode(userDetail.value!.id, { is_minor: false })
    }
    ElMessage.success(`${action}青少年模式成功`)
    fetchDetail()
  } catch (error) {
    // 用户取消操作
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped lang="scss">
.user-detail {
  .page-title {
    font-size: 18px;
    font-weight: bold;
  }

  .detail-content {
    margin-top: 20px;
  }

  .info-card {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
  }

  .stat-item {
    text-align: center;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 4px;

    .stat-value {
      font-size: 24px;
      font-weight: bold;
      color: #409eff;
    }

    .stat-label {
      font-size: 14px;
      color: #909399;
      margin-top: 8px;
    }
  }

  .emotion-chart {
    margin-top: 16px;

    .chart-title {
      font-weight: bold;
      margin-bottom: 8px;
    }

    .emotion-tags {
      display: flex;
      flex-wrap: wrap;
    }
  }

  .action-buttons {
    display: flex;
    gap: 16px;
  }

  .ml-10 {
    margin-left: 10px;
  }

  .text-muted {
    color: #909399;
    font-size: 12px;
  }
}
</style>