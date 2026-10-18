<template>
    <div class="max-w-6xl mx-auto animate-fade-in">
        <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-black uppercase flex items-center gap-3">
                <i data-lucide="edit-3" class="w-6 h-6"></i>
                {{ isEditing ? 'Edit Record' : 'Create New Record' }}
            </h2>
            <button @click="$emit('cancel')" class="text-xs font-bold text-red-500 hover:text-red-700 uppercase tracking-widest">
                Cancel Operation
            </button>
        </div>

        <div class="bg-zinc-900 text-zinc-300 p-1 border-2 border-zinc-900 shadow-xl">
            <div class="border border-zinc-700 p-8 scanline relative">
                <!-- 装饰角标 -->
                <div class="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-yellow-500"></div>
                <div class="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-yellow-500"></div>
                <div class="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-yellow-500"></div>
                <div class="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-yellow-500"></div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <!-- 基础信息 -->
                    <div class="space-y-4 md:col-span-2">
                        <div class="space-y-1">
                            <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">文章标题</label>
                            <input v-model="form.title" class="w-full bg-zinc-800 border-b-2 border-zinc-600 focus:border-yellow-400 p-2 text-white font-bold outline-none transition-colors" placeholder="输入标题">
                        </div>
                        <div class="space-y-1">
                            <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">摘要</label>
                            <input v-model="form.summary" class="w-full bg-zinc-800 border-b-2 border-zinc-600 focus:border-yellow-400 p-2 text-white outline-none transition-colors" placeholder="用于首页展示的一句话摘要">
                        </div>
                    </div>
                    
                    <!-- 分类与标签 -->
                    <div class="space-y-4 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="space-y-1">
                            <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">分类</label>
                            <div class="flex flex-wrap gap-2">
                                <button v-for="cat in ['Python', '计算机基础', '后端开发', '云计算', '项目实践']"
                                    @click="form.category = cat"
                                    :class="['px-3 py-1 text-xs font-bold border transition-all', form.category === cat ? 'bg-yellow-400 text-black border-yellow-400' : 'border-zinc-600 text-zinc-500 hover:border-zinc-400']">
                                    {{ cat }}
                                </button>
                            </div>
                        </div>
                        <div class="space-y-1">
                            <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">标签（逗号分隔）</label>
                            <input v-model="form.tags" class="w-full bg-zinc-800 border-b-2 border-zinc-600 focus:border-yellow-400 p-2 font-mono text-sm outline-none transition-colors" placeholder="例如 FastAPI,MySQL">
                        </div>
                    </div>

                    <!-- 封面：优先使用随前端发布的静态资源 -->
                    <div class="space-y-3 md:col-span-2">
                        <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">文章封面</label>
                        <div class="grid grid-cols-1 md:grid-cols-[220px_1fr] gap-4">
                            <img :src="coverPreview" alt="封面预览" class="w-full aspect-video object-cover border-2 border-zinc-700">
                            <div class="space-y-3">
                                <div class="flex flex-wrap gap-2">
                                    <button
                                        v-for="preset in coverPresets"
                                        :key="preset.path"
                                        type="button"
                                        @click="form.cover_url = preset.path"
                                        :class="['px-3 py-1 text-xs font-bold border transition-colors', form.cover_url === preset.path ? 'bg-yellow-400 text-black border-yellow-400' : 'border-zinc-600 text-zinc-400 hover:border-zinc-300']"
                                    >
                                        {{ preset.label }}
                                    </button>
                                </div>
                                <input
                                    v-model="form.cover_url"
                                    class="w-full bg-zinc-800 border-b-2 border-zinc-600 focus:border-yellow-400 p-2 font-mono text-sm outline-none transition-colors"
                                    placeholder="留空使用分类默认封面，或填写 https:// 稳定图片地址"
                                >
                                <p class="text-xs text-zinc-500">静态路径如 images/covers/cloud-infra.jpg 会按 GitHub Pages 子路径自动解析；Render 上传地址不作为持久存储。</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 正文编辑 (Markdown Split View) -->
                <div class="space-y-2 mb-8">
                    <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex justify-between">
                        <span>Record Content (Markdown Supported)</span>
                        <span class="text-xs text-zinc-500">{{ imageUploadEnabled ? '动态上传已启用（临时存储）' : '演示模式：请使用静态图片或稳定外链' }}</span>
                    </label>
                    <div class="flex flex-wrap items-center gap-2 pb-2">
                        <span class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">插入内置图片</span>
                        <button
                            v-for="image in bodyImagePresets"
                            :key="image.path"
                            type="button"
                            @click="insertBodyImage(image)"
                            class="text-xs font-bold border border-zinc-600 px-2 py-1 text-zinc-300 hover:bg-yellow-400 hover:text-black hover:border-yellow-400"
                        >
                            {{ image.label }}
                        </button>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 h-[600px]">
                        <!-- Editor -->
                        <div class="relative h-full">
                            <textarea 
                                ref="editorRef"
                                v-model="form.content" 
                                @paste="handlePaste"
                                @drop.prevent="handleDrop"
                                class="w-full h-full bg-zinc-800 text-zinc-200 p-4 font-mono text-sm border-2 border-zinc-700 focus:border-yellow-400 outline-none resize-none"
                                placeholder="Write your markdown here..."
                            ></textarea>
                        </div>
                        <!-- Preview -->
                        <div class="h-full bg-white text-black p-4 border-2 border-zinc-700 overflow-y-auto prose prose-sm max-w-none">
                            <div v-html="compiledMarkdown"></div>
                        </div>
                    </div>
                </div>

                <!-- 底部操作栏 -->
                <div class="flex justify-end gap-4 border-t border-zinc-700 pt-6">
                    <button @click="save" class="relative px-6 py-3 font-bold uppercase tracking-widest text-sm transition-all duration-300 border-2 flex items-center justify-center gap-2 bg-yellow-400 text-black border-yellow-400 hover:bg-yellow-300 hover:border-yellow-300 shadow-[4px_4px_0_0_#000]" style="clip-path: polygon(0 0, 100% 0, 100% 85%, 95% 100%, 0 100%)">
                        <i data-lucide="save" class="w-4 h-4"></i>
                        TRANSMIT RECORD
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { reactive, ref, onMounted, onUpdated, nextTick, computed } from 'vue'
import axios from 'axios'
import { renderMarkdown, resolveImageUrl } from '../utils'
import { BODY_IMAGE_PRESETS, COVER_PRESETS, coverForCategory } from '../imageAssets'

const props = defineProps(['post', 'isEditing', 'token'])
const emit = defineEmits(['cancel', 'save'])

const editorRef = ref(null)
const form = reactive({ title: '', content: '', summary: '', category: 'Python', tags: '', cover_url: '' })
const coverPresets = COVER_PRESETS
const bodyImagePresets = BODY_IMAGE_PRESETS
const imageUploadEnabled = import.meta.env.VITE_IMAGE_UPLOAD_ENABLED === 'true'

const compiledMarkdown = computed(() => {
    return renderMarkdown(form.content || '')
})
const coverPreview = computed(() => resolveImageUrl(form.cover_url || coverForCategory(form.category)))

onMounted(() => {
    if (props.isEditing && props.post) {
        form.title = props.post.title
        form.content = props.post.content
        form.summary = props.post.summary || ''
        form.category = props.post.category || 'Python'
        form.tags = props.post.tags || ''
        form.cover_url = props.post.cover_url || ''
    }
    refreshIcons()
})

const refreshIcons = () => {
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons()
  })
}

onUpdated(refreshIcons)

const uploadFile = async (file) => {
    if (!imageUploadEnabled) {
        alert('演示版本已关闭动态图片上传。请使用内置静态图片或稳定的 https 图片地址。')
        return null
    }
    const formData = new FormData()
    formData.append('file', file)
    try {
        const res = await axios.post('/api/upload', formData, {
            headers: { Authorization: `Bearer ${props.token}` }
        })
        return res.data.url
    } catch (e) {
        console.error('Image upload failed', e)
        alert('Image upload failed')
        return null
    }
}

const insertAtCursor = (text) => {
    const textarea = editorRef.value
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const before = form.content.substring(0, start)
    const after = form.content.substring(end)
    form.content = before + text + after
    nextTick(() => {
        textarea.selectionStart = textarea.selectionEnd = start + text.length
        textarea.focus()
    })
}

const insertBodyImage = (image) => {
    insertAtCursor(`![${image.label}](${image.path})\n`)
}

const handlePaste = async (e) => {
    const items = (e.clipboardData || e.originalEvent.clipboardData).items
    for (const item of items) {
        if (item.kind === 'file' && item.type.startsWith('image/')) {
            e.preventDefault()
            if (!imageUploadEnabled) {
                alert('演示版本已关闭粘贴图片上传。请先把图片放入 frontend/public/images，或使用稳定的 https 图片地址。')
                return
            }
            const file = item.getAsFile()
            const url = await uploadFile(file)
            if (url) {
                insertAtCursor(`![Image](${url})`)
            }
        }
    }
}

const handleDrop = async (e) => {
    const files = e.dataTransfer.files
    if (files.length > 0) {
        const file = files[0]
        if (file.type.startsWith('image/')) {
            if (!imageUploadEnabled) {
                alert('演示版本已关闭拖拽图片上传。请使用内置静态图片或稳定的 https 图片地址。')
                return
            }
            const url = await uploadFile(file)
            if (url) {
                insertAtCursor(`![Image](${url})`)
            }
        }
    }
}

const save = () => {
    if (!form.title.trim() || !form.content.trim()) {
        alert('标题和正文不能为空')
        return
    }
    emit('save', { ...form })
}
</script>
