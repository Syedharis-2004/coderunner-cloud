import { Component, inject } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { AuthService, User } from '../../../core/services/auth.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterModule, CommonModule],
  template: `
    <div class="sidebar-container">
      <div class="brand">
        <h2 class="cyber-title">CodeRunner</h2>
        <div class="brand-line"></div>
      </div>
      
      <nav class="nav-menu">
        <a routerLink="/dashboard" routerLinkActive="active" class="nav-item">
          [ Dashboard ]
        </a>
        <a routerLink="/editor" routerLinkActive="active" class="nav-item">
          [ Code Editor ]
        </a>
        <a routerLink="/projects" routerLinkActive="active" class="nav-item">
          [ My Projects ]
        </a>
        <a routerLink="/api-keys" routerLinkActive="active" class="nav-item">
          [ API Keys ]
        </a>
      </nav>

      <div class="admin-section" *ngIf="(user$ | async)?.role === 'ADMIN'">
        <div class="section-title">ADMINISTRATOR</div>
        <a routerLink="/admin" routerLinkActive="active" class="nav-item admin-item">
          [ System Admin ]
        </a>
      </div>
      
      <div class="sidebar-footer">
        STATUS: <span class="status-ok">ONLINE</span>
      </div>
    </div>
  `,
  styles: [`
    .sidebar-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      padding: 24px 0;
    }
    .brand {
      padding: 0 24px;
      margin-bottom: 40px;
    }
    .brand h2 {
      margin: 0;
      font-size: 1.5rem;
    }
    .brand-line {
      height: 2px;
      background-color: var(--cyber-neon);
      width: 40px;
      margin-top: 8px;
      box-shadow: var(--cyber-neon-glow);
    }
    .nav-menu {
      display: flex;
      flex-direction: column;
      gap: 12px;
      flex: 1;
    }
    .nav-item {
      padding: 12px 24px;
      color: var(--cyber-text-dim);
      text-decoration: none;
      font-family: var(--font-family-mono);
      font-size: 0.9rem;
      border-left: 3px solid transparent;
      transition: all 0.2s ease;
    }
    .nav-item:hover {
      color: #fff;
      background-color: rgba(255, 255, 255, 0.05);
    }
    .nav-item.active {
      color: var(--cyber-neon);
      border-left-color: var(--cyber-neon);
      background-color: var(--cyber-neon-dim);
      text-shadow: var(--cyber-neon-glow);
    }
    .admin-section {
      margin-top: auto;
      margin-bottom: 24px;
    }
    .section-title {
      padding: 0 24px;
      font-size: 0.75rem;
      color: var(--cyber-accent-danger);
      margin-bottom: 12px;
      letter-spacing: 2px;
    }
    .admin-item.active {
      color: var(--cyber-accent-danger);
      border-left-color: var(--cyber-accent-danger);
      background-color: rgba(255, 0, 60, 0.1);
      text-shadow: 0 0 8px var(--cyber-accent-danger);
    }
    .sidebar-footer {
      padding: 24px;
      border-top: 1px solid var(--cyber-surface-border);
      font-family: var(--font-family-mono);
      font-size: 0.8rem;
      color: var(--cyber-text-dim);
    }
    .status-ok {
      color: var(--cyber-neon);
      text-shadow: var(--cyber-neon-glow);
    }
  `]
})
export class SidebarComponent {
  private authService = inject(AuthService);
  user$: Observable<User | null> = this.authService.currentUser$;
}
