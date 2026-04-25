/**
 * 回声 - TabBar 图标生成脚本
 * 文件：scripts/generate-icons.js
 * 说明：生成简单的占位 PNG 图标文件
 * 运行：node scripts/generate-icons.js
 */

const fs = require('fs')
const path = require('path')

// 简单的 48x48 PNG 图标生成器（使用最小的有效 PNG 结构）
// 这是一个简化版本，实际项目中应使用专业图标

const icons = {
  // 对话图标 - 气泡形状
  'tab-chat.png': generatePlaceholderPNG('#808080', 'chat'),
  'tab-chat-active.png': generatePlaceholderPNG('#7C6FE0', 'chat'),

  // 日记图标 - 书本形状
  'tab-diary.png': generatePlaceholderPNG('#808080', 'diary'),
  'tab-diary-active.png': generatePlaceholderPNG('#7C6FE0', 'diary'),

  // [+] 按钮图标 - 加号形状
  'tab-add.png': generatePlaceholderPNG('#7C6FE0', 'add'),
  'tab-add-active.png': generatePlaceholderPNG('#7C6FE0', 'add'),

  // 动态图标 - 网格形状
  'tab-community.png': generatePlaceholderPNG('#808080', 'community'),
  'tab-community-active.png': generatePlaceholderPNG('#7C6FE0', 'community'),

  // 我的图标 - 人像形状
  'tab-mine.png': generatePlaceholderPNG('#808080', 'mine'),
  'tab-mine-active.png': generatePlaceholderPNG('#7C6FE0', 'mine'),
}

/**
 * 生成占位 PNG 图片
 * 由于 Node.js 原生不支持图形生成，这里创建最小的有效 PNG 文件
 * 实际项目应使用设计好的图标替换
 */
function generatePlaceholderPNG(color, type) {
  // 创建一个简单的 48x48 PNG 文件
  // PNG 文件结构：签名 + IHDR + IDAT + IEND

  const width = 48
  const height = 48

  // PNG 签名
  const signature = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])

  // IHDR chunk
  const ihdr = createIHDRChunk(width, height)

  // 创建简单的 RGBA 图像数据（纯色背景 + 简单形状）
  const imageData = createSimpleIcon(width, height, color, type)

  // IDAT chunk (压缩的图像数据)
  const idat = createIDATChunk(imageData)

  // IEND chunk
  const iend = createIENDChunk()

  return Buffer.concat([signature, ihdr, idat, iend])
}

function createIHDRChunk(width, height) {
  const data = Buffer.alloc(13)
  data.writeUInt32BE(width, 0)
  data.writeUInt32BE(height, 4)
  data[8] = 8  // bit depth
  data[9] = 6  // color type (RGBA)
  data[10] = 0 // compression method
  data[11] = 0 // filter method
  data[12] = 0 // interlace method

  return createChunk('IHDR', data)
}

function createSimpleIcon(width, height, color, type) {
  // 解析颜色
  const rgb = parseColor(color)

  // 创建原始图像数据（每行前面有一个 filter byte）
  const rawData = []

  for (let y = 0; y < height; y++) {
    rawData.push(0) // filter byte (none)
    for (let x = 0; x < width; x++) {
      // 判断是否在形状内部
      const inShape = isPointInShape(x, y, width, height, type)

      if (inShape) {
        // 形状内部：使用主题色
        rawData.push(rgb.r, rgb.g, rgb.b, 255)
      } else {
        // 形状外部：透明
        rawData.push(0, 0, 0, 0)
      }
    }
  }

  return Buffer.from(rawData)
}

function isPointInShape(x, y, width, height, type) {
  const cx = width / 2
  const cy = height / 2
  const size = Math.min(width, height) / 2 - 4

  switch (type) {
    case 'chat': {
      // 气泡形状（圆形 + 小尾巴）
      const radius = size - 4
      const dist = Math.sqrt((x - cx) ** 2 + (y - cy + 2) ** 2)
      // 主圆形
      if (dist <= radius) return true
      // 小尾巴（右下角三角形）
      if (x > cx + radius - 8 && y > cy + radius - 8 && x < cx + radius + 6 && y < cy + radius + 6) {
        return true
      }
      return false
    }
    case 'diary': {
      // 书本形状（矩形）
      const margin = 6
      return x >= margin && x < width - margin && y >= margin && y < height - margin
    }
    case 'add': {
      // [+] 加号形状
      const barWidth = 6
      const barLength = size - 2
      // 水平条
      const inHorizontalBar = x >= cx - barLength && x <= cx + barLength && y >= cy - barWidth / 2 && y <= cy + barWidth / 2
      // 垂直条
      const inVerticalBar = x >= cx - barWidth / 2 && x <= cx + barWidth / 2 && y >= cy - barLength && y <= cy + barLength
      return inHorizontalBar || inVerticalBar
    }
    case 'community': {
      // 四宫格
      const gap = 4
      const cellSize = (width - gap * 3) / 2
      const inTopLeft = x >= gap && x < gap + cellSize && y >= gap && y < gap + cellSize
      const inTopRight = x >= gap * 2 + cellSize && x < gap * 2 + cellSize * 2 && y >= gap && y < gap + cellSize
      const inBottomLeft = x >= gap && x < gap + cellSize && y >= gap * 2 + cellSize && y < gap * 2 + cellSize * 2
      const inBottomRight = x >= gap * 2 + cellSize && x < gap * 2 + cellSize * 2 && y >= gap * 2 + cellSize && y < gap * 2 + cellSize * 2
      return inTopLeft || inTopRight || inBottomLeft || inBottomRight
    }
    case 'mine': {
      // 人像形状（圆形头部 + 半圆形身体）
      const headRadius = size / 3
      const headCenterY = cy - headRadius
      const headDist = Math.sqrt((x - cx) ** 2 + (y - headCenterY) ** 2)
      if (headDist <= headRadius) return true

      // 身体（下半部分的半圆）
      const bodyCenterY = height - 6
      const bodyRadius = size - 2
      const bodyDist = Math.sqrt((x - cx) ** 2 + (y - bodyCenterY) ** 2)
      if (bodyDist <= bodyRadius && y > cy) return true

      return false
    }
    default:
      // 默认圆形
      const dist = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
      return dist <= size - 4
  }
}

function parseColor(hexColor) {
  // 解析十六进制颜色
  const hex = hexColor.replace('#', '')
  return {
    r: parseInt(hex.substring(0, 2), 16),
    g: parseInt(hex.substring(2, 4), 16),
    b: parseInt(hex.substring(4, 6), 16)
  }
}

function createIDATChunk(data) {
  // 使用 zlib 压缩数据
  const zlib = require('zlib')
  const compressed = zlib.deflateSync(data, { level: 9 })
  return createChunk('IDAT', compressed)
}

function createIENDChunk() {
  return createChunk('IEND', Buffer.alloc(0))
}

function createChunk(type, data) {
  const length = Buffer.alloc(4)
  length.writeUInt32BE(data.length, 0)

  const typeBuffer = Buffer.from(type, 'ascii')
  const crcData = Buffer.concat([typeBuffer, data])
  const crc = crc32(crcData)

  const crcBuffer = Buffer.alloc(4)
  crcBuffer.writeUInt32BE(crc >>> 0, 0)

  return Buffer.concat([length, typeBuffer, data, crcBuffer])
}

// CRC32 计算
function crc32(data) {
  let crc = 0xFFFFFFFF
  const table = getCRC32Table()

  for (let i = 0; i < data.length; i++) {
    crc = (crc >>> 8) ^ table[(crc ^ data[i]) & 0xFF]
  }

  return crc ^ 0xFFFFFFFF
}

function getCRC32Table() {
  const table = new Uint32Array(256)
  for (let i = 0; i < 256; i++) {
    let c = i
    for (let j = 0; j < 8; j++) {
      if (c & 1) {
        c = 0xEDB88320 ^ (c >>> 1)
      } else {
        c = c >>> 1
      }
    }
    table[i] = c
  }
  return table
}

// 主函数
function main() {
  const outputDir = path.join(__dirname, '..', 'static', 'images', 'icons')

  // 确保输出目录存在
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true })
  }

  // 生成所有图标
  for (const [filename, buffer] of Object.entries(icons)) {
    const filepath = path.join(outputDir, filename)
    fs.writeFileSync(filepath, buffer)
    console.log(`已生成: ${filename}`)
  }

  console.log('\n所有 TabBar 图标已生成完毕！')
  console.log(`输出目录: ${outputDir}`)
}

main()
