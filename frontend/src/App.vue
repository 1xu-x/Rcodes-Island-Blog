<template>
  <div id="app" class="bg-[#f2f2f2] text-zinc-900 overflow-x-hidden selection:bg-yellow-400 selection:text-black min-h-screen font-sans">
    <!-- 背景层 -->
    <div class="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div class="absolute top-[10%] -left-[5%] text-[16vw] font-black text-zinc-200/50 leading-none select-none tracking-tighter opacity-50" style="writing-mode: vertical-rl">
            CODE
        </div>
        
        <!-- 几何装饰 -->
        <div class="absolute top-0 right-[20%] w-[1px] h-screen bg-zinc-300"></div>
        <div class="absolute bottom-10 right-10 w-32 h-32 bg-yellow-400 mix-blend-multiply opacity-50 z-0"></div>
    </div>

    <!-- 顶部导航 -->
    <header :class="['fixed top-0 left-0 w-full z-50 transition-all duration-300', scrolled ? 'py-2 bg-white/90 backdrop-blur-md border-b border-zinc-200' : 'py-6 bg-transparent']">
        <div class="w-full mx-auto px-6 flex justify-between items-center">
            <!-- Logo / Home Button -->
            <div @click="switchView('list')" class="flex items-center gap-4 cursor-pointer group">
                <div class="w-10 h-10 bg-black text-white flex items-center justify-center font-bold text-xl transition-transform group-hover:scale-110" style="clip-path: polygon(0 0, 100% 0, 100% 75%, 75% 100%, 0 100%)">
                    <span class="font-mono">C</span>
                </div>
                <div class="leading-none">
                    <h1 class="text-xl font-black tracking-tighter uppercase group-hover:text-zinc-600 transition-colors">Code Journey</h1>
                    <div class="flex items-center gap-2">
                        <span class="text-[10px] font-bold tracking-[0.3em] text-zinc-500">技术成长博客</span>
                        <span v-if="user?.role === 'admin'" class="text-[10px] bg-yellow-400 text-black px-1 font-bold">ADMIN</span>
                    </div>
                </div>
            </div>

            <nav class="flex items-center gap-4 md:gap-6 text-xs md:text-sm font-bold">
                <button @click="switchView('list')" :class="currentView === 'list' ? 'text-yellow-600' : 'hover:text-zinc-600'">文章</button>
                <button @click="switchView('about')" :class="currentView === 'about' ? 'text-yellow-600' : 'hover:text-zinc-600'">关于我</button>
                <button v-if="user?.role === 'admin'" @click="openEditor(null)" :class="currentView === 'editor' ? 'text-yellow-600' : 'hover:text-zinc-600'">文章管理</button>
            </nav>

            <!-- User Status -->
            <div class="flex items-center gap-4">
                <div class="text-right hidden sm:block">
                    <div class="text-xs font-bold text-zinc-900">
                        {{ user ? user.username : 'GUEST USER' }}
                    </div>
                    <div class="text-[10px] font-mono bg-zinc-200 px-1 inline-block">
                        {{ user?.role === 'admin' ? 'ROLE: ADMIN' : user ? 'ROLE: USER' : 'GUEST' }}
                    </div>
                </div>
                
                <button v-if="user" @click="logout" class="p-2 border-2 border-zinc-900 bg-zinc-900 text-white hover:bg-red-600 hover:border-red-600 transition-colors" title="Logout">
                    <i data-lucide="unlock" class="w-5 h-5"></i>
                </button>
                <button v-else @click="isLoginOpen = true" class="p-2 border-2 border-zinc-900 hover:bg-yellow-400 transition-colors" title="Login">
                    <i data-lucide="lock" class="w-5 h-5"></i>
                </button>
            </div>
        </div>
    </header>

    <!-- 主内容容器 -->
    <main class="relative z-10 pt-32 pb-20 px-6 w-full mx-auto min-h-[80vh]">
        
        <!-- ================= VIEW: LIST (列表页) ================= -->
        <PostList 
            v-if="currentView === 'list'"
            :posts="posts"
            :loading="loading"
            :user="user"
            :initial-query="currentSearchQuery"
            :initial-category="currentCategory"
            :current-page="currentPage"
            :total-posts="totalPosts"
            :page-size="pageSize"
            @open-detail="openDetail"
            @open-editor="openEditor(null)"
            @search="handleSearch"
            @page-change="handlePageChange"
        />

        <!-- ================= VIEW: DETAIL (详情页) ================= -->
        <PostDetail 
            v-else-if="currentView === 'detail' && activePost"
            :post="activePost"
            :user="user"
            @back="switchView('list')"
            @edit="openEditor(activePost)"
            @delete="deletePost(activePost.id)"
            @like="likePost(activePost)"
            @add-comment="addComment"
            @delete-comment="(commentId) => deleteComment(activePost, commentId)"
            @search-tag="handleTagSearch"
        />

        <!-- ================= VIEW: EDITOR (编辑器) ================= -->
        <PostEditor 
            v-else-if="currentView === 'editor' && user?.role === 'admin'"
            :post="activePost"
            :is-editing="isEditing"
            :token="token"
            @cancel="cancelEdit"
            @save="handleSavePost"
        />

        <AboutPage v-else-if="currentView === 'about'" />

    </main>

    <!-- Footer -->
    <footer class="bg-zinc-900 text-zinc-400 py-8 px-6 relative overflow-hidden mt-auto">
        <div class="absolute top-0 left-0 w-full h-2 bg-[repeating-linear-gradient(45deg,#eab308,#eab308_20px,#000_20px,#000_40px)]"></div>
        <div class="w-full mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
            <div class="col-span-2">
                <h2 class="text-2xl font-black text-white uppercase tracking-tighter mb-4">Code Journey</h2>
                <p class="text-xs leading-relaxed max-w-md font-mono text-zinc-500">
                    技术成长博客 · 记录 Python、后端开发与云计算实践。二次开发自开源项目 Rcodes Island Blog（MIT）。
                </p>
            </div>
            <div class="text-right flex flex-col justify-between md:col-start-4">
                <div class="text-4xl font-black text-zinc-800">2026</div>
            </div>
        </div>
    </footer>

    <!-- Login Modal -->
    <LoginModal 
        v-model="isLoginOpen"
        @login-success="handleLoginSuccess"
    />

    <!-- Music Player Ball -->
    <MusicPlayer />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, onUpdated } from 'vue'
import axios from 'axios'
import PostList from './components/PostList.vue'
import PostDetail from './components/PostDetail.vue'
import PostEditor from './components/PostEditor.vue'
import LoginModal from './components/LoginModal.vue'
import MusicPlayer from './components/MusicPlayer.vue'
import AboutPage from './components/AboutPage.vue'

// 状态
const posts = ref([])
const loading = ref(false)
const token = ref(localStorage.getItem('token') || '')
const user = ref(null)
const isLoginOpen = ref(false)
const scrolled = ref(false)
const currentSearchQuery = ref('')
const currentCategory = ref('')
const currentPage = ref(1)
const totalPosts = ref(0)
const pageSize = 10
const currentSort = ref({ sortBy: 'date', order: 'desc' })

// 视图状态
const currentView = ref('list') // 'list', 'detail', 'editor'
const activePost = ref(null)
const isEditing = ref(false)
const editingId = ref(null)

// 监听滚动
window.addEventListener('scroll', () => {
  scrolled.value = window.scrollY > 50
})

// 视图切换
const switchView = (view) => {
  currentView.value = view
  window.scrollTo(0, 0)
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons()
  })
}

const openDetail = async (post) => {
  activePost.value = post
  switchView('detail')
  
  try {
    // Fetch fresh post data (increments view count)
    const config = {}
    if (token.value) {
      config.headers = { Authorization: `Bearer ${token.value}` }
    }
    const res = await axios.get(`/api/posts/${post.id}`, config)
    // Merge new data but keep existing properties if any (though res.data should be complete)
    activePost.value = { ...activePost.value, ...res.data }
    
    // Sync updated data (views, etc) back to the list
    const idx = posts.value.findIndex(p => p.id === post.id)
    if (idx !== -1) {
        posts.value[idx] = { ...posts.value[idx], ...res.data }
    }

    // Fetch comments
    const commentsRes = await axios.get(`/api/posts/${post.id}/comments/`)
    activePost.value.comments = commentsRes.data
  } catch (e) {
    console.error(e)
  }
}

const openEditor = (post = null) => {
  if (!user.value || user.value.role !== 'admin') {
    alert('仅管理员可以发布或编辑文章')
    return
  }
  if (post) {
    isEditing.value = true
    editingId.value = post.id
    activePost.value = post // Ensure activePost is set for editor to read
  } else {
    isEditing.value = false
    editingId.value = null
    activePost.value = null
  }
  switchView('editor')
}

const cancelEdit = () => {
  if (isEditing.value && activePost.value) {
    switchView('detail')
  } else {
    switchView('list')
  }
}

// API 操作
const fetchPosts = async (params = {}) => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize
    const finalParams = { 
        skip, 
        limit: pageSize, 
        q: currentSearchQuery.value,
        category: currentCategory.value || undefined,
        sort_by: currentSort.value.sortBy,
        order: currentSort.value.order,
        ...params 
    }
    
    const config = { params: finalParams }
    if (token.value) {
      config.headers = { Authorization: `Bearer ${token.value}` }
    }
    const response = await axios.get('/api/posts/', config)
    posts.value = response.data.items
    totalPosts.value = response.data.total
  } catch (error) {
    console.error('Error fetching posts', error)
  } finally {
    loading.value = false
    nextTick(() => {
      if (window.lucide) window.lucide.createIcons()
    })
  }
}

const handleSearch = (searchParams) => {
    currentSearchQuery.value = searchParams.q
    currentCategory.value = searchParams.category || ''
    currentSort.value = { sortBy: searchParams.sortBy, order: searchParams.order }
    currentPage.value = 1 // Reset to first page on search
    fetchPosts()
}

const handlePageChange = (page) => {
    currentPage.value = page
    fetchPosts()
    window.scrollTo(0, 0)
}

const handleTagSearch = (tag) => {
    currentSearchQuery.value = tag
    currentSort.value = { sortBy: 'date', order: 'desc' }
    currentPage.value = 1
    switchView('list')
    fetchPosts()
}

const fetchCurrentUser = async () => {
  try {
    const response = await axios.get('/api/users/me', {
      headers: { Authorization: `Bearer ${token.value}` }
    })
    user.value = response.data
  } catch (error) {
    console.error('Error fetching user', error)
    logout()
  }
}

const handleLoginSuccess = async (accessToken) => {
    token.value = accessToken
    localStorage.setItem('token', token.value)
    await fetchCurrentUser()
}

const logout = () => {
  token.value = ''
  user.value = null
  localStorage.removeItem('token')
  switchView('list')
}

const handleSavePost = async (formData) => {
  try {
    let savedPost
    if (isEditing.value) {
      const res = await axios.put(`/api/posts/${editingId.value}`, formData, {
        headers: { Authorization: `Bearer ${token.value}` }
      })
      savedPost = res.data
    } else {
      const res = await axios.post('/api/posts/', formData, {
        headers: { Authorization: `Bearer ${token.value}` }
      })
      savedPost = res.data
    }
    await fetchPosts()
    
    // Redirect to detail view of the saved post
    activePost.value = savedPost
    // Ensure comments are initialized if new post
    if (!activePost.value.comments) activePost.value.comments = []
    switchView('detail')
  } catch (error) {
    alert(error.response?.data?.detail || '保存文章失败')
  }
}

const deletePost = async (id) => {
  if (!confirm('Delete this record?')) return
  try {
    await axios.delete(`/api/posts/${id}`, {
      headers: { Authorization: `Bearer ${token.value}` }
    })
    posts.value = posts.value.filter(p => p.id !== id)
    switchView('list')
  } catch (error) {
    alert(error.response?.data?.detail || '删除文章失败')
  }
}

const addComment = async (content) => {
  const post = activePost.value
  try {
    const res = await axios.post(`/api/posts/${post.id}/comments/`, { content }, {
      headers: { Authorization: `Bearer ${token.value}` }
    })
    if (!post.comments) post.comments = []
    post.comments.push(res.data)
  } catch (error) {
    if (error.response?.status === 401) {
      alert('请先登录后再发表评论')
      isLoginOpen.value = true
      return
    }
    alert(error.response?.data?.detail || '发表评论失败')
  }
}

const deleteComment = async (post, commentId) => {
  if (!confirm('Delete comment?')) return
  try {
    await axios.delete(`/api/comments/${commentId}`, {
      headers: { Authorization: `Bearer ${token.value}` }
    })
    post.comments = post.comments.filter(c => c.id !== commentId)
  } catch (error) {
    alert(error.response?.data?.detail || '删除评论失败')
  }
}

const likePost = async (post) => {
  if (!token.value) {
    alert('请先登录后再点赞')
    isLoginOpen.value = true
    return
  }
  try {
    const res = await axios.post(`/api/posts/${post.id}/like`, {}, {
      headers: { Authorization: `Bearer ${token.value}` }
    })
    post.likes = res.data.likes
    post.is_liked = res.data.is_liked

    // Sync updated data back to the list if we are in detail view (where post is activePost)
    const idx = posts.value.findIndex(p => p.id === post.id)
    if (idx !== -1) {
        posts.value[idx].likes = post.likes
        posts.value[idx].is_liked = post.is_liked
    }
  } catch (error) {
    if (error.response && error.response.data && error.response.data.detail) {
      alert(error.response.data.detail)
    } else {
      console.error('Error liking post', error)
    }
  }
}

onMounted(async () => {
  if (token.value) {
    await fetchCurrentUser()
  }
  await fetchPosts()
})

const refreshIcons = () => {
  nextTick(() => {
    if (window.lucide) {
      window.lucide.createIcons()
      setTimeout(() => window.lucide.createIcons(), 50)
    }
  })
}

onUpdated(refreshIcons)

watch([currentView, isLoginOpen], refreshIcons)
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Noto+Sans+SC:wght@400;700;900&display=swap');

body {
    font-family: 'Noto Sans SC', sans-serif;
}
.font-mono {
    font-family: 'JetBrains Mono', monospace;
}
.animate-spin-slow {
    animation: spin 8s linear infinite;
}
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
/* 模拟扫描线效果 */
.scanline {
    background: linear-gradient(to bottom, transparent 50%, rgba(0, 0, 0, 0.05) 50%);
    background-size: 100% 4px;
}
</style>
