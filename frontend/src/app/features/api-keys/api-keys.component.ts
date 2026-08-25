import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiKeyService, ApiKey } from '../../core/services/api-key.service';
import { SubscriptionService, SubscriptionStatus } from '../../core/services/subscription.service';

@Component({
  selector: 'app-api-keys',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h1 class="cyber-title">API_KEYS</h1>
    <p style="color: var(--cyber-text-dim); margin-bottom: 24px;">
      Manage your access keys for the Code Cloud programmatic API.
    </p>

    <!-- SUBSCRIPTION REQUIRED BANNER -->
    <div *ngIf="!subStatus?.allows_api_access && subStatusLoaded" class="subscription-required-banner">
      <div class="banner-icon">🔒</div>
      <div class="banner-content">
        <h3>API Access Requires a Subscription</h3>
        <p>
          To generate production API keys and use the Code Cloud API, you need an active paid subscription.
          <span *ngIf="subStatus?.status === 'past_due'"> Your payment is past due — please update your payment method.</span>
          <span *ngIf="subStatus?.status === 'canceled'"> Your subscription has been canceled.</span>
        </p>
      </div>
      <button class="btn-cyber-solid" (click)="goToPricing()">View Plans →</button>
    </div>

    <!-- GENERATE KEY FORM (only when subscription active) -->
    <div *ngIf="subStatus?.allows_api_access" class="cyber-card" style="margin-bottom: 24px;">
      <h3 style="margin-top: 0; color: var(--cyber-neon);">GENERATE_NEW_KEY</h3>
      <div class="form-row">
        <div class="form-field">
          <label>KEY_ALIAS [NAME]</label>
          <input type="text" [(ngModel)]="newKeyName" placeholder="e.g. CI/CD Pipeline, Production App">
        </div>
        <button class="btn-cyber-solid" (click)="createKey()" [disabled]="!newKeyName.trim() || isCreating">
          {{ isCreating ? 'GENERATING...' : 'GENERATE_KEY' }}
        </button>
      </div>

      <!-- SHOW RAW KEY ONLY ONCE -->
      <div *ngIf="newRawKey" class="raw-key-box">
        <h4 class="warning-title">⚠ SECURE THIS KEY NOW — It will never be shown again</h4>
        <div class="key-display">{{ newRawKey }}</div>
        <div class="key-actions">
          <button class="btn-cyber" (click)="copyKey()">{{ copied ? '✓ COPIED' : 'COPY KEY' }}</button>
          <button class="btn-cyber-danger" (click)="newRawKey = null; copied = false">I HAVE SAVED IT</button>
        </div>
      </div>
    </div>

    <!-- PLAN LIMIT INFO -->
    <div *ngIf="subStatus?.allows_api_access && planLimit > 0" class="plan-info-bar">
      <span>API Keys: <strong>{{ activeKeyCount }} / {{ planLimit }}</strong></span>
      <span *ngIf="activeKeyCount >= planLimit" class="limit-reached">Limit reached — revoke a key to generate a new one</span>
    </div>

    <!-- KEYS TABLE -->
    <div class="cyber-card">
      <div *ngIf="loading" class="loading-row">Loading keys...</div>
      <table *ngIf="!loading" class="cyber-table">
        <thead>
          <tr>
            <th>ALIAS</th>
            <th>PREFIX</th>
            <th>STATUS</th>
            <th>LAST USED</th>
            <th>CREATED</th>
            <th>ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let key of keys">
            <td>{{ key.name }}</td>
            <td class="key-prefix">{{ key.key_prefix }}</td>
            <td>
              <span class="badge" [class.badge-active]="key.is_active" [class.badge-revoked]="!key.is_active">
                {{ key.is_active ? 'ACTIVE' : 'REVOKED' }}
              </span>
            </td>
            <td>{{ key.last_used_at ? (key.last_used_at | date:'short') : 'Never' }}</td>
            <td>{{ key.created_at | date:'short' }}</td>
            <td>
              <button class="btn-cyber-danger btn-sm" *ngIf="key.is_active" (click)="revokeKey(key.id)">REVOKE</button>
              <span *ngIf="!key.is_active" style="color: var(--cyber-text-dim); font-size: 0.8rem;">Revoked</span>
            </td>
          </tr>
          <tr *ngIf="keys.length === 0">
            <td colspan="6" class="empty-row">
              {{ subStatus?.allows_api_access ? 'No API keys yet. Generate your first key above.' : 'Subscribe to a plan to generate API keys.' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [`
    .subscription-required-banner {
      display: flex;
      align-items: center;
      gap: 20px;
      background: linear-gradient(135deg, rgba(255,152,0,0.08), rgba(255,152,0,0.03));
      border: 1px solid rgba(255, 152, 0, 0.5);
      border-radius: 8px;
      padding: 20px 24px;
      margin-bottom: 24px;
    }
    .banner-icon { font-size: 2rem; }
    .banner-content { flex: 1; }
    .banner-content h3 { color: #ff9800; margin: 0 0 6px; }
    .banner-content p { color: var(--cyber-text-dim); margin: 0; font-size: 0.9rem; }
    
    .form-row {
      display: flex;
      gap: 16px;
      align-items: flex-end;
    }
    .form-field {
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    .form-field label {
      color: var(--cyber-text-dim);
      font-size: 0.8rem;
      margin-bottom: 8px;
      font-family: var(--font-family-mono);
    }
    input {
      background-color: #050505;
      border: 1px solid var(--cyber-surface-border);
      color: #fff;
      padding: 10px 14px;
      font-family: var(--font-family-mono);
      outline: none;
      border-radius: 4px;
    }
    input:focus { border-color: var(--cyber-neon); }
    
    .raw-key-box {
      margin-top: 20px;
      border: 1px dashed #ff9800;
      background: rgba(255, 152, 0, 0.05);
      padding: 16px;
      border-radius: 6px;
    }
    .warning-title { color: #ff9800; margin: 0 0 12px; font-size: 0.95rem; }
    .key-display {
      background: #000;
      padding: 12px 16px;
      font-family: var(--font-family-mono);
      color: var(--cyber-neon);
      border: 1px solid var(--cyber-surface-border);
      word-break: break-all;
      border-radius: 4px;
      font-size: 0.9rem;
      user-select: all;
    }
    .key-actions {
      display: flex;
      gap: 12px;
      margin-top: 12px;
    }
    
    .plan-info-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 16px;
      background: rgba(0, 255, 65, 0.05);
      border: 1px solid rgba(0, 255, 65, 0.2);
      border-radius: 6px;
      margin-bottom: 16px;
      font-size: 0.9rem;
      color: var(--cyber-text-dim);
    }
    .limit-reached { color: #ff9800; font-weight: 600; }
    
    .loading-row {
      padding: 24px;
      text-align: center;
      color: var(--cyber-text-dim);
      font-family: var(--font-family-mono);
    }
    
    .cyber-table {
      width: 100%;
      border-collapse: collapse;
      font-family: var(--font-family-mono);
      font-size: 0.9rem;
    }
    .cyber-table th, .cyber-table td {
      padding: 12px 16px;
      text-align: left;
      border-bottom: 1px solid var(--cyber-surface-border);
    }
    .cyber-table th {
      color: var(--cyber-text-dim);
      font-size: 0.8rem;
    }
    .cyber-table tr:hover td { background: rgba(255,255,255,0.02); }
    .key-prefix { font-family: var(--font-family-mono); color: var(--cyber-neon); }
    .empty-row {
      text-align: center;
      color: var(--cyber-text-dim);
      padding: 32px 16px !important;
    }
    
    .badge {
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      border: 1px solid;
    }
    .badge-active  { color: var(--cyber-neon); border-color: var(--cyber-neon); }
    .badge-revoked { color: var(--cyber-accent-danger); border-color: var(--cyber-accent-danger); }
    .btn-sm { padding: 4px 12px; font-size: 0.8rem; }
  `]
})
export class ApiKeysComponent implements OnInit {
  private apiKeyService = inject(ApiKeyService);
  private subscriptionService = inject(SubscriptionService);
  private router = inject(Router);

  keys: ApiKey[] = [];
  newKeyName = '';
  isCreating = false;
  loading = true;
  newRawKey: string | null = null;
  copied = false;
  subStatus: SubscriptionStatus | null = null;
  subStatusLoaded = false;
  planLimit = 0;

  get activeKeyCount(): number {
    return this.keys.filter(k => k.is_active).length;
  }

  ngOnInit() {
    this.loadSubscriptionStatus();
    this.loadKeys();
  }

  loadSubscriptionStatus() {
    this.subscriptionService.getSubscriptionStatus().subscribe({
      next: (res) => {
        if (res.success && res.data) {
          this.subStatus = res.data;
        }
        this.subStatusLoaded = true;
        this.loadPlanLimit();
      },
      error: () => { this.subStatusLoaded = true; }
    });
  }

  loadPlanLimit() {
    if (!this.subStatus?.has_subscription) {
      this.planLimit = 0;
      return;
    }
    // Fetch current subscription for max_api_keys
    this.subscriptionService.getCurrentSubscription().subscribe({
      next: (res) => {
        if (res.success && res.data?.plan) {
          this.planLimit = res.data.plan.max_api_keys;
        }
      }
    });
  }

  loadKeys() {
    this.loading = true;
    this.apiKeyService.listKeys().subscribe({
      next: (res: any) => {
        if (res.success && res.data) {
          this.keys = res.data;
        }
        this.loading = false;
      },
      error: () => { this.loading = false; }
    });
  }

  createKey() {
    if (!this.newKeyName.trim()) return;
    this.isCreating = true;
    this.apiKeyService.createKey(this.newKeyName).subscribe({
      next: (res) => {
        if (res.success && res.data) {
          this.newRawKey = (res.data as any).raw_key || null;
          this.newKeyName = '';
          this.loadKeys();
        }
        this.isCreating = false;
      },
      error: (err) => {
        this.isCreating = false;
        const msg = err.error?.detail || 'Failed to generate key.';
        alert(msg);
      }
    });
  }

  copyKey() {
    if (this.newRawKey) {
      navigator.clipboard.writeText(this.newRawKey).then(() => {
        this.copied = true;
        setTimeout(() => this.copied = false, 3000);
      });
    }
  }

  revokeKey(id: string) {
    if (!confirm('WARNING: Revoking this key will immediately break any integrations using it. Proceed?')) {
      return;
    }
    this.apiKeyService.revokeKey(id).subscribe({
      next: () => this.loadKeys(),
      error: (err) => alert(err.error?.detail || 'Failed to revoke key.')
    });
  }

  goToPricing() {
    this.router.navigate(['/pricing']);
  }
}
