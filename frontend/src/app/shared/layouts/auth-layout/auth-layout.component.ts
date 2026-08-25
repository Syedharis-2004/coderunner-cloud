import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-auth-layout',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <div class="auth-wrapper">
      <div class="cyber-scanline"></div>
      <div class="auth-container">
        <div class="brand">
          <h1 class="cyber-title">CodeRunner Cloud</h1>
          <p class="tagline">Secure Code Execution Infrastructure</p>
        </div>
        <router-outlet></router-outlet>
      </div>
    </div>
  `,
  styles: [`
    .auth-wrapper {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background-color: var(--cyber-bg);
      background-image: radial-gradient(circle at center, #1a2a1a 0%, var(--cyber-bg) 60%);
    }
    .auth-container {
      width: 100%;
      max-width: 400px;
      padding: 2rem;
      position: relative;
      z-index: 10;
    }
    .brand {
      text-align: center;
      margin-bottom: 2rem;
    }
    .brand h1 {
      margin: 0 0 0.5rem 0;
      font-size: 2rem;
    }
    .tagline {
      color: var(--cyber-neon);
      margin: 0;
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      opacity: 0.8;
    }
  `]
})
export class AuthLayoutComponent {

}
