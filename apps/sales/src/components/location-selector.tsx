"use client"

import * as React from "react"
import { ChevronDown, X, MapPin } from "lucide-react"
import { Country, State, City, ICountry, IState, ICity } from "country-state-city"
import { cn } from "@/lib/utils"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import { Command as CommandPrimitive } from "cmdk"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

export interface StructuredLocation {
  city: string | null
  region: string | null
  country: string
  countryCode: string
  regionCode: string | null
  formatted: string
}

export interface LocationSearchResult {
  id: string
  title: string
  subtitle: string
  type: "city" | "region" | "country"
  data: StructuredLocation
}

// Popular starter locations to show when the search is empty
const getPopularLocations = (): LocationSearchResult[] => {
  const popular = [
    { city: "Mumbai", state: "Maharashtra", countryCode: "IN" },
    { city: "Ahmedabad", state: "Gujarat", countryCode: "IN" },
    { city: "Bengaluru", state: "Karnataka", countryCode: "IN" },
    { city: "New York", state: "New York", countryCode: "US" },
    { city: "San Francisco", state: "California", countryCode: "US" },
    { city: "London", state: "England", countryCode: "GB" },
    { city: "Dubai", state: "Dubai", countryCode: "AE" },
    { city: "Singapore", state: null, countryCode: "SG" },
  ]

  const results: LocationSearchResult[] = []
  for (const item of popular) {
    const country = Country.getCountryByCode(item.countryCode)
    if (!country) continue
    const countryName = country.name
    const region = item.state
    const formatted = [item.city, region, countryName].filter(Boolean).join(", ")
    results.push({
      id: `popular_${item.city}_${item.countryCode}`,
      title: item.city,
      subtitle: [region, countryName].filter(Boolean).join(", "),
      type: "city",
      data: {
        city: item.city,
        region: region,
        country: countryName,
        countryCode: item.countryCode,
        regionCode: null,
        formatted,
      },
    })
  }
  return results
}

const POPULAR_LOCATIONS = getPopularLocations()

// Fast in-memory lookup cache for country/state code names
const countryCodeToNameMap = new Map<string, string>()
const stateCodeToNameMap = new Map<string, string>()

const getCountryName = (code: string): string => {
  if (!code) return ""
  if (countryCodeToNameMap.has(code)) return countryCodeToNameMap.get(code)!
  const c = Country.getCountryByCode(code)
  const name = c ? c.name : code
  countryCodeToNameMap.set(code, name)
  return name
}

const getStateName = (stateCode: string, countryCode: string): string => {
  if (!stateCode || !countryCode) return ""
  const key = `${countryCode}_${stateCode}`
  if (stateCodeToNameMap.has(key)) return stateCodeToNameMap.get(key)!
  const s = State.getStateByCodeAndCountry(stateCode, countryCode)
  const name = s ? s.name : stateCode
  stateCodeToNameMap.set(key, name)
  return name
}

// Global cached datasets
let cachedCountries: ICountry[] | null = null
let cachedStates: IState[] | null = null
let cachedCities: ICity[] | null = null

const getCountries = () => {
  if (!cachedCountries) cachedCountries = Country.getAllCountries()
  return cachedCountries
}

const getStates = () => {
  if (!cachedStates) cachedStates = State.getAllStates()
  return cachedStates
}

const getCities = () => {
  if (!cachedCities) cachedCities = City.getAllCities()
  return cachedCities
}

/**
 * Searches across Cities using country-state-city (matching city name, state, or country)
 */
export function searchLocations(query: string, maxResults = 30): LocationSearchResult[] {
  const cleanQuery = query.trim().toLowerCase()
  if (!cleanQuery) return POPULAR_LOCATIONS

  const results: LocationSearchResult[] = []
  const seenKeys = new Set<string>()

  const countries = getCountries()
  const states = getStates()
  const cities = getCities()

  // Pre-match matching country codes & state codes for area-wide matching
  const matchingCountryCodes = new Set<string>()
  for (const c of countries) {
    if (c.name.toLowerCase().includes(cleanQuery) || c.isoCode.toLowerCase() === cleanQuery) {
      matchingCountryCodes.add(c.isoCode)
    }
  }

  const matchingStateCodes = new Set<string>()
  for (const s of states) {
    if (s.name.toLowerCase().includes(cleanQuery) || (s.isoCode && s.isoCode.toLowerCase() === cleanQuery)) {
      matchingStateCodes.add(`${s.countryCode}_${s.isoCode}`)
    }
  }

  // 1. Direct City Name Matches (Prefix match first for highest relevance)
  for (const city of cities) {
    const cityNameLower = city.name.toLowerCase()
    if (cityNameLower.startsWith(cleanQuery)) {
      const countryName = getCountryName(city.countryCode)
      const regionName = city.stateCode ? getStateName(city.stateCode, city.countryCode) : ""
      const key = `city_${city.name}_${regionName}_${city.countryCode}`

      if (!seenKeys.has(key)) {
        seenKeys.add(key)
        const subtitle = [regionName, countryName].filter(Boolean).join(", ")
        const formatted = [city.name, regionName, countryName].filter(Boolean).join(", ")
        results.push({
          id: key,
          title: city.name,
          subtitle,
          type: "city",
          data: {
            city: city.name,
            region: regionName || null,
            country: countryName,
            countryCode: city.countryCode,
            regionCode: city.stateCode || null,
            formatted,
          },
        })
        if (results.length >= maxResults) return results
      }
    }
  }

  // 2. City Name Substring Matches
  for (const city of cities) {
    const cityNameLower = city.name.toLowerCase()
    if (cityNameLower.includes(cleanQuery) && !cityNameLower.startsWith(cleanQuery)) {
      const countryName = getCountryName(city.countryCode)
      const regionName = city.stateCode ? getStateName(city.stateCode, city.countryCode) : ""
      const key = `city_${city.name}_${regionName}_${city.countryCode}`

      if (!seenKeys.has(key)) {
        seenKeys.add(key)
        const subtitle = [regionName, countryName].filter(Boolean).join(", ")
        const formatted = [city.name, regionName, countryName].filter(Boolean).join(", ")
        results.push({
          id: key,
          title: city.name,
          subtitle,
          type: "city",
          data: {
            city: city.name,
            region: regionName || null,
            country: countryName,
            countryCode: city.countryCode,
            regionCode: city.stateCode || null,
            formatted,
          },
        })
        if (results.length >= maxResults) return results
      }
    }
  }

  // 3. State or Country matches (returns cities within matched regions/countries)
  if (matchingStateCodes.size > 0 || matchingCountryCodes.size > 0) {
    for (const city of cities) {
      const stateKey = `${city.countryCode}_${city.stateCode}`
      if (matchingStateCodes.has(stateKey) || matchingCountryCodes.has(city.countryCode)) {
        const countryName = getCountryName(city.countryCode)
        const regionName = city.stateCode ? getStateName(city.stateCode, city.countryCode) : ""
        const key = `city_${city.name}_${regionName}_${city.countryCode}`

        if (!seenKeys.has(key)) {
          seenKeys.add(key)
          const subtitle = [regionName, countryName].filter(Boolean).join(", ")
          const formatted = [city.name, regionName, countryName].filter(Boolean).join(", ")
          results.push({
            id: key,
            title: city.name,
            subtitle,
            type: "city",
            data: {
              city: city.name,
              region: regionName || null,
              country: countryName,
              countryCode: city.countryCode,
              regionCode: city.stateCode || null,
              formatted,
            },
          })
          if (results.length >= maxResults) return results
        }
      }
    }
  }

  return results
}

export interface LocationSelectorProps {
  value?: StructuredLocation | string | null
  onChange?: ((location: StructuredLocation) => void) | ((value: string) => void)
  onLocationChange?: (location: StructuredLocation) => void
  placeholder?: string
  className?: string
  disabled?: boolean
}

export function LocationSelector({
  value,
  onChange,
  onLocationChange,
  placeholder = "Search city, region or country...",
  className = "",
  disabled = false,
}: LocationSelectorProps) {
  const [open, setOpen] = React.useState(false)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [searchResults, setSearchResults] = React.useState<LocationSearchResult[]>(POPULAR_LOCATIONS)

  const handleSelect = React.useCallback(
    (loc: StructuredLocation) => {
      // @ts-ignore
      onChange?.(loc)
      onLocationChange?.(loc)
      setOpen(false)
      setSearchQuery("")
    },
    [onChange, onLocationChange]
  )

  // Compute display string
  const displayLabel = React.useMemo(() => {
    if (!value) return ""
    if (typeof value === "string") return value
    return value.formatted || [value.city, value.region, value.country].filter(Boolean).join(", ")
  }, [value])

  // Update search results on input change with slight debounce
  React.useEffect(() => {
    const handler = setTimeout(() => {
      const results = searchLocations(searchQuery)
      setSearchResults(results)
    }, 50)
    return () => clearTimeout(handler)
  }, [searchQuery])

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          disabled={disabled}
          aria-expanded={open}
          aria-label="Location"
          className={cn(
            "flex items-center justify-between w-full h-[44px] px-5 rounded-full bg-accent/50 hover:bg-accent/80 text-[15px] focus:outline-none focus:ring-2 focus:ring-foreground/20 transition-all group cursor-pointer disabled:opacity-50 disabled:pointer-events-none",
            open && "opacity-0 pointer-events-none",
            className
          )}
        >
          <div className="flex items-center min-w-0 flex-1">
            <span className={cn("truncate font-medium", !displayLabel && "text-muted-foreground/60")}>
              {displayLabel || placeholder}
            </span>
          </div>
          <ChevronDown size={16} className="text-muted-foreground ml-2 shrink-0 opacity-50 group-hover:opacity-100 transition-opacity" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        className="w-[var(--radix-popover-trigger-width)] p-0 rounded-[22px] shadow-none overflow-hidden border-none bg-popover text-popover-foreground"
        align="start"
        side="bottom"
        sideOffset={-44}
      >
        <Command shouldFilter={false} className="p-0 bg-transparent">
          <div className="flex items-center w-full h-[44px] px-5 border-b border-border/40">
            <CommandPrimitive.Input
              placeholder={placeholder}
              value={searchQuery}
              onValueChange={setSearchQuery}
              className="flex-1 bg-transparent text-[15px] font-medium outline-none placeholder:text-muted-foreground/60 placeholder:font-medium"
              autoFocus
            />
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="ml-2 text-muted-foreground shrink-0 opacity-50 hover:opacity-100 transition-opacity cursor-pointer p-1"
              aria-label="Close location search"
            >
              <X size={16} />
            </button>
          </div>
          <CommandList className="max-h-[280px] overflow-y-auto no-scrollbar p-1.5">
            {searchResults.length === 0 ? (
              <CommandEmpty className="py-6 text-center text-[15px] text-muted-foreground">
                No cities found.
              </CommandEmpty>
            ) : (
              <CommandGroup className="p-0">
                {searchResults.map((result) => {
                  const isSelected = displayLabel === result.data.formatted
                  return (
                    <CommandPrimitive.Item
                      key={result.id}
                      value={result.data.formatted}
                      onSelect={() => handleSelect(result.data)}
                      className={cn(
                        "flex items-center justify-between w-full px-4 py-2.5 cursor-pointer rounded-[14px] font-medium text-[15px] transition-colors mb-0.5 outline-none select-none",
                        isSelected
                          ? "bg-accent/60 text-foreground"
                          : "text-muted-foreground hover:bg-accent/40 hover:text-foreground data-[selected=true]:bg-accent/40 data-[selected=true]:text-foreground"
                      )}
                    >
                      <div className="flex flex-col text-left min-w-0 flex-1 mr-3">
                        <span className="font-medium text-[15px] text-foreground truncate">
                          {result.title}
                        </span>
                        {result.subtitle && (
                          <span className="text-xs text-muted-foreground truncate">
                            {result.subtitle}
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-accent/80 text-muted-foreground font-medium shrink-0 ml-auto self-center">
                        City
                      </span>
                    </CommandPrimitive.Item>
                  )
                })}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}