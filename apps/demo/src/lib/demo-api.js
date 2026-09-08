export const DEFAULT_DENTAL_DEMO = {
  status: "active",
  template_id: "dental-default",
  business: {
    name: "Smile Dental Studio",
    category: "Dental Clinic",
    phone: "+91 98765 43210",
    email: "contact@smiledental.com",
    whatsapp: "+91 98765 43210",
    address: "402 Medical Square, Drive-In Road",
    city: "Ahmedabad",
    state: "Gujarat",
    country: "India",
    postal_code: "380054",
    opening_hours: "Mon-Sat: 9:00 AM - 8:00 PM",
    rating: 4.9,
    reviews_count: 142,
    place_id: null,
    website: null,
    logo_url: null,
    whatsapp_url: null,
    social_links: null,
  },
  customization: {
    hero_headline: "Where healthy smiles begin.",
    hero_subheadline: "Comprehensive, gentle dental care tailored to your family's needs.",
    hero_image_url: "/hero_dentist_v1.png",
    doctor_name: "Dr. Sarah Jenkins",
    doctor_title: "Chief Dental Surgeon",
    doctor_bio: "Specializing in cosmetic dentistry, dental implants, and compassionate preventive dental care with over 10 years of clinical excellence.",
    doctor_photo_url: "/female_dentist_portrait_1.png",
    clinic_interior_url: "/hero_dentist_v1.png",
    tagline: null,
    about_text: null,
    brand_colors: null,
    doctors: null,
    testimonials: null,
    faqs: null,
    facilities: null,
    certifications: null,
    insurance_providers: null,
    emergency_info: null,
    booking_url: null,
    branches: null,
    reusable_images: null,
    whatsapp_url: null,
    social_links: null,
  },
}

function getApiBaseUrl() {
  return (
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.FASTUI_API_URL ||
    "http://localhost:8000"
  ).replace(/\/+$/, "")
}

/**
 * Fetch dynamic presentation data for a prospect demo by token.
 * Server-side or client-side compatible.
 */
export async function getDemoData(token) {
  if (!token) return DEFAULT_DENTAL_DEMO

  // Guard against file requests, extensions, and malformed tokens
  if (token.includes(".") || !/^[A-Za-z0-9_-]{10,64}$/.test(token)) {
    return null
  }

  const apiUrl = getApiBaseUrl()
  try {
    const res = await fetch(`${apiUrl}/public/v1/demos/${encodeURIComponent(token)}`, {
      next: { revalidate: 300 }, // 5 min ISR cache
      headers: {
        Accept: "application/json",
      },
    })

    if (!res.ok) {
      if (res.status === 404) {
        return null
      }
      console.warn(`[FastUI Demo] API returned ${res.status} for token ${token}. Using default fallback.`);
      return DEFAULT_DENTAL_DEMO
    }

    const data = await res.json()
    return {
      status: data.status || "active",
      template_id: data.template_id || "dental-default",
      business: { ...DEFAULT_DENTAL_DEMO.business, ...(data.business || {}) },
      customization: { ...DEFAULT_DENTAL_DEMO.customization, ...(data.customization || {}) },
    }
  } catch (err) {
    console.warn(`[FastUI Demo] Network error resolving demo ${token}:`, err.message)
    return null
  }
}

/**
 * Record engagement events on the demo site (client-side only).
 */
export async function trackDemoEvent(token, { event_type, session_id, page_path, metadata }) {
  if (!token || typeof window === "undefined") return

  const apiUrl = getApiBaseUrl()
  try {
    await fetch(`${apiUrl}/public/v1/demos/${encodeURIComponent(token)}/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        event_type,
        session_id: session_id || null,
        page_path: page_path || window.location.pathname,
        referrer: document.referrer || null,
        metadata_json: metadata || null,
      }),
    })
  } catch {
    // Non-blocking analytics telemetry failure
  }
}
