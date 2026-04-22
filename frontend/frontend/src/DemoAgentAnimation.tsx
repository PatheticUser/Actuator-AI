import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Zap, Users, BarChart3, Globe, FileCheck } from 'lucide-react'

const AGENT_ICONS = [
  { icon: Shield, color: '#f59e0b', name: 'Security' },
  { icon: Zap, color: '#06b6d4', name: 'Technical' },
  { icon: Users, color: '#8b5cf6', name: 'Success' },
  { icon: BarChart3, color: '#22c55e', name: 'Billing' },
  { icon: Globe, color: '#0ea5e9', name: 'Linguistic' },
  { icon: FileCheck, color: '#ef4444', name: 'Audit' }
]

export function DemoAgentAnimation() {
  const [currentAgent, setCurrentAgent] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentAgent(prev => (prev + 1) % AGENT_ICONS.length)
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="demo-agent-animation">
      <AnimatePresence mode="wait">
        <motion.div
          key={currentAgent}
          className="agent-demo-icon"
          initial={{ opacity: 0, scale: 0.8, rotate: -10 }}
          animate={{ opacity: 1, scale: 1, rotate: 0 }}
          exit={{ opacity: 0, scale: 1.2, rotate: 10 }}
          transition={{ duration: 0.5 }}
          style={{ color: AGENT_ICONS[currentAgent].color }}
        >
          {AGENT_ICONS[currentAgent].icon &&
            React.createElement(AGENT_ICONS[currentAgent].icon, { size: 48 })
          }
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="agent-demo-name"
          >
            {AGENT_ICONS[currentAgent].name}
          </motion.span>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}