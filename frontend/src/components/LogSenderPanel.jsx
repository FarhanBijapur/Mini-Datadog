import { useState } from 'react'
import { sendLog } from '../services/api'

const LEVELS = ['INFO', 'WARN', 'ERROR', 'DEBUG']

function LogSenderPanel() {
  const [form, setForm] = useState({
    service: 'payment-service',
    level: 'ERROR',
    message: 'Payment failed',
  })
  const [statusMessage, setStatusMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const onChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const onSubmit = async (event) => {
    event.preventDefault()
    setIsSubmitting(true)
    setStatusMessage('')
    try {
      await sendLog(form)
      setStatusMessage('Log sent successfully.')
      setForm((current) => ({ ...current, message: '' }))
    } catch {
      setStatusMessage('Failed to send log.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-lg transition duration-200 hover:border-slate-500">
      <h2 className="mb-4 text-xl font-semibold text-white">Log Sender Panel</h2>
      <form className="space-y-4" onSubmit={onSubmit}>
        <div>
          <label className="mb-1 block text-sm text-gray-300" htmlFor="service">
            Service
          </label>
          <input
            id="service"
            name="service"
            value={form.service}
            onChange={onChange}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white focus:border-blue-400 focus:outline-none"
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-gray-300" htmlFor="level">
            Level
          </label>
          <select
            id="level"
            name="level"
            value={form.level}
            onChange={onChange}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white focus:border-blue-400 focus:outline-none"
          >
            {LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm text-gray-300" htmlFor="message">
            Message
          </label>
          <textarea
            id="message"
            name="message"
            value={form.message}
            onChange={onChange}
            rows={3}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white focus:border-blue-400 focus:outline-none"
            required
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-800"
        >
          {isSubmitting ? 'Sending...' : 'Send Log'}
        </button>

        {statusMessage && <p className="text-sm text-gray-300">{statusMessage}</p>}
      </form>
    </section>
  )
}

export default LogSenderPanel
