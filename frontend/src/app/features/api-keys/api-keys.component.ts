import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiKeyService, ApiKey } from '../../core/services/api-key.service';

@Component({
  selector: 'app-api-keys',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h1 class="cyber-title">API_KEYS</h1>
    <p style="color: var(--cyber-text-dim); margin-bottom: 24px;">
      Manage your access keys for the CodeRunner Cloud programmatic API.
    </p>

    <!-- NEW KEY MODAL / FORM -->
    <div class="cyber-card" style="margin-bottom: 24px;">
      <h3 style="margin-top: 0; color: var(--cyber-neon);">GENERATE_NEW_KEY</h3>
      <div style="display: flex; gap: 16px; align-items: flex-end;">
        <div style="flex: 1; display: flex; flex-direction: column;">
          <label style="color: var(--cyber-text-dim); font-size: 0.8rem; margin-bottom: 8px;">KEY_ALIAS [NAME]</label>
          <input type="text" [(ngModel)]="newKeyName" placeholder="e.g. CI/CD Pipeline Worker">
        </div>
        <button class="btn-cyber-solid" (click)="createKey()" [disabled]="!newKeyName.trim() || isCreating">
          {{ isCreating ? 'GENERATING...' : 'GENERATE_KEY' }}
        </button>
      </div>
      
      <!-- SHOW RAW KEY ONLY ONCE -->
      <div *ngIf="newRawKey" class="raw-key-box mt-4">
        <h4 style="color: var(--cyber-accent-warning); margin-top: 0;">WARNING: SECURE_THIS_KEY_NOW</h4>
        <p>This is the only time your raw API Key will be displayed. Copy it immediately.</p>
        <div class="key-display">{{ newRawKey }}</div>
        <button class="btn-cyber mt-2" (click)="newRawKey = null">I HAVE COPIED IT</button>
      </div>
    </div>

    <!-- KEYS TABLE -->
    <div class="cyber-card">
      <table class="cyber-table">
        <thead>
          <tr>
            <th>ALIAS</th>
            <th>PREFIX</th>
            <th>STATUS</th>
            <th>CREATED</th>
            <th>ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let key of keys">
            <td>{{ key.name }}</td>
            <td style="font-family: var(--font-family-mono); color: var(--cyber-neon);">{{ key.key_prefix }}...</td>
            <td>
              <span class="badge" [class.badge-active]="key.is_active" [class.badge-revoked]="!key.is_active">
                {{ key.is_active ? 'ACTIVE' : 'REVOKED' }}
              </span>
            </td>
            <td>{{ key.created_at | date:'short' }}</td>
            <td>
              <button class="btn-cyber-danger btn-sm" *ngIf="key.is_active" (click)="revokeKey(key.id)">REVOKE</button>
            </td>
          </tr>
          <tr *ngIf="keys.length === 0">
            <td colspan="5" class="text-center" style="color: var(--cyber-text-dim); padding: 24px;">NO_KEYS_FOUND</td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [`
    .mt-2 { margin-top: 12px; }
    .mt-4 { margin-top: 24px; }
    .text-center { text-align: center; }

    input {
      background-color: #050505;
      border: 1px solid var(--cyber-surface-border);
      color: #fff;
      padding: 10px 14px;
      font-family: var(--font-family-mono);
      outline: none;
    }
    input:focus { border-color: var(--cyber-neon); }
    
    .raw-key-box {
      border: 1px dashed var(--cyber-accent-warning);
      background: rgba(255, 176, 0, 0.05);
      padding: 16px;
    }
    .key-display {
      background: #000;
      padding: 12px;
      font-family: var(--font-family-mono);
      color: var(--cyber-neon);
      border: 1px solid var(--cyber-surface-border);
      word-break: break-all;
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
    .badge {
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      border: 1px solid;
    }
    .badge-active {
      color: var(--cyber-neon);
      border-color: var(--cyber-neon);
    }
    .badge-revoked {
      color: var(--cyber-accent-danger);
      border-color: var(--cyber-accent-danger);
    }
    .btn-sm {
      padding: 4px 12px;
      font-size: 0.8rem;
    }
  `]
})
export class ApiKeysComponent implements OnInit {
  apiKeyService = inject(ApiKeyService);
  
  keys: ApiKey[] = [];
  newKeyName = '';
  isCreating = false;
  newRawKey: string | null = null;

  ngOnInit() {
    this.loadKeys();
  }

  loadKeys() {
    this.apiKeyService.listKeys().subscribe((res: any) => {
      if (res.success && res.data) {
        this.keys = res.data;
      }
    });
  }

  createKey() {
    if (!this.newKeyName.trim()) return;
    
    this.isCreating = true;
    this.apiKeyService.createKey(this.newKeyName).subscribe({
      next: (res) => {
        if (res.success && res.data) {
          this.newRawKey = res.data.raw_key || null;
          this.newKeyName = '';
          this.loadKeys();
        }
        this.isCreating = false;
      },
      error: () => {
        this.isCreating = false;
        alert('Failed to generate key. Limit may be reached.');
      }
    });
  }

  revokeKey(id: string) {
    if (confirm('WARNING: Revoking this key will immediately break any integrations using it. Proceed?')) {
      this.apiKeyService.revokeKey(id).subscribe(() => {
        this.loadKeys();
      });
    }
  }
}
