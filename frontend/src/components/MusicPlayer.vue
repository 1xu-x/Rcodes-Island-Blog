<template>
    <div class="fixed bottom-8 right-8 z-50">
        <audio ref="audioPlayer" loop muted>
            <source :src="bgmUrl" type="audio/mpeg">
        </audio>
        <div class="w-12 h-12 rounded-full border-2 border-zinc-900 shadow-[4px_4px_0_0_#000] transition-transform duration-300 hover:scale-110 bg-white overflow-hidden">
            <button 
                @click="toggleMusic" 
                :class="['w-full h-full flex items-center justify-center', isPlaying ? 'bg-yellow-400 animate-spin-slow' : 'bg-white']"
                title="Music Player"
            >
                <i data-lucide="music" :class="['w-5 h-5', isPlaying ? 'text-black' : 'text-zinc-400']"></i>
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { assetUrl } from '../utils'

const isPlaying = ref(false)
const audioPlayer = ref(null)
const bgmUrl = assetUrl('bgm.mp3')

const toggleMusic = () => {
  if (isPlaying.value) {
    audioPlayer.value.pause()
  } else {
    audioPlayer.value.play().catch(e => console.log("Audio play failed:", e))
  }
  isPlaying.value = !isPlaying.value
}

onMounted(() => {
  // 尝试自动播放背景音乐
  if (audioPlayer.value) {
    // 1. 先尝试静音播放（成功率极高）
    audioPlayer.value.muted = true
    audioPlayer.value.play().then(() => {
      isPlaying.value = true
      console.log("Muted autoplay started")
    }).catch(e => {
      console.log("Muted autoplay failed:", e)
    })

    // 2. 监听用户首次交互，恢复声音
    const enableSound = () => {
      if (audioPlayer.value) {
        audioPlayer.value.muted = false
        audioPlayer.value.volume = 0.3
        // 如果之前静音播放失败了，这里再次尝试播放
        if (audioPlayer.value.paused) {
          audioPlayer.value.play().then(() => {
            isPlaying.value = true
          }).catch(e => console.log("Play on interaction failed:", e))
        }
      }
      // 移除监听器
      document.removeEventListener('click', enableSound)
      document.removeEventListener('touchstart', enableSound)
      document.removeEventListener('keydown', enableSound)
    }

    document.addEventListener('click', enableSound)
    document.addEventListener('touchstart', enableSound)
    document.addEventListener('keydown', enableSound)
  }
})
</script>

<style scoped>
.animate-spin-slow {
    animation: spin 8s linear infinite;
}
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
</style>
