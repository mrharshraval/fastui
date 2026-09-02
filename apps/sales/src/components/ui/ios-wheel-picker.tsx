"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface IOSWheelPickerProps {
  date: string // "YYYY-MM-DD"
  time: string // "HH:mm" (24-hour format)
  onChange: (date: string, time: string) => void
  mode?: "date" | "time" | "datetime"
  className?: string
}

const ITEM_HEIGHT = 34
const RADIUS = 92 // Cylinder radius in px for Apple UIDatePicker perspective
const ANGLE_PER_ITEM = 21.5 // Degrees per item along the cylinder curve

interface CylinderWheelProps<T> {
  items: T[]
  value: T
  onSelect: (value: T) => void
  getLabel: (item: T) => string
  getKey: (item: T) => string
  isItemDisabled?: (item: T) => boolean
  align?: "left" | "center" | "right"
  loop?: boolean
  className?: string
}

function CylinderWheel<T>({
  items,
  value,
  onSelect,
  getLabel,
  getKey,
  isItemDisabled,
  align = "center",
  loop = false,
  className,
}: CylinderWheelProps<T>) {
  const containerRef = React.useRef<HTMLDivElement | null>(null)
  const isDraggingRef = React.useRef(false)
  const startYRef = React.useRef(0)
  const startOffsetRef = React.useRef(0)
  const lastYRef = React.useRef(0)
  const lastTimeRef = React.useRef(0)
  const velocityRef = React.useRef(0)
  const animFrameRef = React.useRef<number | null>(null)

  const selectedIndex = React.useMemo(() => {
    const idx = items.findIndex((it) => getKey(it) === getKey(value))
    return idx >= 0 ? idx : 0
  }, [items, value, getKey])

  // Current scroll offset in pixels (0 = item 0 centered)
  const [offsetY, setOffsetY] = React.useState(() => selectedIndex * ITEM_HEIGHT)
  const offsetYRef = React.useRef(offsetY)
  offsetYRef.current = offsetY

  // Sync external value changes
  React.useEffect(() => {
    if (!isDraggingRef.current) {
      const targetOffset = selectedIndex * ITEM_HEIGHT
      if (Math.abs(offsetYRef.current - targetOffset) > 1) {
        setOffsetY(targetOffset)
      }
    }
  }, [selectedIndex])

  // Trigger haptic feedback on index change
  const lastSnappedIndexRef = React.useRef(selectedIndex)
  const checkHaptic = React.useCallback(
    (currentIdx: number) => {
      if (currentIdx !== lastSnappedIndexRef.current) {
        lastSnappedIndexRef.current = currentIdx
        try {
          if (typeof navigator !== "undefined" && "vibrate" in navigator) {
            navigator.vibrate(5)
          }
        } catch {}
      }
    },
    []
  )

  // Find closest valid non-disabled item index
  const getNearestValidIndex = React.useCallback(
    (targetIdx: number) => {
      const clamped = Math.max(0, Math.min(targetIdx, items.length - 1))
      if (!isItemDisabled || !isItemDisabled(items[clamped])) {
        return clamped
      }
      let closestIdx = clamped
      let minDistance = Infinity
      for (let i = 0; i < items.length; i++) {
        if (!isItemDisabled(items[i])) {
          const dist = Math.abs(i - clamped)
          if (dist < minDistance) {
            minDistance = dist
            closestIdx = i
          }
        }
      }
      return closestIdx
    },
    [items, isItemDisabled]
  )

  // Smoothly snap to target offset
  const snapTo = React.useCallback(
    (rawOffset: number, onComplete?: () => void) => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)

      const rawIdx = Math.round(rawOffset / ITEM_HEIGHT)
      const validIdx = getNearestValidIndex(rawIdx)
      const targetOffset = validIdx * ITEM_HEIGHT

      // Immediately inform parent of the valid selected item
      const finalItem = items[validIdx]
      if (finalItem && getKey(finalItem) !== getKey(value)) {
        onSelect(finalItem)
      }

      const start = offsetYRef.current
      const change = targetOffset - start
      const duration = 240
      const startTime = performance.now()

      const animate = (currentTime: number) => {
        const elapsed = currentTime - startTime
        const progress = Math.min(elapsed / duration, 1)
        // iOS ease-out cubic
        const ease = 1 - Math.pow(1 - progress, 3)
        const nextOffset = start + change * ease

        setOffsetY(nextOffset)
        const currentIdx = Math.round(nextOffset / ITEM_HEIGHT)
        checkHaptic(currentIdx)

        if (progress < 1) {
          animFrameRef.current = requestAnimationFrame(animate)
        } else {
          setOffsetY(targetOffset)
          onComplete?.()
        }
      }

      animFrameRef.current = requestAnimationFrame(animate)
    },
    [items, value, getKey, onSelect, checkHaptic, getNearestValidIndex]
  )

  // Ensure current selection is never on a disabled item
  React.useEffect(() => {
    if (isItemDisabled && items[selectedIndex] && isItemDisabled(items[selectedIndex])) {
      const validIdx = getNearestValidIndex(selectedIndex)
      if (items[validIdx] && getKey(items[validIdx]) !== getKey(value)) {
        onSelect(items[validIdx])
      }
    }
  }, [selectedIndex, items, isItemDisabled, value, getKey, getNearestValidIndex, onSelect])

  // Cleanup animation frame on unmount
  React.useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
      if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current)
    }
  }, [])

  // Decelerate with momentum physics on pointer release
  const decelerateWithInertia = React.useCallback(
    (initialVelocity: number) => {
      let vel = initialVelocity
      const friction = 0.94
      const minOffset = 0
      const maxOffset = (items.length - 1) * ITEM_HEIGHT

      const step = () => {
        vel *= friction
        let nextOffset = offsetYRef.current - vel

        // Rubber-banding boundaries
        if (nextOffset < minOffset) {
          nextOffset = minOffset + (nextOffset - minOffset) * 0.3
          vel = 0
        } else if (nextOffset > maxOffset) {
          nextOffset = maxOffset + (nextOffset - maxOffset) * 0.3
          vel = 0
        }

        setOffsetY(nextOffset)
        const currentIdx = Math.round(nextOffset / ITEM_HEIGHT)
        checkHaptic(currentIdx)

        if (Math.abs(vel) > 0.4) {
          animFrameRef.current = requestAnimationFrame(step)
        } else {
          snapTo(offsetYRef.current)
        }
      }

      animFrameRef.current = requestAnimationFrame(step)
    },
    [items, snapTo, checkHaptic]
  )

  // Pointer Event Handlers
  const handlePointerDown = (e: React.PointerEvent) => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    isDraggingRef.current = true
    startYRef.current = e.clientY
    startOffsetRef.current = offsetYRef.current
    lastYRef.current = e.clientY
    lastTimeRef.current = performance.now()
    velocityRef.current = 0

    const target = e.currentTarget as HTMLElement
    target.setPointerCapture(e.pointerId)
  }

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDraggingRef.current) return

    const deltaY = e.clientY - startYRef.current
    let nextOffset = startOffsetRef.current - deltaY

    // iOS Rubber-banding when dragged beyond edges
    const minOffset = 0
    const maxOffset = (items.length - 1) * ITEM_HEIGHT
    if (nextOffset < minOffset) {
      nextOffset = minOffset + (nextOffset - minOffset) * 0.35
    } else if (nextOffset > maxOffset) {
      nextOffset = maxOffset + (nextOffset - maxOffset) * 0.35
    }

    setOffsetY(nextOffset)

    // Calculate instantaneous velocity
    const now = performance.now()
    const dt = now - lastTimeRef.current
    if (dt > 10) {
      const dy = e.clientY - lastYRef.current
      velocityRef.current = (dy / dt) * 16 // Pixels per frame
      lastYRef.current = e.clientY
      lastTimeRef.current = now
    }

    const currentIdx = Math.round(nextOffset / ITEM_HEIGHT)
    checkHaptic(currentIdx)
  }

  const handlePointerUp = (e: React.PointerEvent) => {
    if (!isDraggingRef.current) return
    isDraggingRef.current = false

    const target = e.currentTarget as HTMLElement
    try {
      target.releasePointerCapture(e.pointerId)
    } catch {}

    // If dragged less than 4px, treat as a direct tap on an item
    const totalDist = Math.abs(e.clientY - startYRef.current)
    if (totalDist < 4) {
      const rect = target.getBoundingClientRect()
      const clickY = e.clientY - rect.top
      const centerY = rect.height / 2
      const slotDelta = Math.round((clickY - centerY) / ITEM_HEIGHT)
      const currentIdx = Math.round(offsetYRef.current / ITEM_HEIGHT)
      const targetIdx = Math.max(0, Math.min(currentIdx + slotDelta, items.length - 1))
      snapTo(targetIdx * ITEM_HEIGHT)
      return
    }

    // Apply inertia
    if (Math.abs(velocityRef.current) > 1.5) {
      decelerateWithInertia(velocityRef.current)
    } else {
      snapTo(offsetYRef.current)
    }
  }

  // Wheel event for desktop trackpad / mouse wheel
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    const nextOffset = Math.max(
      0,
      Math.min(offsetYRef.current + e.deltaY * 0.6, (items.length - 1) * ITEM_HEIGHT)
    )
    setOffsetY(nextOffset)

    if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current)
    scrollTimeoutRef.current = setTimeout(() => {
      snapTo(offsetYRef.current)
    }, 90)
  }
  const scrollTimeoutRef = React.useRef<NodeJS.Timeout | null>(null)

  return (
    <div
      ref={containerRef}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      onWheel={handleWheel}
      className={cn(
        "relative h-full select-none touch-none cursor-grab active:cursor-grabbing overflow-hidden",
        className
      )}
      style={{
        perspective: "1000px",
        perspectiveOrigin: "center center",
      }}
    >
      {/* 3D Cylindrical Drum */}
      <div
        className="relative w-full h-full"
        style={{
          transformStyle: "preserve-3d",
        }}
      >
        {/* Render visible slice for 60fps/120fps performance */}
        {(() => {
          const centerIdx = Math.round(offsetY / ITEM_HEIGHT)
          const minIdx = Math.max(0, centerIdx - 6)
          const maxIdx = Math.min(items.length - 1, centerIdx + 6)
          const visible = []
          for (let idx = minIdx; idx <= maxIdx; idx++) {
            const item = items[idx]
            if (!item) continue
            const itemPos = idx * ITEM_HEIGHT
            const diff = itemPos - offsetY
            const angle = (diff / ITEM_HEIGHT) * ANGLE_PER_ITEM

            if (Math.abs(angle) > 85) continue

            const rad = (angle * Math.PI) / 180
            const ty = Math.sin(rad) * RADIUS
            const tz = Math.cos(rad) * RADIUS - RADIUS
            const opacity = Math.max(0.06, Math.pow(Math.cos(rad), 2))
            const isSelected = Math.abs(diff) < ITEM_HEIGHT * 0.45
            const disabled = isItemDisabled ? isItemDisabled(item) : false

            visible.push(
              <div
                key={getKey(item)}
                style={{
                  height: `${ITEM_HEIGHT}px`,
                  position: "absolute",
                  top: `calc(50% - ${ITEM_HEIGHT / 2}px)`,
                  left: 0,
                  right: 0,
                  transform: `translate3d(0, ${ty}px, ${tz}px) rotateX(${-angle}deg)`,
                  transformOrigin: "center center",
                  opacity: disabled ? Math.min(opacity, 0.28) : opacity,
                  backfaceVisibility: "hidden",
                  WebkitBackfaceVisibility: "hidden",
                }}
                className={cn(
                  "flex items-center transition-colors pointer-events-none px-1 select-none",
                  align === "left" && "justify-start pl-2",
                  align === "center" && "justify-center",
                  align === "right" && "justify-end pr-2.5",
                  disabled && "text-muted-foreground/35 dark:text-neutral-600/50 font-normal",
                  !disabled && (isSelected
                    ? "text-neutral-900 dark:text-white font-medium text-[17px] sm:text-[18px] tracking-tight"
                    : "text-neutral-500 dark:text-neutral-400 font-normal text-[16px] sm:text-[17px]"
                  )
                )}
              >
                <span className="truncate">{getLabel(item)}</span>
              </div>
            )
          }
          return visible
        })()}
      </div>
    </div>
  )
}

export function IOSWheelPicker({ date, time, onChange, mode = "datetime", className }: IOSWheelPickerProps) {
  // Current moment references (memoized for referential stability)
  const todayStr = React.useMemo(() => {
    const now = new Date()
    const y = String(now.getFullYear())
    const m = String(now.getMonth() + 1).padStart(2, "0")
    const d = String(now.getDate()).padStart(2, "0")
    return `${y}-${m}-${d}`
  }, [])

  const curYear = React.useMemo(() => todayStr.split("-")[0], [todayStr])
  const curMonth = React.useMemo(() => todayStr.split("-")[1], [todayStr])
  const curDay = React.useMemo(() => todayStr.split("-")[2], [todayStr])

  // Parse initial date into year, month, day
  const { initialYear, initialMonth, initialDay } = React.useMemo(() => {
    const parts = (date || todayStr).split("-")
    let y = parts[0] || curYear
    let m = String(parts[1] || curMonth).padStart(2, "0")
    let d = String(parts[2] || curDay).padStart(2, "0")
    return { initialYear: y, initialMonth: m, initialDay: d }
  }, [date, todayStr, curYear, curMonth, curDay])

  const [selectedYear, setSelectedYear] = React.useState(initialYear)
  const [selectedMonth, setSelectedMonth] = React.useState(initialMonth)
  const [selectedDay, setSelectedDay] = React.useState(initialDay)

  // Sync external date prop changes
  React.useEffect(() => {
    setSelectedYear(initialYear)
    setSelectedMonth(initialMonth)
    setSelectedDay(initialDay)
  }, [initialYear, initialMonth, initialDay])

  // Year options: current year and future 15 years
  const yearOptions = React.useMemo(() => {
    const startYear = parseInt(curYear, 10)
    return Array.from({ length: 15 }, (_, i) => String(startYear + i))
  }, [curYear])

  // Month options: Jan to Dec
  const monthOptions = React.useMemo(() => [
    { value: "01", label: "Jan" },
    { value: "02", label: "Feb" },
    { value: "03", label: "Mar" },
    { value: "04", label: "Apr" },
    { value: "05", label: "May" },
    { value: "06", label: "Jun" },
    { value: "07", label: "Jul" },
    { value: "08", label: "Aug" },
    { value: "09", label: "Sep" },
    { value: "10", label: "Oct" },
    { value: "11", label: "Nov" },
    { value: "12", label: "Dec" },
  ], [])

  // Days in currently selected month and year
  const daysInMonth = React.useMemo(() => {
    const y = parseInt(selectedYear, 10)
    const m = parseInt(selectedMonth, 10)
    if (isNaN(y) || isNaN(m)) return 31
    return new Date(y, m, 0).getDate()
  }, [selectedYear, selectedMonth])

  // Day options: 1 to daysInMonth
  const dayOptions = React.useMemo(() => {
    return Array.from({ length: daysInMonth }, (_, i) => {
      const val = String(i + 1).padStart(2, "0")
      return { value: val, label: String(i + 1) }
    })
  }, [daysInMonth])

  // Check if month is disabled (past month in current year)
  const isMonthDisabled = React.useCallback(
    (m: { value: string; label: string }) => {
      if (selectedYear === curYear && m.value < curMonth) return true
      return false
    },
    [selectedYear, curYear, curMonth]
  )

  // Check if day is disabled (past day in current month and year)
  const isDayDisabled = React.useCallback(
    (d: { value: string; label: string }) => {
      if (selectedYear === curYear && selectedMonth === curMonth && d.value < curDay) return true
      return false
    },
    [selectedYear, curYear, selectedMonth, curMonth, curDay]
  )

  // Parse 24-hour time into 12-hour components: hour (1-12), minute (00-59), ampm ("AM"|"PM")
  const { initialHour, initialMinute, initialAmpm } = React.useMemo(() => {
    let [h, m] = (time || "10:00").split(":").map(Number)
    if (isNaN(h)) h = 10
    if (isNaN(m)) m = 0

    // If on Today and initial time is in the past, default to current time
    const isToday = (date || todayStr) === todayStr
    const now = new Date()
    if (isToday) {
      const curH24 = now.getHours()
      const curMin = now.getMinutes()
      if (h < curH24 || (h === curH24 && m < curMin)) {
        h = curH24
        m = curMin
      }
    }

    const minuteStr = String(m % 60).padStart(2, "0")
    let hour12 = h % 12
    if (hour12 === 0) hour12 = 12
    const ampm = h >= 12 ? "PM" : "AM"

    return {
      initialHour: String(hour12),
      initialMinute: minuteStr,
      initialAmpm: ampm,
    }
  }, [time, date, todayStr])

  const [selectedHour, setSelectedHour] = React.useState(initialHour)
  const [selectedMinute, setSelectedMinute] = React.useState(initialMinute)
  const [selectedAmpm, setSelectedAmpm] = React.useState<"AM" | "PM">(initialAmpm as "AM" | "PM")

  // Sync external time prop changes
  React.useEffect(() => {
    setSelectedHour(initialHour)
    setSelectedMinute(initialMinute)
    setSelectedAmpm(initialAmpm as "AM" | "PM")
  }, [initialHour, initialMinute, initialAmpm])

  // Hours: 1 to 12
  const hourOptions = React.useMemo(() => {
    return Array.from({ length: 12 }, (_, i) => String(i + 1))
  }, [])

  // Minutes: 00 to 59
  const minuteOptions = React.useMemo(() => {
    return Array.from({ length: 60 }, (_, i) => String(i).padStart(2, "0"))
  }, [])

  // AM / PM
  const ampmOptions = React.useMemo(() => ["AM", "PM"] as const, [])

  // Currently selected full date string
  const currentFullDate = `${selectedYear}-${selectedMonth}-${selectedDay}`

  // Check if a time component is disabled (in the past) when Today is selected
  const isTimeComponentInPast = React.useCallback(
    (type: "ampm" | "hour" | "minute", val: string) => {
      if (currentFullDate !== todayStr) return false

      const now = new Date()
      const curH24 = now.getHours()
      const curMin = now.getMinutes()

      if (type === "ampm") {
        if (val === "AM" && curH24 >= 12) return true
        return false
      }

      if (type === "hour") {
        let h24 = parseInt(val, 10) % 12
        if (selectedAmpm === "PM") h24 += 12
        if (h24 < curH24) return true
        return false
      }

      if (type === "minute") {
        let h24 = parseInt(selectedHour, 10) % 12
        if (selectedAmpm === "PM") h24 += 12
        if (h24 < curH24) return true
        if (h24 === curH24 && parseInt(val, 10) < curMin) return true
        return false
      }

      return false
    },
    [currentFullDate, todayStr, selectedAmpm, selectedHour]
  )

  const isHourDisabled = React.useCallback(
    (h: string) => isTimeComponentInPast("hour", h),
    [isTimeComponentInPast]
  )

  const isMinuteDisabled = React.useCallback(
    (m: string) => isTimeComponentInPast("minute", m),
    [isTimeComponentInPast]
  )

  const isAmpmDisabled = React.useCallback(
    (ap: "AM" | "PM") => isTimeComponentInPast("ampm", ap),
    [isTimeComponentInPast]
  )

  // Check if selected time is in the past when "Today" is selected (minute precision)
  const isTimeInPast = React.useCallback(
    (h12: string, mStr: string, ap: "AM" | "PM") => {
      if (currentFullDate !== todayStr) return false

      const now = new Date()
      let h24 = parseInt(h12, 10) % 12
      if (ap === "PM") h24 += 12
      const minVal = parseInt(mStr, 10)

      const curH24 = now.getHours()
      const curMin = now.getMinutes()

      return h24 < curH24 || (h24 === curH24 && minVal < curMin)
    },
    [currentFullDate, todayStr]
  )

  // Convert (hour12, minute, ampm) back to "HH:mm" (24h) and trigger onChange
  const notifyChange = React.useCallback(
    (newDate: string, h12: string, mStr: string, ap: "AM" | "PM") => {
      let h24 = parseInt(h12, 10) % 12
      if (ap === "PM") h24 += 12
      const time24 = `${String(h24).padStart(2, "0")}:${mStr}`
      onChange(newDate, time24)
    },
    [onChange]
  )

  // Clamp date forward if user selected combination is in the past or exceeds days in month
  React.useEffect(() => {
    let changed = false
    let y = selectedYear
    let m = selectedMonth
    let d = selectedDay

    if (y < curYear) {
      y = curYear
      changed = true
    }
    if (y === curYear) {
      if (m < curMonth) {
        m = curMonth
        changed = true
      }
      if (m === curMonth && d < curDay) {
        d = curDay
        changed = true
      }
    }

    const maxDays = new Date(parseInt(y, 10), parseInt(m, 10), 0).getDate()
    if (parseInt(d, 10) > maxDays) {
      d = String(maxDays).padStart(2, "0")
      changed = true
    }

    if (changed) {
      setSelectedYear(y)
      setSelectedMonth(m)
      setSelectedDay(d)
      notifyChange(`${y}-${m}-${d}`, selectedHour, selectedMinute, selectedAmpm)
    }
  }, [selectedYear, selectedMonth, selectedDay, curYear, curMonth, curDay, selectedHour, selectedMinute, selectedAmpm, notifyChange])

  // Clamp time forward if on Today and currently selected time is in the past
  React.useEffect(() => {
    if (currentFullDate === todayStr && isTimeInPast(selectedHour, selectedMinute, selectedAmpm)) {
      const now = new Date()
      let curH = now.getHours()
      let curM = now.getMinutes()

      let h12 = curH % 12
      if (h12 === 0) h12 = 12
      const ap = curH >= 12 ? "PM" : "AM"
      const mStr = String(curM).padStart(2, "0")

      setSelectedHour(String(h12))
      setSelectedMinute(mStr)
      setSelectedAmpm(ap)
      notifyChange(currentFullDate, String(h12), mStr, ap)
    }
  }, [currentFullDate, todayStr, selectedHour, selectedMinute, selectedAmpm, isTimeInPast, notifyChange])

  const handleDayChange = (newDay: { value: string; label: string }) => {
    let d = newDay.value
    if (selectedYear === curYear && selectedMonth === curMonth && d < curDay) {
      d = curDay
    }
    setSelectedDay(d)
    notifyChange(`${selectedYear}-${selectedMonth}-${d}`, selectedHour, selectedMinute, selectedAmpm)
  }

  const handleMonthChange = (newMonth: { value: string; label: string }) => {
    let m = newMonth.value
    let d = selectedDay
    if (selectedYear === curYear) {
      if (m < curMonth) m = curMonth
      if (m === curMonth && d < curDay) d = curDay
    }
    const maxDays = new Date(parseInt(selectedYear, 10), parseInt(m, 10), 0).getDate()
    if (parseInt(d, 10) > maxDays) d = String(maxDays).padStart(2, "0")
    setSelectedMonth(m)
    setSelectedDay(d)
    notifyChange(`${selectedYear}-${m}-${d}`, selectedHour, selectedMinute, selectedAmpm)
  }

  const handleYearChange = (newYear: string) => {
    let m = selectedMonth
    let d = selectedDay
    if (newYear === curYear) {
      if (m < curMonth) m = curMonth
      if (m === curMonth && d < curDay) d = curDay
    }
    const maxDays = new Date(parseInt(newYear, 10), parseInt(m, 10), 0).getDate()
    if (parseInt(d, 10) > maxDays) d = String(maxDays).padStart(2, "0")
    setSelectedYear(newYear)
    setSelectedMonth(m)
    setSelectedDay(d)
    notifyChange(`${newYear}-${m}-${d}`, selectedHour, selectedMinute, selectedAmpm)
  }

  const handleHourChange = (newHour: string) => {
    setSelectedHour(newHour)
    notifyChange(currentFullDate, newHour, selectedMinute, selectedAmpm)
  }

  const handleMinuteChange = (newMinute: string) => {
    setSelectedMinute(newMinute)
    notifyChange(currentFullDate, selectedHour, newMinute, selectedAmpm)
  }

  const handleAmpmChange = (newAmpm: "AM" | "PM") => {
    setSelectedAmpm(newAmpm)
    notifyChange(currentFullDate, selectedHour, selectedMinute, newAmpm)
  }

  return (
    <div
      style={{ height: "186px" }}
      className={cn(
        "relative w-full overflow-hidden bg-transparent select-none font-sans",
        className
      )}
    >
      {/* 1. Selection Lens: Translucent rounded capsule pill matching Apple standard */}
      <div
        style={{
          height: `${ITEM_HEIGHT + 2}px`,
          top: `calc(50% - ${(ITEM_HEIGHT + 2) / 2}px)`,
        }}
        className={cn(
          "pointer-events-none absolute rounded-xl bg-neutral-200/60 dark:bg-white/[0.08] z-0 inset-x-6 max-w-[300px] mx-auto"
        )}
      />

      {/* 2. Top & Bottom Atmospheric Gradient Masks */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-14 bg-gradient-to-b from-card via-card/75 to-transparent z-20" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-14 bg-gradient-to-t from-card via-card/75 to-transparent z-20" />

      {/* 3. The Interactive 3D Cylindrical Wheels */}
      {mode === "date" ? (
        <div className="relative z-10 grid grid-cols-12 h-full w-full max-w-[300px] mx-auto items-center">
          {/* Day Wheel (col-span-3) - Centered */}
          <div className="col-span-3 h-full">
            <CylinderWheel
              items={dayOptions}
              value={dayOptions.find((d) => d.value === selectedDay) || dayOptions[dayOptions.length - 1] || dayOptions[0]}
              onSelect={handleDayChange}
              getLabel={(d) => d.label}
              getKey={(d) => d.value}
              isItemDisabled={isDayDisabled}
              align="center"
            />
          </div>

          {/* Month Wheel (col-span-5) - Centered */}
          <div className="col-span-5 h-full">
            <CylinderWheel
              items={monthOptions}
              value={monthOptions.find((m) => m.value === selectedMonth) || monthOptions[0]}
              onSelect={handleMonthChange}
              getLabel={(m) => m.label}
              getKey={(m) => m.value}
              isItemDisabled={isMonthDisabled}
              align="center"
            />
          </div>

          {/* Year Wheel (col-span-4) - Centered */}
          <div className="col-span-4 h-full">
            <CylinderWheel
              items={yearOptions}
              value={selectedYear}
              onSelect={handleYearChange}
              getLabel={(y) => y}
              getKey={(y) => y}
              align="center"
            />
          </div>
        </div>
      ) : mode === "time" ? (
        <div className="relative z-10 grid grid-cols-12 h-full w-full max-w-[280px] mx-auto items-center">
          {/* Native iOS Colon separator centered between Hour and Minute */}
          <div
            className="pointer-events-none absolute left-[33.33%] -translate-x-1/2 top-1/2 -translate-y-1/2 font-semibold text-lg text-neutral-800/60 dark:text-neutral-200/60 z-20 select-none pb-0.5"
            aria-hidden="true"
          >
            :
          </div>

          {/* Hour Wheel (col-span-4) - Centered */}
          <div className="col-span-4 h-full">
            <CylinderWheel
              items={hourOptions}
              value={selectedHour}
              onSelect={handleHourChange}
              getLabel={(h) => h}
              getKey={(h) => h}
              isItemDisabled={isHourDisabled}
              align="center"
            />
          </div>

          {/* Minute Wheel (col-span-4) - Centered */}
          <div className="col-span-4 h-full">
            <CylinderWheel
              items={minuteOptions}
              value={selectedMinute}
              onSelect={handleMinuteChange}
              getLabel={(m) => m}
              getKey={(m) => m}
              isItemDisabled={isMinuteDisabled}
              align="center"
            />
          </div>

          {/* AM / PM Wheel (col-span-4) - Centered */}
          <div className="col-span-4 h-full">
            <CylinderWheel
              items={ampmOptions as unknown as ("AM" | "PM")[]}
              value={selectedAmpm}
              onSelect={handleAmpmChange}
              getLabel={(ap) => ap}
              getKey={(ap) => ap}
              isItemDisabled={isAmpmDisabled}
              align="center"
            />
          </div>
        </div>
      ) : (
        <div className="relative z-10 grid grid-cols-12 h-full w-full max-w-[300px] mx-auto items-center">
          {/* Day Wheel (col-span-3) */}
          <div className="col-span-3 h-full">
            <CylinderWheel
              items={dayOptions}
              value={dayOptions.find((d) => d.value === selectedDay) || dayOptions[dayOptions.length - 1] || dayOptions[0]}
              onSelect={handleDayChange}
              getLabel={(d) => d.label}
              getKey={(d) => d.value}
              isItemDisabled={isDayDisabled}
              align="center"
            />
          </div>

          {/* Month Wheel (col-span-5) */}
          <div className="col-span-5 h-full">
            <CylinderWheel
              items={monthOptions}
              value={monthOptions.find((m) => m.value === selectedMonth) || monthOptions[0]}
              onSelect={handleMonthChange}
              getLabel={(m) => m.label}
              getKey={(m) => m.value}
              isItemDisabled={isMonthDisabled}
              align="center"
            />
          </div>

          {/* Year Wheel (col-span-4) */}
          <div className="col-span-4 h-full">
            <CylinderWheel
              items={yearOptions}
              value={selectedYear}
              onSelect={handleYearChange}
              getLabel={(y) => y}
              getKey={(y) => y}
              align="center"
            />
          </div>
        </div>
      )}
    </div>
  )
}
