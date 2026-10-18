<template>
    <div class="grid grid-cols-12 gap-8 animate-fade-in">
        <!-- 左侧面板 -->
        <aside class="col-span-12 lg:col-span-3 flex flex-col gap-8">
            <!-- Profile Card -->
            <div class="bg-white border-2 border-zinc-900 p-6 relative shadow-[8px_8px_0_0_rgba(0,0,0,0.1)] transition-transform hover:-translate-y-1">
                <div :class="['absolute top-0 left-0 text-xs font-bold px-2 py-1 border-r-2 border-b-2 border-zinc-900', user ? 'bg-yellow-400' : 'bg-zinc-200']">
                    ID: {{ user ? 'PRTS-001' : 'GUEST-000' }}
                </div>
                <div class="mt-6 mb-4">
                    <div class="w-20 h-20 bg-zinc-100 border-2 border-zinc-900 rounded-full overflow-hidden mb-4">
                        <img :src="avatarImage" alt="Code Journey 站点头像" class="w-full h-full object-cover">
                    </div>
                    <h2 class="text-3xl font-black uppercase leading-none">
                        {{ user ? user.username : '访客' }}
                    </h2>
                    <p class="text-xs font-bold text-zinc-400 mt-1 tracking-widest">
                        {{ user?.role === 'admin' ? '管理员 · 可发布文章' : user ? '已登录读者' : '未登录，仅可浏览' }}
                    </p>
                </div>
                <div class="h-[2px] w-full bg-zinc-900 mb-4"></div>
                <div class="flex justify-between items-center text-xs font-mono">
                    <span class="text-zinc-500">TOTAL LOGS</span>
                    <span class="font-bold">{{ totalPosts }}</span>
                </div>
            </div>
            
            <!-- Tags Cloud -->
            <div class="bg-zinc-900 text-white p-6 shadow-[8px_8px_0_0_rgba(0,0,0,0.1)]" style="clip-path: polygon(0 0, 100% 0, 100% 90%, 90% 100%, 0 100%)">
                <div class="flex justify-between items-center mb-4 border-b border-zinc-700 pb-2">
                    <span class="text-xs font-bold text-yellow-400">HOT TAGS</span>
                    <i data-lucide="tag" class="w-3.5 h-3.5 text-yellow-400"></i>
                </div>
                <div class="flex flex-wrap gap-2">
                    <button 
                        v-for="tag in uniqueTags" 
                        :key="tag"
                        @click="$emit('search', { q: tag, sortBy: 'date', order: 'desc' })"
                        class="text-xs font-mono px-2 py-1 border border-zinc-600 hover:bg-yellow-400 hover:text-black hover:border-yellow-400 transition-colors"
                    >
                        #{{ tag }}
                    </button>
                    <span v-if="uniqueTags.length === 0" class="text-zinc-500 text-xs italic">No tags found in current view</span>
                </div>
            </div>

            <!-- Hot Articles (Top Views from current list) -->
            <div class="bg-white border-2 border-zinc-900 p-6 shadow-[8px_8px_0_0_rgba(0,0,0,0.1)]">
                <div class="text-[10px] font-bold text-zinc-500 mb-4 uppercase tracking-wider flex items-center justify-between">
                    <span>Trending Now</span>
                    <i data-lucide="flame" class="w-3 h-3 text-red-500"></i>
                </div>
                <div class="space-y-4">
                    <div 
                        v-for="post in topPosts" 
                        :key="post.id" 
                        class="group cursor-pointer"
                        @click="$emit('open-detail', post)"
                    >
                        <div class="text-xs font-bold text-zinc-400 mb-1">{{ post.date }}</div>
                        <div class="font-bold text-sm leading-tight group-hover:text-yellow-600 transition-colors line-clamp-2">
                            {{ post.title }}
                        </div>
                        <div class="flex items-center gap-2 mt-1 text-[10px] text-zinc-500">
                            <i data-lucide="eye" class="w-3 h-3"></i> {{ post.views }}
                        </div>
                    </div>
                    <div v-if="topPosts.length === 0" class="text-zinc-400 text-xs italic">No data available</div>
                </div>
            </div>
        </aside>

        <!-- 中间文章流 -->
        <section class="col-span-12 lg:col-span-6 space-y-12">
            <div class="flex flex-col gap-6 border-b-4 border-zinc-900 pb-6 mb-8">
                <div class="flex justify-between items-end">
                    <div>
                        <div class="text-4xl md:text-6xl font-black text-zinc-900 leading-none tracking-tighter">
                            最新文章
                        </div>
                        <div class="text-sm font-mono font-bold text-zinc-500 tracking-widest uppercase mt-2">
                            CODE JOURNEY LOGS
                        </div>
                    </div>
                    <button v-if="user?.role === 'admin'" @click="$emit('open-editor')" class="mb-2 relative px-6 py-3 font-bold uppercase tracking-widest text-sm transition-all duration-300 border-2 flex items-center justify-center gap-2 bg-yellow-400 text-black border-yellow-400 hover:bg-yellow-300 hover:border-yellow-300 shadow-[4px_4px_0_0_#000]" style="clip-path: polygon(0 0, 100% 0, 100% 85%, 95% 100%, 0 100%)">
                        <i data-lucide="plus" class="w-4 h-4"></i> 发布文章
                    </button>
                </div>

                <div class="flex flex-wrap gap-2">
                    <button
                        v-for="cat in categories"
                        :key="cat || 'all'"
                        @click="selectCategory(cat)"
                        :class="['px-3 py-1 text-xs font-bold border-2 uppercase', selectedCategory === cat ? 'bg-zinc-900 text-white border-zinc-900' : 'bg-white border-zinc-300 hover:border-zinc-900']"
                    >
                        {{ cat || '全部' }}
                    </button>
                </div>

                <!-- 搜索和排序栏 -->
                <div class="flex flex-col md:flex-row gap-4">
                    <div class="flex-1 flex gap-2">
                        <div class="relative flex-1">
                            <input 
                                v-model="searchQuery" 
                                @keyup.enter="handleSearch"
                                type="text" 
                                placeholder="按标题搜索文章..."
                                class="w-full bg-white border-2 border-zinc-300 p-3 pl-10 font-mono text-sm focus:border-zinc-900 focus:outline-none transition-colors"
                            >
                            <i data-lucide="search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400"></i>
                        </div>
                        <button @click="handleSearch" class="bg-zinc-900 text-white px-6 font-bold uppercase hover:bg-zinc-700 transition-colors">
                            SEARCH
                        </button>
                    </div>
                    <div class="flex gap-2">
                        <select v-model="sortBy" @change="handleSearch" class="bg-white border-2 border-zinc-300 p-3 font-mono text-sm focus:border-zinc-900 focus:outline-none cursor-pointer uppercase">
                            <option value="date">Date</option>
                            <option value="views">Views</option>
                            <option value="likes">Likes</option>
                        </select>
                        <button @click="toggleOrder" class="bg-white border-2 border-zinc-300 p-3 hover:bg-zinc-100 transition-colors" title="Toggle Order">
                            <i :data-lucide="sortOrder === 'desc' ? 'arrow-down' : 'arrow-up'" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>
            </div>

            <div class="space-y-8">
                <div v-if="loading" class="text-center py-20">Loading...</div>
                <div v-else-if="posts.length === 0" class="text-center py-20 border-2 border-dashed border-zinc-300 text-zinc-400 font-mono">
                    暂无文章 <br/> <span class="text-xs">换个关键词，或等待管理员发布</span>
                </div>
                
                <article 
                    v-else 
                    v-for="(post, index) in posts" 
                    :key="post.id" 
                    @click="$emit('open-detail', post)"
                    class="group relative bg-white border-2 border-transparent hover:border-zinc-900 transition-all duration-300 p-8 shadow-sm hover:shadow-[8px_8px_0_0_#000] cursor-pointer"
                >
                    <!-- 装饰编号 -->
                    <div class="absolute top-0 right-4 text-9xl font-black text-zinc-50 opacity-0 group-hover:opacity-100 transition-opacity duration-300 select-none pointer-events-none -z-10">
                        {{ String(index + 1).padStart(2, '0') }}
                    </div>

                    <div class="flex gap-4 items-baseline mb-2">
                        <span class="text-xs font-black bg-black text-white px-2 py-1 uppercase">{{ post.category || 'Python' }}</span>
                        <span class="text-xs font-mono font-bold text-zinc-400">{{ post.created_at || `${post.year}-${post.date}` }}</span>
                        <span class="text-xs font-bold text-zinc-500">BY {{ post.owner ? post.owner.username : 'UNKNOWN' }}</span>
                    </div>

                    <div class="mb-4 h-48 border-2 border-zinc-900 bg-zinc-100 overflow-hidden">
                        <img
                            :src="post.cover_url ? resolveImageUrl(post.cover_url) : assetUrl(coverForCategory(post.category))"
                            :alt="`${post.title} 封面`"
                            class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                            loading="lazy"
                        >
                    </div>

                    <h3 class="text-3xl font-bold mb-2 leading-tight group-hover:text-zinc-700 transition-colors">
                        {{ post.title }}
                    </h3>
                    
                    <div class="h-1 w-12 bg-yellow-400 mb-6 mt-4"></div>

                    <p class="text-zinc-600 leading-relaxed mb-6 font-medium line-clamp-3 whitespace-pre-line">{{ post.summary || stripHtml(post.content) }}</p>

                    <div class="flex justify-between items-center">
                        <div class="flex gap-4 items-center">
                            <div class="flex gap-2">
                                <span 
                                    v-for="tag in (post.tags ? post.tags.split(',') : [])" 
                                    :key="tag" 
                                    @click.stop="searchByTag(tag)"
                                    class="text-[10px] font-bold text-zinc-400 border border-zinc-200 px-2 py-1 rounded-full uppercase cursor-pointer hover:bg-zinc-100 hover:text-zinc-900 hover:border-zinc-900 transition-colors"
                                >
                                    #{{ tag }}
                                </span>
                            </div>
                            <div class="flex gap-3 text-xs font-mono text-zinc-400">
                                <span class="flex items-center gap-1"><i data-lucide="eye" class="w-3 h-3"></i> {{ post.views || 0 }}</span>
                                <span class="flex items-center gap-1"><i data-lucide="thumbs-up" class="w-3 h-3"></i> {{ post.likes || 0 }}</span>
                                <span class="flex items-center gap-1"><i data-lucide="message-square" class="w-3 h-3"></i> {{ post.comment_count || 0 }}</span>
                            </div>
                        </div>
                        <div class="bg-yellow-400 text-black p-2 group-hover:bg-black group-hover:text-white transition-colors">
                            <i data-lucide="chevron-right" class="w-5 h-5"></i>
                        </div>
                    </div>
                </article>

                <!-- Pagination -->
                <div v-if="totalPages > 1" class="flex justify-center items-center gap-4 pt-8 border-t-2 border-zinc-100">
                    <button 
                        @click="$emit('page-change', currentPage - 1)" 
                        :disabled="currentPage === 1"
                        class="p-2 border-2 border-zinc-300 hover:border-zinc-900 disabled:opacity-30 disabled:hover:border-zinc-300 transition-colors"
                    >
                        <i data-lucide="chevron-left" class="w-5 h-5"></i>
                    </button>
                    
                    <div class="font-mono font-bold text-sm">
                        PAGE {{ currentPage }} / {{ totalPages }}
                    </div>

                    <button 
                        @click="$emit('page-change', currentPage + 1)" 
                        :disabled="currentPage === totalPages"
                        class="p-2 border-2 border-zinc-300 hover:border-zinc-900 disabled:opacity-30 disabled:hover:border-zinc-300 transition-colors"
                    >
                        <i data-lucide="chevron-right" class="w-5 h-5"></i>
                    </button>
                </div>
            </div>
        </section>
        
        <!-- 右侧装饰 -->
        <aside class="hidden lg:block col-span-3 relative">
            <!-- Empty to preserve layout -->
        </aside>
    </div>
</template>

<script setup>
import { onMounted, onUpdated, nextTick, ref, watch, computed } from 'vue'
import { stripHtml, assetUrl, resolveImageUrl } from '../utils'
import { AVATAR_IMAGE, coverForCategory } from '../imageAssets'

const props = defineProps(['posts', 'loading', 'user', 'initialQuery', 'currentPage', 'totalPosts', 'pageSize', 'initialCategory'])
const emit = defineEmits(['open-detail', 'open-editor', 'search', 'page-change'])

const searchQuery = ref(props.initialQuery || '')
const sortBy = ref('date')
const sortOrder = ref('desc')
const selectedCategory = ref(props.initialCategory || '')
const categories = ['', 'Python', '计算机基础', '后端开发', '云计算', '项目实践']
const avatarImage = assetUrl(AVATAR_IMAGE)

const totalPages = computed(() => {
    return Math.ceil((props.totalPosts || 0) / (props.pageSize || 10))
})

watch(() => props.initialQuery, (newVal) => {
    if (newVal !== undefined) {
        searchQuery.value = newVal
    }
})

const handleSearch = () => {
    emit('search', {
        q: searchQuery.value,
        category: selectedCategory.value,
        sortBy: sortBy.value,
        order: sortOrder.value
    })
}

const selectCategory = (cat) => {
    selectedCategory.value = cat
    handleSearch()
}

const toggleOrder = () => {
    sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
    handleSearch()
}

const searchByTag = (tag) => {
    searchQuery.value = tag
    handleSearch()
}

// Computed properties for sidebar
const uniqueTags = computed(() => {
    const tags = new Set()
    if (props.posts) {
        props.posts.forEach(post => {
            if (post.tags) {
                // Handle both string "tag1, tag2" and array formats if any
                const postTags = typeof post.tags === 'string' 
                    ? post.tags.split(',').map(t => t.trim()).filter(t => t)
                    : post.tags
                postTags.forEach(tag => tags.add(tag))
            }
        })
    }
    return Array.from(tags).slice(0, 15) // Limit to 15 tags
})

const topPosts = computed(() => {
    if (!props.posts) return []
    // Create a copy to sort
    return [...props.posts]
        .sort((a, b) => (b.views || 0) - (a.views || 0))
        .slice(0, 5) // Top 5
})

const refreshIcons = () => {
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons()
  })
}

onMounted(refreshIcons)
onUpdated(refreshIcons)
</script>
