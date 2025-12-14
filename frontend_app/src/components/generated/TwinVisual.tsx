import React from 'react';
import { motion } from 'framer-motion';
export const TwinVisual: React.FC<{
  status?: 'stable' | 'improving' | 'attention';
  className?: string;
  minimized?: boolean;
}> = ({
  status = 'stable',
  className = '',
  minimized = false
}) => {
  // Physiology-driven colors
  const getColors = () => {
    switch (status) {
      case 'improving':
        return {
          core: '#8DA399',
          // Sage
          glow: '#EBF0EE',
          highlight: '#B8C9C1'
        };
      case 'attention':
        return {
          core: '#D4B483',
          // Soft Amber
          glow: '#F9F4EB',
          highlight: '#E6D0B3'
        };
      case 'stable':
      default:
        return {
          core: '#CFCBC4',
          // Warm Neutral
          glow: '#F2F0EB',
          highlight: '#EBE8E2'
        };
    }
  };
  const colors = getColors();

  // Breathing animation variants
  const breathingVariant = {
    inhale: {
      scale: 1.05,
      opacity: 0.9,
      filter: 'blur(8px)',
      transition: {
        duration: 4,
        ease: [0.42, 0.0, 0.58, 1.0] // Slow, organic sine-like curve
      }
    },
    exhale: {
      scale: 0.98,
      opacity: 0.7,
      filter: 'blur(10px)',
      transition: {
        duration: 5,
        ease: [0.42, 0.0, 0.58, 1.0]
      }
    }
  };
  const glowVariant = {
    pulse: {
      opacity: [0.4, 0.6, 0.4],
      scale: [1, 1.1, 1],
      transition: {
        duration: 8,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  };
  if (minimized) {
    return <div className={`relative flex items-center justify-center w-12 h-12 ${className}`}>
        <motion.div animate="pulse" variants={glowVariant} className="absolute inset-0 rounded-full blur-md" style={{
        backgroundColor: colors.core
      }} />
        <div className="relative z-10 w-6 h-6 rounded-full bg-white/50 backdrop-blur-sm" />
      </div>;
  }
  return <div className={`relative flex items-center justify-center ${className}`}>
      {/* Background Ambient Glow */}
      <motion.div animate="pulse" variants={glowVariant} className="absolute w-80 h-96 rounded-full blur-3xl opacity-40 mix-blend-multiply dark:mix-blend-screen" style={{
      background: `radial-gradient(circle, ${colors.core} 0%, transparent 70%)`
    }} />

      {/* Core Body Form - Abstracted & Layered */}
      <div className="relative z-10 w-64 h-96">
        {/* Layer 1: Base Silhouette (Soft & Blurred) */}
        <motion.div className="absolute inset-0 flex items-center justify-center" initial="exhale" animate="inhale" variants={{
        inhale: {
          y: -5,
          transition: {
            duration: 4,
            repeat: Infinity,
            repeatType: "reverse",
            ease: "easeInOut"
          }
        }
      }}>
          <svg viewBox="0 0 200 400" className="w-full h-full drop-shadow-xl overflow-visible">
            <defs>
              <linearGradient id="bodyBase" x1="100" y1="0" x2="100" y2="400" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor={colors.highlight} stopOpacity="0.9" />
                <stop offset="100%" stopColor={colors.core} stopOpacity="0.4" />
              </linearGradient>
              <filter id="glassBlur" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="6" />
                <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7" result="goo" />
              </filter>
            </defs>
            
            {/* The Silhouette */}
            <motion.path d="M100 60 C 130 60, 140 90, 135 110 C 130 130, 110 140, 100 140 C 90 140, 70 130, 65 110 C 60 90, 70 60, 100 60 Z" fill="url(#bodyBase)" filter="url(#glassBlur)" initial="exhale" animate="inhale" variants={breathingVariant} />
            <motion.path d="M 100 135 
                 C 140 140, 160 170, 165 210 
                 C 170 280, 150 330, 140 370 
                 C 130 390, 110 400, 100 400 
                 C 90 400, 70 390, 60 370 
                 C 50 330, 30 280, 35 210 
                 C 40 170, 60 140, 100 135" fill="url(#bodyBase)" filter="url(#glassBlur)" initial="exhale" animate="inhale" variants={breathingVariant} />
          </svg>
        </motion.div>

        {/* Layer 2: Inner Light (Vitality) */}
        <motion.div className="absolute inset-0 flex items-center justify-center pointer-events-none" animate={{
        opacity: [0.3, 0.6, 0.3]
      }} transition={{
        duration: 6,
        repeat: Infinity,
        ease: "easeInOut"
      }}>
           <div className="w-24 h-24 rounded-full blur-2xl bg-white mix-blend-overlay" style={{
          transform: 'translateY(-20px)'
        }} />
        </motion.div>
        
        {/* Layer 3: Interaction Ripple (Subtle) */}
        <motion.div className="absolute inset-0 z-20" whileHover={{
        scale: 1.02
      }} whileTap={{
        scale: 0.98
      }} transition={{
        duration: 0.5,
        ease: "easeOut"
      }} />
      </div>
    </div>;
};