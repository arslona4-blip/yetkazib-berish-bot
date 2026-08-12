import type { ReactElement } from 'react'

/** Oddiy SVG ikonkalar */
const paths: Record<string, ReactElement> = {
  schedule: (
    <>
      <rect x="4" y="5" width="16" height="15" rx="2" />
      <path d="M8 3v4M16 3v4M4 10h16" />
    </>
  ),
  week: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M3 9h18M8 4v16M13 4v16" />
    </>
  ),
  alarm: (
    <>
      <circle cx="12" cy="13" r="7" />
      <path d="M12 10v4l2 1M6 4l-2 2M18 4l2 2" />
    </>
  ),
  homework: (
    <>
      <path d="M5 4h11l3 3v13H5z" />
      <path d="M14 4v4h4M8 12h8M8 16h6" />
    </>
  ),
  bells: (
    <>
      <path d="M6 16a6 6 0 0 1 12 0H6z" />
      <path d="M12 4v2M10 19h4" />
    </>
  ),
  grades: <path d="M12 3l2.5 6.5H21l-5 4 2 7-6-4.5L6 20.5l2-7-5-4h6.5z" />,
  attendance: (
    <>
      <circle cx="12" cy="12" r="8" />
      <path d="M8 12l3 3 5-6" />
    </>
  ),
  events: <path d="M12 3v18M5 8h14M7 13h10M9 18h6" />,
  checklist: (
    <>
      <rect x="5" y="4" width="14" height="16" rx="2" />
      <path d="M8 9h8M8 13h8M8 17h5" />
    </>
  ),
  clubs: <circle cx="12" cy="12" r="8" />,
  weather: (
    <>
      <circle cx="10" cy="10" r="3" />
      <path d="M14 15h4a3 3 0 0 0 0-6 4 4 0 0 0-7.5-1" />
    </>
  ),
  voice: (
    <>
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M6 11a6 6 0 0 0 12 0M12 17v3" />
    </>
  ),
  share: <path d="M12 4v10M8 8l4-4 4 4M5 14v5h14v-5" />,
  print: (
    <>
      <rect x="6" y="3" width="12" height="6" rx="1" />
      <path d="M5 9h14v8H5zM8 17v3h8v-3" />
    </>
  ),
  backup: (
    <>
      <path d="M4 14a6 6 0 0 1 10.5-4H18a4 4 0 0 1 0 8H7a3 3 0 0 1-3-4z" />
    </>
  ),
  calendar: (
    <>
      <rect x="4" y="5" width="16" height="15" rx="2" />
      <path d="M8 3v4M16 3v4M4 10h16" />
    </>
  ),
  templates: <path d="M5 5h6v6H5zM13 5h6v6h-6zM5 13h6v6H5zM13 13h6v6h-6z" />,
  profiles: (
    <>
      <circle cx="9" cy="9" r="3" />
      <circle cx="16" cy="10" r="2.5" />
      <path d="M3 19c1.5-3 4-4.5 6-4.5S13.5 16 15 19M14 15.5c1.2 0 2.8.7 4 3.5" />
    </>
  ),
  theme: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2M12 19v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M3 12h2M19 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </>
  ),
  lang: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18" />
    </>
  ),
  parent: (
    <>
      <circle cx="8" cy="9" r="2.5" />
      <circle cx="16" cy="9" r="2.5" />
      <path d="M3 19c1-3 3-4.5 5-4.5s4 1.5 5 4.5M11 19c1-2.5 2.5-3.5 5-3.5s3.5 1 5 3.5" />
    </>
  ),
  pin: (
    <>
      <rect x="6" y="10" width="12" height="10" rx="2" />
      <path d="M9 10V7a3 3 0 0 1 6 0v3" />
    </>
  ),
  announce: (
    <>
      <path d="M4 10v4h3l5 4V6L7 10H4z" />
      <path d="M16 9a3 3 0 0 1 0 6" />
    </>
  ),
  stats: (
    <>
      <path d="M5 19V10M12 19V5M19 19v-7" />
    </>
  ),
  favorites: <path d="M12 19l-7-6.5A4.5 4.5 0 0 1 12 6a4.5 4.5 0 0 1 7 6.5z" />,
  commute: (
    <>
      <rect x="3" y="8" width="18" height="9" rx="2" />
      <path d="M6 17v2M18 17v2M3 12h18" />
    </>
  ),
  install: (
    <>
      <rect x="7" y="2" width="10" height="20" rx="2" />
      <path d="M12 17h.01" />
    </>
  ),
  widget: <path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z" />,
  motivation: <path d="M12 2c2 4 6 6 6 10a6 6 0 1 1-12 0c0-4 4-6 6-10z" />,
  admin: (
    <>
      <path d="M3 20h18M5 20V9l7-5 7 5v11" />
      <path d="M10 20v-5h4v5" />
    </>
  ),
  substitute: <path d="M7 7h11M15 4l3 3-3 3M17 17H6M9 14l-3 3 3 3" />,
  notes: (
    <>
      <path d="M9 4h8l3 3v13H9z" />
      <path d="M12 11h5M12 15h4" />
    </>
  ),
  colors: (
    <>
      <circle cx="8" cy="10" r="3" />
      <circle cx="15" cy="9" r="3" />
      <circle cx="12" cy="15" r="3" />
    </>
  ),
  home: <path d="M4 11l8-7 8 7v9H4z" />,
  user: (
    <>
      <circle cx="12" cy="9" r="3.5" />
      <path d="M5 20c1.5-3.5 4-5 7-5s5.5 1.5 7 5" />
    </>
  ),
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  chat: (
    <>
      <path d="M5 5h14v10H9l-4 3z" />
    </>
  ),
  close: <path d="M6 6l12 12M18 6L6 18" />,
  search: (
    <>
      <circle cx="11" cy="11" r="6" />
      <path d="M16 16l4 4" />
    </>
  ),
}

export function Icon({
  name,
  size = 22,
}: {
  name: string
  size?: number
}) {
  const body = paths[name] || paths.widget
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {body}
    </svg>
  )
}
