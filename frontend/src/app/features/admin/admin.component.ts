import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminService, SystemMetrics } from '../../core/services/admin.service';
import { User } from '../../core/services/auth.service';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h1 class="cyber-title">SYSTEM_ADMINISTRATION</h1>
    <p style="color: var(--cyber-text-dim); margin-bottom: 24px;">
      Root access only. Manage infrastructure and user quotas.
    </p>

    <!-- METRICS -->
    <div class="cyber-card" style="margin-bottom: 24px;" *ngIf="metrics">
      <h3 style="margin-top: 0; color: var(--cyber-accent-danger);">SYSTEM_TELEMETRY</h3>
      <div class="metrics-grid">
        <div class="metric-box">
          <div class="m-label">TOTAL_USERS</div>
          <div class="m-value">{{ metrics.users.total }}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">ACTIVE_USERS</div>
          <div class="m-value">{{ metrics.users.active }}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">LIFETIME_EXECS</div>
          <div class="m-value">{{ metrics.executions.total_all_time }}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">DOCKER_ENGINE</div>
          <div class="m-value" [class.text-danger]="metrics.system.docker !== 'connected'">
            {{ metrics.system.docker | uppercase }}
          </div>
        </div>
      </div>
    </div>

    <!-- USERS TABLE -->
    <div class="cyber-card">
      <h3 style="margin-top: 0; color: var(--cyber-accent-info);">USER_DATABASE</h3>
      <table class="cyber-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>EMAIL</th>
            <th>ROLE</th>
            <th>PLAN</th>
            <th>STATUS</th>
            <th>ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let user of users">
            <td style="font-size: 0.75rem; color: var(--cyber-text-dim);">{{ user.id.substring(0,8) }}...</td>
            <td>{{ user.email }}</td>
            <td [class.text-danger]="user.role === 'ADMIN'">{{ user.role }}</td>
            <td>
              <select [ngModel]="user.plan" (ngModelChange)="updatePlan(user.id, $event)" class="cyber-select" [disabled]="user.role === 'ADMIN'">
                <option value="FREE">FREE</option>
                <option value="DEVELOPER">DEVELOPER</option>
                <option value="PRO">PRO</option>
              </select>
            </td>
            <td>
              <span class="badge" [class.badge-active]="user.is_active" [class.badge-revoked]="!user.is_active">
                {{ user.is_active ? 'ACTIVE' : 'LOCKED' }}
              </span>
            </td>
            <td>
              <button 
                class="btn-cyber-danger btn-sm" 
                *ngIf="user.role !== 'ADMIN'"
                (click)="toggleStatus(user.id, !user.is_active)">
                {{ user.is_active ? 'LOCK_NODE' : 'UNLOCK_NODE' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [`
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
    }
    .metric-box {
      border: 1px solid var(--cyber-surface-border);
      background: #050505;
      padding: 16px;
      text-align: center;
    }
    .m-label {
      font-family: var(--font-family-mono);
      font-size: 0.75rem;
      color: var(--cyber-text-dim);
      margin-bottom: 8px;
    }
    .m-value {
      font-size: 1.5rem;
      color: #fff;
      text-shadow: var(--cyber-neon-glow);
    }
    .text-danger { color: var(--cyber-accent-danger); text-shadow: none; }

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
    .cyber-table th { color: var(--cyber-text-dim); font-size: 0.8rem; }
    
    .cyber-select {
      background: #000;
      color: var(--cyber-neon);
      border: 1px solid var(--cyber-surface-border);
      padding: 4px 8px;
      font-family: var(--font-family-mono);
      outline: none;
    }
    .cyber-select:focus { border-color: var(--cyber-neon); }
    
    .badge {
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      border: 1px solid;
    }
    .badge-active { color: var(--cyber-neon); border-color: var(--cyber-neon); }
    .badge-revoked { color: var(--cyber-accent-danger); border-color: var(--cyber-accent-danger); }
    .btn-sm { padding: 4px 12px; font-size: 0.8rem; }
  `]
})
export class AdminComponent implements OnInit {
  adminService = inject(AdminService);
  
  metrics: SystemMetrics | null = null;
  users: User[] = [];

  ngOnInit() {
    this.loadMetrics();
    this.loadUsers();
  }

  loadMetrics() {
    this.adminService.getMetrics().subscribe((res: any) => {
      if (res.success && res.data) {
        this.metrics = res.data;
      }
    });
  }

  loadUsers() {
    this.adminService.getUsers().subscribe((res: any) => {
      if (res.success && res.data) {
        this.users = res.data;
      }
    });
  }

  updatePlan(userId: string, newPlan: string) {
    this.adminService.changeUserPlan(userId, newPlan).subscribe(() => {
      this.loadUsers();
    });
  }

  toggleStatus(userId: string, is_active: boolean) {
    this.adminService.toggleUserStatus(userId, is_active).subscribe(() => {
      this.loadUsers();
    });
  }
}
