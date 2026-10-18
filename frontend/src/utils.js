import { marked } from 'marked'
import { DEFAULT_COVER, LEGACY_UPLOAD_ASSETS, MISSING_IMAGE } from './imageAssets'

const publicBase = () => `${(import.meta.env.BASE_URL || '/').replace(/\/+$/, '')}/`

export const assetUrl = (path = '') => {
  const cleanPath = String(path).replace(/^\/+/, '')
  return `${publicBase()}${cleanPath}`
}

const legacyUploadName = (value) => {
  const match = String(value).match(/(?:^|\/)uploads\/([^/?#]+)/)
  if (!match) return ''
  try {
    return decodeURIComponent(match[1])
  } catch {
    return match[1]
  }
}

const legacyUploadUrl = (fileName) => {
  const mapped = LEGACY_UPLOAD_ASSETS[fileName]
  if (mapped) return assetUrl(mapped)

  const explicitBase = (import.meta.env.VITE_LEGACY_UPLOAD_BASE_URL || '').replace(/\/+$/, '')
  if (explicitBase) {
    return `${explicitBase}/uploads/${encodeURIComponent(fileName)}`
  }

  console.warn(
    `[images] 未迁移的旧上传文件 ${fileName} 已改用占位图。` +
    'Render 临时磁盘中的 /uploads 文件会在重启、重新部署或休眠后丢失。'
  )
  return assetUrl(MISSING_IMAGE)
}

export const resolveImageUrl = (value, fallback = DEFAULT_COVER) => {
  if (!value || typeof value !== 'string') return assetUrl(fallback)

  const raw = value.trim()
  if (!raw) return assetUrl(fallback)
  if (/^data:image\//i.test(raw) || /^blob:/i.test(raw)) return raw
  if (raw.startsWith('//')) return `https:${raw}`

  if (/^https?:\/\//i.test(raw)) {
    const fileName = legacyUploadName(raw)
    if (!fileName) return raw

    const mapped = LEGACY_UPLOAD_ASSETS[fileName]
    if (mapped) return assetUrl(mapped)

    try {
      const host = new URL(raw).hostname
      if (host.endsWith('.onrender.com')) return legacyUploadUrl(fileName)
    } catch {
      return assetUrl(MISSING_IMAGE)
    }
    return raw
  }

  if (/^\/?uploads\//i.test(raw)) {
    const fileName = legacyUploadName(raw)
    if (import.meta.env.DEV && !LEGACY_UPLOAD_ASSETS[fileName]) return `/${raw.replace(/^\/+/, '')}`
    return legacyUploadUrl(fileName)
  }

  if (raw.startsWith('/')) return assetUrl(raw)
  return assetUrl(raw)
}

export const renderMarkdown = (markdown) => {
  const html = marked(markdown || '')
  if (typeof DOMParser === 'undefined') return html

  const documentNode = new DOMParser().parseFromString(html, 'text/html')
  documentNode.querySelectorAll('img[src]').forEach((image) => {
    image.setAttribute('src', resolveImageUrl(image.getAttribute('src'), MISSING_IMAGE))
    image.setAttribute('loading', 'lazy')
  })
  return documentNode.body.innerHTML
}

export const stripHtml = (html) => {
  // 预处理：将块级元素结束标签替换为换行符，保留结构
  let processed = html
    .replace(/<\/p>/gi, '\n')
    .replace(/<\/div>/gi, '\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/li>/gi, '\n');
    
  const tmp = document.createElement("DIV")
  tmp.innerHTML = processed
  return (tmp.textContent || tmp.innerText || "").trim()
}
