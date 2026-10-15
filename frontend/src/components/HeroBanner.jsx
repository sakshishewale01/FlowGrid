import React from 'react';
import heroTruckImg from '../assets/hero_truck.jpg';

/**
 * HeroBanner component matching the cinematic reference design.
 * Features a high-resolution dark-mode semi-truck traversing a highway at dusk,
 * with high-contrast FlowGrid typography and the core tagline: "Predict • Decide • Recover".
 */
export default function HeroBanner() {
  return (
    <section className="flowgrid-hero-banner" aria-label="Control Tower Operations Banner">
      <div 
        className="hero-backdrop"
        style={{ backgroundImage: `url(${heroTruckImg})` }}
      >
        <div className="hero-gradient-overlay" />
      </div>

      <div className="hero-content">
        <h1 className="hero-brand-heading">FlowGrid</h1>
        <div className="hero-tagline-row">
          <span>Predict</span>
          <span className="tagline-dot">•</span>
          <span>Decide</span>
          <span className="tagline-dot">•</span>
          <span>Recover</span>
        </div>
        <p className="hero-subtext">
          Real-time visibility. Smarter decisions. A more resilient supply chain.
        </p>
      </div>
    </section>
  );
}
