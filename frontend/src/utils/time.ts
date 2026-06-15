export function formatBeijingTime(value: string | null | undefined): string {
  if (!value) return '-'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  const beijing = new Date(date.getTime() + 8 * 60 * 60 * 1000)
  const pad = (n: number) => String(n).padStart(2, '0')

  return [
    beijing.getUTCFullYear(),
    pad(beijing.getUTCMonth() + 1),
    pad(beijing.getUTCDate()),
  ].join('-') + ` ${pad(beijing.getUTCHours())}:${pad(beijing.getUTCMinutes())}:${pad(beijing.getUTCSeconds())}`
}
