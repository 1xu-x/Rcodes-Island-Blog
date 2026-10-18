<template>
    <div v-if="modelValue" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
        <div class="bg-zinc-50 w-full max-w-2xl border-2 border-zinc-600 relative shadow-[0_0_50px_rgba(0,0,0,0.5)]"
            style="clip-path: polygon(0 0, 100% 0, 100% 95%, 95% 100%, 0 100%)">
            <div class="bg-zinc-900 text-white px-6 py-3 flex justify-between items-center">
                <div class="flex items-center gap-2">
                    <i data-lucide="terminal" class="w-4 h-4 text-yellow-400"></i>
                    <span class="font-mono font-bold tracking-widest uppercase">IDENTITY VERIFICATION</span>
                </div>
                <button @click="close" class="hover:text-yellow-400 transition-colors"><i data-lucide="x" class="w-5 h-5"></i></button>
            </div>
            <div class="p-8">
                <form @submit.prevent="isRegistering ? register() : login()" class="space-y-6">
                    <div class="text-center mb-8">
                        <div class="w-16 h-16 bg-zinc-100 rounded-full mx-auto mb-4 border-2 border-zinc-900 overflow-hidden">
                            <img :src="avatarImage" alt="站点头像" class="w-full h-full object-cover">
                        </div>
                        <p class="text-sm font-bold text-zinc-500 tracking-widest">{{ isRegistering ? '创建新账号' : '登录后即可点赞和评论' }}</p>
                    </div>
                    
                    <div class="space-y-2">
                        <label class="text-xs font-bold text-zinc-400 uppercase">用户名</label>
                        <input v-model="authForm.username" class="w-full bg-zinc-100 border-2 border-zinc-200 p-3 font-mono text-xl focus:border-yellow-400 focus:outline-none transition-colors" placeholder="3-32 位字母/数字/下划线">
                    </div>
                    <div class="space-y-2">
                        <label class="text-xs font-bold text-zinc-400 uppercase">密码</label>
                        <input type="password" v-model="authForm.password" class="w-full bg-zinc-100 border-2 border-zinc-200 p-3 font-mono text-xl focus:border-yellow-400 focus:outline-none transition-colors" placeholder="至少 6 位">
                    </div>

                    <p v-if="formError" class="text-sm text-red-600 font-bold">{{ formError }}</p>
                    <p v-if="formSuccess" class="text-sm text-emerald-600 font-bold">{{ formSuccess }}</p>

                    <div class="flex justify-between items-center pt-4">
                        <a @click="toggleMode" class="text-xs font-bold text-zinc-500 cursor-pointer hover:text-black underline">
                            {{ isRegistering ? '已有账号？去登录' : '没有账号？立即注册' }}
                        </a>
                        <button type="submit" class="relative px-6 py-3 font-bold uppercase tracking-widest text-sm transition-all duration-300 border-2 flex items-center justify-center gap-2 bg-zinc-900 text-white border-zinc-900 hover:bg-zinc-800" style="clip-path: polygon(0 0, 100% 0, 100% 85%, 95% 100%, 0 100%)">
                            {{ isRegistering ? '注册' : '登录' }}
                        </button>
                    </div>
                </form>
            </div>
            <div class="absolute bottom-0 right-0 w-4 h-4 bg-yellow-400"></div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, onUpdated, nextTick } from 'vue'
import axios from 'axios'
import { assetUrl } from '../utils'
import { AVATAR_IMAGE } from '../imageAssets'

const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue', 'login-success'])

const isRegistering = ref(false)
const authForm = reactive({ username: '', password: '' })
const formError = ref('')
const formSuccess = ref('')
const avatarImage = assetUrl(AVATAR_IMAGE)

const close = () => emit('update:modelValue', false)

const formatDetail = (detail) => {
  if (Array.isArray(detail)) {
    return detail.map(item => item.msg || JSON.stringify(item)).join('；')
  }
  return detail || '请求失败'
}

const validateForm = () => {
  formError.value = ''
  formSuccess.value = ''
  const username = authForm.username.trim()
  if (username.length < 3 || username.length > 32) {
    formError.value = '用户名长度需为 3-32 个字符'
    return false
  }
  if (authForm.password.length < 6) {
    formError.value = '密码至少 6 位'
    return false
  }
  return true
}

const toggleMode = () => {
  isRegistering.value = !isRegistering.value
  formError.value = ''
  formSuccess.value = ''
}

const login = async () => {
  if (!validateForm()) return
  try {
    const formData = new FormData()
    formData.append('username', authForm.username.trim())
    formData.append('password', authForm.password)
    const response = await axios.post('/api/token', formData)
    formSuccess.value = '登录成功'
    emit('login-success', response.data.access_token)
    close()
    authForm.username = ''
    authForm.password = ''
  } catch (error) {
    formError.value = '登录失败：' + formatDetail(error.response?.data?.detail)
  }
}

const register = async () => {
  if (!validateForm()) return
  try {
    await axios.post('/api/register', {
      username: authForm.username.trim(),
      password: authForm.password,
    })
    formSuccess.value = '注册成功，请登录'
    isRegistering.value = false
  } catch (error) {
    formError.value = '注册失败：' + formatDetail(error.response?.data?.detail)
  }
}

// Ensure icons render when modal opens
onUpdated(() => {
    if (props.modelValue) {
        nextTick(() => {
            if (window.lucide) window.lucide.createIcons()
        })
    }
})
</script>
