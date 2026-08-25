import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ResponseEnvelope, User } from './auth.service';

export interface SystemMetrics {
  period: string;
  users: { total: number, active: number };
  executions: { total_all_time: number, current_month: number, monthly_compute_seconds: number };
  system: { docker: string };
}

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private apiUrl = `${environment.apiUrl}/admin`;

  constructor(private http: HttpClient) {}

  getMetrics(): Observable<ResponseEnvelope<SystemMetrics>> {
    return this.http.get<ResponseEnvelope<SystemMetrics>>(`${this.apiUrl}/metrics`);
  }

  getUsers(skip: number = 0, limit: number = 50): Observable<ResponseEnvelope<User[]>> {
    let params = new HttpParams().set('skip', skip.toString()).set('limit', limit.toString());
    return this.http.get<ResponseEnvelope<User[]>>(`${this.apiUrl}/users`, { params });
  }

  toggleUserStatus(userId: string, is_active: boolean): Observable<ResponseEnvelope<User>> {
    return this.http.patch<ResponseEnvelope<User>>(`${this.apiUrl}/users/${userId}/status`, null, {
      params: { is_active: is_active.toString() }
    });
  }

  changeUserPlan(userId: string, plan: string): Observable<ResponseEnvelope<User>> {
    return this.http.patch<ResponseEnvelope<User>>(`${this.apiUrl}/users/${userId}/plan`, null, {
      params: { plan }
    });
  }
}
