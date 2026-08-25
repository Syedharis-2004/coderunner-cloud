import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { AuthService, User } from '../../../core/services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="navbar-container">
      <div class="left-section">
        <!-- Optional Breadcrumbs or Page Title -->
      </div>
      
      <div class="right-section" *ngIf="user$ | async as user">
        <div class="user-info">
          <span class="user-name">{{ user.name }}</span>
          <span class="user-plan" [class.pro]="user.plan === 'PRO'" [class.dev]="user.plan === 'DEVELOPER'">
            {{ user.plan }}
          </span>
        </div>
        <button class="btn-cyber-danger" (click)="logout()">LOGOUT</button>
      </div>
    </div>
  `,
  styles: [`
    .navbar-container {
      display: flex;
      justify-content: space-between;
      align-items: center;
      height: 100%;
      padding: 0 24px;
    }
    .right-section {
      display: flex;
      align-items: center;
      gap: 20px;
    }
    .user-info {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      line-height: 1.2;
    }
    .user-name {
      font-weight: 600;
      color: #fff;
    }
    .user-plan {
      font-size: 0.75rem;
      color: var(--cyber-text-dim);
      border: 1px solid var(--cyber-surface-border);
      padding: 2px 6px;
      border-radius: 4px;
      margin-top: 4px;
    }
    .user-plan.pro {
      color: var(--cyber-accent-warning);
      border-color: var(--cyber-accent-warning);
    }
    .user-plan.dev {
      color: var(--cyber-accent-info);
      border-color: var(--cyber-accent-info);
    }
  `]
})
export class NavbarComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  user$: Observable<User | null> = this.authService.currentUser$;

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
