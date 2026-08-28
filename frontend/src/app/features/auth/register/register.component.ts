import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  template: `
    <div class="cyber-card">
      <h2 class="cyber-title" style="text-align: center; margin-bottom: 24px;">REGISTER_NODE</h2>
      
      <div *ngIf="errorMsg" class="error-box">
        ERROR: {{ errorMsg }}
      </div>

      <form [formGroup]="registerForm" (ngSubmit)="onSubmit()">
        <div class="form-group">
          <label>NODE_ALIAS [NAME]</label>
          <input type="text" formControlName="name" placeholder="Neo" autofocus>
        </div>

        <div class="form-group">
          <label>IDENTITY_NODE [EMAIL]</label>
          <input type="email" formControlName="email" placeholder="neo@matrix.net">
        </div>

        <div class="form-group">
          <label>ACCESS_KEY [PASSWORD]</label>
          <input type="password" formControlName="password" placeholder="••••••••">
        </div>

        <button type="submit" class="btn-cyber-solid w-100 mt-4" [disabled]="registerForm.invalid || isLoading">
          {{ isLoading ? 'PROVISIONING...' : 'INITIALIZE_NODE' }}
        </button>
      </form>

      <div class="text-center mt-4">
        <span style="color: var(--cyber-text-dim); font-size: 0.9rem;">NODE_ALREADY_EXISTS?</span>
        <a routerLink="/login" class="cyber-link ml-2">LOGIN</a>
      </div>
    </div>
  `,
  styles: [`
    .form-group {
      margin-bottom: 20px;
      display: flex;
      flex-direction: column;
    }
    label {
      font-family: var(--font-family-mono);
      font-size: 0.8rem;
      color: var(--cyber-neon);
      margin-bottom: 8px;
    }
    .w-100 { width: 100%; }
    .mt-4 { margin-top: 24px; }
    .text-center { text-align: center; }
    .ml-2 { margin-left: 8px; }
    
    .cyber-link {
      color: var(--cyber-neon);
      text-decoration: none;
      font-family: var(--font-family-mono);
      font-size: 0.9rem;
      transition: all 0.2s;
    }
    .cyber-link:hover {
      text-shadow: var(--cyber-neon-glow);
    }
    
    .error-box {
      background: rgba(255, 0, 60, 0.1);
      border: 1px solid var(--cyber-accent-danger);
      color: var(--cyber-accent-danger);
      padding: 12px;
      margin-bottom: 20px;
      font-family: var(--font-family-mono);
      font-size: 0.85rem;
      border-radius: 4px;
    }
  `]
})
export class RegisterComponent {
  private fb = inject(FormBuilder);
  public authService = inject(AuthService) as any;
  private router = inject(Router);

  registerForm: FormGroup = this.fb.group({
    name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]]
  });

  isLoading = false;
  errorMsg = '';

  onSubmit() {
    if (this.registerForm.invalid) return;

    this.isLoading = true;
    this.errorMsg = '';

    this.authService.register(this.registerForm.value).subscribe({
      next: (res: any) => {
        this.isLoading = false;
        if (res.success) {
          this.router.navigate(['/dashboard']);
        }
      },
      error: (err: any) => {
        this.isLoading = false;
        const detail = err.error?.detail;
        if (typeof detail === 'string') {
          this.errorMsg = detail;
        } else if (Array.isArray(detail)) {
          this.errorMsg = detail[0]?.msg || 'VALIDATION_ERROR';
        } else {
          this.errorMsg = 'REGISTRATION_FAILED. PLEASE TRY AGAIN.';
        }
      }
    });
  }
}
