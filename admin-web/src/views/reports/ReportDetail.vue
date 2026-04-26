<template>
  <div class="report-detail" v-loading="loading">
    <el-page-header @back="goBack">
      <template #content>
        <span class="page-title">举报详情</span>
      </template>
    </el-page-header>

    <div class="detail-content" v-if="reportDetail">
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>举报信息</span>
            <el-tag :type="statusType(reportDetail.status)">{{ statusText(reportDetail.status) }}</el-tag>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="举报ID">{{ reportDetail.id }}</el-descriptions-item>
          <el-descriptions-item label="举报类型">
            <el-tag>{{ reportTypeText(reportDetail.report_type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="内容类型">
            <el-tag type="info">{{ contentTypeText(reportDetail.content_type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(reportDetail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="举报原因" :span="2">{{ reportDetail.reason }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="info-card">
        <template #header>举报人信息</template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="昵称">{{ reportDetail.reporter_nickname || '匿名' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ reportDetail.reporter_phone || '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="info-card">
        <template #header>被举报内容</template>
        <div class="content-preview">
          <p class="content-text">{{ reportDetail.content_preview }}</p>
          <div v-if="reportDetail.content_images?.length" class="content-images">
            <el-image
              v-for="(img, index) in reportDetail.content_images"
              :key="index"
              :src="img"
              :preview-src-list="reportDetail.content_images"
              fit="cover"
              class="image-item"
            />
          </div>
        </div>
        <el-descriptions :column="2" border style="margin-top: 16px;">
          <el-descriptions-item label="被举报人">{{ reportDetail.reported_user_nickname || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ reportDetail.reported_user_phone || '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 处理表单 -->
      <el-card class="info-card" v-if="reportDetail.status === 'pending' && hasPermission('report:process')">
        <template #header>处理举报</template>
        <el-form ref="formRef" :model="processForm" :rules="formRules" label-width="100px">
          <el-form-item label="处理动作" prop="action">
            <el-radio-group v-model="processForm.action">
              <el-radio value="approve">通过举报</el-radio>
              <el-radio value="reject">驳回举报</el-radio>
              <el-radio value="ban_user">封禁用户</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="处理原因" prop="reason">
            <el-input
              v-model="processForm.reason"
              type="textarea"
              :rows="3"
              placeholder="请输入处理原因"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="隐藏内容" v-if="processForm.action === 'approve' || processForm.action === 'ban_user'">
            <el-switch v-model="processForm.hide_content" />
          </el-form-item>
          <el-form-item label="封禁天数" v-if="processForm.action === 'ban_user'">
            <el-input-number v-model="processForm.ban_duration_days" :min="1" :max="365" />
            <span class="ml-10 text-muted">不填则永久封禁</span>
          </el-form-item>
          <el-form-item label="通知举报人">
            <el-switch v-model="processForm.notify_reporter" />
          </el-form-item>
          <el-form-item label="通知被举报人">
            <el-switch v-model="processForm.notify_reported_user" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleProcess" :loading="processing">
              确认处理
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 处理结果 -->
      <el-card class="info-card" v-if="reportDetail.status !== 'pending'">
        <template #header>处理结果</template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="处理时间">{{ formatDate(reportDetail.processed_at || '') }}</el-descriptions-item>
          <el-descriptions-item label="处理结果">{{ reportDetail.process_result || '-' }}</el-descriptions-item>
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
import { getReportDetail, processReport } from '@/api/report'
import { useAdminStore } from '@/stores/admin'
import type { ReportDetail, ReportType, ContentType, ReportStatus, ProcessReportRequest } from '@/types/report'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const processing = ref(false)
const reportDetail = ref<ReportDetail | null>(null)
const formRef = ref<FormInstance>()

const processForm = reactive<ProcessReportRequest>({
  action: 'approve',
  reason: '',
  hide_content: true,
  ban_duration_days: undefined,
  notify_reporter: true,
  notify_reported_user: false,
})

const formRules: FormRules = {
  action: [{ required: true, message: '请选择处理动作', trigger: 'change' }],
  reason: [
    { required: true, message: '请输入处理原因', trigger: 'blur' },
    { min: 5, max: 500, message: '原因长度在5-500字符之间', trigger: 'blur' },
  ],
}

// 类型映射函数（同列表页）
function reportTypeText(type: ReportType): string {
  const map: Record<ReportType, string> = {
    porn: '色情低俗',
    ad: '广告骚扰',
    harassment: '恶意骚扰',
    abuse: '人身攻击',
    scam: '诈骗欺诈',
    self_harm: '自残自杀',
    other: '其他',
  }
  return map[type] || type
}

function contentTypeText(type: ContentType): string {
  const map: Record<ContentType, string> = {
    post: '动态',
    treehole_post: '树洞',
    comment: '评论',
    user: '用户',
  }
  return map[type] || type
}

function statusText(status: ReportStatus): string {
  const map: Record<ReportStatus, string> = {
    pending: '待处理',
    processing: '处理中',
    approved: '已通过',
    rejected: '已驳回',
  }
  return map[status] || status
}

function statusType(status: ReportStatus): string {
  const map: Record<ReportStatus, string> = {
    pending: 'danger',
    processing: 'warning',
    approved: 'success',
    rejected: 'info',
  }
  return map[status] || ''
}

function formatDate(date: string): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function hasPermission(permission: string) {
  return adminStore.hasPermission(permission)
}

function goBack() {
  router.push('/reports')
}

async function fetchDetail() {
  loading.value = true
  try {
    const id = route.params.id as string
    reportDetail.value = await getReportDetail(id)
  } catch (error) {
    console.error('获取举报详情失败', error)
    ElMessage.error('获取举报详情失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function handleProcess() {
  const valid = await formRef.value?.validate()
  if (!valid) return

  try {
    await ElMessageBox.confirm(
      `确定要执行"${processForm.action === 'approve' ? '通过举报' : processForm.action === 'reject' ? '驳回举报' : '封禁用户'}"操作吗？`,
      '确认操作',
      { type: 'warning' }
    )
  } catch {
    return
  }

  processing.value = true
  try {
    await processReport(reportDetail.value!.id, processForm)
    ElMessage.success('处理成功')
    router.push('/reports')
  } catch (error) {
    console.error('处理举报失败', error)
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
.report-detail {
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

  .content-preview {
    .content-text {
      background: #f5f7fa;
      padding: 12px;
      border-radius: 4px;
      line-height: 1.6;
      white-space: pre-wrap;
    }

    .content-images {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 10px;

      .image-item {
        width: 100px;
        height: 100px;
        border-radius: 4px;
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