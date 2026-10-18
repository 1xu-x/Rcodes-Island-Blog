<template>
    <div class="max-w-4xl mx-auto animate-fade-in">
        <div class="bg-white border-2 border-zinc-900 shadow-[12px_12px_0_0_#18181b] p-8 md:p-12">
            <div class="text-xs font-mono font-bold text-yellow-600 tracking-[0.3em] mb-3">ABOUT / 关于我</div>
            <h1 class="text-4xl md:text-5xl font-black tracking-tight mb-6">技术成长路上的记录员</h1>
            <p class="text-lg leading-relaxed text-zinc-700 mb-8">
                这里是 <strong>Code Journey</strong>（技术成长博客）。我用这个站点记录 Python、计算机基础、后端开发和云计算课程中的实践过程，把能跑通的代码、踩过的坑和部署步骤写成可以复查的笔记。
            </p>

            <figure class="mb-10 border-2 border-zinc-900 bg-zinc-100">
                <img
                    :src="automataImage"
                    alt="LR(1) 自动机项目笔记"
                    class="w-full max-h-[520px] object-cover object-top"
                    loading="lazy"
                >
                <figcaption class="px-4 py-3 text-xs font-bold text-zinc-500 border-t-2 border-zinc-900">
                    课程笔记：LR(1) 项目集规范族与 DFA。图片随前端静态资源发布。
                </figcaption>
            </figure>

            <section class="mb-10">
                <h2 class="text-2xl font-black mb-4">学习方向</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="item in directions" :key="item.title" class="border-2 border-zinc-900 p-4">
                        <div class="text-xs font-bold uppercase tracking-widest text-zinc-400 mb-1">{{ item.en }}</div>
                        <div class="text-xl font-black mb-2">{{ item.title }}</div>
                        <p class="text-sm text-zinc-600 leading-relaxed">{{ item.desc }}</p>
                    </div>
                </div>
            </section>

            <section class="mb-10">
                <h2 class="text-2xl font-black mb-4">学习经历</h2>
                <ol class="space-y-4">
                    <li v-for="(step, index) in timeline" :key="step" class="flex gap-4">
                        <div class="w-10 h-10 bg-yellow-400 border-2 border-zinc-900 flex items-center justify-center font-black">{{ index + 1 }}</div>
                        <p class="flex-1 text-zinc-700 leading-relaxed pt-2">{{ step }}</p>
                    </li>
                </ol>
            </section>

            <section>
                <h2 class="text-2xl font-black mb-4">实践项目</h2>
                <p class="text-zinc-700 leading-relaxed">
                    当前站点本身就是课程实践项目：基于开源仓库 Rcodes Island Blog 二次开发，保留 FastAPI、SQLAlchemy 与 MySQL 的数据链路，补齐注册登录、管理员发文、点赞、评论和云端部署说明。文章列表、点赞状态和评论都从数据库读取，刷新或重启后仍然保留。
                </p>
            </section>
        </div>
    </div>
</template>

<script setup>
import { assetUrl } from '../utils'

const automataImage = assetUrl('images/posts/automata-lr.jpg')

const directions = [
    { en: 'Python', title: 'Python 基础', desc: '文件处理、JSON 持久化、异常处理和结构化编程。' },
    { en: 'CS', title: '计算机基础', desc: 'HTTP、进程与端口、环境变量和日志，为部署打底。' },
    { en: 'Backend', title: '后端开发', desc: 'FastAPI 路由、JWT 认证、SQLAlchemy 模型与权限校验。' },
    { en: 'Cloud', title: '云计算实践', desc: 'MySQL、Docker Compose、安全组和公网访问配置。' },
]
const timeline = [
    '完成 Python 语法与标准库练习，能独立读写文件和 JSON。',
    '使用 FastAPI 编写带认证的 REST 接口，并用 /docs 自测。',
    '把用户、文章、点赞、评论落到 MySQL，验证刷新后数据仍在。',
    '整理本地启动与云服务器部署步骤，准备课程汇报演示。',
]
</script>
