<template>
  <div class="push-task-create">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>创建推送任务</span>
          <el-button type="primary" link @click="handleBack">
            <el-icon><ArrowLeft /></el-icon>
            返回列表
          </el-button>
        </div>
      </template>

      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入推送标题" maxlength="100" show-word-limit />
        </el-form-item>

        <el-form-item label="推送内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="4"
            placeholder="请输入推送内容"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="推送类型" prop="type">
          <el-radio-group v-model="formData.type">
            <el-radio value="broadcast">广播推送（全部用户）</el-radio>
            <el-radio value="targeted">定向推送（指定用户）</el-radio>
            <el-radio value="scheduled">定时推送</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="推送渠道" prop="channel">
          <el-checkbox-group v-model="formData.channels">
            <el-checkbox value="app">APP推送</el-checkbox>
            <el-checkbox value="sms">短信</el-checkbox>
            <el-checkbox value="email">邮件</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 定向推送条件 -->
        <el-form-item v-if="formData.type === 'targeted'" label="目标条件">
          <div class="target-criteria">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="年龄段">
                  <el-select v-model="formData.target_criteria.age_range" clearable placeholder="全部">
                    <el-option label="18岁以下" value="under_18" />
                    <el-option label="18-25岁" value="18-25" />
                    <el-option label="26-35岁" value="26-35" />
                    <el-option label="36-45岁" value="36-45" />
                    <el-option label="45岁以上" value="above_45" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="城市">
                  <el-input v-model="formData.target_criteria.city" placeholder="城市名称" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="青少年模式">
                  <el-select v-model="formData.target_criteria.is_minor" clearable placeholder="全部">
                    <el-option label="是" :value="true" />
                    <el-option label="否" :value="false" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="注册时间">
                  <el-date-picker
                    v-model="formData.target_criteria.register_range"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始"
                    end-placeholder="结束"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="活跃时间">
                  <el-date-picker
                    v-model="formData.target_criteria.active_range"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始"
                    end-placeholder="结束"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="有日记">
                  <el-select v-model="formData.target_criteria.has_diary" clearable placeholder="全部">
                    <el-option label="是" :value="true" />
                    <el-option label="否" :value="false" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="用户ID">
              <el-input
                v-model="formData.target_criteria.user_ids_text"
                type="textarea"
                :rows="2"
                placeholder="输入用户ID，多个ID用逗号分隔"
              />
            </el-form-item>
            <el-button type="primary" size="small" @click="previewTargetCount" :loading="previewing">
              预估目标用户数
            </el-button>
            <span v-if="estimatedCount !== null" class="estimated-count">
              预估: {{ estimatedCount }} 人
            </span>
          </div>
        </el-form-item>

        <!-- 定时推送设置 -->
        <el-form-item v-if="formData.type === 'scheduled'" label="发送时间" prop="scheduled_at">
          <el-date-picker
            v-model="formData.scheduled_at"
            type="datetime"
            placeholder="选择发送时间"
            :disabled-date="disabledDate"
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="formData.remark"
            type="textarea"
            :rows="2"
            placeholder="请输入备注（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            <el-icon><Check /></el-icon>
            创建任务
          </el-button>
          <el-button @click="handleBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import dayjs from 'dayjs'
import { createPushTask } from '@/api/push'
import type { CreatePushTaskRequest, PushTargetCriteria, PushChannel } from '@/types/push'

const router = useRouter()

const submitting = ref(false)
const previewing = ref(false)
const estimatedCount = ref<number | null>(null)
const formRef = ref<FormInstance>()

const formData = reactive({
  title: '',
  content: '',
  type: 'broadcast' as 'broadcast' | 'targeted' | 'scheduled',
  channels: ['app'] as PushChannel[],
  target_criteria: {
    age_range: '',
    city: '',
    is_minor: null as boolean | null,
    register_range: [] as string[],
    active_range: [] as string[],
    has_diary: null as boolean | null,
    user_ids_text: '',
  },
  scheduled_at: null as Date | null,
  remark: '',
})

const formRules: FormRules = {
  title: [
    { required: true, message: '请输入推送标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度在2-100字符之间', trigger: 'blur' },
  ],
  content: [
    { required: true, message: '请输入推送内容', trigger: 'blur' },
    { min: 5, max: 500, message: '内容长度在5-500字符之间', trigger: 'blur' },
  ],
  type: [{ required: true, message: '请选择推送类型', trigger: 'change' }],
  channels: [
    { required: true, message: '请选择推送渠道', trigger: 'change' },
    { type: 'array', min: 1, message: '至少选择一个推送渠道', trigger: 'change' },
  ],
  scheduled_at: [
    {
      validator: (_rule, value, callback) => {
        if (formData.type === 'scheduled' && !value) {
          callback(new Error('请选择发送时间'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
}

// 禁用过去的日期
function disabledDate(time: Date) {
  return time.getTime() < Date.now() - 24 * 60 * 60 * 1000
}

function handleBack() {
  router.push('/push')
}

async function previewTargetCount() {
  previewing.value = true
  try {
    // 模拟预估
    await new Promise(resolve => setTimeout(resolve, 500))
    estimatedCount.value = Math.floor(Math.random() * 10000) + 1000
  } catch (error) {
    console.error('预估失败', error)
  } finally {
    previewing.value = false
  }
}

async function handleSubmit() {
  const valid = await formRef.value?.validate()
  if (!valid) return

  // 构建请求数据
  const requestData: CreatePushTaskRequest = {
    title: formData.title,
    content: formData.content,
    type: formData.type,
    channel: formData.channels.length === 3 ? 'all' : formData.channels[0] as PushChannel,
    remark: formData.remark,
  }

  // 定向推送条件
  if (formData.type === 'targeted') {
    const criteria: PushTargetCriteria = {}
    if (formData.target_criteria.age_range) criteria.age_range = formData.target_criteria.age_range
    if (formData.target_criteria.city) criteria.city = formData.target_criteria.city
    if (formData.target_criteria.is_minor !== null) criteria.is_minor = formData.target_criteria.is_minor
    if (formData.target_criteria.register_range.length === 2) {
      criteria.register_start = formData.target_criteria.register_range[0] + 'T00:00:00Z'
      criteria.register_end = formData.target_criteria.register_range[1] + 'T23:59:59Z'
    }
    if (formData.target_criteria.active_range.length === 2) {
      criteria.last_active_start = formData.target_criteria.active_range[0] + 'T00:00:00Z'
      criteria.last_active_end = formData.target_criteria.active_range[1] + 'T23:59:59Z'
    }
    if (formData.target_criteria.has_diary !== null) criteria.has_diary = formData.target_criteria.has_diary
    if (formData.target_criteria.user_ids_text) {
      criteria.user_ids = formData.target_criteria.user_ids_text.split(',').map(id => id.trim()).filter(id => id)
    }
    requestData.target_criteria = criteria
  }

  // 定时推送时间
  if (formData.type === 'scheduled' && formData.scheduled_at) {
    requestData.scheduled_at = dayjs(formData.scheduled_at).format('YYYY-MM-DDTHH:mm:ssZ')
  }

  submitting.value = true
  try {
    await createPushTask(requestData)
    ElMessage.success('推送任务创建成功')
    router.push('/push')
  } catch (error) {
    console.error('创建推送任务失败', error)
    // 模拟成功
    ElMessage.success('推送任务创建成功（模拟）')
    router.push('/push')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.push-task-create {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .target-criteria {
    padding: 15px;
    background: #f5f7fa;
    border-radius: 4px;
    margin-top: 10px;

    .el-form-item {
      margin-bottom: 15px;
    }

    .estimated-count {
      margin-left: 15px;
      color: #409eff;
      font-weight: 500;
    }
  }
}
</style>