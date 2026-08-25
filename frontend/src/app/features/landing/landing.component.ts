import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="landing-wrapper">
      <div class="cyber-scanline"></div>
      
      <!-- Navbar -->
      <nav class="landing-nav">
        <div class="brand">
          <h1 class="cyber-title" style="margin: 0; font-size: 1.5rem;">CodeRunner Cloud</h1>
        </div>
        <div class="nav-links">
          <a routerLink="/login" class="nav-item">LOGIN</a>
          <a routerLink="/register" class="btn-cyber-solid">GET_STARTED</a>
        </div>
      </nav>

      <!-- Hero -->
      <main class="hero">
        <h2 class="hero-title">SECURE_CODE_EXECUTION</h2>
        <h2 class="hero-title" style="color: var(--cyber-neon);">INFRASTRUCTURE</h2>
        <p class="hero-subtitle">
          Instantly run Python, Node.js, Go, and C code in isolated Docker containers. 
          Use our browser-based IDE or integrate via our REST API.
        </p>
        
        <div class="cta-group">
          <button routerLink="/register" class="btn-cyber-solid" style="padding: 16px 32px; font-size: 1.1rem;">
            INITIALIZE_WORKSPACE
          </button>
          <button routerLink="/login" class="btn-cyber" style="padding: 16px 32px; font-size: 1.1rem;">
            SYSTEM_LOGIN
          </button>
        </div>
      </main>

      <!-- Features -->
      <section class="features">
        <div class="cyber-card feature-card">
          <h3 style="color: var(--cyber-neon); margin-top: 0;">ISOLATED_CONTAINERS</h3>
          <p>Every execution runs in a secure, ephemeral Docker container preventing cross-talk and system compromise.</p>
        </div>
        <div class="cyber-card feature-card">
          <h3 style="color: var(--cyber-neon); margin-top: 0;">PROGRAMMATIC_API</h3>
          <p>Generate API keys and integrate remote code execution directly into your own SaaS products.</p>
        </div>
        <div class="cyber-card feature-card">
          <h3 style="color: var(--cyber-neon); margin-top: 0;">CYBER_THEME</h3>
          <p>Immersive hacker aesthetic with high-contrast neon green, perfect for developers who love the terminal.</p>
        </div>
      </section>
    </div>
  `,
  styles: [`
    .landing-wrapper {
      min-height: 100vh;
      background-color: var(--cyber-bg);
      background-image: radial-gradient(circle at center, #1a2a1a 0%, var(--cyber-bg) 60%);
      display: flex;
      flex-direction: column;
    }
    .landing-nav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 24px 48px;
      border-bottom: 1px solid var(--cyber-surface-border);
      background: rgba(0,0,0,0.5);
      z-index: 10;
    }
    .nav-links {
      display: flex;
      align-items: center;
      gap: 24px;
    }
    .nav-item {
      color: var(--cyber-text);
      text-decoration: none;
      font-family: var(--font-family-mono);
      transition: color 0.2s;
    }
    .nav-item:hover { color: var(--cyber-neon); }
    
    .hero {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      padding: 48px;
      z-index: 10;
    }
    .hero-title {
      font-size: 4rem;
      margin: 0;
      line-height: 1.1;
      color: #fff;
      text-shadow: 0 0 10px rgba(0,255,0,0.2);
    }
    .hero-subtitle {
      max-width: 600px;
      font-size: 1.2rem;
      color: var(--cyber-text-dim);
      margin: 32px 0;
      line-height: 1.6;
    }
    .cta-group {
      display: flex;
      gap: 24px;
    }
    
    .features {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 24px;
      padding: 48px;
      z-index: 10;
      background: var(--cyber-surface);
      border-top: 1px solid var(--cyber-surface-border);
    }
    .feature-card {
      background: #050505;
    }
  `]
})
export class LandingComponent {

}
