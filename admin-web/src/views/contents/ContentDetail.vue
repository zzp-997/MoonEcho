<template>
  <div class="content-detail" v-loading="loading">
    <el-page-header @back="goBack">
      <template #content>
        <span class="page-title">内容详情</span>
      </template>
    </el-page-header>

    <div class="detail-content" v-if="contentDetail">
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>内容信息</span>
            <div>
              <el-tag type="info">{{ contentTypeText(contentDetail.content_type) }}</el-tag>
              <el-tag :type="statusType(contentDetail.status)" style="margin-left: 8px;">
                {{ statusText(contentDetail.status) }}
              </el-tag>
            </div>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="内容ID">{{ contentDetail.id }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(contentDetail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="话题标签">{{ contentDetail.topic_tag || '-' }}</el-descriptions-item>
          <el-descriptions-item label="举报次数">
            <el-tag v-if="contentDetail.report_count > 0" type="danger">{{ contentDetail.report_count }}</el-tag>
            <span v-else>0</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="info-card">
        <template #header>内容详情</template>
        <div class="content-preview">
          <p class="content-text">{{ contentDetail.content }}</p>
          <div v-if="contentDetail.image_urls?.length" class="content-images">
            <el-image
              v-for="(img, index) in contentDetail.image_urls"
              :key="index"
              :src="img"
              :preview-src-list="contentDetail.image_urls"
              fit="cover"
              class="image-item"
            />
          </div>
        </div>
      </el-card>

      <el-card class="info-card">
        <template #header>作者信息</template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="作者ID">{{ contentDetail.author_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ contentDetail.author_nickname || '匿名' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ contentDetail.author_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="匿名发布">
            <el-tag v-if="contentDetail.is_anonymous" type="warning">是</el-tag>
            <span v-else>否</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="info-card">
        <template #header>互动数据</template>
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ contentDetail.like_count || contentDetail.resonance_count || 0 }}</div>
              <div class="stat-label">{{ contentDetail.content_type === 'treehole_post' ? '共鸣数' : '点赞数' }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ contentDetail.comment_count || 0 }}</div>
              <div class="stat-label">评论数</div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 操作按钮 -->
      <el-card class="info-card" v-if="hasPermission('content:moderate')">
        <template #header>操作</template>
        <div class="action-buttons">
          <el-button
            v-if="contentDetail.status === 'active'"
            type="warning"
            @click="handleHide"
          >
            隐藏内容
          </el-button>
          <el-button
            v-if="contentDetail.status === 'hidden'"
            type="success"
            @click="handleShow"
          >
            显示内容
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { getContentDetail, updateContentStatus } from '@/api/content'
import { useAdminStore } from '@/stores/admin'
import type { ContentDetail, AdminContentType, ContentStatus } from '@/types/content'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const contentDetail = ref<ContentDetail | null>(null)

// 类型映射
function contentTypeText(type: AdminContentType): string {
  const map: Record<AdminContentType, string> = {
    post: '动态',
    treehole_post: '树洞',
  }
  return map[type] || type
}

function statusText(status: ContentStatus): string {
  const map: Record<ContentStatus, string> = {
    active: '正常',
    hidden: '已隐藏',
    deleted: '已删除',
  }
  return map[status] || status
}

function statusType(status: ContentStatus): string {
  const map: Record<ContentStatus, string> = {
    active: 'success',
    hidden: 'warning',
    deleted: 'info',
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
  router.push('/contents')
}

async function fetchDetail() {
  loading.value = true
  try {
    const type = route.params.type as AdminContentType
    const id = route.params.id as string
    contentDetail.value = await getContentDetail(type, id)
  } catch (error) {
    console.error('获取内容详情失败', error)
    ElMessage.error('获取内容详情失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function handleHide() {
  try {
    const { value } = await ElMessageBox.prompt('请输入隐藏原因', '隐藏内容', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPattern: /^.{5,200}$/,
      inputErrorMessage: '原因长度在5-200字符之间',
    })

    await updateContentStatus(contentDetail.value!.content_type, contentDetail.value!.id, {
      action: 'hide',
      reason: value,
    })
    ElMessage.success('内容已隐藏')
    fetchDetail()
  } catch (error) {
    // 用户取消操作
  }
}

async function handleShow() {
  try {
    await ElMessageBox.confirm('确定要显示该内容吗？', '显示内容', { type: 'info' })

    await updateContentStatus(contentDetail.value!.content_type, contentDetail.value!.id, { action: 'show' })
    ElMessage.success('内容已显示')
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
.content-detail {
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
      padding: 16px;
      border-radius: 4px;
      line-height: 1.8;
      white-space: pre-wrap;
      font-size: 15px;
    }

    .content-images {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;

      .image-item {
        width: 120px;
        height: 120px;
        border-radius: 4px;
      }
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

  .action-buttons {
    display: flex;
    gap: 16px;
  }
}
</style>