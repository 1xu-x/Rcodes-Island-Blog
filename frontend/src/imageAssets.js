export const DEFAULT_COVER = 'images/covers/default.svg'

export const CATEGORY_COVERS = {
  Python: 'images/covers/python.svg',
  计算机基础: 'images/posts/automata-lr.jpg',
  后端开发: 'images/covers/backend.svg',
  云计算: 'images/covers/cloud-infra.jpg',
  项目实践: 'images/covers/projects.svg',
}

export const COVER_PRESETS = [
  { label: '默认封面', path: DEFAULT_COVER },
  { label: 'Python', path: CATEGORY_COVERS.Python },
  { label: '计算机基础', path: CATEGORY_COVERS['计算机基础'] },
  { label: '后端开发', path: CATEGORY_COVERS['后端开发'] },
  { label: '云计算', path: CATEGORY_COVERS['云计算'] },
  { label: '项目实践', path: CATEGORY_COVERS['项目实践'] },
]

export const BODY_IMAGE_PRESETS = [
  { label: '自动机 LR 笔记', path: 'images/posts/automata-lr.jpg' },
  { label: '云计算封面', path: 'images/covers/cloud-infra.jpg' },
]

// 只登记已确认可以公开、且已经复制到 frontend/public 的旧上传文件。
// 原始文件仍保留在 backend/uploads，不在这里做删除或覆盖。
export const LEGACY_UPLOAD_ASSETS = {
  '92a5f8e7-dca2-4fb9-aa3a-049f4f95e76c.png': 'images/covers/cloud-infra.jpg',
  'c763daf7-71b0-4cfb-bbea-5944262c8dbb.jpg': 'images/posts/automata-lr.jpg',
}

export const AVATAR_IMAGE = 'images/avatar.png'
export const MISSING_IMAGE = 'images/missing-image.svg'

export function coverForCategory(category) {
  return CATEGORY_COVERS[category] || DEFAULT_COVER
}
