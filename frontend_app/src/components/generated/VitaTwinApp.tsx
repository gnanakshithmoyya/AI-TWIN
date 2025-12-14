import React, { useState, useRef, useEffect } from 'react';
import { Home, Activity, MessageCircle, FileText, TrendingUp, ChevronRight, ArrowUpRight, ArrowDownRight, Minus, Upload, X, Check, Search, Calendar, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TwinVisual } from './TwinVisual';

// --- TYPES ---
type Screen = 'home' | 'dashboard' | 'chat' | 'labs' | 'trends';
type Status = 'normal' | 'elevated' | 'high' | 'low';
type Trend = 'up' | 'down' | 'stable';
interface Metric {
  id: string;
  name: string;
  value: string;
  unit: string;
  status: Status;
  trend: Trend;
  description: string;
  history: {
    date: string;
    value: number;
  }[];
  category: 'metabolic' | 'heart' | 'lifestyle' | 'nutrition';
  insight: string;
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

const DEFAULT_HEALTH = {
  fasting_glucose: 118,
  bp_systolic: 118,
  bp_diastolic: 76,
  sleep_hours: 6.5,
  activity_minutes: 30,
  history: {
    fasting_glucose: [132, 125],
    total_cholesterol: [210, 205],
    ldl: [170, 160, 150],
    triglycerides: [200, 190],
    bmi: [31, 30],
  }
};

// --- MOCK DATA ---
const METRICS: Metric[] = [{
  id: 'glucose',
  name: 'Fasting Glucose',
  value: '98',
  unit: 'mg/dL',
  status: 'normal',
  trend: 'down',
  description: 'Optimal range is 70-100 mg/dL.',
  insight: 'Your glucose levels are stable and within the optimal range, indicating good metabolic health.',
  category: 'metabolic',
  history: [{
    date: 'Jan',
    value: 110
  }, {
    date: 'Feb',
    value: 105
  }, {
    date: 'Mar',
    value: 102
  }, {
    date: 'Apr',
    value: 98
  }]
}, {
  id: 'ldl',
  name: 'LDL Cholesterol',
  value: '145',
  unit: 'mg/dL',
  status: 'elevated',
  trend: 'down',
  description: 'Considered elevated. Normal is < 100.',
  insight: 'Your LDL decreased from 175 → 160 → 145. This is a positive trend.',
  category: 'heart',
  history: [{
    date: 'Jan',
    value: 175
  }, {
    date: 'Feb',
    value: 160
  }, {
    date: 'Mar',
    value: 155
  }, {
    date: 'Apr',
    value: 145
  }]
}, {
  id: 'hrv',
  name: 'HRV',
  value: '42',
  unit: 'ms',
  status: 'normal',
  trend: 'up',
  description: 'Higher is generally better.',
  insight: 'Your recovery score is improving. This suggests your nervous system is balancing stress well.',
  category: 'heart',
  history: [{
    date: 'Jan',
    value: 35
  }, {
    date: 'Feb',
    value: 38
  }, {
    date: 'Mar',
    value: 40
  }, {
    date: 'Apr',
    value: 42
  }]
}, {
  id: 'sleep',
  name: 'Deep Sleep',
  value: '1h 12m',
  unit: '',
  status: 'normal',
  trend: 'stable',
  description: 'Healthy range: 1-2 hours.',
  insight: 'Consistent deep sleep supports cognitive recovery and immune function.',
  category: 'lifestyle',
  history: [{
    date: 'Jan',
    value: 65
  }, {
    date: 'Feb',
    value: 70
  }, {
    date: 'Mar',
    value: 72
  }, {
    date: 'Apr',
    value: 72
  }]
}];

// --- ANIMATION VARIANTS ---
const pageVariants = {
  initial: {
    opacity: 0,
    y: 10
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: [0.22, 1, 0.36, 1]
    } // Long gentle ease
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: {
      duration: 0.4,
      ease: "easeIn"
    }
  }
};
const cardVariants = {
  hidden: {
    opacity: 0,
    y: 20
  },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.1,
      duration: 0.5,
      ease: "easeOut"
    }
  })
};

// --- SHARED COMPONENTS ---

const Header = ({
  title,
  subtitle
}: {
  title: string;
  subtitle?: string;
}) => <div className="mb-8 pt-4">
    <motion.h1 initial={{
    opacity: 0
  }} animate={{
    opacity: 1
  }} className="text-3xl font-semibold text-vita-text tracking-tight">
      {title}
    </motion.h1>
    {subtitle && <motion.p initial={{
    opacity: 0
  }} animate={{
    opacity: 1
  }} transition={{
    delay: 0.1
  }} className="text-vita-text-muted mt-2 text-lg font-light leading-relaxed">
        {subtitle}
      </motion.p>}
  </div>;
const Card = ({
  children,
  className = '',
  onClick
}: {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}) => <motion.div onClick={onClick} whileHover={onClick ? {
  scale: 1.01,
  boxShadow: "0 10px 30px -10px rgba(0,0,0,0.05)"
} : {}} whileTap={onClick ? {
  scale: 0.99
} : {}} className={`bg-white rounded-[2rem] p-6 shadow-sm border border-vita-border/60 ${onClick ? 'cursor-pointer' : ''} ${className}`}>
    {children}
  </motion.div>;
const TrendBadge = ({
  trend
}: {
  trend: Trend;
}) => {
  const config = {
    up: {
      icon: ArrowUpRight,
      color: 'text-vita-sage',
      bg: 'bg-vita-sage-light'
    },
    down: {
      icon: ArrowDownRight,
      color: 'text-vita-sage',
      bg: 'bg-vita-sage-light'
    },
    // Assuming down is good for some or neutral
    stable: {
      icon: Minus,
      color: 'text-vita-text-muted',
      bg: 'bg-gray-100'
    }
  };

  // Custom logic for "bad" trends could be added here, but keeping it neutral/positive as requested
  // For LDL, down is good (Sage). For HRV, up is good (Sage).
  // Keeping it simple and calm.

  const {
    icon: Icon,
    color,
    bg
  } = config[trend];
  return <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full ${bg} ${color} text-xs font-medium`}>
      <Icon className="w-3.5 h-3.5" />
      <span className="capitalize">{trend}</span>
    </div>;
};
const StatusLabel = ({
  status
}: {
  status: Status;
}) => {
  const styles = {
    normal: 'text-vita-sage bg-vita-sage-light',
    elevated: 'text-[#B08968] bg-[#FFF9F0]',
    // Soft Amber
    high: 'text-[#C46D6D] bg-[#FFF0F0]',
    // Soft Red (very muted)
    low: 'text-[#6D8BC4] bg-[#F0F7FF]' // Soft Blue
  };
  return <span className={`px-3 py-1 rounded-full text-xs font-medium tracking-wide ${styles[status]}`}>
      {status === 'normal' ? 'Optimal' : status.charAt(0).toUpperCase() + status.slice(1)}
    </span>;
};

// --- SCREENS ---

const HomeScreen = ({
  onNavigate
}: {
  onNavigate: (s: Screen) => void;
}) => {
  return <div className="h-full flex flex-col relative overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-white to-transparent pointer-events-none" />

      <div className="flex-1 flex flex-col items-center justify-center relative z-10 pt-10">
        <motion.div initial={{
        opacity: 0,
        scale: 0.95
      }} animate={{
        opacity: 1,
        scale: 1
      }} transition={{
        duration: 1,
        ease: "easeOut"
      }} className="relative mb-8">
          <TwinVisual status="improving" className="scale-125" />
          
          {/* Subtle Pulse Rings behind Twin */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none -z-10">
            <motion.div animate={{
            scale: [1, 1.2, 1],
            opacity: [0, 0.2, 0]
          }} transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }} className="w-64 h-64 rounded-full border border-vita-sage/20" />
            <motion.div animate={{
            scale: [1, 1.4, 1],
            opacity: [0, 0.1, 0]
          }} transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1
          }} className="w-80 h-80 rounded-full border border-vita-sage/10" />
          </div>
        </motion.div>

        <div className="text-center max-w-lg mx-auto px-6 z-20">
          <motion.div initial={{
          opacity: 0,
          y: 10
        }} animate={{
          opacity: 1,
          y: 0
        }} transition={{
          delay: 0.3
        }} className="flex items-center justify-center gap-2 mb-4">
            <div className="px-4 py-1.5 rounded-full bg-white border border-vita-border/50 shadow-sm flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-vita-sage opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-vita-sage"></span>
              </span>
              <span className="text-xs font-medium text-vita-text-muted uppercase tracking-wider">System Status: Stable</span>
            </div>
          </motion.div>

          <motion.h1 initial={{
          opacity: 0,
          y: 10
        }} animate={{
          opacity: 1,
          y: 0
        }} transition={{
          delay: 0.4
        }} className="text-4xl font-semibold text-vita-text mb-4 tracking-tight">
            Good morning.
          </motion.h1>
          
          <motion.p initial={{
          opacity: 0,
          y: 10
        }} animate={{
          opacity: 1,
          y: 0
        }} transition={{
          delay: 0.5
        }} className="text-vita-text-muted text-xl mb-10 font-light leading-relaxed">
            This is your Body Twin. <br />
            <span className="text-vita-sage">2 metrics improving</span> · <span className="text-vita-amber">1 needs attention</span>
          </motion.p>

          <motion.div initial={{
          opacity: 0,
          y: 10
        }} animate={{
          opacity: 1,
          y: 0
        }} transition={{
          delay: 0.6
        }} className="grid grid-cols-1 md:grid-cols-3 gap-3 w-full">
             <button onClick={() => onNavigate('dashboard')} className="flex items-center justify-center gap-2 px-6 py-4 bg-vita-text text-white rounded-2xl font-medium shadow-lg shadow-gray-200/50 hover:bg-vita-text/90 hover:scale-[1.02] active:scale-[0.98] transition-all">
               View Dashboard
             </button>
             <button onClick={() => onNavigate('chat')} className="flex items-center justify-center gap-2 px-6 py-4 bg-white text-vita-text border border-vita-border rounded-2xl font-medium hover:bg-vita-bg hover:border-vita-sage/30 active:scale-[0.98] transition-all">
               Chat with Twin
             </button>
             <button onClick={() => onNavigate('labs')} className="flex items-center justify-center gap-2 px-6 py-4 bg-white text-vita-text border border-vita-border rounded-2xl font-medium hover:bg-vita-bg hover:border-vita-sage/30 active:scale-[0.98] transition-all">
               Upload Report
             </button>
          </motion.div>
        </div>
      </div>
    </div>;
};
const DashboardScreen = () => {
  const [activeCat, setActiveCat] = useState('All');
  const [metrics, setMetrics] = useState<Metric[]>(METRICS);
  const [disclaimer, setDisclaimer] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const severityToStatus = (severity?: string): Status => {
    if (!severity) return 'normal';
    if (severity === 'low' || severity === 'context') return 'normal';
    if (severity === 'moderate') return 'elevated';
    if (severity === 'high' || severity === 'critical') return 'high';
    return 'normal';
  };

  const trendDirToTrend = (dir?: string): Trend => {
    if (dir === 'improving' || dir === 'down') return 'down';
    if (dir === 'worsening' || dir === 'up') return 'up';
    return 'stable';
  };

  const mapCategory = (name: string): Metric['category'] => {
    const lower = name.toLowerCase();
    if (lower.includes('glucose')) return 'metabolic';
    if (lower.includes('cholesterol') || lower.includes('blood pressure') || lower.includes('ldl') || lower.includes('hdl') || lower.includes('triglycerides')) return 'heart';
    if (lower.includes('sleep') || lower.includes('activity')) return 'lifestyle';
    if (lower.includes('vitamin') || lower.includes('bmi') || lower.includes('ferritin')) return 'nutrition';
    return 'metabolic';
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await fetch(`${API_BASE}/twin/summary`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(DEFAULT_HEALTH),
        });
        if (!resp.ok) throw new Error(`Summary failed: ${resp.status}`);
        const data = await resp.json();
        const summary = data.summary || data;
        setDisclaimer(data.disclaimer || '');
        if (summary?.signals) {
          const mapped = summary.signals.map((sig: any, idx: number): Metric => {
            const history = sig.sparkline?.values || [];
            const historyPoints = history.map((v: number, i: number) => ({ date: `t${i + 1}`, value: v }));
            return {
              id: (sig.name?.toLowerCase().replace(/\s+/g, '-') || 'signal') + idx,
              name: sig.name || 'Signal',
              value: String(sig.value ?? ''),
              unit: '',
              status: severityToStatus(sig.severity),
              trend: trendDirToTrend(sig.trend?.direction),
              description: sig.explanation?.why_it_matters || sig.explanation?.rule || 'Rule-based health signal.',
              insight: sig.explanation?.rule || '',
              category: mapCategory(sig.name || ''),
              history: historyPoints.length ? historyPoints : [{ date: 'Now', value: Number(sig.value) || 0 }],
            };
          });
          setMetrics(mapped);
        }
      } catch (err: any) {
        setError(err.message || 'Unable to load data');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const categories = ['All', 'Metabolic', 'Heart', 'Lifestyle', 'Nutrition'];
  const filteredMetrics = activeCat === 'All' ? metrics : metrics.filter(m => m.category.toLowerCase() === activeCat.toLowerCase());
  return <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit" className="max-w-5xl mx-auto p-6 md:p-12 pb-24">
      <Header title="Twin Dashboard" subtitle="A calm, structured view of your physiology." />

      {loading && <p className="text-sm text-vita-text-muted mb-4">Loading latest signals...</p>}
      {error && <p className="text-sm text-red-500 mb-4">Error: {error}</p>}

      {/* Category Pills */}
      <div className="flex flex-wrap gap-2 mb-10">
        {categories.map((cat, i) => <motion.button key={cat} initial={{
        opacity: 0,
        scale: 0.9
      }} animate={{
        opacity: 1,
        scale: 1
      }} transition={{
        delay: i * 0.05
      }} onClick={() => setActiveCat(cat)} className={`px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-300 ${activeCat === cat ? 'bg-vita-text text-white shadow-md' : 'bg-white text-vita-text-muted border border-vita-border hover:bg-vita-bg'}`}>
            {cat}
          </motion.button>)}
      </div>

      {disclaimer && <p className="text-xs text-vita-text-muted mb-4">{disclaimer}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <AnimatePresence mode="popLayout">
          {filteredMetrics.map((metric, i) => <motion.div layout key={metric.id} variants={cardVariants} custom={i} initial="hidden" animate="visible" exit={{
          opacity: 0,
          scale: 0.95
        }}>
              <Card className="hover:border-vita-sage/30 transition-colors h-full flex flex-col justify-between group">
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${metric.status === 'normal' ? 'bg-vita-sage' : 'bg-vita-amber'}`} />
                      <h3 className="text-lg font-semibold text-vita-text">{metric.name}</h3>
                    </div>
                    <StatusLabel status={metric.status} />
                  </div>
                  
                  <div className="flex items-baseline gap-2 mb-6">
                    <span className="text-4xl font-light text-vita-text tracking-tight">{metric.value}</span>
                    <span className="text-sm text-vita-text-muted font-medium">{metric.unit}</span>
                  </div>
                  
                  <div className="mb-6 h-16 w-full relative">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={metric.history}>
                        <defs>
                          <linearGradient id={`grad-${metric.id}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={metric.status === 'normal' ? '#8DA399' : '#D4B483'} stopOpacity={0.2} />
                            <stop offset="95%" stopColor={metric.status === 'normal' ? '#8DA399' : '#D4B483'} stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <Area type="monotone" dataKey="value" stroke={metric.status === 'normal' ? '#8DA399' : '#D4B483'} fillOpacity={1} fill={`url(#grad-${metric.id})`} strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="pt-4 border-t border-vita-border/50">
                   <p className="text-sm text-vita-text-muted leading-relaxed">
                     <span className="font-medium text-vita-text">Why this matters:</span> {metric.description}
                   </p>
                </div>
              </Card>
            </motion.div>)}
        </AnimatePresence>
      </div>
    </motion.div>;
};
const ChatScreen = () => {
  const [messages, setMessages] = useState([{
    id: 1,
    sender: 'twin',
    text: "Hello. I've analyzed your latest report. Your metabolic markers are looking stable, though your sleep patterns suggest you might benefit from earlier rest. How are you feeling today?"
  }]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: input
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setSending(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/twin/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: input,
          health_state: DEFAULT_HEALTH,
        }),
      });
      if (!resp.ok) throw new Error(`Chat failed: ${resp.status}`);
      const data = await resp.json();
      const reply = data.reply || "I'm here to help with educational insights only.";
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'twin',
        text: reply
      }]);
    } catch (err: any) {
      setError(err.message || 'Unable to reach twin right now.');
      setMessages(prev => [...prev, {
        id: Date.now() + 2,
        sender: 'twin',
        text: "I'm having trouble connecting right now. Please try again shortly."
      }]);
    } finally {
      setSending(false);
    }
  };
  useEffect(() => {
    endRef.current?.scrollIntoView({
      behavior: 'smooth'
    });
  }, [messages]);
  return <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit" className="max-w-3xl mx-auto h-full flex flex-col p-6">
      <div className="flex-none mb-4">
        <h1 className="text-2xl font-semibold text-vita-text text-center">Chat with Twin</h1>
        <div className="flex justify-center mt-2">
           <div className="px-3 py-1 rounded-full bg-vita-sage-light text-vita-sage text-xs font-medium">
             Active & Listening
           </div>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto space-y-8 p-4">
        {messages.map((msg, i) => <motion.div key={msg.id} initial={{
        opacity: 0,
        y: 10
      }} animate={{
        opacity: 1,
        y: 0
      }} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.sender === 'twin' && <div className="w-8 h-8 rounded-full overflow-hidden mr-3 mt-1 flex-shrink-0 bg-vita-bg">
                <TwinVisual status="stable" minimized className="w-full h-full" />
              </div>}
            <div className={`max-w-[85%] p-5 rounded-2xl text-[1.05rem] leading-relaxed shadow-sm ${msg.sender === 'user' ? 'bg-vita-text text-white rounded-br-sm' : 'bg-white text-vita-text border border-vita-border rounded-bl-sm'}`}>
              {msg.text}
            </div>
          </motion.div>)}
        <div ref={endRef} />
      </div>

      <div className="flex-none pt-4">
        <div className="relative shadow-lg shadow-gray-100 rounded-2xl">
          <input type="text" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSend()} placeholder="Share how you're feeling..." className="w-full p-5 pr-14 rounded-2xl border border-vita-border focus:outline-none focus:border-vita-sage focus:ring-1 focus:ring-vita-sage transition-all bg-white text-lg placeholder:text-vita-text-muted/60" />
          <button onClick={handleSend} disabled={!input.trim() || sending} className="absolute right-3 top-3 p-2 text-vita-sage hover:text-vita-text disabled:opacity-30 transition-colors">
            <ArrowUpRight className="w-6 h-6" />
          </button>
        </div>
        <p className="text-center text-xs text-vita-text-muted mt-4">
          VitaTwin does not provide medical diagnosis.
        </p>
        {error && <p className="text-center text-xs text-red-500 mt-2">{error}</p>}
      </div>
    </motion.div>;
};
const LabsScreen = () => {
  return <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit" className="max-w-3xl mx-auto p-6 md:p-12 pb-24">
      <Header title="Labs & Reports" subtitle="Your personal, secure health vault." />

      <div className="space-y-6">
        <Card className="bg-gradient-to-br from-[#F5F7F6] to-white border-dashed border-2 border-vita-border flex flex-col items-center justify-center py-16 hover:border-vita-sage/50 hover:bg-[#F2F5F4] transition-all cursor-pointer group">
          <div className="w-16 h-16 bg-white rounded-full shadow-sm flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-500 ease-out">
            <Upload className="w-7 h-7 text-vita-sage" />
          </div>
          <h3 className="text-lg font-medium text-vita-text">Upload New Report</h3>
          <p className="text-vita-text-muted mt-1 font-light">Drag & drop or tap to select</p>
        </Card>

        <div className="mt-8">
           <h3 className="text-sm font-semibold text-vita-text-muted uppercase tracking-widest mb-6">Timeline</h3>
           
           {[1, 2].map(i => <div key={i} className="flex gap-6 mb-8 relative">
               {/* Timeline Line */}
               {i === 1 && <div className="absolute left-[19px] top-10 bottom-[-32px] w-[2px] bg-vita-border/60" />}
               
               <div className="flex-none w-10 h-10 rounded-full bg-white border border-vita-border flex items-center justify-center z-10 shadow-sm">
                 <FileText className="w-5 h-5 text-vita-text-muted" />
               </div>
               
               <div className="flex-1">
                 <Card className="hover:shadow-md transition-shadow p-5">
                   <div className="flex justify-between items-start">
                     <div>
                       <h4 className="font-semibold text-vita-text text-lg">Comprehensive Metabolic Panel</h4>
                       <p className="text-sm text-vita-text-muted mt-1">May 12, 2024 · LabCorp</p>
                     </div>
                     <ChevronRight className="w-5 h-5 text-vita-border" />
                   </div>
                   
                   <div className="mt-4 pt-4 border-t border-vita-border/50 grid grid-cols-2 gap-4">
                     <div>
                       <span className="text-xs text-vita-text-muted block mb-1">Status</span>
                       <span className="text-sm font-medium text-vita-sage flex items-center gap-1">
                         <Check className="w-3 h-3" /> Reviewed
                       </span>
                     </div>
                     <div>
                       <span className="text-xs text-vita-text-muted block mb-1">Key Insight</span>
                       <span className="text-sm text-vita-text">Vitamin D levels normalized</span>
                     </div>
                   </div>
                 </Card>
               </div>
             </div>)}
        </div>
      </div>
    </motion.div>;
};
const TrendsScreen = () => {
  return <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit" className="max-w-4xl mx-auto p-6 md:p-12 pb-24">
      <Header title="Health Trends" subtitle="Reassurance through long-term progress." />
      
      <div className="space-y-8">
        {METRICS.map((metric, i) => <motion.div key={metric.id} initial={{
        opacity: 0,
        y: 20
      }} animate={{
        opacity: 1,
        y: 0
      }} transition={{
        delay: i * 0.1
      }}>
            <Card className="p-8">
               <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                       <h3 className="text-2xl font-semibold text-vita-text">{metric.name}</h3>
                       <TrendBadge trend={metric.trend} />
                    </div>
                    <p className="text-vita-text-muted font-light text-lg max-w-xl">
                      {metric.insight}
                    </p>
                  </div>
                  <div className="text-right flex-none">
                    <div className="text-4xl font-light text-vita-text tracking-tight">{metric.value}</div>
                    <div className="text-sm text-vita-text-muted font-medium mt-1">{metric.unit}</div>
                  </div>
               </div>
               
               <div className="h-64 w-full bg-vita-bg/30 rounded-xl p-4">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={metric.history} margin={{
                top: 10,
                right: 10,
                left: 0,
                bottom: 0
              }}>
                    <defs>
                      <linearGradient id={`trend-grad-${metric.id}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8DA399" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#8DA399" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#EBE8E2" />
                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{
                  fill: '#8C8882',
                  fontSize: 12
                }} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{
                  fill: '#8C8882',
                  fontSize: 12
                }} />
                    <Tooltip contentStyle={{
                  borderRadius: '12px',
                  border: 'none',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                  padding: '12px 16px',
                  fontFamily: 'sans-serif'
                }} />
                    <Area type="monotone" dataKey="value" stroke="#8DA399" fill={`url(#trend-grad-${metric.id})`} strokeWidth={3} animationDuration={2000} />
                  </AreaChart>
                </ResponsiveContainer>
               </div>
            </Card>
          </motion.div>)}
      </div>
    </motion.div>;
};

// --- NAVIGATION & LAYOUT ---

const NavBar = ({
  active,
  onChange
}: {
  active: Screen;
  onChange: (s: Screen) => void;
}) => {
  const items = [{
    id: 'home',
    icon: Home,
    label: 'Overview'
  }, {
    id: 'dashboard',
    icon: Activity,
    label: 'Dashboard'
  }, {
    id: 'chat',
    icon: MessageCircle,
    label: 'Chat'
  }, {
    id: 'labs',
    icon: FileText,
    label: 'Labs'
  }, {
    id: 'trends',
    icon: TrendingUp,
    label: 'Trends'
  }] as const;
  return <>
      {/* Desktop Sidebar */}
      <nav className="hidden md:flex w-72 flex-col border-r border-vita-border bg-white p-6 z-20 shadow-[4px_0_24px_-12px_rgba(0,0,0,0.02)]">
        <div className="flex items-center gap-3 mb-16 px-2">
          <div className="w-10 h-10 rounded-xl bg-vita-text flex items-center justify-center text-white font-serif italic text-xl shadow-lg shadow-vita-text/20">V</div>
          <span className="text-xl font-bold tracking-tight text-vita-text">VitaTwin</span>
        </div>
        
        <div className="space-y-2 flex-1">
          {items.map(item => {
          const Icon = item.icon;
          const isActive = active === item.id;
          return <button key={item.id} onClick={() => onChange(item.id)} className={`w-full flex items-center gap-4 px-4 py-3.5 rounded-2xl transition-all duration-300 group ${isActive ? 'bg-vita-text text-white shadow-lg shadow-vita-text/10' : 'text-vita-text-muted hover:bg-vita-bg hover:text-vita-text'}`}>
                <Icon className={`w-5 h-5 transition-transform group-hover:scale-110 ${isActive ? 'text-white' : 'text-current'}`} />
                <span className="font-medium tracking-wide">{item.label}</span>
                {isActive && <motion.div layoutId="active-dot" className="w-1.5 h-1.5 rounded-full bg-white ml-auto" />}
              </button>;
        })}
        </div>

        <div className="pt-6 border-t border-vita-border">
           <button className="flex items-center gap-3 px-4 py-3 w-full text-vita-text-muted hover:bg-vita-bg rounded-2xl transition-colors">
             <div className="w-9 h-9 rounded-full bg-vita-sage/20 flex items-center justify-center border border-white shadow-sm">
               <span className="text-xs font-bold text-vita-sage">AJ</span>
             </div>
             <div className="text-left">
               <div className="text-sm font-semibold text-vita-text">Alex Johnson</div>
               <div className="text-xs text-vita-text-muted opacity-80">Connected</div>
             </div>
           </button>
        </div>
      </nav>

      {/* Mobile Bottom Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-lg border-t border-vita-border flex justify-around p-2 pb-6 z-50 shadow-[0_-4px_20px_-10px_rgba(0,0,0,0.05)]">
        {items.map(item => {
        const Icon = item.icon;
        const isActive = active === item.id;
        return <button key={item.id} onClick={() => onChange(item.id)} className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-all w-full ${isActive ? 'text-vita-text' : 'text-vita-text-muted hover:bg-vita-bg'}`}>
              <div className={`p-1.5 rounded-full ${isActive ? 'bg-vita-text/5' : ''}`}>
                 <Icon className={`w-6 h-6 ${isActive ? 'stroke-[2.5px]' : ''}`} />
              </div>
              <span className="text-[10px] font-medium tracking-wide">{item.label}</span>
            </button>;
      })}
      </nav>
    </>;
};
export const VitaTwinApp = () => {
  const [activeScreen, setActiveScreen] = useState<Screen>('home');
  return <div className="flex h-screen w-full bg-vita-bg font-sans text-vita-text overflow-hidden selection:bg-vita-sage/20 selection:text-vita-text">
      <NavBar active={activeScreen} onChange={setActiveScreen} />

      <main className="flex-1 relative overflow-hidden flex flex-col">
        {/* Mobile Header */}
        <div className="md:hidden h-16 flex-none bg-vita-bg/80 backdrop-blur-md flex items-center justify-between px-6 z-40 sticky top-0">
          <div className="flex items-center gap-2">
             <div className="w-8 h-8 rounded-lg bg-vita-text flex items-center justify-center text-white font-serif italic font-bold">V</div>
             <span className="font-bold text-lg tracking-tight">VitaTwin</span>
          </div>
          <button className="w-8 h-8 rounded-full bg-vita-sage/20 border border-vita-sage/10 text-xs font-bold text-vita-sage flex items-center justify-center">
            AJ
          </button>
        </div>

        <div className="flex-1 overflow-y-auto scroll-smooth pb-20 md:pb-0">
          <AnimatePresence mode="wait">
            <motion.div key={activeScreen} className="h-full">
              {activeScreen === 'home' && <HomeScreen onNavigate={setActiveScreen} />}
              {activeScreen === 'dashboard' && <DashboardScreen />}
              {activeScreen === 'chat' && <ChatScreen />}
              {activeScreen === 'labs' && <LabsScreen />}
              {activeScreen === 'trends' && <TrendsScreen />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>;
};
