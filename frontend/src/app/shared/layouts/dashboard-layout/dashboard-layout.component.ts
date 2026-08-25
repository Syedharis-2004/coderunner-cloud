import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavbarComponent } from '../../components/navbar/navbar.component';
import { SidebarComponent } from '../../components/sidebar/sidebar.component';

@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [RouterOutlet, NavbarComponent, SidebarComponent],
  template: `
    <div class="dashboard-wrapper">
      <div class="cyber-scanline"></div>
      
      <app-sidebar class="sidebar"></app-sidebar>
      
      <div class="main-content">
        <app-navbar class="navbar"></app-navbar>
        
        <div class="page-content">
          <router-outlet></router-outlet>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-wrapper {
      display: flex;
      height: 100vh;
      overflow: hidden;
      background-color: var(--cyber-bg);
    }
    .sidebar {
      width: 250px;
      flex-shrink: 0;
      border-right: 1px solid var(--cyber-surface-border);
      background-color: var(--cyber-surface);
      z-index: 10;
    }
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .navbar {
      height: 64px;
      flex-shrink: 0;
      border-bottom: 1px solid var(--cyber-surface-border);
      background-color: var(--cyber-surface);
      z-index: 9;
    }
    .page-content {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      position: relative;
    }
  `]
})
export class DashboardLayoutComponent {

}
