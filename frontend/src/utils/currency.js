// Fallback exchange rates to EUR (approximate, for display purposes only).
// Backend should ideally supply pre-converted amounts for accuracy.
const RATES_TO_EUR = {
  EUR: 1,
  USD: 0.92,
  GBP: 1.17,
  CHF: 1.05,
  PLN: 0.23,
  JPY: 0.006,
  CAD: 0.68,
}

export function toEUR(amount, currency) {
  const rate = RATES_TO_EUR[currency?.toUpperCase()]
  if (rate == null) return null
  return amount * rate
}

export function formatCurrency(amount, currency) {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

export function formatEUR(amount) {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}
