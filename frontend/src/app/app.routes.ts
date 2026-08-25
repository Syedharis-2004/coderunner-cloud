import { Routes } from '@angular/router';
import { AuthLayoutComponent } from './shared/layouts/auth-layout/auth-layout.component';
import { DashboardLayoutComponent } from './shared/layouts/dashboard-layout/dashboard-layout.component';
import { LoginComponent } from './features/auth/login/login.component';
import { RegisterComponent } from './features/auth/register/register.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { EditorComponent } from './features/editor/editor.component';
import { ProjectsComponent } from './features/projects/projects.component';
import { ApiKeysComponent } from './features/api-keys/api-keys.component';
import { AdminComponent } from './features/admin/admin.component';
import { LandingComponent } from './features/landing/landing.component';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
  {
    path: '',
    component: LandingComponent,
    pathMatch: 'full'
  },
  {
    path: '',
    component: AuthLayoutComponent,
    children: [
      { path: 'login', component: LoginComponent },
      { path: 'register', component: RegisterComponent },
    ]
  },
  {
    path: '',
    component: DashboardLayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: 'dashboard', component: DashboardComponent },
      { path: 'editor', component: EditorComponent },
      { path: 'editor/:id', component: EditorComponent },
      { path: 'projects', component: ProjectsComponent },
      { path: 'api-keys', component: ApiKeysComponent },
      { path: 'admin', component: AdminComponent, canActivate: [adminGuard] },
    ]
  },
  { path: '**', redirectTo: '' }
];
