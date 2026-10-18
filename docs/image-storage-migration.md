# 图片存储与旧上传路径迁移

## 当前策略

课程演示使用 **静态资源优先**：

- 固定头像、分类封面和正文展示图放在 `frontend/public/images/`，由 GitHub Pages 随前端一起发布。
- TiDB 的 `posts.cover_url` 继续保存字符串，不需要改表结构；相对路径如 `images/covers/cloud-infra.jpg` 会在前端按 Pages 子路径解析。
- 稳定外部图片可使用完整 `https://` 地址。
- 动态上传默认关闭：后端 `ENABLE_IMAGE_UPLOAD=false`，前端 `VITE_IMAGE_UPLOAD_ENABLED=false`。
- 用户、文章、点赞和评论模型及接口业务逻辑不变。

## Render 临时文件系统风险

`backend/uploads` 和 `/api/upload` 仍保留给本地开发或带持久卷的环境。Render Free Web Service 没有持久磁盘，上传文件只存在当前实例中：

- 服务重启后可能丢失；
- 重新部署后可能丢失；
- 免费实例休眠或重建后可能丢失。

因此，接口返回的 `https://<service>.onrender.com/uploads/...` 只是当前文件的可访问 URL，不是对象存储，也不能当作备份或持久化方案。接口响应已标记 `storage: "ephemeral"` 和 `persistent: false`。

## 现有文件检查结果

本地 `backend/uploads` 中有 3 个文件，当前本地 MySQL 文章表的 `cover_url` 和正文都没有引用它们：

| 原文件 | 内容 | 处理 |
| --- | --- | --- |
| `92a5f8e7-dca2-4fb9-aa3a-049f4f95e76c.png` | 载具概念图 | 已生成静态副本 `images/covers/cloud-infra.jpg` |
| `c763daf7-71b0-4cfb-bbea-5944262c8dbb.jpg` | 自动机 LR(1) 手写笔记 | 已生成静态副本 `images/posts/automata-lr.jpg` |
| `cd45c968-609e-4dda-8f65-ca7593a86406.jpg` | 含教师联系方式、邮箱等个人信息的邮件截图 | 未复制到公开静态目录 |

原始文件均未删除或覆盖。邮件截图不应直接公开；如确需展示，应先遮挡个人信息并取得相关方同意。

## 迁移旧文章步骤

1. 先备份数据库表和上传目录，不要删除原文件。
2. 查找引用：

```sql
SELECT id, title, cover_url
FROM posts
WHERE cover_url LIKE '%/uploads/%'
   OR cover_url LIKE 'uploads/%';

SELECT id, title
FROM posts
WHERE content LIKE '%/uploads/%'
   OR content LIKE '%uploads/%';
```

3. 把需要的文件复制到 `frontend/public/images/legacy/`，建议保留原文件名便于核对；不要移动或覆盖 `backend/uploads` 中的原件。
4. 更新文章数据，把旧路径改成静态路径：

```sql
UPDATE posts
SET cover_url = 'images/legacy/<filename>'
WHERE cover_url = '/uploads/<filename>';
```

正文可执行对应替换：

```sql
UPDATE posts
SET content = REPLACE(content, '/uploads/<filename>', 'images/legacy/<filename>')
WHERE content LIKE '%/uploads/<filename>%';
```

5. 对少量尚未改库的文章，可把文件名映射加入 `frontend/src/imageAssets.js` 的 `LEGACY_UPLOAD_ASSETS`。前端会把已知旧路径重写到静态副本。
6. 未知旧路径默认显示占位图并输出控制台警告。仅在临时排查时设置 `VITE_LEGACY_UPLOAD_BASE_URL=https://<service>.onrender.com`，不要把它当成长期方案。
7. 重新构建并验证：

```powershell
Set-Location frontend
$env:VITE_BASE_PATH = '/<仓库名>/'
npm run build
```

打开文章列表和详情，确认图片 URL 为 `/<仓库名>/images/...` 且返回 200。

## 本地方案何时可开启上传

只有在以下条件同时满足时才设置 `ENABLE_IMAGE_UPLOAD=true`：

- 后端运行在本地或 Docker，且 `backend/uploads` 已挂载持久卷；
- 已有备份策略；
- 前端构建同时设置 `VITE_IMAGE_UPLOAD_ENABLED=true`。

Render 免费演示环境和 GitHub Pages 静态托管不应开启该开关。
