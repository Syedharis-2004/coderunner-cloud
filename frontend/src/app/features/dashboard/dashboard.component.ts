import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { UsageService, UsageStats } from '../../core/services/usage.service';
import { ProjectService, ProjectSummary } from '../../core/services/project.service';
import { SubscriptionService, SubscriptionStatus } from '../../core/services/subscription.service';
import { PaymentService } from '../../core/services/payment.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <h1 class="cyber-title">DASHBOARD</h1>

    <!-- PAYMENT SUCCESS BANNER -->
    <div *ngIf="paymentSuccess" class="success-banner">
      ✓ Payment successful! Your subscription is now active.
    </div>

    <!-- SUBSCRIPTION STATUS CARD -->
    <div class="sub-card" [ngClass]="getSubCardClass()">
      <div class="sub-card-left">
        <div class="sub-plan-name">{{ subStatus?.plan_name || 'Free' }}</div>
        <div class="sub-label">Current Plan</div>
      </div>
      <div class="sub-card-mid">
        <span class="sub-status-badge" [ngClass]="getStatusBadgeClass()">
          {{ getStatusText() }}
        </span>
        <div *ngIf="subStatus?.current_period_end" class="sub-period">
          {{ subStatus?.cancel_at_period_end ? 'Ends' : 'Renews' }}
          {{ subStatus?.current_period_end | date:'mediumDate' }}
        </div>
        <div *ngIf="subStatus?.cancel_at_period_end" class="sub-cancel-warn">
          ⚠ Subscription scheduled to cancel
          <a routerLink="/subscription" class="cyber-link"> — Reactivate</a>
        </div>
      </div>
      <div class="sub-card-right">
        <a *ngIf="!subStatus?.has_subscription" routerLink="/pricing" class="btn-cyber-solid">
          Upgrade Plan →
        </a>
        <a *ngIf="subStatus?.has_subscription" routerLink="/subscription" class="btn-cyber">
          Manage
        </a>
      </div>
    </div>

    <!-- USAGE + STATS GRID -->
    <div class="stats-grid mt-4">
      <!-- Usage Progress -->
      <div class="cyber-card stat-card usage-card">
        <div class="stat-label">MONTHLY EXECUTIONS</div>
        <div class="usage-numbers">
          <span class="stat-value">{{ usageStats?.total_executions || 0 }}</span>
          <span class="usage-sep">/</span>
          <span class="usage-limit">{{ usageStats?.monthly_limit || 100 }}</span>
        </div>
        <div class="usage-bar-wrap">
          <div class="usage-bar" [style.width]="getUsagePercent() + '%'" [ngClass]="getUsageBarClass()"></div>
        </div>
        <div class="usage-remaining">{{ usageStats?.remaining || 0 }} remaining</div>
      </div>

      <!-- Compute seconds -->
      <div class="cyber-card stat-card">
        <div class="stat-label">COMPUTE SECONDS</div>
        <div class="stat-value">{{ usageStats?.total_compute_seconds | number:'1.0-1' }}s</div>
        <div class="stat-sub">this month</div>
      </div>

      <!-- API executions -->
      <div class="cyber-card stat-card">
        <div class="stat-label">API EXECUTIONS</div>
        <div class="stat-value">{{ usageStats?.api_executions || 0 }}</div>
        <div class="stat-sub">via API key</div>
      </div>
    </div>

    <!-- RECENT PROJECTS -->
    <h2 class="cyber-title mt-4" style="font-size: 1.2rem;">RECENT PROJECTS</h2>
    <div class="cyber-card mt-2">
      <table class="cyber-table" *ngIf="recentProjects.length > 0; else noProjects">
        <thead>
          <tr>
            <th>PROJECT_NAME</th>
            <th>LANGUAGE</th>
            <th>VISIBILITY</th>
            <th>LAST_UPDATED</th>
            <th>ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let project of recentProjects">
            <td>{{ project.name }}</td>
            <td class="text-neon">{{ project.language | uppercase }}</td>
            <td>
              <span class="badge" [class.badge-public]="project.is_public">
                {{ project.is_public ? 'PUBLIC' : 'PRIVATE' }}
              </span>
            </td>
            <td>{{ project.updated_at | date:'short' }}</td>
            <td>
              <button class="btn-cyber btn-sm" [routerLink]="['/editor', project.id]">OPEN</button>
            </td>
          </tr>
        </tbody>
      </table>
      <ng-template #noProjects>
        <div class="text-center" style="padding: 24px; color: var(--cyber-text-dim);">
          NO_PROJECTS_FOUND. <a routerLink="/editor" class="cyber-link">CREATE_NEW</a>
        </div>
      </ng-template>
    </div>
  `,
  styles: [`
    .mt-4 { margin-top: 24px; }
    .mt-2 { margin-top: 12px; }
    .text-center { text-align: center; }

    /* ── Success banner ── */
    .success-banner {
      background: rgba(0, 255, 65, 0.1);
      border: 1px solid var(--cyber-neon, #00ff41);
      border-radius: 8px;
      padding: 12px 20px;
      color: var(--cyber-neon, #00ff41);
      font-weight: 600;
      margin-bottom: 20px;
    }

    /* ── Subscription card ── */
    .sub-card {
      display: flex;
      align-items: center;
      gap: 24px;
      padding: 20px 24px;
      border-radius: 10px;
      border: 2px solid #333;
      background: #1a1a1a;
      margin-bottom: 8px;
      flex-wrap: wrap;
    }
    .sub-card.active  { border-color: var(--cyber-neon, #00ff41); background: rgba(0,255,65,0.04); }
    .sub-card.warning { border-color: #ff9800; background: rgba(255,152,0,0.04); }
    .sub-card.free    { border-color: #444; }

    .sub-card-left { min-width: 100px; }
    .sub-plan-name { font-size: 1.6rem; font-weight: 700; color: #fff; }
    .sub-label { font-size: 0.75rem; color: var(--cyber-text-dim); margin-top: 2px; font-family: var(--font-family-mono); }

    .sub-card-mid { flex: 1; }
    .sub-status-badge {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 12px;
      font-size: 0.75rem;
      font-weight: 700;
      font-family: var(--font-family-mono);
    }
    .badge-active   { background: var(--cyber-neon,#00ff41); color: #000; }
    .badge-trialing { background: #4a90e2; color: #fff; }
    .badge-warning  { background: #ff9800; color: #000; }
    .badge-free     { background: #444; color: #ccc; }
    .sub-period { font-size: 0.85rem; color: var(--cyber-text-dim); margin-top: 6px; }
    .sub-cancel-warn { font-size: 0.85rem; color: #ff9800; margin-top: 4px; }

    .sub-card-right { margin-left: auto; }

    /* ── Stats grid ── */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 20px;
    }
    .stat-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 28px 16px;
      text-align: center;
    }
    .stat-label {
      font-family: var(--font-family-mono);
      font-size: 0.75rem;
      color: var(--cyber-neon);
      margin-bottom: 10px;
      letter-spacing: 1px;
    }
    .stat-value {
      font-size: 2.25rem;
      font-weight: 700;
      color: #fff;
    }
    .stat-sub {
      font-size: 0.8rem;
      color: var(--cyber-text-dim);
      margin-top: 4px;
    }

    /* ── Usage bar ── */
    .usage-card { padding: 24px 20px; }
    .usage-numbers { display: flex; align-items: baseline; gap: 4px; }
    .usage-sep { color: #666; font-size: 1.4rem; }
    .usage-limit { font-size: 1.2rem; color: #888; }
    .usage-bar-wrap {
      width: 100%;
      height: 6px;
      background: #2a2a2a;
      border-radius: 3px;
      margin: 12px 0 6px;
      overflow: hidden;
    }
    .usage-bar {
      height: 100%;
      border-radius: 3px;
      transition: width 0.6s ease;
      background: var(--cyber-neon, #00ff41);
    }
    .usage-bar.warn   { background: #ff9800; }
    .usage-bar.danger { background: #ff4444; }
    .usage-remaining { font-size: 0.8rem; color: var(--cyber-text-dim); }

    /* ── Table ── */
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
    .cyber-table tr:last-child td { border-bottom: none; }
    .cyber-table tbody tr:hover { background-color: rgba(255,255,255,0.02); }
    .text-neon { color: var(--cyber-neon); }
    .badge {
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      border: 1px solid var(--cyber-text-dim);
      color: var(--cyber-text-dim);
    }
    .badge-public { border-color: var(--cyber-accent-info, #4a90e2); color: var(--cyber-accent-info, #4a90e2); }
    .btn-sm { padding: 4px 12px; font-size: 0.8rem; }
    .cyber-link { color: var(--cyber-neon); text-decoration: none; }
    .cyber-link:hover { text-shadow: 0 0 6px var(--cyber-neon); }
  `]
})
export class DashboardComponent implements OnInit {
  private usageService = inject(UsageService);
  private projectService = inject(ProjectService);
  private subscriptionService = inject(SubscriptionService);
  private paymentService = inject(PaymentService);

  usageStats: UsageStats | null = null;
  recentProjects: ProjectSummary[] = [];
  subStatus: SubscriptionStatus | null = null;
  paymentSuccess = false;

  ngOnInit() {
    const params = new URLSearchParams(window.location.search);
    const tracker = params.get('tracker');
    const sig = params.get('sig');

    if (params.get('payment') === 'success' && tracker && sig) {
      // SafePay redirect with signature — verify server-side
      this.paymentService.verifyPayment(tracker, sig).subscribe({
        next: (res) => {
          if (res.success) {
            this.paymentSuccess = true;
            this.loadSubscriptionStatus(); // reload to show active plan
          }
        },
        error: () => { /* silent — show banner anyway */ this.paymentSuccess = true; }
      });
      window.history.replaceState({}, '', '/dashboard');
    } else if (params.get('payment') === 'success') {
      // Fallback without sig (e.g. manual test)
      this.paymentSuccess = true;
      window.history.replaceState({}, '', '/dashboard');
    }

    this.loadUsage();
    this.loadProjects();
    this.loadSubscriptionStatus();
  }

  loadSubscriptionStatus() {
    this.subscriptionService.getSubscriptionStatus().subscribe({
      next: (res) => {
        if (res.success && res.data) this.subStatus = res.data;
      }
    });
  }

  loadUsage() {
    this.usageService.getCurrentUsage().subscribe({
      next: (res: any) => {
        if (res.success && res.data) this.usageStats = res.data;
      }
    });
  }

  loadProjects() {
    this.projectService.getProjects(1, 5).subscribe({
      next: (res: any) => {
        if (res.success && res.data) this.recentProjects = res.data.items;
      }
    });
  }

  getUsagePercent(): number {
    if (!this.usageStats || !this.usageStats.monthly_limit) return 0;
    return Math.min(100, (this.usageStats.total_executions / this.usageStats.monthly_limit) * 100);
  }

  getUsageBarClass(): string {
    const pct = this.getUsagePercent();
    if (pct >= 90) return 'danger';
    if (pct >= 70) return 'warn';
    return '';
  }

  getSubCardClass(): string {
    if (!this.subStatus?.has_subscription) return 'free';
    if (this.subStatus.is_active) return 'active';
    return 'warning';
  }

  getStatusBadgeClass(): string {
    if (!this.subStatus?.has_subscription) return 'badge-free';
    const s = this.subStatus.status;
    if (s === 'active') return 'badge-active';
    if (s === 'trialing') return 'badge-trialing';
    return 'badge-warning';
  }

  getStatusText(): string {
    if (!this.subStatus?.has_subscription) return 'FREE TIER';
    return (this.subStatus.status || 'unknown').toUpperCase();
  }
}
