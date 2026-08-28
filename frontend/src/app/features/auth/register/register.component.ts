import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="cyber-card">
      <h2 class="cyber-title" style="text-align:center;margin-bottom:24px;">REGISTER_NODE</h2>

      <div *ngIf="errorMsg" class="error-box">ERROR: {{ errorMsg }}</div>
      <div *ngIf="successMsg" class="success-box">{{ successMsg }}</div>

      <div class="form-group">
        <label>NODE_ALIAS [NAME]</label>
        <input type="text" [(ngModel)]="name" placeholder="Neo" autofocus>
      </div>

      <div class="form-group">
        <label>IDENTITY_NODE [EMAIL]</label>
        <input type="email" [(ngModel)]="email" placeholder="neo@matrix.net">
      </div>

      <div class="form-group">
        <label>ACCESS_KEY [PASSWORD] <span style="color:#888;font-size:0.75rem;">(min 8 chars)</span></label>
        <input type="password" [(ngModel)]="password" placeholder="••••••••">
      </div>

      <button class="btn-cyber-solid w-100 mt-4"
              (click)="onSubmit()"
              [disabled]="isLoading">
        {{ isLoading ? 'PROVISIONING...' : 'INITIALIZE_NODE' }}
      </button>

      <div class="text-center mt-4">
        <span style="color:var(--cyber-text-dim);font-size:0.9rem;">NODE_ALREADY_EXISTS?</span>
        <a routerLink="/login" class="cyber-link ml-2">LOGIN</a>
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
    .success-box { background:rgba(0,255,65,0.1); border:1px solid #00ff41; color:#00ff41; padding:12px; margin-bottom:20px; font-family:var(--font-family-mono); font-size:0.85rem; border-radius:4px; }
  `]
})
export class RegisterComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  name = '';
  email = '';
  password = '';
  isLoading = false;
  errorMsg = '';
  successMsg = '';

  onSubmit() {
    this.errorMsg = '';
    this.successMsg = '';

    // Manual validation — no silent failures
    if (!this.name.trim()) {
      this.errorMsg = 'Name is required.';
      return;
    }
    if (!this.email.trim() || !this.email.includes('@')) {
      this.errorMsg = 'Valid email is required.';
      return;
    }
    if (this.password.length < 8) {
      this.errorMsg = 'Password must be at least 8 characters.';
      return;
    }

    this.isLoading = true;

    this.authService.register({
      name: this.name.trim(),
      email: this.email.trim(),
      password: this.password
    }).subscribe({
      next: (res: any) => {
        this.isLoading = false;
        if (res.success) {
          this.successMsg = 'Account created! Redirecting...';
          setTimeout(() => this.router.navigate(['/dashboard']), 800);
        }
      },
      error: (err: any) => {
        this.isLoading = false;
        const detail = err.error?.detail;
        if (typeof detail === 'string') {
          this.errorMsg = detail;
        } else if (Array.isArray(detail)) {
          this.errorMsg = detail[0]?.msg || 'Validation error';
        } else {
          this.errorMsg = `Error ${err.status}: Registration failed. Try again.`;
        }
      }
    });
  }
}
