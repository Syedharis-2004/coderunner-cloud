import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="cyber-card">
      <h2 class="cyber-title" style="text-align:center;margin-bottom:24px;">SYSTEM_LOGIN</h2>

      <div *ngIf="errorMsg" class="error-box">ERROR: {{ errorMsg }}</div>

      <div class="form-group">
        <label>IDENTITY_NODE [EMAIL]</label>
        <input type="email" [(ngModel)]="email" placeholder="user@node.network" autofocus>
      </div>

      <div class="form-group">
        <label>ACCESS_KEY [PASSWORD]</label>
        <input type="password" [(ngModel)]="password" placeholder="••••••••">
      </div>

      <button class="btn-cyber-solid w-100 mt-4"
              (click)="onSubmit()"
              [disabled]="isLoading">
        {{ isLoading ? 'AUTHENTICATING...' : 'INITIATE_CONNECTION' }}
      </button>

      <div class="text-center mt-4">
        <span style="color:var(--cyber-text-dim);font-size:0.9rem;">NO_RECORD_FOUND?</span>
        <a routerLink="/register" class="cyber-link ml-2">CREATE_NODE</a>
      </div>
    </div>
  `,
  styles: [`
    .form-group { margin-bottom:20px; display:flex; flex-direction:column; }
    label { font-family:var(--font-family-mono); font-size:0.8rem; color:var(--cyber-neon); margin-bottom:8px; }
    input { background:#111; border:1px solid #333; color:#fff; padding:10px 14px; border-radius:4px; font-size:0.95rem; outline:none; }
    input:focus { border-color:var(--cyber-neon); }
    .w-100 { width:100%; }
    .mt-4 { margin-top:24px; }
    .text-center { text-align:center; }
    .ml-2 { margin-left:8px; }
    .cyber-link { color:var(--cyber-neon); text-decoration:none; font-family:var(--font-family-mono); font-size:0.9rem; }
    .error-box { background:rgba(255,0,60,0.1); border:1px solid #ff003c; color:#ff003c; padding:12px; margin-bottom:20px; font-family:var(--font-family-mono); font-size:0.85rem; border-radius:4px; }
  `]
})
export class LoginComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  email = '';
  password = '';
  isLoading = false;
  errorMsg = '';

  onSubmit() {
    this.errorMsg = '';

    if (!this.email.trim() || !this.email.includes('@')) {
      this.errorMsg = 'Valid email is required.';
      return;
    }
    if (!this.password) {
      this.errorMsg = 'Password is required.';
      return;
    }

    this.isLoading = true;

    this.authService.login({
      email: this.email.trim(),
      password: this.password
    }).subscribe({
      next: (res: any) => {
        this.isLoading = false;
        if (res.success) {
          this.router.navigate(['/dashboard']);
        }
      },
      error: (err: any) => {
        this.isLoading = false;
        const detail = err.error?.detail;
        this.errorMsg = typeof detail === 'string'
          ? detail
          : `Error ${err.status}: Login failed. Check credentials.`;
      }
    });
  }
}
