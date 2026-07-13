/**
 * 将 ISO 等时间字符串格式化为 YYYY-MM-DD HH:mm:ss。
 */
export function formatDateTime(value) {
  if (value == null || value === '') return '-'

  const str = String(value).trim()
  const match = str.match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})/)
  if (match) return `${match[1]} ${match[2]}`

  const date = new Date(str)
  if (Number.isNaN(date.getTime())) return str

  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

/** el-table-column formatter 用法。 */
export function dateTimeColumnFormatter(_row, _column, cellValue) {
  return formatDateTime(cellValue)
}
