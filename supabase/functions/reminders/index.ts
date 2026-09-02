import { handleReminders } from "./handler.ts"

// Bootstrap HTTP server for Supabase Edge Runtime
Deno.serve(handleReminders)

export default {
  fetch: handleReminders,
}
