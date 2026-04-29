<template>
  <div class="crisis-detail" v-loading="loading">
    <el-page-header @back="goBack">
      <template #content>
        <span class="page-title">危机事件详情</span>
      </template>
    </el-page-header>

    <div class="detail-content" v-if="crisisDetail">
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>危机信息</span>
            <div>
              <el-tag :type="levelType(crisisDetail.level)" effect="dark" size="large">
                {{ levelText(crisisDetail.level) }}
              </el-tag>
              <el-tag :type="statusType(crisisDetail.status)" style="margin-left: 8px;">
                {{ statusText(crisisDetail.status) }}
              </el-tag>
            </div>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="消息ID">{{ crisisDetail.message_id }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(crisisDetail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="触发关键词" :span="2">
            <el-tag v-for="kw in crisisDetail.trigger_keywords" :key="kw" size="small" style="margin-right: 4px;">
              {{ kw }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="info-card">
        <template #header>用户信息</template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户ID">{{ crisisDetail.user_id }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ crisisDetail.user_nickname || '匿名' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ crisisDetail.user_phone }}</el-descriptions-item>
          <el-descriptions-item label="历史危机次数">
            <el-tag type="warning">{{ crisisDetail.user_crisis_history.total_crisis_events }} 次</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="info-card">
        <template #header>触发内容</template>
        <div class="message-content">
          <div class="message-item">
            <div class="message-label">用户消息：</div>
            <div class="message-text">{{ crisisDetail.trigger_message }}</div>
          </div>
          <div class="message-item" v-if="crisisDetail.ai_response">
            <div class="message-label">AI 回复：</div>
            <div class="message-text ai-response">{{ crisisDetail.ai_response }}</div>
          </div>
        </div>
      </el-card>

      <!-- 处理表单 -->
      <el-card class="info-card" v-if="crisisDetail.status === 'pending' && hasPermission('crisis:resolve')">
        <template #header>处理危机</template>
        <el-form ref="formRef" :model="resolveForm" :rules="formRules" label-width="100px">
          <el-form-item label="处理状态" prop="status">
            <el-radio-group v-model="resolveForm.status">
              <el-radio value="resolved">已解决</el-radio>
              <el-radio value="false_positive">误报</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="处理备注" prop="notes">
            <el-input
              v-model="resolveForm.notes"
              type="textarea"
              :rows="4"
              placeholder="请输入处理备注，如已联系用户、用户情况描述等"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="通知用户">
            <el-switch v-model="resolveForm.notify_user" />
            <span class="ml-10 text-muted">开启后会给用户发送关怀通知</span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleResolve" :loading="processing">
              确认处理
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 处理结果 -->
      <el-card class="info-card" v-if="crisisDetail.status !== 'pending'">
        <template #header>处理结果</template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="处理状态">{{ statusText(crisisDetail.status) }}</el-descriptions-item>
          <el-descriptions-item label="处理时间">{{ formatDate(crisisDetail.resolved_at || '') }}</el-descriptions-item>
          <el-descriptions-item label="处理备注" :span="2">{{ crisisDetail.resolution_notes || '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import dayjs from 'dayjs'
import { getCrisisDetail, resolveCrisis } from '@/api/crisis'
import { useAdminStore } from '@/stores/admin'
import type { CrisisDetail, CrisisLevel, CrisisStatus, ResolveCrisisRequest } from '@/types/crisis'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const processing = ref(false)
const crisisDetail = ref<CrisisDetail | null>(null)
const formRef = ref<FormInstance>()

const resolveForm = reactive<ResolveCrisisRequest>({
  status: 'resolved',
  notes: '',
  notify_user: true,
})

const formRules: FormRules = {
  status: [{ required: true, message: '请选择处理状态', trigger: 'change' }],
  notes: [
    { required: true, message: '请输入处理备注', trigger: 'blur' },
    { min: 5, max: 500, message: '备注长度在5-500字符之间', trigger: 'blur' },
  ],
}

// 类型映射
function levelText(level: CrisisLevel): string {
  const map: Record<CrisisLevel, string> = {
    high: '高危',
    medium: '中危',
    low: '低危',
  }
  return map[level] || level
}

function levelType(level: CrisisLevel): 'danger' | 'warning' | 'info' {
  const map: Record<CrisisLevel, 'danger' | 'warning' | 'info'> = {
    high: 'danger',
    medium: 'warning',
    low: 'info',
  }
  return map[level] || 'info'
}

function statusText(status: CrisisStatus): string {
  const map: Record<CrisisStatus, string> = {
    pending: '待处理',
    intervening: '处理中',
    resolved: '已解决',
    false_positive: '误报',
  }
  return map[status] || status
}

function statusType(status: CrisisStatus): 'danger' | 'warning' | 'success' | 'info' {
  const map: Record<CrisisStatus, 'danger' | 'warning' | 'success' | 'info'> = {
    pending: 'danger',
    intervening: 'warning',
    resolved: 'success',
    false_positive: 'info',
  }
  return map[status] || 'info'
}

function formatDate(date: string): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function hasPermission(permission: string) {
  return adminStore.hasPermission(permission)
}

function goBack() {
  router.push('/crisis')
}

async function fetchDetail() {
  loading.value = true
  try {
    const id = route.params.id as string
    crisisDetail.value = await getCrisisDetail(id)
  } catch (error) {
    console.error('获取危机详情失败', error)
    ElMessage.error('获取危机详情失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function handleResolve() {
  const valid = await formRef.value?.validate()
  if (!valid) return

  try {
    await ElMessageBox.confirm(
      `确定要标记为"${resolveForm.status === 'resolved' ? '已解决' : '误报'}"吗？`,
      '确认操作',
      { type: 'warning' }
    )
  } catch {
    return
  }

  processing.value = true
  try {
    await resolveCrisis(crisisDetail.value!.message_id, resolveForm)
    ElMessage.success('处理成功')
    router.push('/crisis')
  } catch (error) {
    console.error('处理危机失败', error)
    ElMessage.error('处理失败，请稍后重试')
  } finally {
    processing.value = false
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped lang="scss">
.crisis-detail {
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

  .message-content {
    .message-item {
      margin-bottom: 16px;

      &:last-child {
        margin-bottom: 0;
      }

      .message-label {
        font-weight: bold;
        margin-bottom: 8px;
        color: #606266;
      }

      .message-text {
        background: #f5f7fa;
        padding: 12px;
        border-radius: 4px;
        line-height: 1.6;
        white-space: pre-wrap;

        &.ai-response {
          background: #ecf5ff;
          color: #409eff;
        }
      }
    }
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