import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { UsageService, UsageStats } from '../../core/services/usage.service';
import { ProjectService, ProjectSummary } from '../../core/services/project.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <h1 class="cyber-title">DASHBOARD</h1>

    <div class="stats-grid mt-4">
      <div class="cyber-card stat-card">
        <div class="stat-label">TOTAL EXECUTIONS</div>
        <div class="stat-value">{{ usageStats?.total_executions || 0 }}</div>
      </div>
      <div class="cyber-card stat-card">
        <div class="stat-label">COMPUTE SECONDS (MONTH)</div>
        <div class="stat-value">{{ usageStats?.total_compute_seconds | number:'1.0-2' }}s</div>
      </div>
      <div class="cyber-card stat-card">
        <div class="stat-label">API INVOCATIONS</div>
        <div class="stat-value">{{ usageStats?.api_executions || 0 }}</div>
      </div>
    </div>

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
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
    }
    .stat-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 32px 16px;
    }
    .stat-label {
      font-family: var(--font-family-mono);
      font-size: 0.8rem;
      color: var(--cyber-neon);
      margin-bottom: 8px;
    }
    .stat-value {
      font-size: 2.5rem;
      font-weight: 700;
      color: #fff;
      text-shadow: var(--cyber-neon-glow);
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
    .cyber-table tr:last-child td {
      border-bottom: none;
    }
    .cyber-table tbody tr:hover {
      background-color: rgba(255, 255, 255, 0.02);
    }
    .text-neon {
      color: var(--cyber-neon);
    }
    .badge {
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      border: 1px solid var(--cyber-text-dim);
      color: var(--cyber-text-dim);
    }
    .badge-public {
      border-color: var(--cyber-accent-info);
      color: var(--cyber-accent-info);
    }
    .btn-sm {
      padding: 4px 12px;
      font-size: 0.8rem;
    }
    .cyber-link {
      color: var(--cyber-neon);
      text-decoration: none;
    }
    .cyber-link:hover { text-shadow: var(--cyber-neon-glow); }
  `]
})
export class DashboardComponent implements OnInit {
  usageService = inject(UsageService);
  projectService = inject(ProjectService);

  usageStats: UsageStats | null = null;
  recentProjects: ProjectSummary[] = [];

  ngOnInit() {
    this.loadUsage();
    this.loadProjects();
  }

  loadUsage() {
    this.usageService.getCurrentUsage().subscribe((res: any) => {
      if (res.success && res.data) {
        this.usageStats = res.data;
      }
    });
  }

  loadProjects() {
    this.projectService.getProjects(1, 5).subscribe((res: any) => {
      if (res.success && res.data) {
        this.recentProjects = res.data.items;
      }
    });
  }
}
