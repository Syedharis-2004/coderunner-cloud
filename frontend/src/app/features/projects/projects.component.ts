import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ProjectService, ProjectSummary } from '../../core/services/project.service';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h1 class="cyber-title">MY_PROJECTS</h1>
      <button class="btn-cyber-solid" routerLink="/editor">NEW_PROJECT</button>
    </div>
    
    <p style="color: var(--cyber-text-dim); margin-bottom: 24px;">
      View and manage your saved code buffers.
    </p>

    <div class="cyber-card">
      <table class="cyber-table">
        <thead>
          <tr>
            <th>PROJECT_NAME</th>
            <th>LANGUAGE</th>
            <th>VISIBILITY</th>
            <th>CREATED</th>
            <th>ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let project of projects">
            <td>{{ project.name }}</td>
            <td style="color: var(--cyber-neon);">{{ project.language | uppercase }}</td>
            <td>
              <span class="badge" [class.badge-public]="project.is_public">
                {{ project.is_public ? 'PUBLIC' : 'PRIVATE' }}
              </span>
            </td>
            <td>{{ project.created_at | date:'medium' }}</td>
            <td>
              <button class="btn-cyber btn-sm" [routerLink]="['/editor', project.id]">OPEN</button>
              <button class="btn-cyber-danger btn-sm" style="margin-left: 8px;" (click)="deleteProject(project.id)">DELETE</button>
            </td>
          </tr>
          <tr *ngIf="projects.length === 0">
            <td colspan="5" style="text-align: center; padding: 24px; color: var(--cyber-text-dim);">
              NO_PROJECTS_FOUND in the database.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [`
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
    .btn-sm { padding: 4px 12px; font-size: 0.8rem; }
  `]
})
export class ProjectsComponent implements OnInit {
  projectService = inject(ProjectService);
  projects: ProjectSummary[] = [];

  ngOnInit() {
    this.loadProjects();
  }

  loadProjects() {
    this.projectService.getProjects(1, 50).subscribe((res: any) => {
      if (res.success && res.data) {
        this.projects = res.data.items;
      }
    });
  }

  deleteProject(id: string) {
    if (confirm('Are you sure you want to delete this project?')) {
      this.projectService.deleteProject(id).subscribe(() => {
        this.loadProjects();
      });
    }
  }
}
